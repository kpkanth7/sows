"""90-day retention. Deletes news + stock history older than the cutoff to keep
the Supabase free-tier DB small and queries fast.

Scope (decided 2026-05-29): news_items (ingested_at) + stock_snapshots (captured_at).
Run daily via supabase_keepalive.yml.
"""
import logging
from datetime import datetime, timedelta, timezone
from db import get_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RETENTION_DAYS = 90

# (table, timestamp column) pairs to prune.
TARGETS = [
    ("news_items", "ingested_at"),
    ("stock_snapshots", "captured_at"),
]


def prune(sb, table: str, ts_col: str, cutoff_iso: str) -> int:
    res = sb.table(table).delete().lt(ts_col, cutoff_iso).execute()
    deleted = len(res.data or [])
    logger.info(f"{table}: deleted {deleted} rows older than {cutoff_iso}")
    return deleted


def main():
    sb = get_client()
    cutoff_iso = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    total = 0
    for table, ts_col in TARGETS:
        try:
            total += prune(sb, table, ts_col, cutoff_iso)
        except Exception as e:
            logger.error(f"Error pruning {table}: {e}")
            raise
    logger.info(f"cleanup_old_data completed. Total deleted: {total}")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'cleanup_old_data', 'ok')
    except Exception as e:
        record_health(get_client(), 'cleanup_old_data', 'error', str(e))
        raise
