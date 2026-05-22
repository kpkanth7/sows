import os
import httpx
import logging
from datetime import datetime, timezone
from db import get_client, extract_entities
from companies_config import ALL_COMPANIES
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    sb = get_client()
    ph_token = os.environ.get('PRODUCTHUNT_TOKEN')
    
    if not ph_token:
        logger.warning("PRODUCTHUNT_TOKEN not set")
        return
        
    query = """
    query {
      posts(first: 20) {
        edges {
          node {
            id
            name
            tagline
            url
            createdAt
            votesCount
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {ph_token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = httpx.post("https://api.producthunt.com/v2/api/graphql", json={"query": query}, headers=headers, timeout=10)
        resp.raise_for_status()
        
        edges = resp.json().get('data', {}).get('posts', {}).get('edges', [])
        
        for edge in edges:
            node = edge['node']
            title = f"{node['name']}: {node['tagline']}"
            url = node['url']
            
            entities = extract_entities(title, ALL_COMPANIES)
            
            news_item = {
                'title': title,
                'url': url,
                'source': 'producthunt',
                'source_type': 'news',
                'source_credibility_tier': 3,
                'category': 'release',
                'entity_names': entities,
                'sentiment': 0.5,
                'buzz_score': calc_buzz(0.5, entities),
                'published_at': node['createdAt'],
                'hn_score': node.get('votesCount', 0)
            }
            save_news(sb, news_item)
            
    except Exception as e:
        logger.error(f"Error fetching ProductHunt: {e}")

if __name__ == '__main__':
    main()
