"""SEC EDGAR 8-K (material events) firehose ingestor.

Free, no key. We poll the SEC's "current filings" Atom feed for form 8-K and keep
entries whose filer name maps to a tracked public company. 8-K = material events
(M&A, exec changes, lawsuits, exec departures) — high-signal for the investor view.

SEC's fair-access policy REQUIRES a User-Agent that includes a contact email
(requests without one are 403'd). We read it from env `SEC_USER_AGENT` so the
contact isn't hardcoded in this public repo. Format expected:
  "AppName your-email@example.com"
SEC TOS: max ~10 req/s; we do one request per hour.

Docs: https://www.sec.gov/os/accessing-edgar-data
"""
import os
import logging
from datetime import datetime, timezone
import feedparser
import httpx
from textblob import TextBlob
from db import get_client, extract_entities
from companies_config import ALL_COMPANIES
from ingest_news import save_news, calc_buzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEC_FEED = ("https://www.sec.gov/cgi-bin/browse-edgar"
            "?action=getcurrent&type=8-K&output=atom&count=100")


def main():
    sb = get_client()
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not user_agent or "@" not in user_agent:
        logger.warning("SEC_USER_AGENT not set or missing email — skipping SEC ingest. "
                       "Set it as a repo secret in the form 'AppName email@example.com'.")
        return
    try:
        resp = httpx.get(SEC_FEED, headers={"User-Agent": user_agent}, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"SEC fetch error: {e}")
        return

    feed = feedparser.parse(resp.content)
    matched = 0
    for entry in feed.entries:
        title = entry.get("title", "")
        url = entry.get("link")
        if not title or not url:
            continue
        entities = extract_entities(title, ALL_COMPANIES)
        if not entities:
            continue
        matched += 1
        sentiment = TextBlob(title).sentiment.polarity
        published = entry.get("updated") or datetime.now(timezone.utc).isoformat()
        save_news(sb, {
            'title': title,
            'url': url,
            'source': 'sec_edgar',
            'source_type': 'news',
            'source_credibility_tier': 1,  # regulatory filing = highest credibility
            'category': 'ma',  # 8-K covers M&A + other material events
            'entity_names': entities,
            'sentiment': sentiment,
            'buzz_score': calc_buzz(sentiment, entities),
            'published_at': published,
        })
    logger.info(f"SEC EDGAR: {len(feed.entries)} 8-K filings fetched, {matched} matched tracked companies.")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_sec', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_sec', 'error', str(e))
        raise
