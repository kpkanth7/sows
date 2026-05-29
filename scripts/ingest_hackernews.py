"""Dedicated HackerNews poller (every ~20 min).

HN Algolia is unlimited + real-time — breaking software/AI news lands here first.
Reuses fetch_hn from ingest_news (dedup-aware via save_news), so frequent runs are
cheap: re-seen stories are skipped, only new/improved ones written.
"""
import logging
from db import get_client
from ingest_news import fetch_hn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    sb = get_client()
    fetch_hn(sb)
    logger.info("ingest_hackernews completed.")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_hackernews', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_hackernews', 'error', str(e))
        raise
