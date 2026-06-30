import math
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from db import get_client
from llm import generate_llm_content, strip_json_fence, has_llm_capacity, get_primary_provider
from companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Phase 2.13: precomputed set of mega-cap names so any T1 mention boosts buzz_v2.
TIER1_NAMES = {c['name'] for c in TIER1_COMPANIES}
TIER2_NAMES = {c['name'] for c in TIER2_COMPANIES}
TIER3_NAMES = {c['name'] for c in TIER3_COMPANIES}

ENTITY_TIER_PRIORITY = {
    **{name: 1 for name in TIER1_NAMES},
    **{name: 2 for name in TIER2_NAMES},
    **{name: 3 for name in TIER3_NAMES},
}


def compute_buzz_v2(item: dict, relevance: float) -> float:
    """Composite ranking score for the news feed.

      buzz_v2 = 0.5*relevance + 0.2*source_credibility + 0.15*hn_engagement + 0.15*recency
      × 1.2 if any tracked T1 mega-cap is mentioned, capped at 100.

    Inputs come from the news_items row + the LLM-rated relevance (0-100).
    """
    # source_credibility: tier 1 -> 100, 2 -> 75, 3 -> 50, 4 -> 25.
    tier = item.get('source_credibility_tier') or 3
    cred = max(0.0, 125.0 - tier * 25.0)

    # hn_engagement: only HN items carry score/comments; everything else 0.
    score = item.get('hn_score') or 0
    comments = item.get('hn_comments') or 0
    hn = min(100.0, math.log10(score + 1) * 30.0 + math.log10(comments + 1) * 20.0) if (score or comments) else 0.0

    # recency: exponential decay with a 24h half-life-ish (decay constant 24).
    ts_str = item.get('published_at') or item.get('ingested_at')
    try:
        published = datetime.fromisoformat(ts_str.replace('Z', '+00:00')) if ts_str else None
    except Exception:
        published = None
    if published:
        hours = max(0.0, (datetime.now(timezone.utc) - published).total_seconds() / 3600.0)
        recency = 100.0 * math.exp(-hours / 24.0)
    else:
        recency = 50.0  # unknown publish time -> neutral

    base = 0.5 * relevance + 0.2 * cred + 0.15 * hn + 0.15 * recency
    entity_tiers = [ENTITY_TIER_PRIORITY.get(entity) for entity in (item.get('entity_names') or []) if ENTITY_TIER_PRIORITY.get(entity)]
    if entity_tiers:
        best_tier = min(entity_tiers)
        boost = {1: 1.25, 2: 1.12, 3: 1.0}.get(best_tier, 1.0)
    else:
        boost = 1.0
    return round(min(100.0, base * boost), 2)


