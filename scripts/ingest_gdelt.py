"""GDELT 2.0 DOC API ingestor (free, no key).

Global news firehose. We query English tech/AI coverage from the last hour, then
keep only articles mentioning a tracked company (same entity filter as ingest_news)
and persist via the dedup-aware save_news. Sentiment via TextBlob for consistency
with the other news sources.

Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""
import logging
import time
from datetime import datetime, timezone
import httpx
from textblob import TextBlob
from db import get_client, extract_entities
from companies_config import ALL_COMPANIES
from ingest_news import save_news, calc_buzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
# Broad tech net; per-article entity extraction narrows to tracked companies.
QUERY = ('(AI OR "artificial intelligence" OR "machine learning" OR software '
         'OR semiconductor OR startup OR robotics OR chip) sourcelang:english')


def parse_seendate(s: str) -> str:
    # GDELT format: 20260529T120000Z
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).isoformat()


def main():
    sb = get_client()
    params = {
        "query": QUERY,
        "mode": "artlist",
        "maxrecords": 250,
        "timespan": "60min",
        "sort": "datedesc",
        "format": "json",
    }
    # GDELT throttles aggressively per-IP; brief retry on 429.
    articles = []
    backoff = 5
    for attempt in range(3):
        try:
            resp = httpx.get(GDELT_URL, params=params, timeout=20)
            if resp.status_code == 429 and attempt < 2:
                logger.warning(f"GDELT 429; sleeping {backoff}s (attempt {attempt+1}/3)")
                time.sleep(backoff)
                backoff *= 2
                continue
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            break
        except Exception as e:
            logger.error(f"GDELT fetch error: {e}")
            return

    matched = 0
    for art in articles:
        title = art.get("title")
        url = art.get("url")
        if not title or not url:
            continue
        entities = extract_entities(title, ALL_COMPANIES)
        if not entities:
            continue
        matched += 1
        sentiment = TextBlob(title).sentiment.polarity
        save_news(sb, {
            'title': title,
            'url': url,
            'source': 'gdelt',
            'source_type': 'news',
            'source_credibility_tier': 3,
            'entity_names': entities,
            'sentiment': sentiment,
            'buzz_score': calc_buzz(sentiment, entities),
            'image_url': art.get('socialimage'),
            'published_at': parse_seendate(art.get('seendate')),
        })
    logger.info(f"GDELT: {len(articles)} fetched, {matched} matched tracked companies.")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_gdelt', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_gdelt', 'error', str(e))
        raise
