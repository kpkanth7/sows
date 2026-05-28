import logging
from datetime import datetime, timedelta, timezone
from db import get_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    sb = get_client()
    six_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    
    try:
        res = sb.table('news_items').select('entity_names, sentiment').gte('ingested_at', six_hours_ago).execute()
        recent_news = res.data
        
        company_stats = {}
        for item in recent_news:
            entities = item.get('entity_names') or []
            sentiment = float(item.get('sentiment') or 0)
            
            for entity in entities:
                if entity not in company_stats:
                    company_stats[entity] = {'count': 0, 'sentiment_sum': 0}
                company_stats[entity]['count'] += 1
                company_stats[entity]['sentiment_sum'] += sentiment
                
        res = sb.table('companies').select('id, name, poll_tier').execute()
        companies = {c['name']: c for c in res.data}
        
        res = sb.table('company_poll_config').select('*').execute()
        configs = {c['company_id']: c for c in res.data}
        
        for name, comp in companies.items():
            comp_id = comp['id']
            
            if comp_id not in configs:
                sb.table('company_poll_config').insert({
                    'company_id': comp_id,
                    'base_tier': comp['poll_tier'],
                    'current_tier': comp['poll_tier']
                }).execute()
                res = sb.table('company_poll_config').select('*').eq('company_id', comp_id).execute()
                config = res.data[0]
            else:
                config = configs[comp_id]
            
            if name in company_stats:
                stats = company_stats[name]
                vol_6h = stats['count']
                avg_sentiment = stats['sentiment_sum'] / vol_6h
            else:
                vol_6h = 0
                avg_sentiment = 0
                
            avg_vol = float(config.get('avg_news_volume_6h', 1) or 1)
            last_sent = float(config.get('last_sentiment_delta', 0) or 0)
            
            sentiment_delta = abs((avg_sentiment * 100) - last_sent)
            
            if vol_6h > (2 * avg_vol) or sentiment_delta > 20:
                promotion_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
                sb.table('company_poll_config').update({
                    'current_tier': 2,
                    'promoted_at': datetime.now(timezone.utc).isoformat(),
                    'promotion_expires': promotion_expires,
                    'buzz_spike_count': config.get('buzz_spike_count', 0) + 1,
                    'last_news_volume_6h': vol_6h,
                    'last_sentiment_delta': avg_sentiment * 100
                }).eq('company_id', comp_id).execute()
                
                sb.table('companies').update({
                    'poll_tier': 2
                }).eq('id', comp_id).execute()
            else:
                new_avg = (avg_vol * 0.9) + (vol_6h * 0.1)
                
                update_data = {
                    'last_news_volume_6h': vol_6h,
                    'avg_news_volume_6h': new_avg,
                    'last_sentiment_delta': avg_sentiment * 100
                }
                
                expires = config.get('promotion_expires')
                if expires and datetime.fromisoformat(expires.replace('Z', '+00:00')) < datetime.now(timezone.utc):
                    update_data['current_tier'] = config['base_tier']
                    sb.table('companies').update({
                        'poll_tier': config['base_tier']
                    }).eq('id', comp_id).execute()
                    
                sb.table('company_poll_config').update(update_data).eq('company_id', comp_id).execute()
                
    except Exception as e:
        logger.error(f"Error checking buzz spikes: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'check_buzz_spikes', 'ok')
    except Exception as e:
        record_health(get_client(), 'check_buzz_spikes', 'error', str(e))
        raise
