import os
import logging
import json
from datetime import datetime, timedelta, timezone
import httpx
from atproto import Client
from db import get_client, extract_entities, COMPANY_SYNONYMS
from llm import generate_llm_content, strip_json_fence, has_llm_capacity
from companies_config import BLUESKY_ACCOUNTS, ALL_COMPANIES
from textblob import TextBlob
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CANONICAL_COMPANY_LOOKUP = {name.lower(): name for name in ALL_COMPANIES}
for canonical, synonyms in COMPANY_SYNONYMS.items():
    if canonical not in ALL_COMPANIES:
        continue
    for synonym in synonyms:
        CANONICAL_COMPANY_LOOKUP.setdefault(str(synonym).strip().lower(), canonical)


def canonicalize_entities(values):
    canonical = []
    for value in values or []:
        if not value:
            continue
        normalized = CANONICAL_COMPANY_LOOKUP.get(str(value).strip().lower())
        if normalized and normalized not in canonical:
            canonical.append(normalized)
    return canonical


def infer_bluesky_category(text: str) -> str:
    text_lower = (text or "").lower()
    if any(term in text_lower for term in ['ipo', 'public offering']):
        return 'ipo'
    if any(term in text_lower for term in ['acquire', 'acquisition', 'merge', 'merger']):
        return 'ma'
    if any(term in text_lower for term in ['launch', 'released', 'release', 'debut', 'announced', 'announcement', 'rollout']):
        return 'release'
    if any(term in text_lower for term in ['lawsuit', 'controversy', 'scandal', 'deceiv', 'fraud', 'risk']):
        return 'controversy'
    if any(term in text_lower for term in ['conference', 'keynote', 'wwdc', 'build ', 'google i/o', 'gdc']):
        return 'conference'
    if any(term in text_lower for term in ['earnings', 'guidance', 'revenue', 'margin']):
        return 'earnings'
    if any(term in text_lower for term in ['model', 'ai', 'agent', 'llm', 'inference', 'chip', 'gpu']):
        return 'ai'
    return 'other'


def summarize_bluesky_post(text: str, sb) -> dict:
    prompt = (
        "Analyze this Bluesky post for a tech-investor signal.\n"
        "Return ONLY valid JSON with keys: "
        "\"title\" (8-14 word headline), "
        "\"summary\" (1 concise sentence), "
        "\"entities\" (tracked company names or products), "
        "\"sentiment\" (-1.0 to 1.0), "
        "\"category\" (ai/release/ma/ipo/controversy/conference/opensource/earnings/other).\n\n"
        f"Post:\n{text}"
    )
    parsed = json.loads(strip_json_fence(generate_llm_content(prompt, sb)))
    return {
        'title': (parsed.get('title') or '').strip(),
        'summary': (parsed.get('summary') or '').strip(),
        'entities': canonicalize_entities(parsed.get('entities', [])),
        'sentiment': float(parsed.get('sentiment', 0.0) or 0.0),
        'category': parsed.get('category') or infer_bluesky_category(text),
    }

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
                    
                    entities = []
                    sentiment = TextBlob(text).sentiment.polarity
                    summary = text
                    title = f"Bluesky post by {handle}"
                    category = infer_bluesky_category(text)
                    llm_processed_flag = False

                    if has_llm_capacity(sb, 1):
                        try:
                            enriched = summarize_bluesky_post(text, sb)
                            title = enriched['title'] or title
                            summary = enriched['summary'] or summary
                            entities = enriched['entities']
                            extracted_entities = extract_entities(text, ALL_COMPANIES)
                            for entity in extracted_entities:
                                if entity not in entities:
                                    entities.append(entity)
                            sentiment = enriched['sentiment']
                            category = enriched['category']
                            llm_processed_flag = True
                        except Exception as e:
                            logger.warning(f"Bluesky LLM enrichment failed for {handle}: {e}")
                            entities = extract_entities(text, ALL_COMPANIES)
                    else:
                        entities = extract_entities(text, ALL_COMPANIES)

                    if entities:
                        news_item = {
                            'title': title,
                            'summary': summary,
                            'url': post_url,
                            'source': handle,
                            'source_type': 'influencer',
                            'source_credibility_tier': 3,
                            'entity_names': entities,
                            'sentiment': sentiment,
                            'buzz_score': calc_buzz(sentiment, entities),
                            'category': category,
                            'published_at': published_at.isoformat()
                        }
                        if llm_processed_flag:
                            news_item['llm_processed'] = True
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
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_bluesky', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_bluesky', 'error', str(e))
        raise
