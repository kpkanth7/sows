import os
import logging
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import YOUTUBE_CHANNELS, ALL_COMPANIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    sb = get_client()
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
    
    if not youtube_api_key:
        logger.warning("YOUTUBE_API_KEY not set")
        return
        
    youtube = build('youtube', 'v3', developerKey=youtube_api_key, cache_discovery=False)
    
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)

    for channel in YOUTUBE_CHANNELS:
        name = channel['name']
        channel_id = channel['channel_id']
        playlist_id = channel['playlist_id']
        category = channel['category']
        
        try:
            res = sb.table('influencers').select('id').eq('channel_id', channel_id).execute()
            if not res.data:
                sb.table('influencers').insert({
                    'name': name,
                    'platform': 'youtube',
                    'channel_id': channel_id,
                    'category': category
                }).execute()
                res = sb.table('influencers').select('id').eq('channel_id', channel_id).execute()
                
            influencer_id = res.data[0]['id']
            
            if not check_quota(sb, 'youtube', 1):
                logger.warning("YouTube quota limit reached")
                break
                
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=10
            )
            response = request.execute()
            log_api_call(sb, 'youtube', 1)
            
            for item in response.get('items', []):
                snippet = item['snippet']
                published_at_str = snippet['publishedAt']
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                
                if published_at >= two_hours_ago:
                    title = snippet['title']
                    video_id = snippet['resourceId']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    entities = extract_entities(title, ALL_COMPANIES)
                    for entity in entities:
                        sb.table('influencer_signals').insert({
                            'influencer_id': influencer_id,
                            'platform': 'youtube',
                            'entity_name': entity,
                            'content_title': title,
                            'content_url': video_url,
                            'published_at': published_at.isoformat()
                        }).execute()
                        
            sb.table('influencers').update({'last_checked': 'now()'}).eq('id', influencer_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing YouTube channel {name}: {e}")

if __name__ == '__main__':
    main()
