"""Critical-path unit tests for the ingestion pipeline.

Pure functions only — no network, no live Supabase. The DB client is faked.
Run: PYTHONPATH=scripts pytest tests/ -q   (or just `pytest` from repo root)
"""
import json
from datetime import date, datetime, timedelta, timezone

from ingest_news import (
    calc_buzz,
    clean_title_words,
    get_jaccard_similarity,
    compute_title_hash,
    extract_official_page_entries,
    enrich_item_metadata,
)
from db import extract_entities, check_quota
from llm import ProviderError, generate_llm_content, strip_json_fence
from generate_daily_digest import DIGEST_PROMPT_MAX_CHARS, _build_prompt, _parse_digest_response
from ingest_bluesky import canonicalize_entities, infer_bluesky_category
from run_llm_batch import _chunk_by_char_budget, compute_buzz_v2


# --- 1. buzz calc -----------------------------------------------------------
def test_calc_buzz_scales_and_caps():
    assert calc_buzz(0.0, []) == 0.0
    # 2 entities * 10 + |0.5| * 20 = 30
    assert calc_buzz(0.5, ["A", "B"]) == 30.0
    # caps at 100 even with many entities
    assert calc_buzz(1.0, ["A"] * 50) == 100.0


# --- 2. dedup helpers -------------------------------------------------------
def test_jaccard_and_title_hash_dedup():
    a = clean_title_words("OpenAI Launches New GPT Model Today")
    b = clean_title_words("OpenAI launches a new GPT model today!")
    # stop words / punctuation / case stripped -> near-identical sets
    assert get_jaccard_similarity(a, b) >= 0.4

    # title_hash is order- and case-insensitive after normalization
    h1 = compute_title_hash("OpenAI Launches New GPT Model")
    h2 = compute_title_hash("new gpt model launches openai")
    assert h1 == h2
    # different story -> different hash
    assert compute_title_hash("Apple unveils Vision Pro headset") != h1


# --- 3. entity extraction ---------------------------------------------------
def test_extract_entities_matches_name_and_synonym():
    known = ["OpenAI", "Anthropic", "Google"]
    # canonical name
    assert "OpenAI" in extract_entities("OpenAI ships a new feature", known)
    # synonym ("claude" -> Anthropic) from COMPANY_SYNONYMS
    assert "Anthropic" in extract_entities("I tried claude today", known)
    # no false positive
    assert extract_entities("just a generic headline", known) == []


def test_extract_entities_ambiguous_names_need_context():
    known = ["Modal", "Notion", "Linear", "Unity", "Together AI"]

    assert extract_entities("Researchers propose a tri-modal dynamics benchmark", known) == []
    assert extract_entities("The notion of linear progress created unity among teams", known) == []
    assert extract_entities("Working together improves software quality", known) == []

    assert "Modal" in extract_entities("Modal Labs launches serverless GPU inference platform", known)
    assert "Notion" in extract_entities("Notion AI adds calendar automation for workspaces", known)
    assert "Linear" in extract_entities("Linear launches roadmap tools for engineering teams", known)
    assert "Unity" in extract_entities("Unity game engine update improves runtime performance", known)
    assert "Together AI" in extract_entities("Together AI releases a faster open-model inference API", known)


# --- 4. quota check (fake client) -------------------------------------------
class _FakeQuery:
    def __init__(self, data):
        self._data = data

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def update(self, *a, **k):
        return self

    def execute(self):
        return type("Res", (), {"data": self._data})()


class _FakeClient:
    def __init__(self, data):
        self._data = data

    def table(self, *a, **k):
        return _FakeQuery(self._data)


def test_check_quota_allows_and_blocks():
    today = str(date.today())
    # unknown source (no row) -> allowed
    assert check_quota(_FakeClient([]), "newsource") is True
    # well under limit -> allowed
    ok = _FakeClient([{"calls_today": 10, "daily_limit": 100, "last_reset": today}])
    assert check_quota(ok, "finnhub") is True
    # over 90% -> blocked
    near = _FakeClient([{"calls_today": 95, "daily_limit": 100, "last_reset": today}])
    assert check_quota(near, "finnhub") is False


def test_check_quota_blocks_when_per_minute_budget_is_near_limit():
    now = datetime.now(timezone.utc).isoformat()
    today = str(date.today())
    minute_hot = _FakeClient([{
        "calls_today": 10,
        "daily_limit": 100,
        "calls_this_min": 27,
        "per_min_limit": 30,
        "last_reset": today,
        "last_updated": now,
    }])
    assert check_quota(minute_hot, "groq", 1) is False


def test_check_quota_resets_minute_bucket_after_cooldown():
    cooled_down = (datetime.now(timezone.utc) - timedelta(seconds=70)).isoformat()
    today = str(date.today())
    recovered = _FakeClient([{
        "calls_today": 10,
        "daily_limit": 100,
        "calls_this_min": 29,
        "per_min_limit": 30,
        "last_reset": today,
        "last_updated": cooled_down,
    }])
    assert check_quota(recovered, "groq", 1) is True


# --- 5. LLM JSON fence parsing ----------------------------------------------
def test_strip_json_fence_variants():
    payload = '[{"a": 1}]'
    assert json.loads(strip_json_fence(f"```json\n{payload}\n```")) == [{"a": 1}]
    assert json.loads(strip_json_fence(f"```\n{payload}\n```")) == [{"a": 1}]
    assert json.loads(strip_json_fence(payload)) == [{"a": 1}]
    assert strip_json_fence("") == ""
    assert strip_json_fence(None) == ""


