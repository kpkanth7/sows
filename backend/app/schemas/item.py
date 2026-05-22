from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NormalizedEvent(BaseModel):
    source: str
    external_id: str
    title: str
    body_text: str | None = None
    url: str | None = None
    author_name: str | None = None
    score: float = 0.0
    created_at: datetime
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    item_type: str


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    title: str
    body_text: str | None
    url: str | None
    author_name: str | None
    score: float
    created_at: datetime
    item_type: str
