"""Phase 3.5: CourtListener (Free Law Project) controversy tracker.

Free API. Token signup at https://www.courtlistener.com/api/ (recommended;
unauth quota is ~100/day, token quota ~5000/hr). We poll the RECAP/docket
search endpoint per tracked public company, filter for recent filings, and
write hits into `news_items` as:
    source='courtlistener', source_type='news',
    source_credibility_tier=1 (court doc = official),
    category='controversy'

This makes the rows surface in the existing News & Signals "Controversy" pill
plus the global feed with no new UI work — same dedup pipeline as everything
else.

Docs: https://www.courtlistener.com/help/api/rest/
"""
import os
import time
import logging
from datetime import datetime, timedelta, timezone
import httpx
from textblob import TextBlob
from db import get_client, record_health
from companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES
from ingest_news import save_news, calc_buzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://www.courtlistener.com/api/rest/v4/search/"
LOOKBACK_DAYS = 7
PER_COMPANY_LIMIT = 5
REQ_SLEEP = 0.4  # ~150 req/min safely under the 5000/hr token cap


def _public_tracked():
    """Iterate only public tracked cos to keep the query loop small.

    NOTE: `ALL_COMPANIES` from companies_config is a flat list of NAME STRINGS
    (used elsewhere for fast entity matching). We need the original dicts to
    filter by ticker, so we walk the tier lists directly.
    """
    for c in TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES:
        if c.get('ticker') and c.get('name'):
            yield c


def main():
    sb = get_client()
    token = os.environ.get('COURTLISTENER_API_TOKEN', '').strip()
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    else:
        logger.warning("COURTLISTENER_API_TOKEN not set — using unauth (low quota).")

    since = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).date().isoformat()
    saved = 0
    queried = 0
    for comp in _public_tracked():
        name = comp['name']
        params = {
            'q': f'"{name}"',
            'type': 'r',                 # RECAP / dockets
            'filed_after': since,
            'order_by': 'dateFiled desc',
        }
        try:
            resp = httpx.get(API_BASE, params=params, headers=headers, timeout=20)
            if resp.status_code == 429:
                logger.warning("CourtListener 429 — backing off 30s")
                time.sleep(30)
                continue
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"CourtListener fetch error for {name}: {e}")
            continue
        queried += 1
        results = (resp.json() or {}).get('results', []) or []
        for r in results[:PER_COMPANY_LIMIT]:
            case_name = r.get('caseName') or r.get('case_name')
            if not case_name:
                continue
            url = r.get('absolute_url') or r.get('docket_absolute_url')
            if url and url.startswith('/'):
                url = f"https://www.courtlistener.com{url}"
            if not url:
                continue
            date_filed = r.get('dateFiled') or r.get('date_filed')
            court = r.get('court') or r.get('court_id') or ''
            title = f"{case_name} ({court})" if court else case_name
            sentiment = TextBlob(case_name).sentiment.polarity
            save_news(sb, {
                'title': title,
                'url': url,
                'source': 'courtlistener',
                'source_type': 'news',
                'source_credibility_tier': 1,
                'category': 'controversy',
                'entity_names': [name],
                'sentiment': sentiment,
                'buzz_score': calc_buzz(sentiment, [name]),
                'published_at': date_filed,
            })
            saved += 1
        time.sleep(REQ_SLEEP)

    logger.info(f"CourtListener: queried {queried} companies, saved {saved} filings.")


if __name__ == '__main__':
    try:
        main()
        record_health(get_client(), 'ingest_courtlistener', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_courtlistener', 'error', str(e))
        raise
