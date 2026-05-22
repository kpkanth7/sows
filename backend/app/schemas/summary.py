from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary_type: str
    content: str
    created_at: datetime
    entity_id: int | None = None
    source_id: int | None = None
