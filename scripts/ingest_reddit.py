import os
import logging
import praw
from textblob import TextBlob
from datetime import datetime, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import REDDIT_SUBREDDITS, ALL_COMPANIES
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    sb = get_client()
    
    client_id = os.environ.get('REDDIT_CLIENT_ID')
    client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
    user_agent = os.environ.get('REDDIT_USER_AGENT', 'TechIntelBot/1.0')
    
    if not all([client_id, client_secret]):
        logger.warning("Reddit API credentials not fully set")
        return

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    for sub_name in REDDIT_SUBREDDITS:
        if not check_quota(sb, 'reddit', 1):
            logger.warning("Reddit quota limit reached")
            break
            
        try:
            subreddit = reddit.subreddit(sub_name)
            hot_posts = subreddit.hot(limit=25)
            log_api_call(sb, 'reddit', 1)
            
            for post in hot_posts:
                title = post.title
                score = post.score
                url = f"https://www.reddit.com{post.permalink}"
                
                entities = extract_entities(title, ALL_COMPANIES)
                sentiment = TextBlob(title).sentiment.polarity
                
                for entity in entities:
                    try:
                        sb.table('community_signals').insert({
                            'source': f"reddit_r_{sub_name}",
                            'entity_name': entity,
                            'post_title': title,
                            'post_url': url,
                            'post_score': score,
                            'comment_count': post.num_comments,
                            'sentiment': sentiment
                        }).execute()
                    except Exception:
                        pass
                        
                if score > 500:
                    item = {
                        'title': title,
                        'url': url,
                        'source': f"reddit_r_{sub_name}",
                        'source_type': 'community',
                        'source_credibility_tier': 3,
                        'entity_names': entities,
                        'sentiment': sentiment,
                        'buzz_score': calc_buzz(sentiment, entities),
                        'author': str(post.author) if post.author else None,
                        'published_at': datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat()
                    }
                    save_news(sb, item)
                    
        except Exception as e:
            logger.error(f"Error processing subreddit {sub_name}: {e}")

if __name__ == '__main__':
    main()
