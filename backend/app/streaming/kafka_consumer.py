import asyncio
import json
import logging

from backend.app.core.config import get_settings
from backend.app.core.database import SessionLocal
from backend.app.schemas.item import NormalizedEvent
from backend.app.workflows.trend_graph import process_event

logger = logging.getLogger(__name__)


def consume_topics(topics: list[str]) -> None:
    from kafka import KafkaConsumer

    settings = get_settings()
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        group_id="tech-intel-consumers",
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
    logger.info("Listening to Kafka topics: %s", ", ".join(topics))
    
    loop = asyncio.get_event_loop()
    
    for message in consumer:
        event = NormalizedEvent.model_validate(message.value)
        with SessionLocal() as db:
            loop.run_until_complete(process_event(event, db))
            db.commit()
