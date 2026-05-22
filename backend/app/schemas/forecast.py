from datetime import datetime

from pydantic import BaseModel


class ForecastRead(BaseModel):
    entity_name: str
    source_name: str | None = None
    forecast_date: datetime
    predicted_value: float
    horizon: int
    created_at: datetime
