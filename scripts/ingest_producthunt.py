import os
import httpx
import logging
from db import get_client, extract_entities
from companies_config import ALL_COMPANIES
from ingest_news import calc_buzz, save_news, sentiment_text
from textblob import TextBlob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.producthunt.com/v2/oauth/token"
GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"


def get_producthunt_token() -> str | None:
    token = os.environ.get('PRODUCTHUNT_TOKEN')
    if token:
        return token

    client_id = os.environ.get('PRODUCTHUNT_CLIENT_ID')
    client_secret = os.environ.get('PRODUCTHUNT_CLIENT_SECRET')
    if not client_id or not client_secret:
        logger.warning("Product Hunt credentials not set")
        return None

    resp = httpx.post(
        TOKEN_URL,
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    access_token = resp.json().get("access_token")
    if not access_token:
        raise RuntimeError("Product Hunt token response missing access_token")
    return access_token


def main():
    sb = get_client()
    ph_token = get_producthunt_token()
    
    if not ph_token:
        logger.warning("Product Hunt token unavailable")
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
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        resp = httpx.post(GRAPHQL_URL, json={"query": query}, headers=headers, timeout=10)
        resp.raise_for_status()
        
        edges = resp.json().get('data', {}).get('posts', {}).get('edges', [])
        
        for edge in edges:
            node = edge['node']
            title = f"{node['name']}: {node['tagline']}"
            url = node['url']
            
            entities = extract_entities(title, ALL_COMPANIES)
            sentiment = TextBlob(sentiment_text(title, node.get('tagline'))).sentiment.polarity
            
            news_item = {
                'title': title,
                'url': url,
                'source': 'producthunt',
                'source_type': 'news',
                'source_credibility_tier': 3,
                'category': 'release',
                'entity_names': entities,
                'sentiment': sentiment,
                'buzz_score': calc_buzz(sentiment, entities),
                'published_at': node['createdAt'],
                'hn_score': node.get('votesCount', 0)
            }
            save_news(sb, news_item)
            
    except Exception as e:
        logger.error(f"Error fetching ProductHunt: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_producthunt', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_producthunt', 'error', str(e))
        raise
