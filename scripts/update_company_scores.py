import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from companies_config import TIER1_NAMES, TIER2_NAMES
from db import get_client, record_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FORECAST_RISK = {
    'strong_bullish': 10,
    'bullish': 20,
    'neutral': 40,
    'bearish': 68,
    'high_risk': 85,
}


def clamp(value, floor=0.0, ceil=100.0):
    return max(floor, min(ceil, float(value)))


def average(values):
    return sum(values) / len(values) if values else 0.0


def get_company_rows(sb):
    return (
        sb.table('companies')
        .select('id, name, ticker, is_private, sentiment_score, buzz_score, controversy_score, forecast_direction, forecast_confidence')
        .execute()
        .data
        or []
    )


def news_buckets(sb, since_iso):
    rows = (
        sb.table('news_items')
        .select('entity_names, sentiment, buzz_v2, buzz_score, category, is_major_release, source_priority, published_at, ingested_at')
        .gte('ingested_at', since_iso)
        .limit(10000)
        .execute()
        .data
        or []
    )
    buckets = defaultdict(list)
    for row in rows:
        for entity in (row.get('entity_names') or []):
            buckets[entity].append(row)
    return buckets


def community_buckets(sb, since_iso):
    rows = (
        sb.table('community_signals')
        .select('entity_name, post_score, comment_count, sentiment')
        .gte('captured_at', since_iso)
        .limit(5000)
        .execute()
        .data
        or []
    )
    buckets = defaultdict(list)
    for row in rows:
        if row.get('entity_name'):
            buckets[row['entity_name']].append(row)
    return buckets


def influencer_buckets(sb, since_iso):
    rows = (
        sb.table('influencer_signals')
        .select('entity_name, engagement_score')
        .gte('published_at', since_iso)
        .limit(5000)
        .execute()
        .data
        or []
    )
    buckets = defaultdict(list)
    for row in rows:
        if row.get('entity_name'):
            buckets[row['entity_name']].append(row)
    return buckets


def event_buckets(sb, today_iso, future_iso):
    rows = (
        sb.table('events_calendar')
        .select('company_ids, company_names, event_name, event_date, event_type, source_priority, confidence, is_official')
        .gte('event_date', today_iso)
        .lte('event_date', future_iso)
        .order('event_date')
        .limit(1000)
        .execute()
        .data
        or []
    )
    by_id = defaultdict(list)
    by_name = defaultdict(list)
    for row in rows:
        for company_id in (row.get('company_ids') or []):
            by_id[company_id].append(row)
        for name in (row.get('company_names') or []):
            by_name[name].append(row)
    return by_id, by_name


def _event_score(event):
    if not event:
        return 0.0
    try:
        days = max(0, (datetime.fromisoformat(event['event_date']) - datetime.now()).days)
    except Exception:
        days = 30
    urgency = max(0, 50 - min(days, 25) * 2)
    priority = 12 if int(event.get('source_priority') or 3) == 1 else 6
    confidence = float(event.get('confidence') or 75) * 0.2
    return urgency + priority + confidence


def main():
    sb = get_client()
    now = datetime.now(timezone.utc)
    news_since = (now - timedelta(days=7)).isoformat()
    signal_since = (now - timedelta(days=14)).isoformat()
    today_iso = now.date().isoformat()
    future_iso = (now + timedelta(days=45)).date().isoformat()

    companies = get_company_rows(sb)
    news = news_buckets(sb, news_since)
    community = community_buckets(sb, signal_since)
    influencers = influencer_buckets(sb, signal_since)
    events_by_id, events_by_name = event_buckets(sb, today_iso, future_iso)

    updates = []
    for company in companies:
        name = company['name']
        rows = news.get(name, [])
        comm = community.get(name, [])
        infl = influencers.get(name, [])
        event_rows = events_by_id.get(company['id']) or events_by_name.get(name) or []
        next_event = event_rows[0] if event_rows else None

        sentiments = [float(row['sentiment']) for row in rows if row.get('sentiment') is not None]
        buzzes = [float(row.get('buzz_v2') or row.get('buzz_score') or 0) for row in rows]
        controversy_hits = sum(1 for row in rows if row.get('category') == 'controversy')
        major_release_hits = sum(1 for row in rows if row.get('is_major_release'))
        official_hits = sum(1 for row in rows if int(row.get('source_priority') or 3) == 1)
        comm_engagement = sum((row.get('post_score') or 0) + (row.get('comment_count') or 0) for row in comm)
        infl_engagement = sum(float(row.get('engagement_score') or 0) for row in infl)

        sentiment_score = clamp(50 + average(sentiments) * 45)
        buzz_score = clamp(
            average(buzzes) * 0.7 +
            min(len(rows) * 5, 25) +
            min(comm_engagement / 40, 12) +
            min(infl_engagement / 5000, 10)
        )
        controversy_score = clamp(controversy_hits * 22 + max(0, 30 - sentiment_score * 0.3))
        catalyst_score = clamp(_event_score(next_event) + major_release_hits * 12 + official_hits * 4)
        forecast_conf = float(company.get('forecast_confidence') or 0)
        tier_boost = 8 if name in TIER1_NAMES else 4 if name in TIER2_NAMES else 0
        momentum_score = clamp(
            buzz_score * 0.45 +
            max(0, sentiment_score - 50) * 0.45 +
            catalyst_score * 0.35 +
            major_release_hits * 8 +
            tier_boost +
            forecast_conf * 0.15
        )
        risk_score = clamp(
            controversy_score * 0.55 +
            max(0, 50 - sentiment_score) * 0.55 +
            FORECAST_RISK.get(company.get('forecast_direction'), 40) * 0.35
        )

        updates.append({
            'id': company['id'],
            'sentiment_score': round(sentiment_score, 2),
            'buzz_score': round(buzz_score, 2),
            'controversy_score': round(controversy_score, 2),
            'momentum_score': round(momentum_score, 2),
            'risk_score': round(risk_score, 2),
            'catalyst_score': round(catalyst_score, 2),
            'recent_event': next_event.get('event_type') if next_event else None,
            'recent_event_date': next_event.get('event_date') if next_event else None,
            'last_updated': now.isoformat(),
        })

    for row in updates:
        company_id = row['id']
        payload = dict(row)
        payload.pop('id', None)
        sb.table('companies').update(payload).eq('id', company_id).execute()

    logger.info(f"updated company scores for {len(updates)} companies")


if __name__ == '__main__':
    try:
        main()
        record_health(get_client(), 'update_company_scores', 'ok')
    except Exception as e:
        record_health(get_client(), 'update_company_scores', 'error', str(e))
        raise
