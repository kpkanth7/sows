from backend.app.core.config import get_settings


def source_topic(source: str) -> str:
    settings = get_settings()
    topics = settings.kafka_topics
    if source not in topics:
        raise KeyError(f"No Kafka topic configured for source '{source}'")
    return topics[source]


def all_source_topics() -> list[str]:
    settings = get_settings()
    return [
        settings.kafka_topic_github,
        settings.kafka_topic_hn,
        settings.kafka_topic_stack,
        settings.kafka_topic_arxiv,
        settings.kafka_topic_producthunt,
        settings.kafka_topic_gdelt,
    ]
