"""Reddit RSS ingestor (Phase 2.6 swap, 2026-05-29).

Replaces the unauthenticated `/hot.json` path that was getting 403/429'd and
needed a 6s inter-request sleep. RSS is effectively unlimited and stable.

Trade-off: RSS feeds DON'T expose post score / num_comments, so we drop the
score>30 gate that previously promoted Reddit posts into `news_items`. Reddit
now feeds `community_signals` only — a softer signal stream the LLM/buzz
pipeline can still consume.
"""
import os
import logging
import feedparser
import httpx
from textblob import TextBlob
from db import get_client, extract_entities
from companies_config import REDDIT_SUBREDDITS, ALL_COMPANIES
from ingest_news import sentiment_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_subreddit_rss(url: str, headers: dict):
    """Reddit requires a descriptive User-Agent even for RSS."""
    resp = httpx.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def main():
    sb = get_client()
    user_agent = os.environ.get(
        'REDDIT_USER_AGENT',
        'python:tech-intel-scraper:v2.0 (by /u/TechIntelUser)'
    )
    headers = {"User-Agent": user_agent}

    total = 0
    for sub in REDDIT_SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/hot/.rss?limit=25"
        try:
            feed = fetch_subreddit_rss(url, headers)
        except Exception as e:
            logger.error(f"Reddit RSS error for r/{sub}: {e}")
            continue

        matched = 0
        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            link = entry.get("link")
            if not title or not link:
                continue
            entities = extract_entities(title, ALL_COMPANIES)
            if not entities:
                continue
            sentiment = TextBlob(sentiment_text(title, entry.get("summary"), entry.get("description"))).sentiment.polarity
            for entity in entities:
                try:
                    sb.table('community_signals').insert({
                        'source': f"reddit_r_{sub}",
                        'entity_name': entity,
                        'post_title': title,
                        'post_url': link,
                        'post_score': None,           # RSS doesn't expose score
                        'comment_count': None,
                        'sentiment': sentiment,
                    }).execute()
                    matched += 1
                except Exception:
                    # Likely a unique-constraint collision on re-fetch — silent skip.
                    pass
        total += matched
        logger.info(f"r/{sub}: {len(feed.entries)} entries, {matched} entity-matched signals.")
    logger.info(f"ingest_reddit (RSS) total community_signals written: {total}")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_reddit', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_reddit', 'error', str(e))
        raise
