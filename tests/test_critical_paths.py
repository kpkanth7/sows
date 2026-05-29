"""Critical-path unit tests for the ingestion pipeline.

Pure functions only — no network, no live Supabase. The DB client is faked.
Run: PYTHONPATH=scripts pytest tests/ -q   (or just `pytest` from repo root)
"""
import json

from ingest_news import (
    calc_buzz,
    clean_title_words,
    get_jaccard_similarity,
    compute_title_hash,
)
from db import extract_entities, check_quota
from llm import strip_json_fence


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
    from datetime import date
    today = str(date.today())
    # unknown source (no row) -> allowed
    assert check_quota(_FakeClient([]), "newsource") is True
    # well under limit -> allowed
    ok = _FakeClient([{"calls_today": 10, "daily_limit": 100, "last_reset": today}])
    assert check_quota(ok, "finnhub") is True
    # over 90% -> blocked
    near = _FakeClient([{"calls_today": 95, "daily_limit": 100, "last_reset": today}])
    assert check_quota(near, "finnhub") is False


# --- 5. LLM JSON fence parsing ----------------------------------------------
def test_strip_json_fence_variants():
    payload = '[{"a": 1}]'
    assert json.loads(strip_json_fence(f"```json\n{payload}\n```")) == [{"a": 1}]
    assert json.loads(strip_json_fence(f"```\n{payload}\n```")) == [{"a": 1}]
    assert json.loads(strip_json_fence(payload)) == [{"a": 1}]
    assert strip_json_fence("") == ""
    assert strip_json_fence(None) == ""
