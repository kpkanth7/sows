import os
import logging
from datetime import date
from supabase import create_client, Client
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_QUOTA_DEFAULTS = {
    "groq": {"daily_limit": 1000, "per_min_limit": 30},
    "gemini": {"daily_limit": 1000, "per_min_limit": 15},
    "cerebras": {"daily_limit": 1000, "per_min_limit": 30},
    "openrouter": {"daily_limit": 1000, "per_min_limit": 20},
}

def get_client() -> Client:
    supabase_url = os.environ.get('SUPABASE_URL', '')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    return create_client(supabase_url, supabase_key)

def check_quota(sb: Client, source_name: str, cost: int = 1) -> bool:
    """Returns True if quota OK, False if near limit (>90%)"""
    try:
        res = sb.table("api_quota_log").select("*").eq("source_name", source_name).execute()
        if not res.data:
            defaults = LLM_QUOTA_DEFAULTS.get(source_name)
            if defaults:
                sb.table("api_quota_log").upsert({
                    "source_name": source_name,
                    "calls_today": 0,
                    "daily_limit": defaults["daily_limit"],
                    "calls_this_min": 0,
                    "per_min_limit": defaults["per_min_limit"],
                    "last_reset": str(date.today())
                }, on_conflict="source_name").execute()
                return True
            return True
        row = res.data[0]
        today = str(date.today())
        
        if row.get("last_reset") != today:
            sb.table("api_quota_log").update({
                "calls_today": 0,
                "last_reset": today
            }).eq("source_name", source_name).execute()
            row["calls_today"] = 0
            
        calls_today = row.get("calls_today", 0)
        daily_limit = row.get("daily_limit", 100)
        
        if calls_today + cost > daily_limit * 0.9:
            logger.warning(f"Quota near limit for {source_name}: {calls_today}/{daily_limit}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error in check_quota: {e}")
        return False  # Fail-safe: deny on error rather than blow past API limits

def log_api_call(sb: Client, source_name: str, cost: int = 1):
    """Increment daily counter. Upserts the row if it does not exist yet."""
    try:
        res = sb.table("api_quota_log").select("calls_today").eq("source_name", source_name).execute()
        if not res.data:
            # No row yet — create one so tracking works on a fresh DB
            sb.table("api_quota_log").upsert({
                "source_name": source_name,
                "calls_today": cost,
                "daily_limit": 1000,
                "last_reset": str(date.today())
            }, on_conflict="source_name").execute()
            return
        row = res.data[0]
        calls_today = (row.get("calls_today") or 0) + cost

        sb.table("api_quota_log").update({
            "calls_today": calls_today
        }).eq("source_name", source_name).execute()
    except Exception as e:
        logger.error(f"Error in log_api_call: {e}")

def record_health(sb: Client, job_name: str, status: str, detail: str = None):
    """Write last-run status for a job so failures are visible on the dashboard."""
    try:
        sb.table("health_checks").upsert({
            "job_name": job_name,
            "status": status,
            "detail": (detail or "")[:500],
            "last_run": "now()"
        }, on_conflict="job_name").execute()
    except Exception as e:
        logger.error(f"Error in record_health for {job_name}: {e}")

COMPANY_SYNONYMS = {
    'Google': ['googl', 'goog', 'alphabet', 'google cloud', 'gemma', 'gemma-2', 'gemini'],
    'Microsoft': ['msft', 'microsoft corp', 'microsoft corporation', 'phi-3', 'phi-4'],
    'Apple': ['aapl', 'apple inc', 'apple inc.'],
    'NVIDIA': ['nvda', 'nvidia corp', 'nvidia corporation'],
    'Meta': ['facebook', 'fb', 'meta platforms', 'meta platforms inc.', 'llama', 'llama-3', 'meta-llama'],
    'Amazon': ['amzn', 'amazon.com', 'aws', 'amazon web services'],
    'Tesla': ['tsla', 'tesla motors'],
    'Mistral': ['mistral ai', 'mistralai', 'pixtral', 'codestral'],
    'Stability AI': ['stability.ai', 'stabilityai', 'stable diffusion', 'sdxl'],
    'HuggingFace': ['hugging face', 'huggingface.co', 'hf'],
    'Perplexity': ['perplexity ai', 'perplexity.ai', 'perplexity-ai'],
    'Salesforce': ['crm', 'salesforce.com'],
    'xAI': ['x.ai', 'grok'],
    'Together AI': ['together.ai', 'togethercomputer'],
    'Supabase': ['supabase'],
    'Vercel': ['vercel'],
    'OpenAI': ['gpt-4', 'gpt-4o', 'chatgpt', 'whisper', 'sora', 'o1-preview', 'o1-mini'],
    'Anthropic': ['claude', 'claude-3', 'claude-3.5', 'claude-3.5-sonnet', 'sonnet']
}

AMBIGUOUS_ENTITY_CONTEXT = {
    'Modal': [
        'modal labs', 'modal.com', 'serverless', 'gpu', 'inference',
        'cloud compute', 'ai infrastructure', 'container', 'compute platform',
    ],
    'Notion': [
        'notion ai', 'notion.so', 'workspace', 'productivity', 'notes',
        'docs', 'database', 'calendar', 'collaboration app',
    ],
    'Linear': [
        'linear.app', 'issue tracker', 'project management', 'roadmap',
        'sprint', 'bug tracking', 'engineering teams', 'software teams',
    ],
    'Unity': [
        'unity software', 'unity technologies', 'game engine', 'runtime',
        'developers', 'game developers', 'unity ads', '3d content',
    ],
    'Together AI': [
        'together ai', 'together.ai', 'togethercomputer', 'open-model',
        'open model', 'inference api', 'gpu cloud',
    ],
}


def _has_ambiguous_entity_context(text_lower: str, entity: str) -> bool:
    context_terms = AMBIGUOUS_ENTITY_CONTEXT.get(entity)
    if not context_terms:
        return True
    return any(term in text_lower for term in context_terms)


def extract_entities(text: str, known_entities: list) -> list:
    """Find company/tech mentions in text (case-insensitive)"""
    if not text:
        return []
    
    found = set()
    text_lower = text.lower()
    
    for entity in known_entities:
        # Match canonical name
        pattern = r'\b' + re.escape(entity.lower()) + r'\b'
        if re.search(pattern, text_lower):
            if not _has_ambiguous_entity_context(text_lower, entity):
                continue
            found.add(entity)
            continue
            
        # Match synonyms/tickers
        syns = COMPANY_SYNONYMS.get(entity, [])
        for syn in syns:
            syn_pattern = r'\b' + re.escape(syn.lower()) + r'\b'
            if re.search(syn_pattern, text_lower):
                found.add(entity)
                break
            
    return list(found)

if __name__ == '__main__':
    print("DB module loaded.")
