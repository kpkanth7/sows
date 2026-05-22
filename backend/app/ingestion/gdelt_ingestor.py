import httpx

from backend.app.services.normalization_service import build_event


class GDELTIngestor:
    source = "gdelt"

    async def fetch(self, limit: int = 25) -> list:
        params = {
            "query": "technology OR artificial intelligence OR software",
            "mode": "artlist",
            "format": "json",
            "maxrecords": min(limit, 250),
            "sort": "hybridrel",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params)
            response.raise_for_status()
            payload = response.json()
        return [
            build_event(
                source=self.source,
                external_id=item.get("url", item.get("title", "")),
                title=item.get("title", ""),
                body_text=item.get("seendate"),
                url=item.get("url"),
                author_name=item.get("domain"),
                score=1,
                created_at=item.get("seendate"),
                raw_payload=item,
                item_type="news_event",
            )
            for item in payload.get("articles", [])
        ]
