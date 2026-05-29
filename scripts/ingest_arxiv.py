"""arXiv ingestor — leading R&D indicator.

Free, no key. We pull the latest cs.AI / cs.LG / cs.CL / cs.CV / cs.RO submissions
and keep papers whose title OR abstract mentions a tracked company (catches lab
attributions like "DeepMind" / "Anthropic" / "Meta AI" in title+summary even when
arXiv's author-affiliation field is sparse).

Saved as source_type='research', credibility tier 2.

API docs: https://info.arxiv.org/help/api/user-manual.html
"""
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

ARXIV_URL = "https://export.arxiv.org/api/query"
CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO"]
PARAMS = {
    "search_query": "+OR+".join(f"cat:{c}" for c in CATEGORIES),
    "max_results": 100,
    "sortBy": "submittedDate",
    "sortOrder": "descending",
}


def main():
    sb = get_client()
    try:
        # arXiv parses '+' literally — pass params as a pre-built query string.
        qs = "&".join(f"{k}={v}" for k, v in PARAMS.items())
        resp = httpx.get(f"{ARXIV_URL}?{qs}", timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"arXiv fetch error: {e}")
        return

    feed = feedparser.parse(resp.content)
    matched = 0
    for entry in feed.entries:
        title = (entry.get("title") or "").replace("\n", " ").strip()
        summary = (entry.get("summary") or "").replace("\n", " ").strip()
        url = entry.get("link")
        if not title or not url:
            continue
        # Search both title + abstract for company mentions; persist any unique hits.
        entities = list(set(
            extract_entities(title, ALL_COMPANIES)
            + extract_entities(summary, ALL_COMPANIES)
        ))
        if not entities:
            continue
        matched += 1
        sentiment = TextBlob(title).sentiment.polarity
        published = entry.get("published") or datetime.now(timezone.utc).isoformat()
        save_news(sb, {
            'title': title,
            'url': url,
            'source': 'arxiv',
            'source_type': 'research',
            'source_credibility_tier': 2,
            'category': 'ai',
            'entity_names': entities,
            'sentiment': sentiment,
            'buzz_score': calc_buzz(sentiment, entities),
            'summary': summary[:500] if summary else None,
            'published_at': published,
        })
    logger.info(f"arXiv: {len(feed.entries)} papers fetched, {matched} mentioned tracked companies.")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_arxiv', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_arxiv', 'error', str(e))
        raise
