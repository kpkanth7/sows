import os
import time
import argparse
import logging
from datetime import datetime, date, timedelta, timezone
import finnhub
import yfinance as yf
from textblob import TextBlob
from db import get_client, check_quota, log_api_call, extract_entities
from companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES, ALL_COMPANIES
from ingest_news import save_news, calc_buzz

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
        
        try:
            res = sb.table('companies').select('id').eq('name', name).execute()
            if not res.data:
                sb.table('companies').insert({
                    'name': name,
                    'ticker': ticker,
                    'is_private': is_private,
                    'sector': sector,
                    'is_ai_company': comp.get('is_ai_company', False),
                    'github_org': comp.get('github_org'),
                    'poll_tier': args.tier
                }).execute()
                res = sb.table('companies').select('id').eq('name', name).execute()
                
            company_id = res.data[0]['id']
            
            if is_private:
                sb.table('companies').update({'sector': sector, 'last_updated': 'now()'}).eq('id', company_id).execute()
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
                    info = stock.info
                    price = info.get('currentPrice')
                    if price is None:
                        price = info.get('regularMarketPrice')
                    if 'regularMarketChangePercent' in info and info['regularMarketChangePercent'] is not None:
                        change_pct = info['regularMarketChangePercent'] * 100
                except Exception as e:
                    logger.error(f"Yfinance quote error for {ticker}: {e}")
                    
            if price is not None:
                sb.table('companies').update({
                    'stock_price': price,
                    'change_pct_24h': change_pct,
                    'last_updated': 'now()'
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
