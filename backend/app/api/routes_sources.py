from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Item, Source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/status")
def source_status(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Source).order_by(Source.name)).all()
    return [
        {
            "name": source.name,
            "display_name": source.display_name,
            "status": source.status,
            "last_checked_at": source.last_checked_at,
        }
        for source in rows
    ]


def _latest_for_source(source_name: str, limit: int, db: Session) -> list[dict]:
    stmt = (
        select(Item, Source)
        .join(Source, Item.source_id == Source.id)
        .where(Source.name == source_name)
        .order_by(desc(Item.created_at))
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "source": source.name,
            "external_id": item.external_id,
            "title": item.title,
            "url": item.url,
            "score": item.score,
            "created_at": item.created_at,
            "item_type": item.item_type,
        }
        for item, source in rows
    ]


@router.get("/{source_name}/latest")
def latest_source_items(
    source_name: str,
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    return _latest_for_source(source_name, limit, db)


@router.get("/github/latest")
def latest_github(limit: int = Query(default=25, ge=1, le=100), db: Session = Depends(get_db)) -> list[dict]:
    return _latest_for_source("github", limit, db)


@router.get("/hn/latest")
def latest_hn(limit: int = Query(default=25, ge=1, le=100), db: Session = Depends(get_db)) -> list[dict]:
    return _latest_for_source("hn", limit, db)


@router.get("/stackexchange/latest")
def latest_stackexchange(limit: int = Query(default=25, ge=1, le=100), db: Session = Depends(get_db)) -> list[dict]:
    return _latest_for_source("stackexchange", limit, db)


@router.get("/arxiv/latest")
def latest_arxiv(limit: int = Query(default=25, ge=1, le=100), db: Session = Depends(get_db)) -> list[dict]:
    return _latest_for_source("arxiv", limit, db)
