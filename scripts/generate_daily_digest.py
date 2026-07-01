"""Phase 3.7: daily investor digest.

Once per day, synthesize the last-24h signal stream into a 1-paragraph
"what an investor should know today" via the LLM, plus a top-tickers list.
Persisted to `daily_digests` (PK = UTC date) and surfaced by
`DailyDigestBanner.jsx` at the top of the dashboard.

Signals fed into the prompt:
  - Top 20 news_items by buzz_v2 (last 24h)
  - Notable insider transactions (|change| >= 10K shares, last 24h)
  - SEC 8-K filings (source='sec_edgar', last 24h)
  - Upcoming earnings (next 7d) + recent earnings (last 7d) with sentiment_delta

Idempotent: UPSERT by digest_date — re-running on the same UTC day overwrites.
"""
import logging
import json
from datetime import datetime, timedelta, timezone, date
from collections import Counter

from db import get_client, record_health
from llm import generate_llm_content, strip_json_fence, has_llm_capacity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEWS_LIMIT = 40
INSIDER_THRESHOLD = 10_000
DIGEST_PROMPT_MAX_CHARS = 12000
SECTION_ITEM_LIMIT = 8
LINE_ITEM_MAX_CHARS = 220


def _fetch_signals(sb):
    """Returns dict of signal arrays for the last 24h window."""
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=24)).isoformat()
    week_ahead = (now + timedelta(days=7)).date().isoformat()
    week_back = (now - timedelta(days=7)).date().isoformat()
    today = now.date().isoformat()

    # Broad news slice: keep the top feed plus category-specific slices so the
    # digest is not dominated by one source family.
    news_res = (
        sb.table('news_items')
          .select('title, summary, entity_names, source, source_type, category, buzz_v2, sentiment, published_at')
          .gte('ingested_at', since)
          .not_.is_('buzz_v2', None)
          .order('buzz_v2', desc=True)
          .limit(NEWS_LIMIT)
          .execute()
    )

    controversy_res = (
        sb.table('news_items')
          .select('title, summary, entity_names, source, source_type, category, buzz_v2, sentiment, published_at')
          .gte('ingested_at', since)
          .in_('category', ['controversy', 'ma', 'earnings'])
          .order('ingested_at', desc=True)
          .limit(12)
          .execute()
    )

    release_res = (
        sb.table('news_items')
          .select('title, summary, entity_names, source, source_type, category, buzz_v2, sentiment, published_at')
          .gte('ingested_at', since)
          .in_('category', ['release', 'ai', 'opensource'])
          .order('buzz_v2', desc=True)
          .limit(12)
          .execute()
    )

    research_res = (
        sb.table('news_items')
          .select('title, summary, entity_names, source, source_type, category, buzz_v2, sentiment, published_at')
          .gte('ingested_at', since)
          .eq('category', 'research')
          .order('buzz_v2', desc=True)
          .limit(12)
          .execute()
    )

    conference_res = (
        sb.table('news_items')
          .select('title, summary, entity_names, source, source_type, category, buzz_v2, sentiment, published_at')
          .gte('ingested_at', since)
          .in_('category', ['conference', 'ipo'])
          .order('ingested_at', desc=True)
          .limit(12)
          .execute()
    )

    community_res = (
        sb.table('community_signals')
          .select('source, entity_name, post_title, post_url, post_score, comment_count, sentiment, captured_at')
          .gte('captured_at', since)
          .order('captured_at', desc=True)
          .limit(20)
          .execute()
    )

    dark_horse_res = (
        sb.table('dark_horse_movers')
          .select('rank, score, reasons, components, companies(name, ticker)')
          .limit(10)
          .execute()
    )

    # Insider trades.
    ins_res = (
        sb.table('insider_transactions')
          .select('person, position, change, transaction_type, transaction_date, companies(name, ticker)')
          .gte('transaction_date', (now - timedelta(days=1)).date().isoformat())
          .order('transaction_date', desc=True)
          .limit(50)
          .execute()
    )
    insider = [r for r in (ins_res.data or []) if abs(r.get('change') or 0) >= INSIDER_THRESHOLD]

    # SEC 8-Ks already live in news_items (source='sec_edgar') — filtered subset:
    sec_res = (
        sb.table('news_items')
          .select('title, entity_names, published_at')
          .eq('source', 'sec_edgar')
          .gte('ingested_at', since)
          .order('ingested_at', desc=True)
          .limit(15)
          .execute()
    )

    # Earnings — upcoming + recently reported with sentiment delta.
    up_res = (
        sb.table('earnings_calendar')
          .select('earnings_date, hour, companies(name, ticker)')
          .gte('earnings_date', today)
          .lte('earnings_date', week_ahead)
          .order('earnings_date')
          .limit(15)
          .execute()
    )
    rec_res = (
        sb.table('earnings_calendar')
          .select('earnings_date, eps_actual, eps_estimate, sentiment_delta, companies(name, ticker)')
          .gte('earnings_date', week_back)
          .lt('earnings_date', today)
          .order('earnings_date', desc=True)
          .limit(15)
          .execute()
    )

    return {
        'news': news_res.data or [],
        'controversy': controversy_res.data or [],
        'release': release_res.data or [],
        'research': research_res.data or [],
        'conference': conference_res.data or [],
        'community': community_res.data or [],
        'insider': insider,
        'sec': sec_res.data or [],
        'upcoming_earn': up_res.data or [],
        'recent_earn': rec_res.data or [],
        'dark_horse': dark_horse_res.data or [],
    }


