import os
import logging
from datetime import date
from supabase import create_client, Client
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        return True

def log_api_call(sb: Client, source_name: str, cost: int = 1):
    """Increment daily counter"""
    try:
        res = sb.table("api_quota_log").select("calls_today").eq("source_name", source_name).execute()
        if not res.data:
            return
        row = res.data[0]
        calls_today = row.get("calls_today", 0) + cost
        
        sb.table("api_quota_log").update({
            "calls_today": calls_today
        }).eq("source_name", source_name).execute()
    except Exception as e:
        logger.error(f"Error in log_api_call: {e}")

def extract_entities(text: str, known_entities: list) -> list:
    """Find company/tech mentions in text (case-insensitive)"""
    if not text:
        return []
    
    found = set()
    text_lower = text.lower()
    
    for entity in known_entities:
        pattern = r'\b' + re.escape(entity.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.add(entity)
            
    return list(found)

if __name__ == '__main__':
    print("DB module loaded.")
