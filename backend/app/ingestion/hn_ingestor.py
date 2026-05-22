import httpx

from backend.app.services.normalization_service import build_event


class HackerNewsIngestor:
    source = "hn"
    base_url = "https://hacker-news.firebaseio.com/v0"

    async def fetch(self, limit: int = 25) -> list:
        async with httpx.AsyncClient(timeout=20) as client:
            ids_response = await client.get(f"{self.base_url}/topstories.json")
            ids_response.raise_for_status()
            story_ids = ids_response.json()[:limit]
            events = []
            for story_id in story_ids:
                item_response = await client.get(f"{self.base_url}/item/{story_id}.json")
                item_response.raise_for_status()
                item = item_response.json()
                events.append(
                    build_event(
                        source=self.source,
                        external_id=item["id"],
                        title=item.get("title", ""),
                        body_text=item.get("text"),
                        url=item.get("url"),
                        author_name=item.get("by"),
                        score=item.get("score"),
                        created_at=item.get("time"),
                        raw_payload=item,
                        item_type=item.get("type", "story"),
                    )
                )
        return events
