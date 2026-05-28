import logging
from datetime import datetime, timedelta, timezone
from db import get_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    sb = get_client()
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    try:
        res = sb.table('claims').select('*').is_('validated', 'null').lte('made_at', thirty_days_ago).execute()
        claims = res.data
        
        for claim in claims:
            res_news = sb.table('news_items').select('*')\
                .contains('entity_names', [claim['entity_name']])\
                .in_('source_credibility_tier', [1, 2])\
                .gte('published_at', claim['made_at'])\
                .execute()
                
            news = res_news.data
            validated = False
            
            for n in news:
                # Basic naive matching for demo
                text_to_search = (n.get('title', '') + str(n.get('summary', ''))).lower()
                words = claim['claim_text'].lower().split()
                if len([w for w in words if w in text_to_search]) > len(words) * 0.5:
                    validated = True
                    break
                    
            sb.table('claims').update({
                'validated': validated,
                'validated_at': datetime.now(timezone.utc).isoformat(),
                'validated_by': 'system_check'
            }).eq('id', claim['id']).execute()
            
            inf_res = sb.table('influencers').select('*').eq('name', claim['source_name']).execute()
            if not inf_res.data:
                inf_res = sb.table('influencers').select('*').eq('channel_id', claim['source_name']).execute()
                
            if inf_res.data:
                influencer = inf_res.data[0]
                trust = float(influencer['trust_score'] or 0.2)
                correct_claims = influencer['correct_claims'] or 0
                total_claims = influencer['total_claims'] or 0
                
                if validated:
                    trust += 0.02
                    correct_claims += 1
                else:
                    trust -= 0.03
                    
                trust = max(0.05, min(0.60, trust))
                total_claims += 1
                
                sb.table('influencers').update({
                    'trust_score': trust,
                    'correct_claims': correct_claims,
                    'total_claims': total_claims
                }).eq('id', influencer['id']).execute()
                    
    except Exception as e:
        logger.error(f"Error updating influencer trust: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'update_influencer_trust', 'ok')
    except Exception as e:
        record_health(get_client(), 'update_influencer_trust', 'error', str(e))
        raise
