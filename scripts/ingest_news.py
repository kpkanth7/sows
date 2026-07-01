import os
import hashlib
import time
import httpx
import feedparser
from html.parser import HTMLParser
from textblob import TextBlob
from datetime import datetime, timedelta, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import (
    ALL_COMPANIES,
    RSS_FEEDS,
    OFFICIAL_COMPANY_RELEASE_FEEDS,
    OFFICIAL_COMPANY_SOURCE_REGISTRY,
    SOURCE_REGION_BY_DOMAIN,
    TIER1_NAMES,
    TIER2_NAMES,
    TIER3_NAMES,
)
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import re

GENERIC_LINK_TEXT = {
    'news', 'read more', 'read story', 'read announcement', 'learn more',
    'about', 'support', 'contact', 'careers', 'events', 'pricing',
}


class _AnchorExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._parts = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        attrs_dict = dict(attrs)
        self._href = attrs_dict.get('href')
        self._parts = []

    def handle_data(self, data):
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag != 'a' or self._href is None:
            return
        text = re.sub(r'\s+', ' ', ''.join(self._parts)).strip()
        self.links.append((self._href, text))
        self._href = None
        self._parts = []

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


def sentiment_text(*parts) -> str:
    """Flatten and clean multiple text fragments for sentiment analysis."""
    cleaned = []
    for part in parts:
        if not part:
            continue
        if isinstance(part, list):
            for item in part:
                if isinstance(item, dict):
                    cleaned.append(str(item.get('value') or item.get('content') or ''))
                else:
                    cleaned.append(str(item))
            continue
        text = str(part)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            cleaned.append(text)
    return ' '.join(cleaned).strip()


def infer_rss_category(title: str, feed_url: str = "") -> str:
    """Fast keyword classifier for RSS/news headlines.

    This keeps release / conference / IPO / M&A / research items visible before
    the later LLM pass runs.
    """
    text = f"{title}\n{feed_url}".lower()
    if any(term in text for term in ['ipo', 'public offering', 'listing', 'went public']):
        return 'ipo'
    if any(term in text for term in ['acquire', 'acquisition', 'merge', 'merger', 'm&a']):
        return 'ma'
    if any(term in text for term in ['lawsuit', 'controv', 'scandal', 'fraud', 'breach', 'investigation']):
        return 'controversy'
    if any(term in text for term in ['conference', 'keynote', 'summit', 'devday', 'build ', 'google i/o', 'wwdc', 're:invent', 'ignite', 'gdc']):
        return 'conference'
    if any(term in text for term in ['earnings', 'guidance', 'revenue', 'margin', 'quarter', 'q1 ', 'q2 ', 'q3 ', 'q4 ']):
        return 'earnings'
    if any(term in text for term in ['research', 'paper', 'benchmark', 'arxiv', 'study', 'model card']):
        return 'research'
    if any(term in text for term in ['open source', 'opensource', 'github', 'release', 'launch', 'released', 'announced', 'announcement', 'debut', 'rollout', 'preview', 'beta', 'unveil']):
        return 'release'
    if any(term in text for term in ['ai', 'llm', 'model', 'agent', 'inference', 'chip', 'gpu']):
        return 'ai'
    return 'other'


def extract_official_page_entries(html: str, page_url: str, official_company: str):
    parser = _AnchorExtractor()
    parser.feed(html or "")
    base_domain = urlparse(page_url).netloc
    seen = set()
    entries = []

    for href, text in parser.links:
        normalized_text = re.sub(r'\s+', ' ', text).strip()
        if not normalized_text:
            continue
        if normalized_text.lower() in GENERIC_LINK_TEXT:
            continue
        if len(normalized_text) < 18 or len(normalized_text) > 180:
            continue

        absolute_url = urljoin(page_url, href)
        parsed = urlparse(absolute_url)
        if parsed.netloc and parsed.netloc != base_domain:
            continue
        path = parsed.path.lower()
        looks_like_story = any(part in path for part in ['/news/', '/blog/', '/press/', '/announcements/', '/research/'])
        title_signals = infer_rss_category(normalized_text, page_url)
        if not looks_like_story and title_signals not in {'release', 'conference', 'research', 'ai'}:
            continue
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        entries.append({
            'title': normalized_text,
            'url': absolute_url,
            'source': official_company,
            'source_type': 'official_company',
            'source_credibility_tier': 1,
            'entity_names': [official_company],
            'sentiment': TextBlob(sentiment_text(normalized_text)).sentiment.polarity,
            'buzz_score': calc_buzz(0.25, [official_company]),
            'category': infer_rss_category(normalized_text, page_url),
            'published_at': datetime.now(timezone.utc).isoformat(),
        })
    return entries[:20]


def source_domain(url: str) -> str | None:
    try:
        netloc = urlparse(url or "").netloc.lower()
        return netloc[4:] if netloc.startswith('www.') else netloc
    except Exception:
        return None


def infer_source_region(url: str) -> str | None:
    domain = source_domain(url)
    if not domain:
        return None
    for known, region in SOURCE_REGION_BY_DOMAIN.items():
        if domain == known or domain.endswith(f'.{known}'):
            return region
    return None


def infer_source_kind(url: str, source_type: str, official_company: str | None = None) -> str:
    domain = source_domain(url) or ""
    if official_company:
        if "github.com" in domain:
            return "official_release_feed"
        return "official_company_page"
    if "github.com" in domain:
        return "code_host"
    if source_type == "research":
        return "research_feed"
    if source_type == "community":
        return "community_feed"
    return "tech_media"


