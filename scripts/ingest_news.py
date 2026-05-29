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

import re

def compute_hash(url: str) -> str:
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def calc_buzz(sentiment: float, entities: list) -> float:
    return min(100.0, len(entities) * 10.0 + abs(sentiment) * 20.0)

def clean_title_words(title: str) -> set:
    if not title:
        return set()
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
    words = normalized.split()
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 'to', 'of', 'with', 'by', 
        'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 
        'below', 'from', 'up', 'down', 'in', 'out', 'off', 'over', 'under', 'again', 'further', 
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
        'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
        'should', 'now', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 
        'had', 'having', 'do', 'does', 'did', 'doing', 'it', 'its', 'they', 'them', 'their', 
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'our', 'us'
    }
    return {w for w in words if w not in stop_words and len(w) > 2}

def get_jaccard_similarity(words1: set, words2: set) -> float:
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)

def compute_title_hash(title: str) -> str:
    """MD5 of normalized, stop-word-stripped, sorted title words.

    Catches case changes and word reordering as exact dups (cheap, indexed).
    Falls back to a lowercased-title hash when normalization empties the set.
    """
    words = sorted(clean_title_words(title))
    if not words:
        return compute_hash((title or '').lower())
    return hashlib.md5(' '.join(words).encode('utf-8')).hexdigest()

def save_news(sb, item):
    try:
        url_hash = compute_hash(item['url'])
        
        # 1. Check if identical URL exists
        res = sb.table('news_items').select('id, source_credibility_tier, hn_score, hn_comments').eq('url_hash', url_hash).execute()
        if res.data:
            existing = res.data[0]
            improved = False
            
            existing_hn_score = existing.get('hn_score') or 0
            existing_hn_comments = existing.get('hn_comments') or 0
            item_hn_score = item.get('hn_score') or 0
            item_hn_comments = item.get('hn_comments') or 0
            
            if item_hn_score > existing_hn_score or item_hn_comments > existing_hn_comments:
                improved = True
                
            existing_tier = existing.get('source_credibility_tier')
            existing_tier = 3 if existing_tier is None else existing_tier
            item_tier = item.get('source_credibility_tier')
            item_tier = 3 if item_tier is None else item_tier
            
            if item_tier < existing_tier:
                improved = True
                
            if improved:
                sb.table('news_items').update({
                    'title': item['title'],
                    'url': item['url'],
                    'source': item['source'],
                    'source_credibility_tier': item_tier,
                    'hn_score': item_hn_score,
                    'hn_comments': item_hn_comments,
                    'published_at': item.get('published_at', datetime.now(timezone.utc).isoformat())
                }).eq('id', existing['id']).execute()
            return
            
        # 2. Check if identical (normalized) Title exists via indexed title_hash
        title_hash = compute_title_hash(item['title'])
        res_title = sb.table('news_items').select('id').eq('title_hash', title_hash).execute()
        if res_title.data:
            return

        # 3. Check for duplicate story via Jaccard similarity in the last 18 hours.
        # Trigram RPC narrows candidates server-side (indexed); we apply the precise
        # word-Jaccard cutoff on the small returned set instead of scanning all rows.
        item_words = clean_title_words(item['title'])
        if item_words:
            eighteen_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=18)).isoformat()
            rpc_res = sb.rpc('match_similar_news', {
                'p_title': item['title'],
                'p_since': eighteen_hours_ago,
                'p_threshold': 0.3
            }).execute()

            for recent in (rpc_res.data or []):
                recent_entities = recent.get('entity_names', [])
                item_entities = item.get('entity_names', [])
                shared_entities = set(recent_entities) & set(item_entities)
                if not shared_entities and (recent_entities or item_entities):
                    continue
                    
                recent_words = clean_title_words(recent['title'])
                sim = get_jaccard_similarity(item_words, recent_words)
                if sim >= 0.40:
                    # It's a duplicate story! Check for improvement
                    improved = False
                    
                    recent_hn_score = recent.get('hn_score') or 0
                    recent_hn_comments = recent.get('hn_comments') or 0
                    item_hn_score = item.get('hn_score') or 0
                    item_hn_comments = item.get('hn_comments') or 0
                    
                    if item_hn_score > recent_hn_score or item_hn_comments > recent_hn_comments:
                        improved = True
                        
                    recent_tier = recent.get('source_credibility_tier')
                    recent_tier = 3 if recent_tier is None else recent_tier
                    item_tier = item.get('source_credibility_tier')
                    item_tier = 3 if item_tier is None else item_tier
                    
                    if item_tier < recent_tier:
                        improved = True
                        
                    if improved:
                        sb.table('news_items').update({
                            'title': item['title'],
                            'url': item['url'],
                            'source': item['source'],
                            'source_credibility_tier': item_tier,
                            'hn_score': item_hn_score,
                            'hn_comments': item_hn_comments,
                            'published_at': item.get('published_at', datetime.now(timezone.utc).isoformat())
                        }).eq('id', recent['id']).execute()
                    return

        item['url_hash'] = url_hash
        item['title_hash'] = title_hash
        if 'llm_processed' not in item:
            item['llm_processed'] = False
        sb.table('news_items').insert(item).execute()
    except Exception as e:
        logger.error(f"Error saving news {item.get('url')}: {e}")

