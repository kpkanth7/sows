import httpx

from backend.app.core.config import get_settings
from backend.app.services.normalization_service import build_event


class StackExchangeIngestor:
    source = "stackexchange"

    async def fetch(self, limit: int = 25) -> list:
        settings = get_settings()
        params = {
            "order": "desc",
            "sort": "activity",
            "site": "stackoverflow",
            "pagesize": min(limit, 100),
            "filter": "default",
        }
        if settings.stackexchange_key:
            params["key"] = settings.stackexchange_key
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.stackexchange.com/2.3/questions", params=params)
            response.raise_for_status()
            payload = response.json()
        return [
            build_event(
                source=self.source,
                external_id=item["question_id"],
                title=item.get("title", ""),
                body_text=" ".join(item.get("tags", [])),
                url=item.get("link"),
                author_name=item.get("owner", {}).get("display_name"),
                score=item.get("score"),
                created_at=item.get("creation_date"),
                raw_payload=item,
                item_type="question",
            )
            for item in payload.get("items", [])
        ]
