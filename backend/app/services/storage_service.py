from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models import Entity, Forecast, Item, ItemEntity, Metric, Source, Summary
from backend.app.schemas.item import NormalizedEvent
from backend.app.services.entity_extraction_service import ExtractedEntity
from backend.app.services.trend_scoring_service import TrendScoringService
from backend.app.utils.time_utils import start_of_day


SOURCE_CATALOG = {
    "github": ("GitHub", "https://api.github.com"),
    "hn": ("Hacker News", "https://hacker-news.firebaseio.com"),
    "stackexchange": ("Stack Exchange", "https://api.stackexchange.com"),
    "arxiv": ("arXiv", "https://export.arxiv.org"),
    "producthunt": ("Product Hunt", "https://api.producthunt.com"),
    "gdelt": ("GDELT", "https://api.gdeltproject.org"),
}


class StorageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.scoring = TrendScoringService()

    def get_or_create_source(self, name: str) -> Source:
        source = self.db.scalar(select(Source).where(Source.name == name))
        if source:
            return source
        display_name, base_url = SOURCE_CATALOG.get(name, (name.title(), None))
        source = Source(name=name, display_name=display_name, base_url=base_url)
        self.db.add(source)
        self.db.flush()
        return source

    def get_or_create_entity(self, extracted: ExtractedEntity) -> Entity:
        entity = self.db.scalar(
            select(Entity).where(
                Entity.canonical_name == extracted.canonical_name,
                Entity.entity_type == extracted.entity_type,
            )
        )
        if entity:
            return entity
        entity = Entity(
            name=extracted.name,
            entity_type=extracted.entity_type,
            canonical_name=extracted.canonical_name,
        )
        self.db.add(entity)
        self.db.flush()
        return entity

    def upsert_item(self, event: NormalizedEvent) -> Item:
        source = self.get_or_create_source(event.source)
        item = self.db.scalar(
            select(Item).where(Item.source_id == source.id, Item.external_id == event.external_id)
        )
        if item:
            return item
        item = Item(
            source_id=source.id,
            external_id=event.external_id,
            title=event.title,
            body_text=event.body_text,
            url=event.url,
            author_name=event.author_name,
            score=event.score,
            created_at=event.created_at,
            raw_payload=event.raw_payload,
            item_type=event.item_type,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def attach_entities(self, item: Item, entities: Sequence[ExtractedEntity]) -> list[Entity]:
        stored_entities: list[Entity] = []
        for extracted in entities:
            entity = self.get_or_create_entity(extracted)
            stored_entities.append(entity)
            existing = self.db.scalar(
                select(ItemEntity).where(ItemEntity.item_id == item.id, ItemEntity.entity_id == entity.id)
            )
            if not existing:
                self.db.add(ItemEntity(item_id=item.id, entity_id=entity.id))
        self.db.flush()
        return stored_entities

    def update_metrics(self, item: Item, entities: Sequence[Entity]) -> list[Metric]:
        metrics: list[Metric] = []
        metric_date = start_of_day(item.created_at)
        for entity in entities:
            metric = self.db.scalar(
                select(Metric).where(
                    Metric.entity_id == entity.id,
                    Metric.source_id == item.source_id,
                    Metric.metric_date == metric_date,
                )
            )
            if not metric:
                metric = Metric(
                    entity_id=entity.id,
                    source_id=item.source_id,
                    metric_date=metric_date,
                    mention_count=0,
                    item_count=0,
                    score_sum=0.0,
                )
                self.db.add(metric)
            metric.mention_count += 1
            metric.item_count += 1
            metric.score_sum += item.score
            scored = self.scoring.score(metric.mention_count, metric.score_sum, metric.item_count)
            metric.trend_score = scored.trend_score
            metrics.append(metric)
        self.db.flush()
        return metrics

    def add_summary(
        self,
        *,
        summary_type: str,
        content: str,
        entity_id: int | None = None,
        source_id: int | None = None,
    ) -> Summary:
        summary = Summary(
            summary_type=summary_type,
            content=content,
            entity_id=entity_id,
            source_id=source_id,
        )
        self.db.add(summary)
        self.db.flush()
        return summary

    def replace_forecasts(
        self,
        *,
        entity_id: int,
        predictions: list[dict],
        source_id: int | None = None,
    ) -> list[Forecast]:
        stmt = delete(Forecast).where(Forecast.entity_id == entity_id)
        if source_id is None:
            stmt = stmt.where(Forecast.source_id.is_(None))
        else:
            stmt = stmt.where(Forecast.source_id == source_id)
        self.db.execute(stmt)
        forecasts: list[Forecast] = []
        for prediction in predictions:
            forecast = Forecast(
                entity_id=entity_id,
                source_id=source_id,
                forecast_date=prediction["forecast_date"],
                predicted_value=prediction["predicted_value"],
                horizon=prediction["horizon"],
            )
            self.db.add(forecast)
            forecasts.append(forecast)
        self.db.flush()
        return forecasts

    def metric_values_for_entity(self, entity_id: int, source_id: int | None = None) -> list[float]:
        stmt = select(Metric).where(Metric.entity_id == entity_id).order_by(Metric.metric_date)
        if source_id is not None:
            stmt = stmt.where(Metric.source_id == source_id)
        return [metric.trend_score for metric in self.db.scalars(stmt).all()]


def seed_sources(db: Session) -> None:
    storage = StorageService(db)
    for source_name in SOURCE_CATALOG:
        storage.get_or_create_source(source_name)
    db.commit()
