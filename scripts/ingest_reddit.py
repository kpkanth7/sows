import os
import logging
import requests
import time
from textblob import TextBlob
from datetime import datetime, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import REDDIT_SUBREDDITS, ALL_COMPANIES
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLEEP = 6  # Required 6-second sleep for unauthenticated reddit access

def main():
    sb = get_client()
    
    # Must use descriptive user agent for unauthenticated access
    user_agent = os.environ.get('REDDIT_USER_AGENT', 'python:tech-intel-scraper:v2.0 (by /u/TechIntelUser)')
    headers = {"User-Agent": user_agent}

    for sub_name in REDDIT_SUBREDDITS:
        if not check_quota(sb, 'reddit', 1):
            logger.warning("Reddit quota limit reached")
            break
            
        try:
            url = f"https://www.reddit.com/r/{sub_name}/hot.json"
            params = {"limit": 25, "raw_json": 1}
            
            logger.info(f"Fetching {url}")
            r = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Rate limit or block fallback
            if r.status_code in [429, 403]:
                logger.error(f"Reddit blocked or rate limited (HTTP {r.status_code}) on {sub_name}")
                break
                
            r.raise_for_status()
            data = r.json()
            
            log_api_call(sb, 'reddit', 1)
            
            children = data.get("data", {}).get("children", [])
            
            for child in children:
                if child.get("kind") != "t3":
                    continue
                    
                post = child.get("data", {})
                title = post.get("title", "")
                score = post.get("score", 0)
                permalink = post.get("permalink", "")
                url_str = f"https://www.reddit.com{permalink}"
                
                entities = extract_entities(title, ALL_COMPANIES)
                sentiment = TextBlob(title).sentiment.polarity
                
                for entity in entities:
                    try:
                        sb.table('community_signals').insert({
                            'source': f"reddit_r_{sub_name}",
                            'entity_name': entity,
                            'post_title': title,
                            'post_url': url_str,
                            'post_score': score,
                            'comment_count': post.get("num_comments", 0),
                            'sentiment': sentiment
                        }).execute()
                    except Exception:
                        pass
                        
                if entities and score > 30:
                    item = {
                        'title': title,
                        'url': url_str,
                        'source': f"reddit_r_{sub_name}",
                        'source_type': 'community',
                        'source_credibility_tier': 3,
                        'entity_names': entities,
                        'sentiment': sentiment,
                        'buzz_score': calc_buzz(sentiment, entities),
                        'author': post.get("author"),
                        'published_at': datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc).isoformat()
                    }
                    save_news(sb, item)
                    
            # Mandatory sleep between subreddit polls
            time.sleep(SLEEP)
            
        except Exception as e:
            logger.error(f"Error processing subreddit {sub_name}: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_reddit', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_reddit', 'error', str(e))
        raise
