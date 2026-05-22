from datetime import datetime
from typing import Any

from backend.app.schemas.item import NormalizedEvent
from backend.app.utils.text_utils import compact_text
from backend.app.utils.time_utils import parse_timestamp


def build_event(
    *,
    source: str,
    external_id: str,
    title: str,
    item_type: str,
    created_at: datetime | str | int | float | None,
    body_text: str | None = None,
    url: str | None = None,
    author_name: str | None = None,
    score: float | int | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> NormalizedEvent:
    return NormalizedEvent(
        source=source,
        external_id=str(external_id),
        title=compact_text(title, 500),
        body_text=compact_text(body_text),
        url=url,
        author_name=author_name,
        score=float(score or 0),
        created_at=parse_timestamp(created_at),
        raw_payload=raw_payload or {},
        item_type=item_type,
    )