def fetch_hn(sb):
    logger.info("Fetching HN")
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date"
        six_hours_ago = int((datetime.now() - timedelta(minutes=390)).timestamp())
        params = {"tags": "story", "numericFilters": f"created_at_i>{six_hours_ago}", "hitsPerPage": 100}
        
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get('hits', [])
        
        for hit in hits:
            title = hit.get('title', '')
            if not title:
                continue
            story_url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            
            entities = extract_entities(title, ALL_COMPANIES)
            if not entities:
                continue
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
            for entry in feed.entries[:30]:
                title = entry.title
                link = entry.link
                
                entities = extract_entities(title, ALL_COMPANIES)
                if not entities:
                    continue
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
    api_token = os.environ.get('THENEWSAPI_KEY') or os.environ.get('THENEWSAPI_TOKEN')
    if not api_token:
        logger.warning("Neither THENEWSAPI_KEY nor THENEWSAPI_TOKEN set")
        return
        
    page = 1
    max_pages = 3
    while page <= max_pages:
        if not check_quota(sb, 'thenewsapi'):
            logger.info("TheNewsAPI quota limit reached, stopping pagination.")
            break
            
        try:
            # Query v1/news/all to search all tech category news
            url = "https://api.thenewsapi.com/v1/news/all"
            params = {
                "api_token": api_token,
                "language": "en",
                "limit": 15,
                "categories": "tech",
                "page": page
            }
            logger.info(f"Querying TheNewsAPI page {page} with categories=tech")
            resp = httpx.get(url, params=params, timeout=12)
            resp.raise_for_status()
            log_api_call(sb, 'thenewsapi')
            
            data = resp.json()
            articles = data.get('data', [])
            if not articles:
                logger.info("No more articles returned by TheNewsAPI.")
                break
                
            matched_count = 0
            for article in articles:
                title = article.get('title')
                link = article.get('url')
                if not title or not link:
                    continue
                    
                entities = extract_entities(title, ALL_COMPANIES)
                if not entities:
                    continue
                    
                matched_count += 1
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
                    'published_at': article.get('published_at') or datetime.now(timezone.utc).isoformat()
                }
                save_news(sb, item)
                
            logger.info(f"TheNewsAPI page {page} processed. Total: {len(articles)}, Matched: {matched_count}")
            
            # If we match 2 or more articles on this page, it indicates high tech activity.
            # We fetch the next page. Otherwise, 1 call is enough.
            if matched_count >= 2:
                page += 1
            else:
                break
        except Exception as e:
            logger.error(f"TheNewsAPI error on page {page}: {e}")
            break

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
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_news', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_news', 'error', str(e))
        raise
