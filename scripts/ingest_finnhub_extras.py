"""Finnhub extra-endpoint ingestor — earnings calendar, insider transactions,
analyst recommendations, upgrade/downgrade actions.

All free-tier endpoints on the same Finnhub key already used by ingest_stocks.
Run daily. Foreign tickers (.HK / .NS / .KS / .SZ / .AX) lack Finnhub coverage —
errors are swallowed so one bad ticker can't break the batch.

Free tier: 60 calls/min — we sleep ~1.1s between calls. Quota-gated via
check_quota('finnhub') so we exit cleanly if the daily budget is hit.
"""
import os
import time
import logging
from datetime import datetime, date, timedelta, timezone
import finnhub
from db import get_client, check_quota, log_api_call
from companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CALL_SLEEP = 1.1  # seconds — keeps us under Finnhub 60/min free-tier rate limit


def _public_tickers(sb):
    """Resolve (company_id, ticker) for every tracked public company from the DB."""
    all_cfg = TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES
    public = [c for c in all_cfg if not c['is_private'] and c.get('ticker')]
    names = [c['name'] for c in public]
    rows = sb.table('companies').select('id,name,ticker').in_('name', names).execute().data
    return [(r['id'], r['ticker']) for r in rows]


def fetch_earnings_calendar(sb, client):
    """One call covers all companies in the next ~60 days."""
    if not check_quota(sb, 'finnhub'):
        return
    try:
        today = date.today().strftime('%Y-%m-%d')
        end = (date.today() + timedelta(days=60)).strftime('%Y-%m-%d')
        data = client.earnings_calendar(_from=today, to=end, symbol=None)
        log_api_call(sb, 'finnhub')
        time.sleep(CALL_SLEEP)
    except Exception as e:
        logger.error(f"earnings_calendar error: {e}")
        return

    rows = data.get('earningsCalendar') or []
    # Map ticker -> company_id once.
    ticker_to_id = {t: cid for cid, t in _public_tickers(sb)}
    upserts = []
    for r in rows:
        cid = ticker_to_id.get(r.get('symbol'))
        if not cid or not r.get('date'):
            continue
        upserts.append({
            'company_id': cid,
            'earnings_date': r['date'],
            'eps_estimate': r.get('epsEstimate'),
            'eps_actual': r.get('epsActual'),
            'revenue_estimate': r.get('revenueEstimate'),
            'revenue_actual': r.get('revenueActual'),
            'hour': r.get('hour'),
        })
    if upserts:
        sb.table('earnings_calendar').upsert(upserts, on_conflict='company_id,earnings_date').execute()
    logger.info(f"earnings_calendar: upserted {len(upserts)} rows.")


def fetch_insider_transactions(sb, client, company_id: str, ticker: str):
    if not check_quota(sb, 'finnhub'):
        return 0
    try:
        # Finnhub returns most-recent transactions; no date range required.
        data = client.stock_insider_transactions(symbol=ticker)
        log_api_call(sb, 'finnhub')
        time.sleep(CALL_SLEEP)
    except Exception as e:
        logger.debug(f"insider error {ticker}: {e}")
        return 0

    rows = (data or {}).get('data') or []
    if not rows:
        return 0
    payload = []
    seen = set()
    for r in rows[:25]:  # cap per company
        row = {
            'company_id': company_id,
            'person': r.get('name'),
            'position': r.get('position'),
            'transaction_type': r.get('transactionCode'),
            'share': r.get('share'),
            'change': r.get('change'),
            'transaction_date': r.get('transactionDate'),
            'filing_date': r.get('filingDate'),
        }
        key = (row['company_id'], row['person'], row['transaction_date'], row['share'], row['change'])
        if key in seen:
            continue
        seen.add(key)
        payload.append(row)
    if payload:
        sb.table('insider_transactions').upsert(
            payload, on_conflict='company_id,person,transaction_date,share,change'
        ).execute()
    return len(payload)


def fetch_recommendations(sb, client, company_id: str, ticker: str):
    if not check_quota(sb, 'finnhub'):
        return 0
    try:
        data = client.recommendation_trends(symbol=ticker)
        log_api_call(sb, 'finnhub')
        time.sleep(CALL_SLEEP)
    except Exception as e:
        logger.debug(f"recommendation error {ticker}: {e}")
        return 0

    if not data:
        return 0
    payload = []
    seen = set()
    for r in data:
        row = {
            'company_id': company_id,
            'period': r.get('period'),
            'strong_buy': r.get('strongBuy'),
            'buy': r.get('buy'),
            'hold': r.get('hold'),
            'sell': r.get('sell'),
            'strong_sell': r.get('strongSell'),
        }
        key = (row['company_id'], row['period'])
        if key in seen:
            continue
        seen.add(key)
        payload.append(row)
    if payload:
        sb.table('analyst_recommendations').upsert(payload, on_conflict='company_id,period').execute()
    return len(payload)


def fetch_upgrade_downgrade(sb, client, company_id: str, ticker: str):
    if not check_quota(sb, 'finnhub'):
        return 0
    try:
        end = date.today().strftime('%Y-%m-%d')
        start = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')
        data = client.stock_upgrade_downgrade(symbol=ticker, _from=start, to=end)
        log_api_call(sb, 'finnhub')
        time.sleep(CALL_SLEEP)
    except Exception as e:
        logger.debug(f"upgrade/downgrade error {ticker}: {e}")
        return 0

    if not data:
        return 0
    payload = []
    seen = set()
    for r in data:
        # Finnhub gradeTime is unix seconds
        ts = r.get('gradeTime')
        action_date = (datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
                       if ts else None)
        row = {
            'company_id': company_id,
            'action': r.get('action'),
            'from_grade': r.get('fromGrade'),
            'to_grade': r.get('toGrade'),
            'firm': r.get('company'),
            'action_date': action_date,
        }
        key = (row['company_id'], row['firm'], row['action_date'], row['to_grade'])
        if key in seen:
            continue
        seen.add(key)
        payload.append(row)
    if payload:
        sb.table('upgrade_downgrade').upsert(
            payload, on_conflict='company_id,firm,action_date,to_grade'
        ).execute()
    return len(payload)


def main():
    sb = get_client()
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        logger.warning("FINNHUB_API_KEY not set — skipping finnhub extras.")
        return
    client = finnhub.Client(api_key=api_key)

    fetch_earnings_calendar(sb, client)

    totals = {'insider': 0, 'recs': 0, 'upd': 0, 'tickers': 0}
    for cid, ticker in _public_tickers(sb):
        totals['tickers'] += 1
        totals['insider'] += fetch_insider_transactions(sb, client, cid, ticker)
        totals['recs'] += fetch_recommendations(sb, client, cid, ticker)
        totals['upd'] += fetch_upgrade_downgrade(sb, client, cid, ticker)
    logger.info(f"finnhub_extras done. {totals}")


if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_finnhub_extras', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_finnhub_extras', 'error', str(e))
        raise