def test_parse_digest_response_accepts_embedded_json_after_prose():
    payload = (
        "Today's tech-investor digest\n\n"
        "The market narrative was mixed today.\n\n"
        '{"summary":"The market narrative was mixed today.","top_tickers":["NVDA","MSFT"]}'
    )
    parsed = _parse_digest_response(payload)
    assert parsed["summary"] == "The market narrative was mixed today."
    assert parsed["top_tickers"] == ["NVDA", "MSFT"]


def test_bluesky_entity_canonicalization_and_category_inference():
    assert canonicalize_entities(["Claude", "gemini", "OpenAI"]) == ["Anthropic", "Google", "OpenAI"]
    assert infer_bluesky_category("OpenAI announced a new model rollout for coding agents") == "release"
    assert infer_bluesky_category("Microsoft posts strong earnings and raises guidance") == "earnings"
    assert infer_bluesky_category("A broad discussion about startup hiring and strategy") == "other"


def test_generate_llm_content_retries_primary_before_fallback(monkeypatch):
    calls = []

    monkeypatch.setattr("llm._resolve_chain", lambda: ["groq", "gemini"])
    monkeypatch.setattr("llm._provider_has_key", lambda provider: True)
    monkeypatch.setattr("llm.check_quota", lambda sb, provider, cost=1: True)

    def fake_call(provider, prompt, sb, max_tokens=None):
        calls.append(provider)
        if provider == "groq" and len(calls) < 3:
            raise ProviderError("rate limited", provider=provider, retryable=True, fallback_allowed=True)
        return f"{provider}:ok"

    monkeypatch.setattr("llm._call_provider", fake_call)

    assert generate_llm_content("prompt", object()) == "groq:ok"
    assert calls == ["groq", "groq", "groq"]


def test_chunk_by_char_budget_splits_large_batches():
    items = [
        {"id": 1, "title": "A" * 80},
        {"id": 2, "title": "B" * 80},
        {"id": 3, "title": "C" * 80},
    ]

    chunks = list(
        _chunk_by_char_budget(
            items,
            base_prompt="HEADER\n",
            render_item=lambda item, idx: f"Item {idx}: {item['title']}\n",
            max_chars=140,
            max_items=10,
        )
    )

    assert len(chunks) == 3
    assert chunks[0][0][0]["id"] == 1
    assert all(len(prompt) <= 140 for _, prompt in chunks)


def test_build_digest_prompt_respects_budget():
    long_item = {
        "title": "Launch " * 40,
        "summary": "Summary " * 40,
        "entity_names": ["OpenAI", "Google", "NVIDIA"],
        "source": "test",
        "source_type": "news",
        "category": "release",
        "buzz_v2": 99,
        "sentiment": 0.4,
        "published_at": "2026-07-01T00:00:00+00:00",
    }
    signals = {
        "news": [long_item for _ in range(30)],
        "controversy": [long_item for _ in range(20)],
        "release": [long_item for _ in range(20)],
        "research": [long_item for _ in range(20)],
        "conference": [long_item for _ in range(20)],
        "community": [{
            "source": "reddit",
            "entity_name": "OpenAI",
            "post_title": "Post " * 30,
            "post_url": "https://example.com",
            "post_score": 10,
            "comment_count": 5,
            "sentiment": 0.1,
            "captured_at": "2026-07-01T00:00:00+00:00",
        } for _ in range(20)],
        "insider": [],
        "sec": [],
        "upcoming_earn": [],
        "recent_earn": [],
        "dark_horse": [],
    }

    prompt = _build_prompt(signals)
    assert len(prompt) <= DIGEST_PROMPT_MAX_CHARS
    assert "Today's tech-investor digest" in prompt


def test_extract_official_page_entries_pulls_story_links_from_company_news_page():
    html = """
    <html><body>
      <a href="/news/introducing-claude-sonnet-5">Introducing Claude Sonnet 5</a>
      <a href="/news/claude-science-now-available">Claude Science, an AI workbench for scientists, is now available</a>
      <a href="/about">About</a>
      <a href="/news">News</a>
    </body></html>
    """

    entries = extract_official_page_entries(html, "https://www.anthropic.com/news", "Anthropic")

    assert len(entries) == 2
    assert entries[0]["title"] == "Introducing Claude Sonnet 5"
    assert entries[0]["url"] == "https://www.anthropic.com/news/introducing-claude-sonnet-5"
    assert all(entry["source"] == "Anthropic" for entry in entries)


def test_enrich_item_metadata_marks_major_official_release():
    item = enrich_item_metadata({
        'title': 'Introducing Claude Sonnet 5',
        'url': 'https://www.anthropic.com/news/introducing-claude-sonnet-5',
        'source': 'Anthropic',
        'source_type': 'official_company',
        'source_credibility_tier': 1,
        'entity_names': ['Anthropic'],
        'category': 'release',
    }, official_company='Anthropic')

    assert item['source_domain'] == 'anthropic.com'
    assert item['source_region'] == 'US'
    assert item['source_priority'] == 1
    assert item['entity_tier_max'] == 1
    assert item['is_major_release'] is True


def test_compute_buzz_v2_boosts_major_official_release():
    base_item = {
        'source_credibility_tier': 1,
        'hn_score': 0,
        'hn_comments': 0,
        'published_at': datetime.now(timezone.utc).isoformat(),
        'entity_names': ['Anthropic'],
        'source_priority': 1,
        'category': 'release',
    }
    normal = compute_buzz_v2(dict(base_item, source_type='news', is_major_release=False), 35)
    official = compute_buzz_v2(dict(base_item, source_type='official_company', is_major_release=True), 35)
    assert official > normal
