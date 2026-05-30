"""Phase 3.2: post-earnings sentiment delta backfill.

For each earnings_calendar row whose post-window has closed (T+7d <= today)
and where sentiment_delta is still NULL, compute:

    sentiment_pre  = AVG(news_items.sentiment) for the company over [T-7d, T-1d]
    sentiment_post = AVG(news_items.sentiment) for the company over [T+1d, T+7d]
    sentiment_delta = sentiment_post - sentiment_pre

We match news to a company via the JSONB `entity_names` containment check (same
mechanism the InvestorHub already uses). Rows with zero news in either window
are skipped (cannot compute a meaningful delta).

Designed to be idempotent + safe to re-run daily.
"""
import logging
from datetime import date, timedelta, datetime, timezone

from db import get_client, record_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Past window (days each side of earnings date).
WINDOW_DAYS = 7


def _avg_sentiment(sb, company_name: str, start: date, end: date):
    """Mean sentiment of news_items mentioning `company_name` in [start, end]."""
    res = (
        sb.table('news_items')
          .select('sentiment')
          .contains('entity_names', [company_name])
          .gte('ingested_at', start.isoformat())
          .lte('ingested_at', (end + timedelta(days=1)).isoformat())
          .execute()
    )
    vals = [r['sentiment'] for r in (res.data or []) if r.get('sentiment') is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def main():
    sb = get_client()
    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=WINDOW_DAYS)  # T+7 must already be in the past

    # Only rows whose post-window has fully closed AND don't yet have a delta.
    res = (
        sb.table('earnings_calendar')
          .select('id, company_id, earnings_date')
          .lte('earnings_date', cutoff.isoformat())
          .is_('sentiment_delta', None)
          .order('earnings_date', desc=True)
          .limit(200)
          .execute()
    )
    rows = res.data or []
    logger.info(f"earnings_delta: {len(rows)} rows to compute")

    updated = 0
    skipped = 0
    for row in rows:
        comp_res = sb.table('companies').select('name').eq('id', row['company_id']).execute()
        if not comp_res.data:
            skipped += 1
            continue
        name = comp_res.data[0]['name']
        e_date = date.fromisoformat(row['earnings_date'])
        pre = _avg_sentiment(sb, name, e_date - timedelta(days=WINDOW_DAYS), e_date - timedelta(days=1))
        post = _avg_sentiment(sb, name, e_date + timedelta(days=1), e_date + timedelta(days=WINDOW_DAYS))
        if pre is None or post is None:
            skipped += 1
            continue
        delta = round(post - pre, 4)
        sb.table('earnings_calendar').update({
            'sentiment_pre': round(pre, 4),
            'sentiment_post': round(post, 4),
            'sentiment_delta': delta,
        }).eq('id', row['id']).execute()
        updated += 1

    logger.info(f"earnings_delta: updated={updated} skipped={skipped}")


if __name__ == '__main__':
    try:
        main()
        record_health(get_client(), 'compute_earnings_delta', 'ok')
    except Exception as e:
        record_health(get_client(), 'compute_earnings_delta', 'error', str(e))
        raise
