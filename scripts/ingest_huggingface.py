import os
import logging
import httpx
from datetime import datetime, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import ALL_COMPANIES
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_trending_models(sb):
    logger.info("Fetching Hugging Face trending models")
    if not check_quota(sb, 'arxiv'): # share quota tracking with arxiv
        return
        
    hf_token = os.environ.get('HF_TOKEN')
    headers = {}
    if hf_token:
        # Strip quotes if any
        hf_token = hf_token.strip('"').strip("'")
        headers["Authorization"] = f"Bearer {hf_token}"
        
    try:
        # Fetch trending models sorted by likes
        url = "https://huggingface.co/api/models"
        params = {"sort": "likes", "direction": -1, "limit": 25}
        
        resp = httpx.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        log_api_call(sb, 'arxiv', 1)
        
        models = resp.json()
        logger.info(f"Retrieved {len(models)} models from Hugging Face")
        
        for m in models:
            model_id = m.get('id', '')
            if not model_id:
                continue
                
            # Match entities in model ID (e.g. meta-llama/Llama-3-8b -> Meta)
            entities = extract_entities(model_id, ALL_COMPANIES)
            
            # Check if creator matches any entity (e.g. stabilityai -> Stability AI)
            author = model_id.split('/')[0] if '/' in model_id else ''
            if author:
                author_entities = extract_entities(author, ALL_COMPANIES)
                entities.extend(author_entities)
                
            entities = list(set(entities))
            
            # Skip if it doesn't match any company we track
            if not entities:
                continue
                
            likes = m.get('likes', 0)
            downloads = m.get('downloads', 0)
            model_url = f"https://huggingface.co/{model_id}"
            
            # Parse publication/modification date
            published_at = m.get('lastModified')
            if published_at:
                try:
                    # e.g. "2024-05-26T12:00:00.000Z" -> isoformat
                    published_at = published_at.replace('Z', '+00:00')
                except Exception:
                    published_at = datetime.now(timezone.utc).isoformat()
            else:
                published_at = datetime.now(timezone.utc).isoformat()
                
            title = f"Trending HF Model: {model_id} ({likes} Likes)"
            summary = f"The model {model_id} by {author or 'open-source'} is trending on Hugging Face with {likes} likes and {downloads} downloads."
            
            item = {
                'title': title,
                'summary': summary,
                'url': model_url,
                'source': 'huggingface',
                'source_type': 'code',
                'source_credibility_tier': 2,
                'category': 'opensource',
                'entity_names': entities,
                'sentiment': 0.60, # OSS releases are positive signals
                'buzz_score': calc_buzz(0.60, entities),
                'published_at': published_at
            }
            save_news(sb, item)
            
    except Exception as e:
        logger.error(f"Hugging Face API error: {e}")

def fetch_daily_papers(sb):
    logger.info("Fetching Hugging Face daily papers")
    if not check_quota(sb, 'arxiv'): # share quota with arxiv
        return
        
    try:
        url = "https://huggingface.co/api/daily_papers"
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        log_api_call(sb, 'arxiv', 1)
        
        papers = resp.json()
        logger.info(f"Retrieved {len(papers)} papers from Hugging Face")
        
        for item in papers:
            paper_data = item.get('paper')
            if not paper_data:
                continue
                
            arxiv_id = paper_data.get('id')
            title = paper_data.get('title', '')
            summary = paper_data.get('ai_summary') or paper_data.get('summary', '')
            if len(summary) > 500:
                summary = summary[:497] + "..."
                
            published_at = paper_data.get('publishedAt') or datetime.now(timezone.utc).isoformat()
            
            # Extract entities
            entities = extract_entities(title + " " + summary, ALL_COMPANIES)
            if not entities:
                continue
                
            paper_url = f"https://huggingface.co/papers/{arxiv_id}"
            
            news_item = {
                'title': f"HF Paper: {title}",
                'summary': summary,
                'url': paper_url,
                'source': 'huggingface_papers',
                'source_type': 'news',
                'source_credibility_tier': 2,
                'category': 'ai',
                'entity_names': entities,
                'sentiment': 0.50, # Scientific papers are generally positive updates
                'buzz_score': calc_buzz(0.50, entities),
                'published_at': published_at
            }
            save_news(sb, news_item)
            
    except Exception as e:
        logger.error(f"Hugging Face daily papers error: {e}")

def main():
    sb = get_client()
    fetch_trending_models(sb)
    fetch_daily_papers(sb)
    logger.info("ingest_huggingface completed.")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_huggingface', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_huggingface', 'error', str(e))
        raise
