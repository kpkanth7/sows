from backend.app.core.database import init_db
from backend.app.core.logging_config import configure_logging
from backend.app.services.storage_service import seed_sources
from backend.app.core.database import SessionLocal
from backend.app.streaming.kafka_consumer import consume_topics
from backend.app.streaming.topics import all_source_topics


def main() -> None:
    configure_logging()
    init_db()
    with SessionLocal() as db:
        seed_sources(db)
    consume_topics(all_source_topics())


if __name__ == "__main__":
    main()
