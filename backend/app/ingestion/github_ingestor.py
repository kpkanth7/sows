import httpx

from backend.app.core.config import get_settings
from backend.app.services.normalization_service import build_event


class GitHubIngestor:
    source = "github"

    async def fetch(self, limit: int = 25) -> list:
        settings = get_settings()
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        params = {
            "q": "stars:>1000 pushed:>2026-01-01",
            "sort": "updated",
            "order": "desc",
            "per_page": min(limit, 100),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.github.com/search/repositories", headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
        return [
            build_event(
                source=self.source,
                external_id=item["id"],
                title=item["full_name"],
                body_text=item.get("description"),
                url=item.get("html_url"),
                author_name=item.get("owner", {}).get("login"),
                score=item.get("stargazers_count"),
                created_at=item.get("updated_at"),
                raw_payload=item,
                item_type="repository",
            )
            for item in payload.get("items", [])
        ]
