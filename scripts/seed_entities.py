import logging
from db import get_client
from companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES, YOUTUBE_CHANNELS, BLUESKY_ACCOUNTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    sb = get_client()
    
    # 1. Seed Companies
    logger.info("Seeding companies...")
    for tier, companies in [(1, TIER1_COMPANIES), (2, TIER2_COMPANIES), (3, TIER3_COMPANIES)]:
        for c in companies:
            try:
                row_data = {
                    'name': c['name'],
                    'ticker': c['ticker'],
                    'is_private': c['is_private'],
                    'sector': c['sector'],
                    'is_ai_company': c['is_ai_company'],
                    'github_org': c['github_org'],
                    'poll_tier': tier,
                    'last_valuation': c.get('last_valuation'),
                    'valuation_source': c.get('valuation_source')
                }
                res = sb.table('companies').select('id').eq('name', c['name']).execute()
                if res.data:
                    sb.table('companies').update(row_data).eq('id', res.data[0]['id']).execute()
                else:
                    sb.table('companies').insert(row_data).execute()
            except Exception as e:
                logger.error(f"Failed to insert company {c['name']}: {e}")

    # 2. Seed Influencers (YouTube)
    logger.info("Seeding YouTube influencers...")
    for y in YOUTUBE_CHANNELS:
        try:
            row_data = {
                'name': y['name'],
                'platform': 'youtube',
                'channel_id': y['channel_id'],
                'category': y['category'],
                'trust_score': 0.30
            }
            res = sb.table('influencers').select('id').eq('name', y['name']).execute()
            if res.data:
                sb.table('influencers').update(row_data).eq('id', res.data[0]['id']).execute()
            else:
                sb.table('influencers').insert(row_data).execute()
        except Exception as e:
            logger.error(f"Failed to insert influencer {y['name']}: {e}")
            
    # 3. Seed Influencers (Bluesky)
    logger.info("Seeding Bluesky influencers...")
    for b in BLUESKY_ACCOUNTS:
        try:
            row_data = {
                'name': b,
                'platform': 'bluesky',
                'channel_id': b,
                'category': 'tech_general',
                'trust_score': 0.30
            }
            res = sb.table('influencers').select('id').eq('name', b).execute()
            if res.data:
                sb.table('influencers').update(row_data).eq('id', res.data[0]['id']).execute()
            else:
                sb.table('influencers').insert(row_data).execute()
        except Exception as e:
            logger.error(f"Failed to insert influencer {b}: {e}")

    logger.info("Database seeding complete!")

if __name__ == "__main__":
    main()
