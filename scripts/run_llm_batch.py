import os
import json
import logging
import time
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
from db import get_client, check_quota, log_api_call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_news_batch(sb, items):
    if not items:
        return
        
    prompt = "Analyze the following news items. For each, return a JSON object with 'category' (ai/release/ma/ipo/controversy/conference/opensource/earnings/other), 'entities' (list of company names), 'sentiment' (-1.0 to 1.0), 'summary' (1 sentence), 'hype_score' (0-100), and 'reality_score' (0-100). Return a JSON array of these objects in the exact same order.\n\n"
    for i, item in enumerate(items):
        prompt += f"Item {i+1}: {item['title']}\n"
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        log_api_call(sb, 'gemini', 1)
        
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        results = json.loads(text.strip())
        
        for i, item in enumerate(items):
            if i < len(results):
                res = results[i]
                
                sb.table('news_items').update({
                    'category': res.get('category', 'other'),
                    'entity_names': res.get('entities', item.get('entity_names', [])),
                    'sentiment': res.get('sentiment', item.get('sentiment', 0.0)),
                    'summary': res.get('summary', ''),
                    'llm_processed': True
                }).eq('id', item['id']).execute()
                
                for entity in res.get('entities', []):
                    company_res = sb.table('companies').select('id, hype_score, reality_score').eq('name', entity).execute()
                    if company_res.data:
                        cid = company_res.data[0]['id']
                        new_hype = (float(company_res.data[0]['hype_score'] or 50) + float(res.get('hype_score', 50))) / 2
                        new_real = (float(company_res.data[0]['reality_score'] or 50) + float(res.get('reality_score', 50))) / 2
                        sb.table('companies').update({
                            'hype_score': new_hype,
                            'reality_score': new_real
                        }).eq('id', cid).execute()
                        
    except Exception as e:
        logger.error(f"Error processing news batch: {e}")

def run_dispute_detection(sb):
    logger.info("Running dispute detection")
    try:
        time_limit = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
        res = sb.table('claims').select('*').gte('made_at', time_limit).execute()
        claims = res.data
        
        entities = {}
        for c in claims:
            entities.setdefault(c['entity_name'], []).append(c)
            
        model = genai.GenerativeModel('gemini-1.5-flash')
            
        for entity, entity_claims in entities.items():
            if len(entity_claims) < 2:
                continue
                
            for i in range(len(entity_claims)):
                for j in range(i + 1, len(entity_claims)):
                    c1 = entity_claims[i]
                    c2 = entity_claims[j]
                    
                    if c1['claim_type'] != c2['claim_type']:
                        continue
                        
                    prompt = f"Do these two claims contradict each other? Claim 1: '{c1['claim_text']}'. Claim 2: '{c2['claim_text']}'. Answer with only YES or NO."
                    
                    if check_quota(sb, 'gemini', 1):
                        resp = model.generate_content(prompt)
                        log_api_call(sb, 'gemini', 1)
                        if "YES" in resp.text.upper():
                            conf1 = float(c1['credibility_weight']) * 100
                            conf2 = float(c2['credibility_weight']) * 100
                            
                            if conf1 <= 75 and conf2 <= 75:
                                brief_prompt = f"Write a 2 sentence dispute brief comparing these two claims: 1: {c1['claim_text']} 2: {c2['claim_text']}"
                                brief_resp = model.generate_content(brief_prompt)
                                log_api_call(sb, 'gemini', 1)
                                
                                if c1.get('news_item_id'):
                                    sb.table('news_items').update({
                                        'is_disputed': True,
                                        'dispute_claim_a': c1['claim_text'],
                                        'dispute_confidence_a': conf1,
                                        'dispute_claim_b': c2['claim_text'],
                                        'dispute_confidence_b': conf2,
                                        'dispute_brief': brief_resp.text.strip(),
                                        'dispute_checked': True
                                    }).eq('id', c1['news_item_id']).execute()
                                    
    except Exception as e:
        logger.error(f"Error in dispute detection: {e}")

def update_company_briefs(sb):
    logger.info("Updating company briefs")
    try:
        res = sb.table('companies').select('*').in_('poll_tier', [1, 2]).execute()
        companies = res.data
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        for comp in companies:
            if not check_quota(sb, 'gemini', 1):
                break
                
            prompt = f"Provide a short investor brief and a forecast_direction (must be exactly one of: strong_bullish, bullish, neutral, bearish, high_risk) for {comp['name']} based on recent market conditions. Return JSON format: {{'forecast_direction': '...', 'investor_brief': '...', 'forecast_confidence': 80}}"
            resp = model.generate_content(prompt)
            log_api_call(sb, 'gemini', 1)
            
            text = resp.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            try:
                data = json.loads(text.strip())
                sb.table('companies').update({
                    'forecast_direction': data.get('forecast_direction', 'neutral'),
                    'investor_brief': data.get('investor_brief', ''),
                    'forecast_confidence': data.get('forecast_confidence', 50)
                }).eq('id', comp['id']).execute()
            except Exception as e:
                logger.error(f"Error parsing Gemini JSON for company {comp['name']}: {e}")
                
    except Exception as e:
        logger.error(f"Error updating company briefs: {e}")

def main():
    sb = get_client()
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.warning("GEMINI_API_KEY not set")
        return
        
    genai.configure(api_key=api_key)
    
    if not check_quota(sb, 'gemini', 1):
        logger.warning("Gemini quota limit reached")
        return
        
    six_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    res = sb.table('news_items').select('*').eq('llm_processed', False).gte('ingested_at', six_hours_ago).limit(50).execute()
    
    items = res.data
    logger.info(f"Found {len(items)} unprocessed news items")
    
    batch_size = 5
    for i in range(0, len(items), batch_size):
        if not check_quota(sb, 'gemini', 1):
            break
        batch = items[i:i+batch_size]
        process_news_batch(sb, batch)
        
    run_dispute_detection(sb)
    update_company_briefs(sb)

if __name__ == '__main__':
    main()
