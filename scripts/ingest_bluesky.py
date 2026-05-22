import os
import logging
from datetime import datetime, timedelta, timezone
from atproto import Client
from db import get_client, extract_entities
from companies_config import BLUESKY_ACCOUNTS, ALL_COMPANIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    sb = get_client()
    client = Client()
    
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)

    for handle in BLUESKY_ACCOUNTS:
        try:
            res = sb.table('influencers').select('id').eq('channel_id', handle).execute()
            if not res.data:
                sb.table('influencers').insert({
                    'name': handle,
                    'platform': 'bluesky',
                    'channel_id': handle
                }).execute()
                res = sb.table('influencers').select('id').eq('channel_id', handle).execute()
                
            influencer_id = res.data[0]['id']
            
            feed = client.get_author_feed(actor=handle, limit=20)
            
            for feed_view in feed.feed:
                post = feed_view.post
                record = post.record
                
                published_at_str = record.created_at
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                
                if published_at >= two_hours_ago:
                    text = getattr(record, 'text', '')
                    if not text:
                        continue
                    post_url = f"https://bsky.app/profile/{handle}/post/{post.uri.split('/')[-1]}"
                    
                    entities = extract_entities(text, ALL_COMPANIES)
                    for entity in entities:
                        sb.table('influencer_signals').insert({
                            'influencer_id': influencer_id,
                            'platform': 'bluesky',
                            'entity_name': entity,
                            'content_title': text[:100],
                            'content_url': post_url,
                            'like_count': post.like_count,
                            'published_at': published_at.isoformat()
                        }).execute()
                        
            sb.table('influencers').update({'last_checked': 'now()'}).eq('id', influencer_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing bluesky handle {handle}: {e}")

if __name__ == '__main__':
    main()
