import xml.etree.ElementTree as ET

import httpx

from backend.app.services.normalization_service import build_event


class ArxivIngestor:
    source = "arxiv"

    async def fetch(self, limit: int = 25) -> list:
        params = {
            "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.SE",
            "start": 0,
            "max_results": min(limit, 100),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://export.arxiv.org/api/query", params=params)
            response.raise_for_status()
        root = ET.fromstring(response.text)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        events = []
        for entry in root.findall("atom:entry", namespace):
            external_id = entry.findtext("atom:id", default="", namespaces=namespace).rsplit("/", maxsplit=1)[-1]
            title = entry.findtext("atom:title", default="", namespaces=namespace)
            summary = entry.findtext("atom:summary", default="", namespaces=namespace)
            author = entry.find("atom:author/atom:name", namespace)
            published = entry.findtext("atom:published", default=None, namespaces=namespace)
            events.append(
                build_event(
                    source=self.source,
                    external_id=external_id,
                    title=title,
                    body_text=summary,
                    url=entry.findtext("atom:id", default=None, namespaces=namespace),
                    author_name=author.text if author is not None else None,
                    score=1,
                    created_at=published,
                    raw_payload={"title": title, "summary": summary},
                    item_type="paper",
                )
            )
        return events
