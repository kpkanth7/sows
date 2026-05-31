import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { GitCompare, TrendingUp, Github, DollarSign, Calendar } from 'lucide-react';
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
    .contains('entity_names', [companyName])
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
    <div className="flex items-center justify-between" style={{ padding: '0.45rem 0', borderBottom: '1px solid var(--border-color)' }}>
      <span className={`font-bold text-sm`} style={{ width: '35%', textAlign: 'left', color: aWins ? 'var(--accent-green)' : 'var(--text-primary)' }}>{a}</span>
      <span className="text-xs text-muted flex items-center gap-1" style={{ width: '30%', justifyContent: 'center' }}>
        <Icon size={12} /> {label}
      </span>
      <span className={`font-bold text-sm`} style={{ width: '35%', textAlign: 'right', color: bWins ? 'var(--accent-green)' : 'var(--text-primary)' }}>{b}</span>
    </div>
  );
}

export default function ComparisonWidget() {
  const [companies, setCompanies] = useState([]);
  const [idA, setIdA] = useState('');
  const [idB, setIdB] = useState('');
  const [enrichedA, setEnrichedA] = useState(null);
  const [enrichedB, setEnrichedB] = useState(null);

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

  if (!compA || !compB) return null;

  const valuationA = compA.market_cap || compA.last_valuation || null;
  const valuationB = compB.market_cap || compB.last_valuation || null;

  return (
    <div className="card glass-panel mt-6">
      <h3 className="flex items-center gap-2 mb-4">
        <GitCompare size={20} className="text-accent-amber" /> Head-to-Head
      </h3>

      <div className="flex gap-4 mb-6">
        <select value={idA} onChange={e => setIdA(e.target.value)} className="flex-1" style={{ background: 'var(--bg-color)' }}>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <div className="font-bold text-muted flex items-center justify-center px-2">VS</div>
        <select value={idB} onChange={e => setIdB(e.target.value)} className="flex-1" style={{ background: 'var(--bg-color)' }}>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      <div>
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

      <div className="flex justify-between items-center mt-4 gap-4">
        <ForecastBadge direction={compA.forecast_direction} confidence={compA.forecast_confidence} />
        <ForecastBadge direction={compB.forecast_direction} confidence={compB.forecast_confidence} />
      </div>
    </div>
  );
}
