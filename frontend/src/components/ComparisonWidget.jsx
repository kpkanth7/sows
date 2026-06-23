import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { GitCompare, TrendingUp, Github, DollarSign, Calendar, ChevronDown, Newspaper, LineChart } from 'lucide-react';
import ForecastBadge from './ForecastBadge';

const LOOKBACK_DAYS = 7;
const ANALYST_LOOKBACK_DAYS = 30;
const INSIDER_LOOKBACK_DAYS = 30;
const NOTABLE_INSIDER_THRESHOLD = 10000;
const NOT_APPLICABLE = 'N/A';

function isoDaysAgo(days) {
  return new Date(Date.now() - days * 86400000).toISOString();
}

function dateDaysAgo(days) {
  return new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
}

function fmtBig(n) {
  if (n == null) return '—';
  const abs = Math.abs(Number(n));
  if (abs >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${Math.round(n).toLocaleString()}`;
}

function fmtPercent(n) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  const num = Number(n);
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
}

function fmtDecimal(n) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  return Number(n).toFixed(1);
}

function fmtCount(n) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  return Number(n).toLocaleString();
}

function fmtCompactNumber(n) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  const abs = Math.abs(Number(n));
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return `${Math.round(n)}`;
}

function fmtDate(value) {
  if (!value) return '—';
  const dt = new Date(`${value}T00:00:00`);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function hourLabel(hour) {
  if (hour === 'bmo') return 'BMO';
  if (hour === 'amc') return 'AMC';
  if (hour === 'dmh') return 'DMH';
  return '';
}

function eventLabel(eventType) {
  if (!eventType) return 'Catalyst';
  return eventType.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
}

function buildCell({ value = null, format = (v) => String(v), detail = '', comparable = null, applicable = true }) {
  if (!applicable) {
    return { display: NOT_APPLICABLE, detail: 'Not public-market data', comparable: null, applicable: false };
  }
  if (value == null) {
    return { display: '—', detail, comparable: null, applicable: true };
  }
  return {
    display: format(value),
    detail,
    comparable: comparable ?? (typeof value === 'number' ? value : null),
    applicable: true,
  };
}

function metricCellStyle({ winner, applicable }) {
  return {
    minWidth: 0,
    padding: '0.65rem 0.75rem',
    borderRadius: '8px',
    border: `1px solid ${winner ? 'rgba(239, 179, 62, 0.45)' : 'var(--border-color)'}`,
    background: winner ? 'rgba(239, 179, 62, 0.08)' : 'rgba(5, 10, 20, 0.22)',
    opacity: applicable ? 1 : 0.75,
  };
}

function compareWinner(left, right) {
  const leftValue = left?.comparable;
  const rightValue = right?.comparable;
  if (leftValue == null || rightValue == null) return { left: false, right: false };
  if (leftValue === rightValue) return { left: false, right: false };
  return { left: leftValue > rightValue, right: rightValue > leftValue };
}

function MetricRow({ icon: Icon, label, freshness, left, right }) {
  const winner = compareWinner(left, right);
  return (
    <div
      className="comparison-row"
      style={{
        gridTemplateColumns: 'minmax(0,1fr) minmax(120px,0.72fr) minmax(0,1fr)',
        gap: '0.75rem',
        alignItems: 'stretch',
      }}
    >
      <div className="comparison-value" style={metricCellStyle({ winner: winner.left, applicable: left.applicable })}>
        <strong style={{ display: 'block', fontSize: '0.98rem', lineHeight: 1.15 }}>{left.display}</strong>
        <small className="text-muted" style={{ display: 'block', marginTop: '0.2rem', fontSize: '0.72rem' }}>{left.detail || ' '}</small>
      </div>
      <div
        className="comparison-label"
        style={{
          flexDirection: 'column',
          gap: '0.18rem',
          padding: '0.25rem 0',
          minWidth: 0,
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
          <Icon size={12} />
          {label}
        </span>
        <small className="text-muted" style={{ fontSize: '0.68rem', textTransform: 'none', fontWeight: 600 }}>
          {freshness}
        </small>
      </div>
      <div className="comparison-value comparison-value-right" style={metricCellStyle({ winner: winner.right, applicable: right.applicable })}>
        <strong style={{ display: 'block', fontSize: '0.98rem', lineHeight: 1.15 }}>{right.display}</strong>
        <small className="text-muted" style={{ display: 'block', marginTop: '0.2rem', fontSize: '0.72rem' }}>{right.detail || ' '}</small>
      </div>
    </div>
  );
}

function CompanyPicker({ label, company, value, companies, onChange }) {
  return (
    <label className="comparison-picker">
      <span className="comparison-picker-label">{label}</span>
      <span className="comparison-picker-main">
        <span>
          <strong>{company?.ticker || company?.name || '—'}</strong>
          <small>{company?.name || 'Select company'}</small>
        </span>
        <ChevronDown size={16} aria-hidden="true" />
      </span>
      <select value={value} onChange={e => onChange(e.target.value)} aria-label={`${label} company`}>
        {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
    </label>
  );
}

function forecastEvidence(company, signals) {
  const parts = [];
  if (signals?.newsCount7d != null) parts.push(`${signals.newsCount7d} articles / 7d`);
  if (signals?.githubMomentum7d != null && signals.githubMomentum7d > 0) parts.push(`${signals.githubMomentum7d} GH stars / 7d`);
  if (company?.is_private === false && signals?.nextEarnings?.date) parts.push(`next earnings ${fmtDate(signals.nextEarnings.date)}`);
  if (company?.is_private && signals?.nextCatalyst?.date) parts.push(`${eventLabel(signals.nextCatalyst.type)} ${fmtDate(signals.nextCatalyst.date)}`);
  return parts.slice(0, 2).join(' · ') || 'Waiting for more fresh signal coverage';
}

function ForecastPanel({ side, company, signals }) {
  return (
    <div className="comparison-forecast">
      <span>{side}</span>
      <strong>{company.ticker || company.name}</strong>
      <ForecastBadge direction={company.forecast_direction} confidence={company.forecast_confidence} />
      <div className="text-xs text-muted" style={{ marginTop: '0.45rem', lineHeight: 1.35 }}>
        {forecastEvidence(company, signals)}
      </div>
    </div>
  );
}

function summarizeAnalyst(rec, revisions) {
  if (!rec) return null;
  const strongBuy = Number(rec.strong_buy || 0);
  const buy = Number(rec.buy || 0);
  const hold = Number(rec.hold || 0);
  const sell = Number(rec.sell || 0);
  const strongSell = Number(rec.strong_sell || 0);
  const coverage = strongBuy + buy + hold + sell + strongSell;
  if (!coverage) return null;

  const weighted = ((strongBuy * 2) + buy - sell - (strongSell * 2)) / coverage;
  let label = 'Mixed';
  if (weighted >= 1) label = 'Bullish';
  else if (weighted <= -1) label = 'Bearish';
  else if (weighted > 0.2) label = 'Positive';
  else if (weighted < -0.2) label = 'Cautious';

  const upgrades = revisions.filter(r => r.action === 'up' || r.action === 'main' || r.action === 'init').length;
  const downgrades = revisions.filter(r => r.action === 'down').length;
  const net = upgrades - downgrades;

  return {
    label,
    detail: `${coverage} firms${net ? ` · ${net > 0 ? '+' : ''}${net} rev / 30d` : ''}`,
    score: weighted + (net * 0.25),
  };
}

function summarizeInsiders(rows) {
  if (!rows) return null;
  const notable = rows.filter(r => Math.abs(Number(r.change || 0)) >= NOTABLE_INSIDER_THRESHOLD);
  if (!notable.length) {
    return { label: 'Quiet', detail: `No notable ${INSIDER_LOOKBACK_DAYS}d filings`, score: 0 };
  }
  const net = notable.reduce((sum, row) => sum + Number(row.change || 0), 0);
  return {
    label: net >= 0 ? 'Buying' : 'Selling',
    detail: `${notable.length} filings · ${net > 0 ? '+' : ''}${fmtCompactNumber(net)} shares`,
    score: net,
  };
}

function buildSignalsByCompany({
  selectedCompanies,
  newsResults,
  stockSnapshots,
  githubSignals,
  earningsRows,
  eventRows,
  analystRows,
  revisionRows,
  insiderRows,
}) {
  const out = {};

  selectedCompanies.forEach((company, index) => {
    const newsData = newsResults[index]?.data || [];
    const buzzValues = newsData
      .map(item => Number(item.buzz_v2))
      .filter(value => !Number.isNaN(value));
    const latestSnapshot = stockSnapshots.find(row => row.company_id === company.id);
    const latestEarnings = earningsRows.find(row => row.company_id === company.id) || null;
    const nextEvent = eventRows.find(row => Array.isArray(row.company_ids) && row.company_ids.includes(company.id)) || null;
    const analyst = analystRows.find(row => row.company_id === company.id) || null;
    const revisions = revisionRows.filter(row => row.company_id === company.id);
    const insider = insiderRows.filter(row => row.company_id === company.id);
    const ghRows = githubSignals.filter(row => row.company_id === company.id);
    const latestGh = ghRows[0] || null;

    out[company.id] = {
      newsCount7d: newsData.length,
      buzzAvg7d: buzzValues.length ? buzzValues.reduce((sum, value) => sum + value, 0) / buzzValues.length : null,
      priceMove24h: latestSnapshot?.change_pct ?? company.change_pct_24h ?? null,
      githubMomentum7d: ghRows.reduce((sum, row) => sum + Number(row.stars_this_week || 0), 0),
      githubLatestStars: latestGh?.stars ?? null,
      nextEarnings: latestEarnings ? { date: latestEarnings.earnings_date, hour: latestEarnings.hour } : null,
      nextCatalyst: nextEvent
        ? { date: nextEvent.event_date, type: nextEvent.event_type, name: nextEvent.event_name }
        : (company.recent_event_date
            ? { date: company.recent_event_date, type: company.recent_event, name: company.recent_event }
            : null),
      analyst: summarizeAnalyst(analyst, revisions),
      insider: summarizeInsiders(insider),
    };
  });

  return out;
}

export default function ComparisonWidget() {
  const [companies, setCompanies] = useState([]);
  const [idA, setIdA] = useState('');
  const [idB, setIdB] = useState('');
  const [signals, setSignals] = useState({});
  const [loading, setLoading] = useState(true);
  const [signalsLoading, setSignalsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    supabase
      .from('companies')
      .select(`
        id,
        name,
        ticker,
        is_private,
        market_cap,
        last_valuation,
        valuation_source,
        change_pct_24h,
        forecast_direction,
        forecast_confidence,
        recent_event,
        recent_event_date
      `)
      .order('name')
      .then(({ data }) => {
        if (cancelled) return;
        if (data) {
          setCompanies(data);
          if (data.length > 1) {
            setIdA(data[0].id);
            setIdB(data[1].id);
          }
        }
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const compA = companies.find(c => c.id === idA);
  const compB = companies.find(c => c.id === idB);

  useEffect(() => {
    const selectedCompanies = [compA, compB].filter(Boolean);
    if (!selectedCompanies.length) {
      setSignals({});
      return;
    }

    let cancelled = false;
    const selectedIds = selectedCompanies.map(company => company.id);
    const publicIds = selectedCompanies.filter(company => !company.is_private && company.ticker).map(company => company.id);
    const signalsWindow = isoDaysAgo(LOOKBACK_DAYS);
    const analystWindow = dateDaysAgo(ANALYST_LOOKBACK_DAYS);
    const insiderWindow = dateDaysAgo(INSIDER_LOOKBACK_DAYS);
    const today = new Date().toISOString().slice(0, 10);

    const run = async () => {
      setSignalsLoading(true);

      const [
        newsResults,
        stockRes,
        githubRes,
        earningsRes,
        eventsRes,
        analystRes,
        revisionsRes,
        insiderRes,
      ] = await Promise.all([
        Promise.all(
          selectedCompanies.map(company =>
            supabase
              .from('news_items')
              .select('buzz_v2')
              .contains('entity_names', [company.name])
              .gte('ingested_at', signalsWindow)
          )
        ),
        publicIds.length
          ? supabase
              .from('stock_snapshots')
              .select('company_id, change_pct, captured_at')
              .in('company_id', publicIds)
              .order('captured_at', { ascending: false })
          : Promise.resolve({ data: [] }),
        supabase
          .from('github_signals')
          .select('company_id, stars_this_week, stars, captured_at')
          .in('company_id', selectedIds)
          .gte('captured_at', signalsWindow)
          .order('captured_at', { ascending: false }),
        publicIds.length
          ? supabase
              .from('earnings_calendar')
              .select('company_id, earnings_date, hour')
              .in('company_id', publicIds)
              .gte('earnings_date', today)
              .order('earnings_date', { ascending: true })
          : Promise.resolve({ data: [] }),
        supabase
          .from('events_calendar')
          .select('event_name, event_date, event_type, company_ids')
          .gte('event_date', today)
          .order('event_date', { ascending: true })
          .limit(100),
        publicIds.length
          ? supabase
              .from('analyst_recommendations')
              .select('company_id, period, strong_buy, buy, hold, sell, strong_sell')
              .in('company_id', publicIds)
              .gte('period', analystWindow)
              .order('period', { ascending: false })
          : Promise.resolve({ data: [] }),
        publicIds.length
          ? supabase
              .from('upgrade_downgrade')
              .select('company_id, action, action_date')
              .in('company_id', publicIds)
              .gte('action_date', analystWindow)
              .order('action_date', { ascending: false })
          : Promise.resolve({ data: [] }),
        publicIds.length
          ? supabase
              .from('insider_transactions')
              .select('company_id, change, transaction_date')
              .in('company_id', publicIds)
              .gte('transaction_date', insiderWindow)
              .order('transaction_date', { ascending: false })
          : Promise.resolve({ data: [] }),
      ]);

      if (cancelled) return;

      setSignals(
        buildSignalsByCompany({
          selectedCompanies,
          newsResults,
          stockSnapshots: stockRes.data || [],
          githubSignals: githubRes.data || [],
          earningsRows: earningsRes.data || [],
          eventRows: eventsRes.data || [],
          analystRows: analystRes.data || [],
          revisionRows: revisionsRes.data || [],
          insiderRows: insiderRes.data || [],
        })
      );
      setSignalsLoading(false);
    };

    run();

    return () => {
      cancelled = true;
    };
  }, [compA, compB]);

  if (loading) {
    return <div className="skeleton skeleton-card mt-6 comparison-widget-skeleton" />;
  }

  if (!compA || !compB) {
    return (
      <div className="card glass-panel mt-6 comparison-widget">
        <div className="comparison-header">
          <GitCompare size={20} className="text-accent-amber" />
          <div>
            <h3>Head-to-Head</h3>
            <p>Pick two tracked companies to compare investor signals.</p>
          </div>
        </div>
        <p className="text-sm text-muted m-0">Need at least two companies to compare.</p>
      </div>
    );
  }

  const signalA = signals[compA.id] || {};
  const signalB = signals[compB.id] || {};

  const valuationA = compA.market_cap || compA.last_valuation || null;
  const valuationB = compB.market_cap || compB.last_valuation || null;

  const rows = [
    {
      key: 'valuation',
      icon: DollarSign,
      label: 'Valuation',
      freshness: 'latest known',
      left: buildCell({
        value: valuationA,
        format: fmtBig,
        detail: compA.market_cap ? 'Market cap' : (compA.valuation_source || 'Last private round'),
      }),
      right: buildCell({
        value: valuationB,
        format: fmtBig,
        detail: compB.market_cap ? 'Market cap' : (compB.valuation_source || 'Last private round'),
      }),
    },
    {
      key: 'move',
      icon: TrendingUp,
      label: '24H Move',
      freshness: 'latest market snapshot',
      left: buildCell({
        value: signalA.priceMove24h,
        format: fmtPercent,
        detail: compA.is_private ? '' : 'Public only',
        applicable: !compA.is_private,
      }),
      right: buildCell({
        value: signalB.priceMove24h,
        format: fmtPercent,
        detail: compB.is_private ? '' : 'Public only',
        applicable: !compB.is_private,
      }),
    },
    {
      key: 'newsCount',
      icon: Newspaper,
      label: 'Articles',
      freshness: 'last 7 days',
      left: buildCell({
        value: signalA.newsCount7d,
        format: fmtCount,
        detail: 'Mention volume',
      }),
      right: buildCell({
        value: signalB.newsCount7d,
        format: fmtCount,
        detail: 'Mention volume',
      }),
    },
    {
      key: 'buzz',
      icon: TrendingUp,
      label: 'Buzz Avg',
      freshness: 'last 7 days',
      left: buildCell({
        value: signalA.buzzAvg7d,
        format: fmtDecimal,
        detail: signalA.newsCount7d ? `${signalA.newsCount7d} article sample` : 'No recent sample',
      }),
      right: buildCell({
        value: signalB.buzzAvg7d,
        format: fmtDecimal,
        detail: signalB.newsCount7d ? `${signalB.newsCount7d} article sample` : 'No recent sample',
      }),
    },
    {
      key: 'github',
      icon: Github,
      label: 'GitHub Momentum',
      freshness: 'last 7 days',
      left: buildCell({
        value: signalA.githubMomentum7d,
        format: fmtCount,
        detail: signalA.githubLatestStars != null ? `${fmtCompactNumber(signalA.githubLatestStars)} total stars latest` : 'No recent GitHub row',
      }),
      right: buildCell({
        value: signalB.githubMomentum7d,
        format: fmtCount,
        detail: signalB.githubLatestStars != null ? `${fmtCompactNumber(signalB.githubLatestStars)} total stars latest` : 'No recent GitHub row',
      }),
    },
    {
      key: 'analyst',
      icon: LineChart,
      label: 'Analyst Signal',
      freshness: 'consensus + 30d revisions',
      left: buildCell({
        value: signalA.analyst?.label || null,
        format: v => v,
        detail: signalA.analyst?.detail || '',
        comparable: signalA.analyst?.score ?? null,
        applicable: !compA.is_private,
      }),
      right: buildCell({
        value: signalB.analyst?.label || null,
        format: v => v,
        detail: signalB.analyst?.detail || '',
        comparable: signalB.analyst?.score ?? null,
        applicable: !compB.is_private,
      }),
    },
    {
      key: 'insider',
      icon: TrendingUp,
      label: 'Insider Flow',
      freshness: `notable ${INSIDER_LOOKBACK_DAYS}d filings`,
      left: buildCell({
        value: signalA.insider?.label || null,
        format: v => v,
        detail: signalA.insider?.detail || '',
        comparable: signalA.insider?.score ?? null,
        applicable: !compA.is_private,
      }),
      right: buildCell({
        value: signalB.insider?.label || null,
        format: v => v,
        detail: signalB.insider?.detail || '',
        comparable: signalB.insider?.score ?? null,
        applicable: !compB.is_private,
      }),
    },
    {
      key: 'catalyst',
      icon: Calendar,
      label: 'Next Catalyst',
      freshness: 'upcoming calendar',
      left: buildCell({
        value: compA.is_private
          ? (signalA.nextCatalyst?.date || null)
          : (signalA.nextEarnings?.date || signalA.nextCatalyst?.date || null),
        format: fmtDate,
        detail: compA.is_private
          ? (signalA.nextCatalyst ? eventLabel(signalA.nextCatalyst.type) : 'No scheduled event')
          : (signalA.nextEarnings?.hour ? `Earnings · ${hourLabel(signalA.nextEarnings.hour)}` : (signalA.nextCatalyst ? eventLabel(signalA.nextCatalyst.type) : 'No scheduled event')),
      }),
      right: buildCell({
        value: compB.is_private
          ? (signalB.nextCatalyst?.date || null)
          : (signalB.nextEarnings?.date || signalB.nextCatalyst?.date || null),
        format: fmtDate,
        detail: compB.is_private
          ? (signalB.nextCatalyst ? eventLabel(signalB.nextCatalyst.type) : 'No scheduled event')
          : (signalB.nextEarnings?.hour ? `Earnings · ${hourLabel(signalB.nextEarnings.hour)}` : (signalB.nextCatalyst ? eventLabel(signalB.nextCatalyst.type) : 'No scheduled event')),
      }),
    },
  ];

  return (
    <div className="card glass-panel mt-6 comparison-widget">
      <div className="comparison-header">
        <GitCompare size={20} className="text-accent-amber" />
        <div>
          <h3>Head-to-Head</h3>
          <p>Reliable market, news, code, analyst, insider, and catalyst signals for any two tracked companies.</p>
        </div>
      </div>

      <div className="comparison-matchup" aria-label="Head-to-head company selectors">
        <CompanyPicker label="Left" company={compA} value={idA} companies={companies} onChange={setIdA} />
        <div className="comparison-versus">VS</div>
        <CompanyPicker label="Right" company={compB} value={idB} companies={companies} onChange={setIdB} />
      </div>

      <div
        className="comparison-table"
        style={{
          opacity: signalsLoading ? 0.72 : 1,
          transition: 'opacity 160ms ease',
        }}
      >
        {rows.map(row => (
          <MetricRow
            key={row.key}
            icon={row.icon}
            label={row.label}
            freshness={row.freshness}
            left={row.left}
            right={row.right}
          />
        ))}
      </div>

      <div className="comparison-forecast-grid">
        <ForecastPanel side="Left forecast" company={compA} signals={signalA} />
        <ForecastPanel side="Right forecast" company={compB} signals={signalB} />
      </div>
    </div>
  );
}
