import os
import time
import httpx
import logging
from datetime import datetime, timedelta, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import ALL_COMPANIES, TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALL_COMPANIES_LIST = TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES

def main():
    sb = get_client()
    github_token = os.environ.get('GITHUB_TOKEN')
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        
    if not check_quota(sb, 'github', 1):
        logger.warning("GitHub quota limit reached")
        return

    try:
        one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
        url = f"https://api.github.com/search/repositories?q=created:>{one_week_ago}&sort=stars&order=desc"
        
        resp = httpx.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        log_api_call(sb, 'github', 1)
        
        items = resp.json().get('items', [])
        
        for item in items[:30]:
            repo_name = item['full_name']
            stars = item['stargazers_count']
            repo_url = item['html_url']
            desc = item.get('description', '') or ''
            
            entities = extract_entities(desc, ALL_COMPANIES)
            
            company_id = None
            org_name = repo_name.split('/')[0].lower()
            
            for comp in ALL_COMPANIES_LIST:
                if comp.get('github_org') and comp['github_org'].lower() == org_name:
                    res = sb.table('companies').select('id').eq('name', comp['name']).execute()
                    if res.data:
                        company_id = res.data[0]['id']
                        entities.append(comp['name'])
                    break
                    
            sb.table('github_signals').insert({
                'repo_name': repo_name,
                'company_id': company_id,
                'repo_url': repo_url,
                'stars': stars,
                'forks': item['forks_count'],
                'stars_this_week': stars,
                'open_issues': item['open_issues_count'],
                'language': item['language'],
                'is_trending': True
            }).execute()
            
            if stars > 1000:
                news_item = {
                    'title': f"Trending Repo: {repo_name} ({stars} stars)",
                    'summary': desc or f"Trending repository {repo_name} with {stars} stars.",
                    'url': repo_url,
                    'source': 'github',
                    'source_type': 'code',
                    'source_credibility_tier': 2,
                    'category': 'opensource',
                    'entity_names': list(set(entities)),
                    'sentiment': 0.5,
                    'buzz_score': calc_buzz(0.5, list(set(entities))),
                    'published_at': item['created_at']
                }
                save_news(sb, news_item)
                
    except Exception as e:
        logger.error(f"Error fetching github trending: {e}")

    for comp in ALL_COMPANIES_LIST:
        org = comp.get('github_org')
        if not org:
            continue
            
        if not check_quota(sb, 'github', 1):
            break
            
        try:
            url = f"https://api.github.com/orgs/{org}/events"
            resp = httpx.get(url, headers=headers, timeout=10)
            if resp.status_code == 404:
                url = f"https://api.github.com/users/{org}/events"
                resp = httpx.get(url, headers=headers, timeout=10)
                
            if resp.status_code == 200:
                log_api_call(sb, 'github', 1)
                events = resp.json()
                for event in events:
                    if event['type'] == 'ReleaseEvent':
                        repo_name = event['repo']['name']
                        release = event['payload']['release']
                        
                        res = sb.table('companies').select('id').eq('name', comp['name']).execute()
                        if res.data:
                            company_id = res.data[0]['id']
                            
                            sb.table('github_signals').insert({
                                'repo_name': repo_name,
                                'company_id': company_id,
                                'repo_url': release['html_url'],
                                'latest_release': release['tag_name'],
                                'release_date': release['published_at']
                            }).execute()
                            
                            rel_body = release.get('body') or ''
                            if len(rel_body) > 300:
                                rel_body = rel_body[:297] + "..."
                            
                            news_item = {
                                'title': f"New Release: {repo_name} {release['tag_name']}",
                                'summary': rel_body or f"New release {release['tag_name']} for {repo_name}.",
                                'url': release['html_url'],
                                'source': 'github',
                                'source_type': 'code',
                                'source_credibility_tier': 1,
                                'category': 'release',
                                'entity_names': [comp['name']],
                                'sentiment': 0.5,
                                'buzz_score': calc_buzz(0.5, [comp['name']]),
                                'published_at': release['published_at']
                            }
                            save_news(sb, news_item)
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error fetching github events for {org}: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_github', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_github', 'error', str(e))
        raise