def process_news_batch(sb, items):
    if not items:
        return

    prompt = (
        "Analyze the following news items. For each, return a JSON object with "
        "'category' (ai/release/ma/ipo/controversy/conference/opensource/earnings/research/other), "
        "'entities' (list of company names), 'sentiment' (-1.0 to 1.0), "
        "'summary' (1 sentence), 'hype_score' (0-100), 'reality_score' (0-100), "
        "and 'relevance' (0-100, how much a tech investor should care about this headline "
        "— breaking M&A/earnings/lawsuit/major-product news = high; minor PR / opinion = low). "
        "Return a JSON array of these objects in the exact same order.\n\n"
    )
    for i, item in enumerate(items):
        prompt += f"Item {i+1}: {item['title']}\n"

    try:
        text = generate_llm_content(prompt, sb)
        results = json.loads(strip_json_fence(text))

        for i, item in enumerate(items):
            if i < len(results):
                res = results[i]
                relevance = float(res.get('relevance', 50))
                # Recompute buzz_v2 using the merged entity list the LLM emitted.
                merged = dict(item)
                merged['entity_names'] = res.get('entities', item.get('entity_names', []))
                buzz_v2 = compute_buzz_v2(merged, relevance)

                sb.table('news_items').update({
                    'category': res.get('category', 'other'),
                    'entity_names': res.get('entities', item.get('entity_names', [])),
                    'sentiment': res.get('sentiment', item.get('sentiment', 0.0)),
                    'summary': res.get('summary', ''),
                    'relevance': relevance,
                    'buzz_v2': buzz_v2,
                    'llm_processed': True,
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
                        
        time.sleep(4)
                        
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
                    
                    if has_llm_capacity(sb, 1):
                        resp_text = generate_llm_content(prompt, sb)
                        if "YES" in resp_text.upper():
                            conf1 = float(c1['credibility_weight']) * 100
                            conf2 = float(c2['credibility_weight']) * 100
                            
                            if conf1 <= 75 and conf2 <= 75:
                                brief_prompt = f"Write a 2 sentence dispute brief comparing these two claims: 1: {c1['claim_text']} 2: {c2['claim_text']}"
                                brief_text = generate_llm_content(brief_prompt, sb)
                                
                                if c1.get('news_item_id'):
                                    sb.table('news_items').update({
                                        'is_disputed': True,
                                        'dispute_claim_a': c1['claim_text'],
                                        'dispute_confidence_a': conf1,
                                        'dispute_claim_b': c2['claim_text'],
                                        'dispute_confidence_b': conf2,
                                        'dispute_brief': brief_text.strip(),
                                        'dispute_checked': True
                                    }).eq('id', c1['news_item_id']).execute()
                                    
                        time.sleep(4)
                                    
    except Exception as e:
        logger.error(f"Error in dispute detection: {e}")

def update_company_briefs(sb):
    logger.info("Updating company briefs")
    try:
        res = sb.table('companies').select('*').in_('poll_tier', [1, 2]).execute()
        companies = res.data
        
        if not has_llm_capacity(sb, 1):
            logger.warning("LLM capacity reached before processing briefs.")
            return

        time_limit = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        
        # Build one massive prompt for all companies
        prompt = (
            "You are a senior tech investor analyst. I will provide recent news and signals for multiple "
            "tech companies. Update the investor brief for EACH company using only the supplied signals.\n"
            "Write for an investor scanning risk, momentum, and what changed recently. Be concrete: mention "
            "the most relevant signal(s), avoid generic growth language, and if evidence is thin say that "
            "clearly instead of inventing conviction.\n\n"
        )
        
        for comp in companies:
            news_res = sb.table('news_items').select('title, summary, source_type, source, category, buzz_v2').contains('entity_names', json.dumps([comp["name"]])).gte('ingested_at', time_limit).order('ingested_at', desc=True).limit(5).execute()
            comm_res = sb.table('community_signals').select('post_title, sentiment').eq('entity_name', comp['name']).gte('captured_at', time_limit).order('captured_at', desc=True).limit(3).execute()
            inf_res = sb.table('influencer_signals').select('content_title').eq('entity_name', comp['name']).gte('published_at', time_limit).order('published_at', desc=True).limit(3).execute()
            
            prompt += f"--- COMPANY: {comp['name']} ---\n"
            prompt += f"Is Private: {comp.get('is_private', False)}\n"
            if comp.get('last_valuation'):
                prompt += f"Latest private valuation / market cap field: {comp.get('last_valuation')}\n"
            prompt += "RECENT SIGNALS:\n"
            for n in news_res.data:
                prompt += (
                    f"- [NEWS:{n.get('source') or n.get('source_type') or 'unknown'}"
                    f"/{n.get('category') or 'uncategorized'} buzz={n.get('buzz_v2')}] "
                    f"{n['title']} ({n.get('summary') or 'No summary'})\n"
                )
            for c in comm_res.data:
                prompt += f"- [COMM] {c['post_title']} (sentiment: {c['sentiment']})\n"
            for i in inf_res.data:
                prompt += f"- [INFL] {i['content_title']}\n\n"
                
        prompt += """
For EACH company provided, you must output a JSON object with its name as the key.
For each company, provide:
- "investor_brief": "2 compact sentences based on the recent signals. Sentence 1 should state what changed or the strongest signal. Sentence 2 should state investor implication, risk, or confidence limit."
- "forecast_direction": EXACTLY one of: "strong_bullish", "bullish", "neutral", "bearish", "high_risk"
  Use "strong_bullish" only when signals are uniformly positive AND highly material.
  Use "high_risk" when controversy / lawsuits / governance issues dominate the signals.
  Default to "neutral" if signals are mixed or thin.
- "forecast_confidence": 0-100

Return ONLY a valid JSON object where keys are the exact company names. Example:
{
  "Google": { "investor_brief": "...", "forecast_direction": "bullish", "forecast_confidence": 85 },
  "OpenAI": { "investor_brief": "...", "forecast_direction": "strong_bullish", "forecast_confidence": 90 }
}
"""
        
        max_retries = 3
        text = ""
        for attempt in range(max_retries):
            try:
                text = generate_llm_content(prompt, sb)
                break
            except Exception as e:
                if '429' in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Rate limited. Sleeping for 30s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(30)
                else:
                    raise e
        
        try:
            results = json.loads(strip_json_fence(text))
            for comp in companies:
                cname = comp['name']
                if cname in results:
                    data = results[cname]
                    update_data = {
                        'forecast_direction': data.get('forecast_direction', 'neutral'),
                        'investor_brief': data.get('investor_brief', ''),
                        'forecast_confidence': data.get('forecast_confidence', 50)
                    }
                    sb.table('companies').update(update_data).eq('id', comp['id']).execute()
        except Exception as e:
            logger.error(f"Error parsing Gemini batch JSON: {e}")
            
    except Exception as e:
        logger.error(f"Error updating company briefs: {e}")

def main():
    sb = get_client()
    provider = get_primary_provider()
    if not has_llm_capacity(sb, 1):
        logger.warning(f"No LLM capacity left for provider chain starting with {provider}")
        return
        
    six_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    res = sb.table('news_items').select('*').eq('llm_processed', False).gte('ingested_at', six_hours_ago).limit(50).execute()
    
    items = res.data
    logger.info(f"Found {len(items)} unprocessed news items")
    
    batch_size = 5
    for i in range(0, len(items), batch_size):
        if not has_llm_capacity(sb, 1):
            break
        batch = items[i:i+batch_size]
        process_news_batch(sb, batch)
        
    run_dispute_detection(sb)
    update_company_briefs(sb)

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'run_llm_batch', 'ok')
    except Exception as e:
        record_health(get_client(), 'run_llm_batch', 'error', str(e))
        raise
