import httpx

from backend.app.core.config import get_settings
from backend.app.services.normalization_service import build_event


class ProductHuntIngestor:
    source = "producthunt"

    async def fetch(self, limit: int = 25) -> list:
        settings = get_settings()
        if not settings.producthunt_access_token:
            return []
        query = """
        query TodayPosts($first: Int!) {
          posts(first: $first, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                url
                votesCount
                createdAt
                user { name }
              }
            }
          }
        }
        """
        headers = {"Authorization": f"Bearer {settings.producthunt_access_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.producthunt.com/v2/api/graphql",
                headers=headers,
                json={"query": query, "variables": {"first": min(limit, 50)}},
            )
            response.raise_for_status()
            payload = response.json()
        edges = payload.get("data", {}).get("posts", {}).get("edges", [])
        return [
            build_event(
                source=self.source,
                external_id=edge["node"]["id"],
                title=edge["node"].get("name", ""),
                body_text=edge["node"].get("tagline"),
                url=edge["node"].get("url"),
                author_name=(edge["node"].get("user") or {}).get("name"),
                score=edge["node"].get("votesCount"),
                created_at=edge["node"].get("createdAt"),
                raw_payload=edge["node"],
                item_type="product_launch",
            )
            for edge in edges
        ]
