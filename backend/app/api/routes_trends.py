from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Entity, Metric, Source
from backend.app.utils.text_utils import canonicalize_name

router = APIRouter(prefix="/trends", tags=["trends"])


def _trend_rows(
    db: Session,
    *,
    entity_type: str,
    limit: int,
    source: str | None = None,
) -> list[dict]:
    stmt = (
        select(Metric, Entity, Source)
        .join(Entity, Metric.entity_id == Entity.id)
        .join(Source, Metric.source_id == Source.id)
        .where(Entity.entity_type == entity_type)
        .order_by(desc(Metric.trend_score), desc(Metric.metric_date))
        .limit(limit)
    )
    if source:
        stmt = stmt.where(Source.name == source)
    rows = db.execute(stmt).all()
    return [
        {
            "entity_name": entity.name,
            "entity_type": entity.entity_type,
            "source_name": source_model.name,
            "metric_date": metric.metric_date,
            "mention_count": metric.mention_count,
            "score_sum": metric.score_sum,
            "item_count": metric.item_count,
            "trend_score": metric.trend_score,
        }
        for metric, entity, source_model in rows
    ]


@router.get("/technologies")
def top_technologies(
    limit: int = Query(default=20, ge=1, le=100),
    source: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    return _trend_rows(db, entity_type="technology", limit=limit, source=source)


@router.get("/companies")
def top_companies(
    limit: int = Query(default=20, ge=1, le=100),
    source: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    return _trend_rows(db, entity_type="company", limit=limit, source=source)


@router.get("/compare")
def compare_entities(
    left: str,
    right: str,
    db: Session = Depends(get_db),
) -> dict:
    names = [canonicalize_name(left), canonicalize_name(right)]
    stmt = (
        select(Metric, Entity, Source)
        .join(Entity, Metric.entity_id == Entity.id)
        .join(Source, Metric.source_id == Source.id)
        .where(Entity.canonical_name.in_(names))
        .order_by(Metric.metric_date)
    )
    rows = db.execute(stmt).all()
    series = [
        {
            "entity_name": entity.name,
            "source_name": source.name,
            "metric_date": metric.metric_date,
            "trend_score": metric.trend_score,
            "mention_count": metric.mention_count,
        }
        for metric, entity, source in rows
    ]
    return {"left": left, "right": right, "series": series}
