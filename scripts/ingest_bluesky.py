import os
import logging
from datetime import datetime, timedelta, timezone
import httpx
from atproto import Client
from db import get_client, extract_entities
from companies_config import BLUESKY_ACCOUNTS, ALL_COMPANIES
from textblob import TextBlob
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def resolve_handle_public(handle: str) -> str:
    if handle.startswith("did:"):
        return handle
    try:
        url = "https://bsky.social/xrpc/com.atproto.identity.resolveHandle"
        resp = httpx.get(url, params={"handle": handle}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("did")
    except Exception as e:
        logger.warning(f"Could not resolve handle {handle} via bsky.social: {e}")
        
    try:
        url = "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle"
        resp = httpx.get(url, params={"handle": handle}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("did")
    except Exception as e:
        logger.warning(f"Could not resolve handle {handle} via public.api.bsky.app: {e}")
        
    return None

def main():
    sb = get_client()
    client = Client(base_url='https://public.api.bsky.app')
    
    six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6.5)

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
            
            did = resolve_handle_public(handle)
            if not did:
                logger.warning(f"Failed to resolve handle {handle} to DID, skipping.")
                continue
                
            feed = client.get_author_feed(actor=did, limit=20)
            
            for feed_view in feed.feed:
                post = feed_view.post
                record = post.record
                
                published_at_str = record.created_at
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                
                if published_at >= six_hours_ago:
                    text = getattr(record, 'text', '')
                    if not text:
                        continue
                    post_url = f"https://bsky.app/profile/{handle}/post/{post.uri.split('/')[-1]}"
                    
                    entities = extract_entities(text, ALL_COMPANIES)
                    if entities:
                        sentiment = TextBlob(text).sentiment.polarity
                        
                        # Save in news_items for main feed
                        news_item = {
                            'title': f"Bluesky post by {handle}",
                            'summary': text,
                            'url': post_url,
                            'source': handle,
                            'source_type': 'influencer',
                            'source_credibility_tier': 3,
                            'entity_names': entities,
                            'sentiment': sentiment,
                            'buzz_score': calc_buzz(sentiment, entities),
                            'published_at': published_at.isoformat()
                        }
                        save_news(sb, news_item)
                        
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
