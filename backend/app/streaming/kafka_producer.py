import json
import logging
from typing import Any

from pydantic import BaseModel

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self) -> None:
        from kafka import KafkaProducer

        settings = get_settings()
        self._producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8") if value else None,
        )

    def send_event(self, topic: str, event: BaseModel | dict[str, Any], key: str | None = None) -> None:
        payload = event.model_dump(mode="json") if isinstance(event, BaseModel) else event
        logger.info("Publishing event to %s: %s", topic, payload.get("external_id"))
        self._producer.send(topic, value=payload, key=key)

    def flush(self) -> None:
        self._producer.flush()
