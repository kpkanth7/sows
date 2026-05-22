from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Entity, Summary
from backend.app.utils.text_utils import canonicalize_name

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/latest")
def latest_summaries(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = db.scalars(select(Summary).order_by(desc(Summary.created_at)).limit(limit)).all()
    return [
        {
            "id": summary.id,
            "summary_type": summary.summary_type,
            "content": summary.content,
            "created_at": summary.created_at,
            "entity_id": summary.entity_id,
            "source_id": summary.source_id,
        }
        for summary in rows
    ]


@router.get("/entity/{entity_name}")
def entity_summaries(
    entity_name: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Summary, Entity)
        .join(Entity, Summary.entity_id == Entity.id)
        .where(Entity.canonical_name == canonicalize_name(entity_name))
        .order_by(desc(Summary.created_at))
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "entity_name": entity.name,
            "summary_type": summary.summary_type,
            "content": summary.content,
            "created_at": summary.created_at,
        }
        for summary, entity in rows
    ]
