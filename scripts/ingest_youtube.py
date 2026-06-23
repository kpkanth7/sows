import os
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from db import get_client, check_quota, log_api_call, extract_entities, COMPANY_SYNONYMS
from llm import generate_llm_content, strip_json_fence, has_llm_capacity
from companies_config import YOUTUBE_CHANNELS, ALL_COMPANIES
from ingest_news import calc_buzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CANONICAL_COMPANY_LOOKUP = {name.lower(): name for name in ALL_COMPANIES}
for canonical, synonyms in COMPANY_SYNONYMS.items():
    if canonical not in ALL_COMPANIES:
        continue
    for synonym in synonyms:
        CANONICAL_COMPANY_LOOKUP.setdefault(str(synonym).strip().lower(), canonical)

def compute_hash(url: str) -> str:
    return hashlib.md5(url.encode('utf-8')).hexdigest()


def canonicalize_entities(values):
    canonical = []
    for value in values or []:
        if not value:
            continue
        normalized = CANONICAL_COMPANY_LOOKUP.get(str(value).strip().lower())
        if normalized and normalized not in canonical:
            canonical.append(normalized)
    return canonical


def infer_youtube_category(channel_category: str, title: str, summary: str) -> str:
    text = f"{title}\n{summary}".lower()
    if any(term in text for term in ['ipo', 'public offering']):
        return 'ipo'
    if any(term in text for term in ['acquire', 'acquisition', 'merge', 'merger']):
        return 'ma'
    if any(term in text for term in ['launch', 'released', 'release', 'debut', 'announced', 'announcement']):
        return 'release'
    if any(term in text for term in ['lawsuit', 'controversy', 'scandal', 'fooling', 'deceiv', 'risk']):
        return 'controversy'
    if any(term in text for term in ['earnings', 'guidance', 'revenue', 'margin']):
        return 'earnings'
    if channel_category in {'ai_ml', 'dev'}:
        return 'ai'
    return 'other'