def entity_tier_max(entities: list[str]) -> int | None:
    tiers = []
    for entity in entities or []:
        if entity in TIER1_NAMES:
            tiers.append(1)
        elif entity in TIER2_NAMES:
            tiers.append(2)
        elif entity in TIER3_NAMES:
            tiers.append(3)
    return min(tiers) if tiers else None


def is_major_release(title: str, entities: list[str], category: str, source_credibility_tier: int, official_company: str | None = None) -> bool:
    text = (title or "").lower()
    strong_terms = [
        "introducing", "introduce", "launch", "launched", "released", "release",
        "sonnet", "gpt", "gemini", "claude", "llama", "model", "api",
        "general availability", "available now", "debut", "unveil", "preview",
        "rollout", "flagship",
    ]
    tracked_tier = entity_tier_max(entities)
    return (
        category == "release"
        and source_credibility_tier <= 2
        and any(term in text for term in strong_terms)
        and (official_company is not None or tracked_tier in {1, 2})
    )


def enrich_item_metadata(item: dict, official_company: str | None = None) -> dict:
    enriched = dict(item)
    entities = list(enriched.get('entity_names') or [])
    category = enriched.get('category') or infer_rss_category(enriched.get('title', ''), enriched.get('url', ''))
    enriched['category'] = category
    enriched['source_domain'] = source_domain(enriched.get('url'))
    enriched['source_region'] = infer_source_region(enriched.get('url'))
    enriched['source_kind'] = infer_source_kind(enriched.get('url'), enriched.get('source_type', 'news'), official_company)
    enriched['source_priority'] = (
        1 if official_company else
        min(5, max(1, int((enriched.get('source_credibility_tier') or 3) + (0 if category in {'release', 'conference', 'controversy'} else 1))))
    )
    enriched['entity_tier_max'] = entity_tier_max(entities)
    enriched['is_major_release'] = is_major_release(
        enriched.get('title', ''),
        entities,
        category,
        int(enriched.get('source_credibility_tier') or 3),
        official_company,
    )
    return enriched

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
                    'published_at': item.get('published_at', datetime.now(timezone.utc).isoformat()),
                    'source_domain': item.get('source_domain'),
                    'source_region': item.get('source_region'),
                    'source_kind': item.get('source_kind'),
                    'source_priority': item.get('source_priority'),
                    'entity_tier_max': item.get('entity_tier_max'),
                    'is_major_release': item.get('is_major_release', False),
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
                            'published_at': item.get('published_at', datetime.now(timezone.utc).isoformat()),
                            'source_domain': item.get('source_domain'),
                            'source_region': item.get('source_region'),
                            'source_kind': item.get('source_kind'),
                            'source_priority': item.get('source_priority'),
                            'entity_tier_max': item.get('entity_tier_max'),
                            'is_major_release': item.get('is_major_release', False),
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
            sentiment = TextBlob(sentiment_text(title)).sentiment.polarity
            
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
            save_news(sb, enrich_item_metadata(item))
    except Exception as e:
        logger.error(f"HN error: {e}")

def fetch_rss(sb):
    logger.info("Fetching RSS")
    feed_source_lookup = {
        url: company
        for company, spec in OFFICIAL_COMPANY_SOURCE_REGISTRY.items()
        for url in spec.get('feeds', [])
    }
    page_source_lookup = {
        url: company
        for company, spec in OFFICIAL_COMPANY_SOURCE_REGISTRY.items()
        for url in spec.get('pages', [])
    }
    seen = set()
    for feed_url in RSS_FEEDS + OFFICIAL_COMPANY_RELEASE_FEEDS + list(feed_source_lookup.keys()):
        if feed_url in seen:
            continue
        seen.add(feed_url)
        try:
            feed = feedparser.parse(feed_url)
            official_company = feed_source_lookup.get(feed_url)
            for entry in feed.entries[:30]:
                title = entry.title
                link = entry.link
                
                entities = extract_entities(title, ALL_COMPANIES)
                if official_company and official_company not in entities:
                    entities.append(official_company)
                if not entities:
                    continue
                sentiment = TextBlob(sentiment_text(title, entry.get('summary'), entry.get('description'), entry.get('content'))).sentiment.polarity
                
                item = {
                    'title': title,
                    'url': link,
                    'source': official_company or 'rss',
                    'source_type': 'official_company' if official_company else 'news',
                    'source_credibility_tier': 1 if official_company else 2,
                    'entity_names': entities,
                    'sentiment': sentiment,
                    'buzz_score': calc_buzz(sentiment, entities),
                    'category': 'release' if official_company else infer_rss_category(title, feed_url),
                    'published_at': entry.get('published') or entry.get('updated') or datetime.now(timezone.utc).isoformat(),
                }
                save_news(sb, enrich_item_metadata(item, official_company=official_company))
        except Exception as e:
            logger.error(f"RSS error for {feed_url}: {e}")

    for page_url, official_company in page_source_lookup.items():
        try:
            resp = httpx.get(page_url, timeout=12, headers={"User-Agent": "TechIntelBot/1.0"})
            resp.raise_for_status()
            for item in extract_official_page_entries(resp.text, page_url, official_company):
                save_news(sb, enrich_item_metadata(item, official_company=official_company))
        except Exception as e:
            logger.error(f"Official page parse error for {page_url}: {e}")

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
                sentiment = TextBlob(sentiment_text(title, article.get('description'), article.get('snippet'))).sentiment.polarity
                
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
                save_news(sb, enrich_item_metadata(item))
                
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
            sentiment = TextBlob(sentiment_text(title, article.get('summary'), article.get('description'), article.get('body'))).sentiment.polarity
            
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
            save_news(sb, enrich_item_metadata(item))
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
