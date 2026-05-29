import os
import time
import argparse
import logging
from datetime import datetime, date, timedelta, timezone
import httpx
import finnhub
import yfinance as yf
from textblob import TextBlob
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES, ALL_COMPANIES
from ingest_news import save_news, calc_buzz


# Stooq fallback (free, no key, broad global coverage). yfinance suffix -> stooq suffix.
STOOQ_SUFFIX = {
    '.HK': '.hk',   # Hong Kong
    '.KS': '.kr',   # Korea
    '.NS': '.in',   # India NSE
    '.SZ': '.cn',   # Shenzhen
    '.SS': '.cn',   # Shanghai
    '.AX': '.au',   # Australia
    '.TO': '.ca',   # Toronto
    '.PA': '.fr',   # Paris
    '.L':  '.uk',   # London
}


def _stooq_ticker(t: str) -> str:
    for src, dst in STOOQ_SUFFIX.items():
        if t.endswith(src):
            return t[:-len(src)].lower() + dst
    return t.lower() + '.us'


def fetch_stooq_price(ticker: str):
    """Last-resort price fallback. Stooq returns a single-row CSV; we read 'Close'.
    Returns (price, change_pct_or_None). change_pct unavailable from this endpoint."""
    try:
        s = _stooq_ticker(ticker)
        url = f"https://stooq.com/q/l/?s={s}&f=sd2t2ohlc&h&e=csv"
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
        lines = r.text.strip().split('\n')
        if len(lines) < 2:
            return None, None
        cols = lines[1].split(',')
        close = cols[6] if len(cols) >= 7 else None
        if not close or close in ('N/D', ''):
            return None, None
        return float(close), None
    except Exception:
        return None, None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_companies_by_tier(tier: int):
    if tier == 1: return TIER1_COMPANIES
    elif tier == 2: return TIER2_COMPANIES
    elif tier == 3: return TIER3_COMPANIES
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tier', type=int, choices=[1,2,3], default=1)
    args = parser.parse_args()

    sb = get_client()
    companies = get_companies_by_tier(args.tier)
    
    finnhub_client = None
    finnhub_api_key = os.environ.get('FINNHUB_API_KEY')
    if finnhub_api_key:
        finnhub_client = finnhub.Client(api_key=finnhub_api_key)

    if finnhub_client and check_quota(sb, 'finnhub'):
        try:
            today = date.today().strftime('%Y-%m-%d')
            next_month = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            ipo_cal = finnhub_client.ipo_calendar(_from=today, to=next_month)
            log_api_call(sb, 'finnhub')
            time.sleep(1.1)
            logger.info(f"IPO calendar fetched: {len(ipo_cal.get('ipoCalendar', []))} items")
        except Exception as e:
            logger.error(f"Finnhub IPO calendar error: {e}")

    for comp in companies:
        name = comp['name']
        ticker = comp['ticker']
        is_private = comp['is_private']
        sector = comp.get('sector')
        
        # Config is the source of truth for descriptive fields + geography/valuation.
        # Reconciled every run so edits (e.g. Figma private->public, valuation updates)
        # propagate to existing rows. poll_tier is intentionally excluded — it is owned
        # by check_buzz_spikes (buzz promotions), so we never overwrite it here.
        sync = {
            'ticker': ticker,
            'is_private': is_private,
            'sector': sector,
            'is_ai_company': comp.get('is_ai_company', False),
            'github_org': comp.get('github_org'),
            'region': comp.get('region'),
            'last_valuation': comp.get('last_valuation'),
            'valuation_source': comp.get('valuation_source'),
        }

        try:
            res = sb.table('companies').select('id').eq('name', name).execute()
            if not res.data:
                sb.table('companies').insert({'name': name, 'poll_tier': args.tier, **sync}).execute()
                res = sb.table('companies').select('id').eq('name', name).execute()

            company_id = res.data[0]['id']

            # Reconcile descriptive fields for existing + new rows.
            sb.table('companies').update({**sync, 'last_updated': 'now()'}).eq('id', company_id).execute()

            if is_private:
                continue

            if not ticker:
                continue

            price = None
            change_pct = None
            
            if finnhub_client and check_quota(sb, 'finnhub'):
                try:
                    quote = finnhub_client.quote(ticker)
                    log_api_call(sb, 'finnhub')
                    time.sleep(1.1)
                    
                    if quote.get('c'):
                        price = quote['c']
                        change_pct = quote['dp']
                except Exception as e:
                    logger.error(f"Finnhub quote error for {ticker}: {e}")
                    
            if price is None:
                try:
                    stock = yf.Ticker(ticker)
                    # history() works for foreign tickers (.HK/.NS/.KS/.SZ/.AX) where
                    # finnhub (US-only) and .info often return nothing. Try it first.
                    hist = stock.history(period='2d')
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])
                        if len(hist) >= 2:
                            prev = float(hist['Close'].iloc[-2])
                            if prev:
                                change_pct = (price - prev) / prev * 100
                    if price is None:
                        # Fallback to .info for US tickers history may miss intraday on.
                        info = stock.info
                        price = info.get('currentPrice') or info.get('regularMarketPrice')
                        if change_pct is None and info.get('regularMarketChangePercent') is not None:
                            change_pct = info['regularMarketChangePercent'] * 100
                except Exception as e:
                    logger.error(f"Yfinance quote error for {ticker}: {e}")

            # Final fallback: Stooq (free, no key, global). Covers the .HK/.KS/.NS/etc
            # tickers that Finnhub free skips and that yfinance flakes on.
            if price is None:
                px, ch = fetch_stooq_price(ticker)
                if px is not None:
                    price = px
                    if ch is not None:
                        change_pct = ch

            if price is not None:
                sb.table('companies').update({
                    'stock_price': price,
                    'change_pct_24h': change_pct,
                    'last_updated': 'now()',
                }).eq('id', company_id).execute()
                
                sb.table('stock_snapshots').insert({
                    'company_id': company_id,
                    'price': price,
                    'change_pct': change_pct
                }).execute()

            if finnhub_client and check_quota(sb, 'finnhub'):
                try:
                    today = date.today().strftime('%Y-%m-%d')
                    news = finnhub_client.company_news(ticker, _from=today, to=today)
                    log_api_call(sb, 'finnhub')
                    time.sleep(1.1)

                    for article in (news or [])[:10]:
                        headline = article.get('headline')
                        link = article.get('url')
                        if not headline or not link:
                            continue
                        entities = extract_entities(headline, ALL_COMPANIES)
                        if name not in entities:
                            entities.append(name)
                        sentiment = TextBlob(headline).sentiment.polarity
                        ts = article.get('datetime')
                        published = (
                            datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                            if ts else datetime.now(timezone.utc).isoformat()
                        )
                        save_news(sb, {
                            'title': headline,
                            'url': link,
                            'source': 'finnhub',
                            'source_type': 'news',
                            'source_credibility_tier': 2,
                            'entity_names': entities,
                            'sentiment': sentiment,
                            'buzz_score': calc_buzz(sentiment, entities),
                            'summary': article.get('summary'),
                            'image_url': article.get('image'),
                            'published_at': published,
                        })
                except Exception as e:
                    logger.error(f"Finnhub news error for {ticker}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing stock for {name}: {e}")

if __name__ == '__main__':
    from db import get_client, record_health
    try:
        main()
        record_health(get_client(), 'ingest_stocks', 'ok')
    except Exception as e:
        record_health(get_client(), 'ingest_stocks', 'error', str(e))
        raise