def main():
    sb = get_client()
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
    
    if not youtube_api_key:
        logger.warning("YOUTUBE_API_KEY not set")
        return
        
    youtube = build('youtube', 'v3', developerKey=youtube_api_key, cache_discovery=False)
    six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6.5)

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
                    'category': category,
                    'trust_score': 0.30
                }).execute()
                res = sb.table('influencers').select('id').eq('channel_id', channel_id).execute()
                
            influencer_id = res.data[0]['id']
            
            if not check_quota(sb, 'youtube', 1):
                logger.warning("YouTube quota limit reached")
                break

            # Skip the channels().list lookup — config already stores the uploads
            # playlist_id (UC -> UU prefix swap done at config time). Saves ~27
            # quota units per run vs the previous per-channel dynamic fetch.
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=5
            )
            response = request.execute()
            log_api_call(sb, 'youtube', 1)
            
            for item in response.get('items', []):
                snippet = item['snippet']
                published_at_str = snippet['publishedAt']
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                
                if published_at >= six_hours_ago:
                    title = snippet['title']
                    video_id = snippet['resourceId']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Try fetching transcript
                    transcript_text = ""
                    try:
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                        # Take first 5 mins (roughly 300 seconds)
                        text_chunks = []
                        for t in transcript_list:
                            if t['start'] > 300:
                                break
                            text_chunks.append(t['text'])
                        transcript_text = " ".join(text_chunks)
                    except Exception as e:
                        logger.warning(f"Could not fetch transcript for {video_id}: {e}")
                    
                    # Fallback to description if no transcript
                    if not transcript_text:
                        transcript_text = snippet.get('description', '')[:1000]
                    
                    entities = []
                    sentiment = 0.0
                    summary = ""
                    claims = []
                    detected_category = infer_youtube_category(category, title, transcript_text[:280])
                    llm_processed_flag = False
                    
                    if transcript_text and has_llm_capacity(sb, 1):
                        prompt = (
                            f"Analyze the following video transcript/description for the video '{title}'.\n\n"
                            f"1. Is this video sponsored (does the creator thank a sponsor, pitch a product promotion, or do an ad read)? Answer true or false.\n"
                            f"2. Based on this text, what are the tech/AI companies or products mentioned? Return a list of company names.\n"
                            f"3. What is the overall sentiment towards them (-1.0 to 1.0)?\n"
                            f"4. Write a concise 1-sentence summary of the main points the creator discussed or thought about these companies/products.\n"
                            f"5. Identify any concrete claims they made that can be verified (e.g. 'Model X is 10% faster than Model Y', 'Company A is acquiring Company B'). "
                            f"For each claim, provide the 'entity' it is about, and a 1-sentence description of the claim.\n\n"
                            f"Return ONLY a valid JSON object with the following keys:\n"
                            f"{{\n"
                            f"  \"is_sponsored\": false,\n"
                            f"  \"entities\": [\"Google\", \"OpenAI\"],\n"
                            f"  \"sentiment\": 0.5,\n"
                            f"  \"summary\": \"Creator thinks Google's new model update will perform better than GPT-4o in coding tasks.\",\n"
                            f"  \"claims\": [\n"
                            f"    {{\"entity\": \"Google\", \"text\": \"Google released a coding model that outperforms GPT-4o on HumanEval\", \"type\": \"benchmark_best\"}}\n"
                            f"  ]\n"
                            f"}}\n\n"
                            f"Text Chunk:\n{transcript_text}"
                        )
                        try:
                            resp_text = generate_llm_content(prompt, sb)
                            data = json.loads(strip_json_fence(resp_text))
                            
                            if data.get('is_sponsored', False):
                                logger.info(f"Skipping video {video_id} - detected as sponsored.")
                                continue
                                
                            summary = data.get('summary', '')
                            entities = canonicalize_entities(data.get('entities', []))
                            extracted_entities = extract_entities(f"{title}\n{summary}\n{transcript_text}", ALL_COMPANIES)
                            for entity in extracted_entities:
                                if entity not in entities:
                                    entities.append(entity)
                            sentiment = data.get('sentiment', 0.0)
                            claims = data.get('claims', [])
                            detected_category = infer_youtube_category(category, title, summary)
                            llm_processed_flag = True
                            
                        except Exception as e:
                            logger.error(f"Gemini parse error for video {video_id}: {e}")
                            entities = extract_entities(f"{title}\n{transcript_text}", ALL_COMPANIES)
                            sentiment = 0.0
                            detected_category = infer_youtube_category(category, title, transcript_text[:280])
                            llm_processed_flag = False
                    else:
                        entities = extract_entities(f"{title}\n{transcript_text}", ALL_COMPANIES)
                        sentiment = 0.0
                        detected_category = infer_youtube_category(category, title, transcript_text[:280])
                        llm_processed_flag = False
                    
                    if not entities:
                        # Skip inserting influencer video if it doesn't match any company we track
                        continue
                        
                    news_item_id = None
                    # Save video in news_items (dashboard feed)
                    try:
                        url_hash = compute_hash(video_url)
                        # Deduplication by URL
                        res_url = sb.table('news_items').select('id').eq('url_hash', url_hash).execute()
                        if not res_url.data:
                            # Deduplication by exact Title
                            res_title = sb.table('news_items').select('id').eq('title', title).execute()
                            if not res_title.data:
                                sb.table('news_items').insert({
                                    'title': title,
                                    'summary': summary or f"YouTube analysis by {name}.",
                                    'url': video_url,
                                    'url_hash': url_hash,
                                    'source': name,
                                    'source_type': 'influencer',
                                    'source_credibility_tier': 3,
                                    'entity_names': entities,
                                    'sentiment': sentiment,
                                    'buzz_score': calc_buzz(sentiment, entities),
                                    'category': detected_category,
                                    'published_at': published_at.isoformat(),
                                    'llm_processed': llm_processed_flag,
                                    'dispute_checked': True
                                }).execute()
                                
                                res_new = sb.table('news_items').select('id').eq('url_hash', url_hash).execute()
                                if res_new.data:
                                    news_item_id = res_new.data[0]['id']
                    except Exception as e:
                        logger.error(f"Failed to insert video into news_items: {e}")

                    # Insert claims
                    for claim in claims:
                        try:
                            entity = CANONICAL_COMPANY_LOOKUP.get(str(claim.get('entity', '')).strip().lower())
                            text = claim.get('text')
                            ctype = claim.get('type', 'general')
                            if entity and text and entity in ALL_COMPANIES:
                                sb.table('claims').insert({
                                    'news_item_id': news_item_id,
                                    'entity_name': entity,
                                    'claim_text': text,
                                    'claim_type': ctype,
                                    'source_name': name,
                                    'source_type': 'youtube',
                                    'credibility_weight': 0.30,
                                    'made_at': published_at.isoformat()
                                }).execute()
                        except Exception as e:
                            logger.error(f"Failed to insert claim: {e}")

                    # Insert signal
                    for entity in entities:
                        try:
                            sb.table('influencer_signals').insert({
                                'influencer_id': influencer_id,
                                'platform': 'youtube',
                                'entity_name': entity,
                                'content_title': title,
                                'content_url': video_url,
                                'published_at': published_at.isoformat()
                              }).execute()
                        except Exception as e:
                            logger.error(f"Failed to insert signal: {e}")
                            
            sb.table('influencers').update({'last_checked': 'now()'}).eq('id', influencer_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing YouTube channel {name}: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_youtube', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_youtube', 'error', str(e))
        raise
