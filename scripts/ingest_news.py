import os
import hashlib
import time
import httpx
import feedparser
from textblob import TextBlob
from datetime import datetime, timedelta, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import ALL_COMPANIES, RSS_FEEDS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_hash(url: str) -> str:
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def calc_buzz(sentiment: float, entities: list) -> float:
    return min(100.0, len(entities) * 10.0 + abs(sentiment) * 20.0)

def save_news(sb, item):
    try:
        url_hash = compute_hash(item['url'])
        
        res = sb.table('news_items').select('id').eq('url_hash', url_hash).execute()
        if res.data:
            return
            
        item['url_hash'] = url_hash
        item['llm_processed'] = False
        sb.table('news_items').insert(item).execute()
    except Exception as e:
        logger.error(f"Error saving news {item.get('url')}: {e}")

def fetch_hn(sb):
    logger.info("Fetching HN")
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date"
        thirty_mins_ago = int((datetime.now() - timedelta(minutes=30)).timestamp())
        params = {"tags": "story", "numericFilters": f"created_at_i>{thirty_mins_ago}"}
        
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get('hits', [])
        
        for hit in hits:
            title = hit.get('title', '')
            if not title:
                continue
            story_url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            
            entities = extract_entities(title, ALL_COMPANIES)
            sentiment = TextBlob(title).sentiment.polarity
            
            item = {
                'title': title,
                'url': story_url,
                'source': 'hackernews',
                'source_type': 'community',
                'source_credibility_tier': 2,
                'entity_names': entities,
                'sentiment': sentiment,
                'buzz_score': calc_buzz(sentiment, entities),
                'author': hit.get('author'),
                'hn_score': hit.get('points', 0),
                'hn_comments': hit.get('num_comments', 0),
                'published_at': hit.get('created_at')
            }
            save_news(sb, item)
    except Exception as e:
        logger.error(f"HN error: {e}")

def fetch_rss(sb):
    logger.info("Fetching RSS")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.title
                link = entry.link
                
                entities = extract_entities(title, ALL_COMPANIES)
                sentiment = TextBlob(title).sentiment.polarity
                
                item = {
                    'title': title,
                    'url': link,
                    'source': 'rss',
                    'source_type': 'news',
                    'source_credibility_tier': 2,
                    'entity_names': entities,
                    'sentiment': sentiment,
                    'buzz_score': calc_buzz(sentiment, entities)
                }
                save_news(sb, item)
        except Exception as e:
            logger.error(f"RSS error for {feed_url}: {e}")

def fetch_thenewsapi(sb):
    logger.info("Fetching TheNewsAPI")
    if not check_quota(sb, 'thenewsapi'):
        return
    
    api_token = os.environ.get('THENEWSAPI_TOKEN')
    if not api_token:
        logger.warning("THENEWSAPI_TOKEN not set")
        return
        
    try:
        url = "https://api.thenewsapi.com/v1/news/top"
        params = {"api_token": api_token, "language": "en", "limit": 10}
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        log_api_call(sb, 'thenewsapi')
        
        data = resp.json()
        for article in data.get('data', []):
            title = article.get('title')
            link = article.get('url')
            
            entities = extract_entities(title, ALL_COMPANIES)
            sentiment = TextBlob(title).sentiment.polarity
            
            item = {
                'title': title,
                'url': link,
                'source': 'thenewsapi',
                'source_type': 'news',
                'source_credibility_tier': 3,
                'entity_names': entities,
                'sentiment': sentiment,
                'buzz_score': calc_buzz(sentiment, entities),
                'published_at': article.get('published_at')
            }
            save_news(sb, item)
    except Exception as e:
        logger.error(f"TheNewsAPI error: {e}")

def fetch_devto(sb):
    logger.info("Fetching Dev.to")
    if not check_quota(sb, 'devto'):
        return
        
    try:
        url = "https://dev.to/api/articles"
        params = {"top": 1}
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        log_api_call(sb, 'devto')
        
        for article in resp.json()[:15]:
            title = article.get('title')
            link = article.get('url')
            
            entities = extract_entities(title, ALL_COMPANIES)
            sentiment = TextBlob(title).sentiment.polarity
            
            item = {
                'title': title,
                'url': link,
                'source': 'devto',
                'source_type': 'community',
                'source_credibility_tier': 3,
                'entity_names': entities,
                'sentiment': sentiment,
                'buzz_score': calc_buzz(sentiment, entities),
                'author': article.get('user', {}).get('username'),
                'published_at': article.get('published_at')
            }
            save_news(sb, item)
    except Exception as e:
        logger.error(f"devto error: {e}")

def main():
    sb = get_client()
    fetch_hn(sb)
    fetch_rss(sb)
    fetch_thenewsapi(sb)
    fetch_devto(sb)
    logger.info("ingest_news completed.")

if __name__ == '__main__':
    main()
