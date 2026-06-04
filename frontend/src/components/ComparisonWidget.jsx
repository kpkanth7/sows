import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { GitCompare, TrendingUp, Github, DollarSign, Calendar, ChevronDown } from 'lucide-react';
import ForecastBadge from './ForecastBadge';

// Phase 3.12: head-to-head decision tool. Beyond price ticker:
//   - buzz_v2 trend (7d avg of news_items buzz_v2 per company)
//   - GitHub momentum (sum of stars_this_week last 7d)
//   - Valuation (market_cap || last_valuation)
//   - Forecast direction + confidence (existing ForecastBadge)
//   - Next earnings date (earnings_calendar)

const LOOKBACK_DAYS = 7;

function fmtBig(n) {
  if (n == null) return '—';
  const abs = Math.abs(n);
  if (abs >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${n}`;
}

async function fetchEnriched(companyId, companyName) {
  const since = new Date(Date.now() - LOOKBACK_DAYS * 86400000).toISOString();
  const today = new Date().toISOString().slice(0, 10);

  // Avg buzz_v2 of news where entity_names contains the company name, last 7d.
  const news = await supabase
    .from('news_items')
    .select('buzz_v2')
    .contains('entity_names', JSON.stringify([companyName]))
    .not('buzz_v2', 'is', null)
    .gte('ingested_at', since);
  const buzzVals = (news.data || []).map(r => Number(r.buzz_v2)).filter(v => !isNaN(v));
  const buzzAvg = buzzVals.length ? buzzVals.reduce((a, b) => a + b, 0) / buzzVals.length : null;

  // Sum stars_this_week last 7d for the company.
  const gh = await supabase
    .from('github_signals')
    .select('stars_this_week')
    .eq('company_id', companyId)
    .gte('captured_at', since);
  const ghMomentum = (gh.data || []).reduce((a, r) => a + (r.stars_this_week || 0), 0);

  // Next earnings date.
  const earn = await supabase
    .from('earnings_calendar')
    .select('earnings_date')
    .eq('company_id', companyId)
    .gte('earnings_date', today)
    .order('earnings_date', { ascending: true })
    .limit(1)
    .maybeSingle();
  const nextEarn = earn.data?.earnings_date || null;

  return { buzzAvg, ghMomentum, nextEarn };
}

function MetricRow({ icon: Icon, label, valueA, valueB, fmt = (v) => v }) {
  const a = valueA == null ? '—' : fmt(valueA);
  const b = valueB == null ? '—' : fmt(valueB);
  // Highlight side with the higher numeric value (if comparable).
  const numA = Number(valueA);
  const numB = Number(valueB);
  const cmpAble = !isNaN(numA) && !isNaN(numB);
  const aWins = cmpAble && numA > numB;
  const bWins = cmpAble && numB > numA;
  return (
    <div className="comparison-row">
      <span className={`comparison-value ${aWins ? 'is-winner' : ''}`}>{a}</span>
      <span className="comparison-label">
        <Icon size={12} /> {label}
      </span>
      <span className={`comparison-value comparison-value-right ${bWins ? 'is-winner' : ''}`}>{b}</span>
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

function ForecastPanel({ side, company }) {
  return (
    <div className="comparison-forecast">
      <span>{side}</span>
      <strong>{company.ticker || company.name}</strong>
      <ForecastBadge direction={company.forecast_direction} confidence={company.forecast_confidence} />
    </div>
  );
}

export default function ComparisonWidget() {
  const [companies, setCompanies] = useState([]);
  const [idA, setIdA] = useState('');
  const [idB, setIdB] = useState('');
  const [enrichedA, setEnrichedA] = useState(null);
  const [enrichedB, setEnrichedB] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase
      .from('companies')
      .select('id, name, ticker, hype_score, reality_score, sentiment_score, buzz_score, forecast_direction, forecast_confidence, market_cap, last_valuation')
      .order('name')
      .then(({ data }) => {
        if (data) {
          setCompanies(data);
          if (data.length > 1) {
            setIdA(data[0].id);
            setIdB(data[1].id);
          }
        }
        setLoading(false);
      });
  }, []);

  const compA = companies.find(c => c.id === idA);
  const compB = companies.find(c => c.id === idB);

  useEffect(() => {
    if (compA) fetchEnriched(compA.id, compA.name).then(setEnrichedA);
  }, [compA]);
  useEffect(() => {
    if (compB) fetchEnriched(compB.id, compB.name).then(setEnrichedB);
  }, [compB]);

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

  const valuationA = compA.market_cap || compA.last_valuation || null;
  const valuationB = compB.market_cap || compB.last_valuation || null;

  return (
    <div className="card glass-panel mt-6 comparison-widget">
      <div className="comparison-header">
        <GitCompare size={20} className="text-accent-amber" />
        <div>
          <h3>Head-to-Head</h3>
          <p>Valuation, buzz, developer momentum, and catalyst timing.</p>
        </div>
      </div>

      <div className="comparison-matchup" aria-label="Head-to-head company selectors">
        <CompanyPicker label="Left" company={compA} value={idA} companies={companies} onChange={setIdA} />
        <div className="comparison-versus">VS</div>
        <CompanyPicker label="Right" company={compB} value={idB} companies={companies} onChange={setIdB} />
      </div>

      <div className="comparison-table">
        <MetricRow
          icon={DollarSign}
          label="VALUATION"
          valueA={valuationA}
          valueB={valuationB}
          fmt={fmtBig}
        />
        <MetricRow
          icon={TrendingUp}
          label="BUZZ_V2 (7d avg)"
          valueA={enrichedA?.buzzAvg != null ? Math.round(enrichedA.buzzAvg) : null}
          valueB={enrichedB?.buzzAvg != null ? Math.round(enrichedB.buzzAvg) : null}
        />
        <MetricRow
          icon={Github}
          label="GH STARS (7d)"
          valueA={enrichedA?.ghMomentum ?? null}
          valueB={enrichedB?.ghMomentum ?? null}
        />
        <MetricRow
          icon={Calendar}
          label="NEXT EARNINGS"
          valueA={enrichedA?.nextEarn}
          valueB={enrichedB?.nextEarn}
          fmt={(v) => v}
        />
      </div>

      <div className="comparison-forecast-grid">
        <ForecastPanel side="Left forecast" company={compA} />
        <ForecastPanel side="Right forecast" company={compB} />
      </div>
    </div>
  );
}
