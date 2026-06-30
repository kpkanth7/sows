"""GitHub ingestor — trending repos (REST) + per-company releases (GraphQL batched).

Phase 2.8 (2026-05-29): replaced the per-org `/orgs/X/events` REST loop (~80 calls
+ 80s of sleeps) with a single batched GraphQL query that aliases every tracked
`github_org` into one round-trip. Each org returns its 3 most-recently-pushed repos
with the latest release. Cost: ~250 GraphQL points vs ~80 REST calls.
"""
import os
import logging
from itertools import islice
import httpx
from datetime import datetime, timedelta, timezone
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import ALL_COMPANIES, TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES
from ingest_news import calc_buzz, save_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALL_COMPANIES_LIST = TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES
GRAPHQL_URL = "https://api.github.com/graphql"
GRAPHQL_BATCH = 50  # orgs per single GraphQL request


def _chunks(seq, n):
    it = iter(seq)
    while True:
        block = list(islice(it, n))
        if not block:
            return
        yield block


def _search_repositories(sb, headers, query, limit=25):
    """Search GitHub repos with quota accounting and return up to `limit` items."""
    if not check_quota(sb, 'github', 1):
        return []
    try:
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
        resp = httpx.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        log_api_call(sb, 'github', 1)
        return (resp.json().get('items') or [])[:limit]
    except Exception as e:
        logger.error(f"github search error for query={query!r}: {e}")
        return []


def fetch_trending(sb, headers):
    """Surface fast-rising repos and older high-star projects."""
    one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_items = _search_repositories(sb, headers, f"created:>{one_week_ago}", limit=25)
    popular_items = _search_repositories(sb, headers, "stars:>1000", limit=25)

    merged = []
    seen = set()
    for item in recent_items + popular_items:
        full_name = item.get('full_name')
        if not full_name or full_name in seen:
            continue
        seen.add(full_name)
        merged.append(item)

    for item in merged[:30]:
        repo_name = item['full_name']
        stars = item['stargazers_count']
        repo_url = item['html_url']
        desc = item.get('description') or ''

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

        try:
            sb.table('github_signals').insert({
                'repo_name': repo_name,
                'company_id': company_id,
                'repo_url': repo_url,
                'stars': stars,
                'forks': item['forks_count'],
                'stars_this_week': stars,
                'open_issues': item['open_issues_count'],
                'language': item['language'],
                'is_trending': True,
            }).execute()
        except Exception:
            pass

        if stars > 1000:
            save_news(sb, {
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
                'published_at': item['created_at'],
            })


def _build_query(batch):
    """Alias every org as o{i} on the RepositoryOwner interface."""
    parts = []
    for i, (_, org) in enumerate(batch):
        # org is from our config; safe to interpolate. GraphQL string-escape just in case.
        safe = org.replace('"', '\\"')
        parts.append(
            f'o{i}: repositoryOwner(login: "{safe}") {{ '
            f'repositories(first: 3, orderBy: {{field: PUSHED_AT, direction: DESC}}) {{ '
            f'nodes {{ name url stargazerCount pushedAt '
            f'releases(last: 1) {{ nodes {{ tagName publishedAt url description }} }} '
            f'}} }} }}'
        )
    return "query { " + " ".join(parts) + " rateLimit { remaining cost } }"


def fetch_releases_via_graphql(sb, github_token):
    if not github_token:
        logger.warning("GH_PAT/GITHUB_TOKEN not set — skipping GraphQL releases fetch.")
        return
    orgs = [(c, c['github_org']) for c in ALL_COMPANIES_LIST if c.get('github_org')]
    if not orgs:
        return
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
    }

    releases_written = 0
    for batch in _chunks(orgs, GRAPHQL_BATCH):
        if not check_quota(sb, 'github', 1):
            break
        query = _build_query(batch)
        try:
            resp = httpx.post(GRAPHQL_URL, json={"query": query}, headers=headers, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"GraphQL batch error: {e}")
            continue

        body = resp.json()
        cost = ((body.get('data') or {}).get('rateLimit') or {}).get('cost', 1)
        log_api_call(sb, 'github', cost)
        if body.get('errors'):
            logger.warning(f"GraphQL errors: {body['errors'][:2]}")

        data = body.get('data') or {}
        for i, (comp, org) in enumerate(batch):
            owner = data.get(f'o{i}')
            if not owner:
                continue
            repos = (owner.get('repositories') or {}).get('nodes') or []
            res = sb.table('companies').select('id').eq('name', comp['name']).execute()
            if not res.data:
                continue
            company_id = res.data[0]['id']

            for repo in repos:
                repo_name = f"{org}/{repo['name']}"
                releases = (repo.get('releases') or {}).get('nodes') or []
                for rel in releases:
                    tag = rel.get('tagName')
                    if not tag or not rel.get('url'):
                        continue
                    try:
                        sb.table('github_signals').insert({
                            'repo_name': repo_name,
                            'company_id': company_id,
                            'repo_url': repo['url'],
                            'stars': repo.get('stargazerCount'),
                            'latest_release': tag,
                            'release_date': rel.get('publishedAt'),
                        }).execute()
                    except Exception:
                        pass

                    body_text = (rel.get('description') or '').strip()
                    if len(body_text) > 300:
                        body_text = body_text[:297] + "..."
                    save_news(sb, {
                        'title': f"New Release: {repo_name} {tag}",
                        'summary': body_text or f"New release {tag} for {repo_name}.",
                        'url': rel['url'],
                        'source': 'github',
                        'source_type': 'code',
                        'source_credibility_tier': 1,
                        'category': 'release',
                        'entity_names': [comp['name']],
                        'sentiment': 0.5,
                        'buzz_score': calc_buzz(0.5, [comp['name']]),
                        'published_at': rel.get('publishedAt'),
                    })
                    releases_written += 1
    logger.info(f"GraphQL releases written: {releases_written}")


def main():
    sb = get_client()
    github_token = os.environ.get('GITHUB_TOKEN')
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    fetch_trending(sb, headers)
    fetch_releases_via_graphql(sb, github_token)


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_github', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_github', 'error', str(e))
        raise
