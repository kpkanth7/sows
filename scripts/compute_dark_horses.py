"""Phase 3.11: Dark-Horse Radar.

Computes a composite "punching above its weight + accelerating" score per
tracked company. Run daily, truncate-and-insert top 20 into
`dark_horse_movers` for the InvestorHub panel to read.

Composite score (each sub-score normalized to 0-100, equal weight):

  1. GH stars-this-week z-score    (last-7d avg vs prior-23d baseline)
  2. News volume z-score           (last-7d daily count vs prior-23d baseline)
  3. Analyst upgrade momentum      ((upgrades - downgrades) last 7d, cohort-normalized)
  4. Insider+market combined       (avg of insider buy ratio + stock 7d % momentum)
  5. Catalyst / release heat       (official upcoming event + major release density)

Equal weighting is deliberate: user explicitly chose all 4 signal families
to dilute single-source bias.

Bulk fetch pattern: one query per signal table, grouped in-memory by
company_id / entity_name. Avoids the 480-call O(N×K) loop.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import sqrt

from db import get_client, record_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 30
RECENT_DAYS = 7
TOP_N = 20

# Score thresholds for human-readable reasons displayed under the rank.
REASON_THRESHOLD = 70.0


def _iso(dt):
    return dt.isoformat()


def _z_to_100(z):
    """Map a z-score to 0-100 with z=0 -> 50, clamped to ±3 sigma."""
    z = max(-3.0, min(3.0, z))
    return round(50.0 + (z * (50.0 / 3.0)), 2)


def _z_score(recent_avg, baseline_vals):
    if not baseline_vals:
        return 0.0
    mean = sum(baseline_vals) / len(baseline_vals)
    var = sum((v - mean) ** 2 for v in baseline_vals) / len(baseline_vals)
    std = sqrt(var) or 1.0
    return (recent_avg - mean) / std


def _fetch_companies(sb):
    res = sb.table('companies').select('id, name, ticker').execute()
    return res.data or []


def _news_by_entity(sb, since_iso):
    """{entity_name: [date, ...]} for last LOOKBACK_DAYS."""
    res = (
        sb.table('news_items')
          .select('entity_names, ingested_at')
          .gte('ingested_at', since_iso)
          .limit(10000)
          .execute()
    )
    out = defaultdict(list)
    for row in (res.data or []):
        try:
            d = datetime.fromisoformat(row['ingested_at'].replace('Z', '+00:00')).date()
        except Exception:
            continue
        for ent in (row.get('entity_names') or []):
            out[ent].append(d)
    return out


def _gh_by_company(sb, since_iso):
    """{company_id: [(date, stars_this_week), ...]}"""
    res = (
        sb.table('github_signals')
          .select('company_id, captured_at, stars_this_week')
          .gte('captured_at', since_iso)
          .not_.is_('company_id', None)
          .limit(10000)
          .execute()
    )
    out = defaultdict(list)
    for row in (res.data or []):
        try:
            d = datetime.fromisoformat(row['captured_at'].replace('Z', '+00:00')).date()
        except Exception:
            continue
        out[row['company_id']].append((d, int(row.get('stars_this_week') or 0)))
    return out


def _upgrade_by_company(sb, recent_iso):
    """{company_id: [(action, date), ...]} last 7d."""
    res = (
        sb.table('upgrade_downgrade')
          .select('company_id, action, action_date')
          .gte('action_date', recent_iso)
          .limit(2000)
          .execute()
    )
    out = defaultdict(list)
    for row in (res.data or []):
        out[row['company_id']].append((row.get('action') or '', row.get('action_date')))
    return out


def _insider_by_company(sb, since_iso):
    """{company_id: [change, ...]} last LOOKBACK_DAYS."""
    res = (
        sb.table('insider_transactions')
          .select('company_id, change, transaction_date')
          .gte('transaction_date', since_iso)
          .limit(5000)
          .execute()
    )
    out = defaultdict(list)
    for row in (res.data or []):
        out[row['company_id']].append(int(row.get('change') or 0))
    return out


def _stock_by_company(sb, since_iso):
    """{company_id: [(captured_at, price), ...]} last 7d (ordered)."""
    res = (
        sb.table('stock_snapshots')
          .select('company_id, captured_at, price')
          .gte('captured_at', since_iso)
          .not_.is_('price', None)
          .order('captured_at')
          .limit(20000)
          .execute()
    )
    out = defaultdict(list)
    for row in (res.data or []):
        out[row['company_id']].append((row['captured_at'], float(row['price'])))
    return out


def _catalyst_by_company(sb, today_iso, future_iso, since_iso):
    events = (
        sb.table('events_calendar')
          .select('company_ids, event_date, source_priority, confidence')
          .gte('event_date', today_iso)
          .lte('event_date', future_iso)
          .limit(1000)
          .execute()
    )
    news = (
        sb.table('news_items')
          .select('entity_names, is_major_release')
          .eq('is_major_release', True)
          .gte('ingested_at', since_iso)
          .limit(5000)
          .execute()
    )
    out = defaultdict(lambda: {'events': [], 'releases': 0})
    for row in (events.data or []):
        for cid in (row.get('company_ids') or []):
            out[cid]['events'].append(row)
    for row in (news.data or []):
        for entity in (row.get('entity_names') or []):
            out[entity]['releases'] += 1
    return out


def _daily_counts(date_list, today, lookback):
    """date_list -> per-day count array (length=lookback, index 0 = today)."""
    counts = defaultdict(int)
    for d in date_list:
        counts[d] += 1
    return [counts.get(today - timedelta(days=i), 0) for i in range(lookback)]


def _split_recent_baseline(series):
    return series[:RECENT_DAYS], series[RECENT_DAYS:]


def _gh_score(stars_series_by_date, today):
    """Avg stars_this_week per day, z-score recent vs baseline."""
    by_date = defaultdict(list)
    for (d, s) in stars_series_by_date:
        by_date[d].append(s)
    daily_avg = [
        (sum(by_date.get(today - timedelta(days=i), [0])) / len(by_date.get(today - timedelta(days=i), [0])))
        if by_date.get(today - timedelta(days=i)) else 0
        for i in range(LOOKBACK_DAYS)
    ]
    recent, baseline = _split_recent_baseline(daily_avg)
    recent_mean = sum(recent) / len(recent) if recent else 0
    return _z_to_100(_z_score(recent_mean, baseline))


def _news_score(date_list, today):
    series = _daily_counts(date_list, today, LOOKBACK_DAYS)
    recent, baseline = _split_recent_baseline(series)
    recent_mean = sum(recent) / len(recent) if recent else 0
    return _z_to_100(_z_score(recent_mean, baseline))


def _analyst_score(actions, max_net):
    """(up - down) cohort-normalized into 0-100."""
    ups = sum(1 for a, _ in actions if a == 'up')
    downs = sum(1 for a, _ in actions if a == 'down')
    net = ups - downs
    if max_net <= 0:
        return 50.0
    return round(max(0.0, min(100.0, 50.0 + (net / max_net) * 50.0)), 2)


def _insider_market_score(insider_changes, stock_points):
    """Average of insider buy ratio (0-100) and stock 7d % momentum (50-centered)."""
    # Insider — sum(positive) / sum(abs). 50 if no trades.
    if insider_changes:
        pos = sum(c for c in insider_changes if c > 0)
        total = sum(abs(c) for c in insider_changes)
        insider_pct = (pos / total) * 100.0 if total > 0 else 50.0
    else:
        insider_pct = 50.0

    # Stock — first vs last price in window.
    if len(stock_points) >= 2:
        first = stock_points[0][1]
        last = stock_points[-1][1]
        if first > 0:
            pct = ((last - first) / first) * 100.0
            # Map ±10% to ±50 around 50; clamp 0-100.
            market_pct = max(0.0, min(100.0, 50.0 + (pct * 5.0)))
        else:
            market_pct = 50.0
    else:
        market_pct = 50.0

    return round((insider_pct + market_pct) / 2.0, 2)


def _reasons(components):
    out = []
    if components['gh'] >= REASON_THRESHOLD:
        out.append('GitHub stars surging')
    if components['news'] >= REASON_THRESHOLD:
        out.append('News volume spike')
    if components['analyst'] >= REASON_THRESHOLD:
        out.append('Analysts piling on')
    if components['market'] >= REASON_THRESHOLD:
        out.append('Insider + market confirm')
    if components['catalyst'] >= REASON_THRESHOLD:
        out.append('Catalyst window opening')
    return out


def _catalyst_score(company, catalyst_rows):
    event_score = 0.0
    for event in catalyst_rows.get('events', []):
        try:
            days = max(0, (datetime.fromisoformat(str(event['event_date'])) - datetime.now()).days)
        except Exception:
            days = 30
        urgency = max(0.0, 80.0 - min(days, 30) * 2.5)
        quality = 10.0 if int(event.get('source_priority') or 3) == 1 else 4.0
        conf = float(event.get('confidence') or 75) * 0.1
        event_score = max(event_score, urgency + quality + conf)

    release_score = min(100.0, float(catalyst_rows.get('releases') or 0) * 22.0)
    name_boost = 10.0 if company['name'] in {'OpenAI', 'Anthropic', 'Google', 'Microsoft', 'NVIDIA'} else 0.0
    return round(min(100.0, max(event_score, release_score) + name_boost), 2)


def main():
    sb = get_client()
    today = datetime.now(timezone.utc).date()
    since_30d = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS))
    since_7d = (datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS))

    companies = _fetch_companies(sb)
    news = _news_by_entity(sb, _iso(since_30d))
    gh = _gh_by_company(sb, _iso(since_30d))
    upgrades = _upgrade_by_company(sb, since_7d.date().isoformat())
    insiders = _insider_by_company(sb, since_30d.date().isoformat())
    stocks = _stock_by_company(sb, _iso(since_7d))
    catalysts = _catalyst_by_company(sb, today.isoformat(), (today + timedelta(days=45)).isoformat(), _iso(since_30d))

    # Cohort max for analyst normalization (so we get a real spread).
    cohort_net = []
    for cid, actions in upgrades.items():
        ups = sum(1 for a, _ in actions if a == 'up')
        downs = sum(1 for a, _ in actions if a == 'down')
        cohort_net.append(abs(ups - downs))
    max_net = max(cohort_net) if cohort_net else 1

    rows = []
    for c in companies:
        cid = c['id']
        name = c['name']
        comp = {
            'gh': _gh_score(gh.get(cid, []), today),
            'news': _news_score(news.get(name, []), today),
            'analyst': _analyst_score(upgrades.get(cid, []), max_net),
            'market': _insider_market_score(insiders.get(cid, []), stocks.get(cid, [])),
            'catalyst': _catalyst_score(c, {
                'events': catalysts.get(cid, {}).get('events', []),
                'releases': catalysts.get(name, {}).get('releases', 0),
            }),
        }
        score = round(sum(comp.values()) / 5.0, 2)
        rows.append({
            'company_id': cid,
            'score': score,
            'components': comp,
            'reasons': _reasons(comp),
        })

    rows.sort(key=lambda r: r['score'], reverse=True)
    top = rows[:TOP_N]
    for i, r in enumerate(top, 1):
        r['rank'] = i
        r['computed_at'] = datetime.now(timezone.utc).isoformat()

    # Truncate via plain delete (no DELETE WHERE TRUE needed in supabase-py).
    sb.table('dark_horse_movers').delete().neq('rank', -1).execute()
    if top:
        sb.table('dark_horse_movers').insert(top).execute()
    logger.info(
        f"dark_horses: scored {len(rows)} cos, wrote top {len(top)}; "
        f"#1 score={top[0]['score'] if top else 'n/a'}"
    )


if __name__ == '__main__':
    try:
        main()
        record_health(get_client(), 'compute_dark_horses', 'ok')
    except Exception as e:
        record_health(get_client(), 'compute_dark_horses', 'error', str(e))
        raise