def _clip_text(value: str, limit: int = LINE_ITEM_MAX_CHARS) -> str:
    text = (value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _append_line_with_budget(lines, line, budget=DIGEST_PROMPT_MAX_CHARS):
    trial = "\n".join(lines + [line])
    if len(trial) > budget:
        return False
    lines.append(line)
    return True


def _build_prompt(signals: dict) -> str:
    lines = [
        "You are a senior tech investor analyst.",
        "Synthesize the following last-24h signals into ONE concise paragraph (5-8 sentences) titled \"Today's tech-investor digest\".",
        "Focus: what changed, what matters, who's moving, what to watch next, and where the signal is concentrated.",
        "Do NOT make up numbers. Reference only the signals shown.",
        "After the paragraph, return strict JSON with this shape:",
        '{"summary":"...the paragraph...","top_tickers":["NVDA","MSFT",...]}',
        "Return ONLY the JSON object — no markdown fences, no preamble.\n",
        "=== TOP NEWS (last 24h, ranked by buzz_v2) ===",
    ]
    for n in signals['news'][:SECTION_ITEM_LIMIT]:
        cat = n.get('category') or '?'
        ents = ','.join((n.get('entity_names') or [])[:3])
        if not _append_line_with_budget(
            lines,
            f"- [{cat}] {_clip_text(n['title'])} (entities: {ents}; buzz_v2={n.get('buzz_v2')})",
        ):
            return "\n".join(lines)

    if signals['sec']:
        if not _append_line_with_budget(lines, "\n=== SEC 8-K MATERIAL EVENTS (last 24h) ==="):
            return "\n".join(lines)
        for s in signals['sec'][:SECTION_ITEM_LIMIT]:
            ents = ','.join((s.get('entity_names') or [])[:2])
            if not _append_line_with_budget(lines, f"- {_clip_text(s['title'])} (entities: {ents})"):
                return "\n".join(lines)

    if signals['controversy']:
        if not _append_line_with_budget(lines, "\n=== CONTROVERSIES / M&A / EARNINGS PRESSURE ==="):
            return "\n".join(lines)
        for n in signals['controversy'][:SECTION_ITEM_LIMIT]:
            ents = ','.join((n.get('entity_names') or [])[:3])
            if not _append_line_with_budget(
                lines,
                f"- [{n.get('category') or '?'}] {_clip_text(n['title'])} (entities: {ents}; buzz_v2={n.get('buzz_v2')})",
            ):
                return "\n".join(lines)

    if signals['release']:
        if not _append_line_with_budget(lines, "\n=== RELEASES / AI / OPEN SOURCE ==="):
            return "\n".join(lines)
        for n in signals['release'][:SECTION_ITEM_LIMIT]:
            ents = ','.join((n.get('entity_names') or [])[:3])
            if not _append_line_with_budget(
                lines,
                f"- [{n.get('category') or '?'}] {_clip_text(n['title'])} (entities: {ents}; buzz_v2={n.get('buzz_v2')})",
            ):
                return "\n".join(lines)

    if signals['research']:
        if not _append_line_with_budget(lines, "\n=== RESEARCH / PAPERS ==="):
            return "\n".join(lines)
        for n in signals['research'][:SECTION_ITEM_LIMIT]:
            ents = ','.join((n.get('entity_names') or [])[:3])
            if not _append_line_with_budget(
                lines,
                f"- [{n.get('category') or '?'}] {_clip_text(n['title'])} (entities: {ents}; buzz_v2={n.get('buzz_v2')})",
            ):
                return "\n".join(lines)

    if signals['conference']:
        if not _append_line_with_budget(lines, "\n=== CONFERENCES / IPOS ==="):
            return "\n".join(lines)
        for n in signals['conference'][:SECTION_ITEM_LIMIT]:
            ents = ','.join((n.get('entity_names') or [])[:3])
            if not _append_line_with_budget(
                lines,
                f"- [{n.get('category') or '?'}] {_clip_text(n['title'])} (entities: {ents}; buzz_v2={n.get('buzz_v2')})",
            ):
                return "\n".join(lines)

    if signals['community']:
        if not _append_line_with_budget(lines, "\n=== COMMUNITY SIGNALS (Reddit / Hacker News) ==="):
            return "\n".join(lines)
        for c in signals['community'][:SECTION_ITEM_LIMIT]:
            if not _append_line_with_budget(
                lines,
                f"- {c.get('source') or '?'} · {c.get('post_title') or '?'} "
                f"(entity: {c.get('entity_name') or '?'}; sentiment={c.get('sentiment')})",
            ):
                return "\n".join(lines)

    if signals['dark_horse']:
        if not _append_line_with_budget(lines, "\n=== DARK-HORSE MOVERS ==="):
            return "\n".join(lines)
        for d in signals['dark_horse'][:SECTION_ITEM_LIMIT]:
            co = d.get('companies') or {}
            if not _append_line_with_budget(
                lines,
                f"- #{d.get('rank')} {co.get('ticker') or co.get('name') or '?'} "
                f"score={d.get('score')} reasons={', '.join(d.get('reasons') or [])}",
            ):
                return "\n".join(lines)

    if signals['insider']:
        if not _append_line_with_budget(lines, "\n=== NOTABLE INSIDER TRADES (last 24h, >=10K shares) ==="):
            return "\n".join(lines)
        for i in signals['insider'][:SECTION_ITEM_LIMIT]:
            co = i.get('companies') or {}
            sign = '+' if (i.get('change') or 0) > 0 else ''
            if not _append_line_with_budget(
                lines,
                f"- {co.get('ticker','?')} · {i.get('person','?')} ({i.get('position','?')}) "
                f"{sign}{i.get('change')} shares · {i.get('transaction_type','')}",
            ):
                return "\n".join(lines)

    if signals['upcoming_earn']:
        if not _append_line_with_budget(lines, "\n=== UPCOMING EARNINGS (next 7d) ==="):
            return "\n".join(lines)
        for e in signals['upcoming_earn'][:SECTION_ITEM_LIMIT]:
            co = e.get('companies') or {}
            if not _append_line_with_budget(lines, f"- {co.get('ticker','?')} {e.get('earnings_date')} {e.get('hour') or ''}"):
                return "\n".join(lines)

    if signals['recent_earn']:
        if not _append_line_with_budget(lines, "\n=== RECENT EARNINGS (last 7d) ==="):
            return "\n".join(lines)
        for e in signals['recent_earn'][:SECTION_ITEM_LIMIT]:
            co = e.get('companies') or {}
            beat = ''
            if e.get('eps_actual') is not None and e.get('eps_estimate') is not None:
                d = float(e['eps_actual']) - float(e['eps_estimate'])
                beat = f" (EPS {'beat' if d >= 0 else 'miss'} {abs(d):.2f})"
            sd = e.get('sentiment_delta')
            sd_str = f" sentiment Δ {sd:+.2f}" if sd is not None else ''
            if not _append_line_with_budget(lines, f"- {co.get('ticker','?')} {e.get('earnings_date')}{beat}{sd_str}"):
                return "\n".join(lines)

    return "\n".join(lines)


def _fallback_tickers(signals: dict):
    """If LLM doesn't return tickers, derive top tickers from signal frequency."""
    counter = Counter()
    for n in signals['news']:
        for e in (n.get('entity_names') or [])[:3]:
            counter[e] += 1
    for s in signals['sec']:
        for e in (s.get('entity_names') or [])[:2]:
            counter[e] += 1
    return [t for t, _ in counter.most_common(6)]


def _parse_digest_response(text: str) -> dict:
    """Parse strict JSON, fenced JSON, or a JSON object embedded after prose."""
    cleaned = strip_json_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for idx, ch in enumerate(cleaned):
            if ch != '{':
                continue
            try:
                obj, _ = decoder.raw_decode(cleaned[idx:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
        raise


def main():
    try:
        sb = get_client()
    except Exception as e:
        logger.warning(f"Supabase unavailable — skipping digest: {e}")
        return {'status': 'partial', 'detail': f'Supabase unavailable; digest skipped: {e}'[:500]}

    if not has_llm_capacity(sb, 1):
        logger.warning("LLM quota exhausted — skipping digest.")
        return {'status': 'partial', 'detail': 'LLM quota exhausted; digest skipped.'}

    signals = _fetch_signals(sb)
    source_count = (len(signals['news']) + len(signals['insider'])
                    + len(signals['sec']) + len(signals['upcoming_earn'])
                    + len(signals['recent_earn']) + len(signals['controversy'])
                    + len(signals['release']) + len(signals['research']) + len(signals['conference'])
                    + len(signals['community']) + len(signals['dark_horse']))
    if source_count == 0:
        logger.warning("No signals in last 24h — skipping digest.")
        return {'status': 'partial', 'detail': 'No signals found in the last 24h; digest skipped.'}

    prompt = _build_prompt(signals)
    result = {'status': 'ok', 'detail': None}
    try:
        text = generate_llm_content(prompt, sb)
        parsed = _parse_digest_response(text)
        summary = (parsed.get('summary') or '').strip()
        top = parsed.get('top_tickers') or _fallback_tickers(signals)
    except Exception as e:
        logger.warning(f"LLM parse failed ({e}) — saving prompt-only fallback.")
        summary = "Digest unavailable (LLM error). Top movers by signal frequency below."
        top = _fallback_tickers(signals)
        result = {'status': 'partial', 'detail': f'LLM digest fallback used: {e}'[:500]}

    today = datetime.now(timezone.utc).date().isoformat()
    sb.table('daily_digests').upsert({
        'digest_date': today,
        'summary': summary,
        'top_tickers': top[:8],
        'source_count': source_count,
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }, on_conflict='digest_date').execute()
    logger.info(f"Digest written for {today}: {source_count} signals, top_tickers={top[:8]}")
    return result


if __name__ == '__main__':
    try:
        result = main() or {'status': 'ok', 'detail': None}
        try:
            record_health(get_client(), 'generate_daily_digest', result['status'], result.get('detail'))
        except Exception as e:
            logger.warning(f"Could not record digest health: {e}")
    except Exception as e:
        try:
            record_health(get_client(), 'generate_daily_digest', 'error', str(e))
        except Exception as record_err:
            logger.warning(f"Could not record digest error health: {record_err}")
        raise
