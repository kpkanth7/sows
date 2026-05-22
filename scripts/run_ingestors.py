import argparse
import asyncio
import logging

from backend.app.core.database import SessionLocal, init_db
from backend.app.core.logging_config import configure_logging
from backend.app.ingestion.arxiv_ingestor import ArxivIngestor
from backend.app.ingestion.gdelt_ingestor import GDELTIngestor
from backend.app.ingestion.github_ingestor import GitHubIngestor
from backend.app.ingestion.hn_ingestor import HackerNewsIngestor
from backend.app.ingestion.producthunt_ingestor import ProductHuntIngestor
from backend.app.ingestion.stackexchange_ingestor import StackExchangeIngestor
from backend.app.services.storage_service import seed_sources
from backend.app.streaming.kafka_producer import EventProducer
from backend.app.streaming.topics import source_topic
from backend.app.workflows.trend_graph import process_event

logger = logging.getLogger(__name__)

INGESTORS = [
    GitHubIngestor(),
    HackerNewsIngestor(),
    StackExchangeIngestor(),
    ArxivIngestor(),
    ProductHuntIngestor(),
    GDELTIngestor(),
]


async def run(limit: int, direct_db: bool) -> None:
    init_db()
    with SessionLocal() as db:
        seed_sources(db)

    producer = None if direct_db else EventProducer()
    for ingestor in INGESTORS:
        try:
            events = await ingestor.fetch(limit=limit)
            logger.info("%s returned %s events", ingestor.source, len(events))
        except Exception:
            logger.exception("%s ingestion failed", ingestor.source)
            continue

        if direct_db:
            with SessionLocal() as db:
                for event in events:
                    process_event(event, db)
                db.commit()
        else:
            topic = source_topic(ingestor.source)
            for event in events:
                producer.send_event(topic, event, key=event.external_id)

    if producer:
        producer.flush()


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Fetch live source APIs and publish normalized events.")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument(
        "--direct-db",
        action="store_true",
        help="Process events directly through LangGraph without Kafka. Useful for local smoke tests only.",
    )
    args = parser.parse_args()
    asyncio.run(run(args.limit, args.direct_db))


if __name__ == "__main__":
    main()
