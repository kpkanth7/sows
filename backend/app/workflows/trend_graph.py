from typing import Any, TypedDict

from sqlalchemy.orm import Session

from backend.app.schemas.item import NormalizedEvent
from backend.app.services.entity_extraction_service import EntityExtractionService, ExtractedEntity
from backend.app.services.forecasting_service import ForecastingService
from backend.app.services.storage_service import StorageService
from backend.app.services.summarization_service import SummarizationService


class TrendState(TypedDict, total=False):
    event: NormalizedEvent
    db: Session
    extracted_entities: list[ExtractedEntity]
    item: Any
    entities: list[Any]
    metrics: list[Any]
    summary: str


def validate_event(state: TrendState) -> TrendState:
    event = NormalizedEvent.model_validate(state["event"])
    return {"event": event}


def extract_entities(state: TrendState) -> TrendState:
    service = EntityExtractionService()
    event = state["event"]
    entities = service.extract(event.title, event.body_text)
    return {"extracted_entities": entities}


def persist_item(state: TrendState) -> TrendState:
    storage = StorageService(state["db"])
    item = storage.upsert_item(state["event"])
    entities = storage.attach_entities(item, state.get("extracted_entities", []))
    metrics = storage.update_metrics(item, entities)
    return {"item": item, "entities": entities, "metrics": metrics}


async def summarize_trend(state: TrendState) -> TrendState:
    entities = state.get("entities", [])
    metrics = state.get("metrics", [])
    if not entities:
        return {}
    signals = [
        {
            "entity_name": metric.entity.name,
            "source_name": metric.source.name,
            "trend_score": metric.trend_score,
            "mention_count": metric.mention_count,
        }
        for metric in metrics
    ]
    summary = await SummarizationService().explain_entity_trend(entities[0].name, signals)
    StorageService(state["db"]).add_summary(
        summary_type="entity",
        content=summary,
        entity_id=entities[0].id,
        source_id=state["item"].source_id,
    )
    return {"summary": summary}


def forecast_trend(state: TrendState) -> TrendState:
    entities = state.get("entities", [])
    if not entities:
        return {}
    storage = StorageService(state["db"])
    forecaster = ForecastingService()
    for entity in entities:
        values = storage.metric_values_for_entity(entity.id)
        if values:
            predictions = forecaster.forecast_next(values, horizon=7)
            storage.replace_forecasts(entity_id=entity.id, predictions=predictions)
    return {}


def build_trend_graph():
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(TrendState)
    workflow.add_node("validate_event", validate_event)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("persist_item", persist_item)
    workflow.add_node("summarize_trend", summarize_trend)
    workflow.add_node("forecast_trend", forecast_trend)

    workflow.set_entry_point("validate_event")
    workflow.add_edge("validate_event", "extract_entities")
    workflow.add_edge("extract_entities", "persist_item")
    workflow.add_edge("persist_item", "summarize_trend")
    workflow.add_edge("summarize_trend", "forecast_trend")
    workflow.add_edge("forecast_trend", END)
    return workflow.compile()


async def process_event(event: NormalizedEvent, db: Session) -> dict:
    graph = build_trend_graph()
    return await graph.ainvoke({"event": event, "db": db})
