from datetime import datetime

from pydantic import BaseModel


class TrendMetricRead(BaseModel):
    entity_name: str
    entity_type: str
    source_name: str
    metric_date: datetime
    mention_count: int
    score_sum: float
    item_count: int
    trend_score: float
