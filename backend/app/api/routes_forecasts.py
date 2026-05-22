from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Entity, Forecast, Source
from backend.app.utils.text_utils import canonicalize_name

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("/entity/{entity_name}")
def entity_forecast(
    entity_name: str,
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Forecast, Entity, Source)
        .join(Entity, Forecast.entity_id == Entity.id)
        .outerjoin(Source, Forecast.source_id == Source.id)
        .where(Entity.canonical_name == canonicalize_name(entity_name))
        .order_by(Forecast.forecast_date)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "entity_name": entity.name,
            "source_name": source.name if source else None,
            "forecast_date": forecast.forecast_date,
            "predicted_value": forecast.predicted_value,
            "horizon": forecast.horizon,
            "created_at": forecast.created_at,
        }
        for forecast, entity, source in rows
    ]


@router.get("/top")
def top_forecasts(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Forecast, Entity, Source)
        .join(Entity, Forecast.entity_id == Entity.id)
        .outerjoin(Source, Forecast.source_id == Source.id)
        .order_by(desc(Forecast.created_at), desc(Forecast.predicted_value))
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "entity_name": entity.name,
            "source_name": source.name if source else None,
            "forecast_date": forecast.forecast_date,
            "predicted_value": forecast.predicted_value,
            "horizon": forecast.horizon,
            "created_at": forecast.created_at,
        }
        for forecast, entity, source in rows
    ]
