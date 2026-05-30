import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';

// Phase 3.3: real Hype vs Reality chart for the CompanyDetailPanel Overview
// tab. Replaces the old `entities*10 + |sentiment|*20` toy score (which lived
// on companies.hype_score / reality_score) with a 30-day z-score trendline.
//
//   Hype    = daily count of news_items mentioning the company over 30d.
//   Reality = max(stars_this_week) from github_signals for the company per day.
//
// Both series are z-scored against their own 30-day mean+std so they share a
// common axis. A reading > 0 means "above the 30-day baseline". Divergence
// (hype z far above reality z) flags overhyped; reverse flags underrated.
//
// NPM/PyPI downloads are deferred to 3.3b — not yet ingested.

const WINDOW_DAYS = 30;

function isoDate(d) { return d.toISOString().slice(0, 10); }

function zscore(series) {
  const vals = series.map(s => s.v);
  const n = vals.length;
  if (!n) return [];
  const mean = vals.reduce((a, b) => a + b, 0) / n;
  const variance = vals.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
  const std = Math.sqrt(variance) || 1;
  return series.map(s => ({ ...s, z: (s.v - mean) / std }));
}

export default function HypeRealityChart({ company }) {
  const [data, setData] = useState([]);
  const [verdict, setVerdict] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!company?.id || !company?.name) return;
    const run = async () => {
      setLoading(true);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const start = new Date(today);
      start.setDate(start.getDate() - WINDOW_DAYS);

      // 1) Hype — news_items mentioning the company name (entity_names contains).
      const newsRes = await supabase
        .from('news_items')
        .select('ingested_at')
        .contains('entity_names', [company.name])
        .gte('ingested_at', start.toISOString());

      // 2) Reality — github_signals for company_id, taking max stars_this_week per day.
      const ghRes = await supabase
        .from('github_signals')
        .select('captured_at, stars_this_week')
        .eq('company_id', company.id)
        .gte('captured_at', start.toISOString());

      // Bin both series by date.
      const hypeByDate = {};
      (newsRes.data || []).forEach(r => {
        const d = isoDate(new Date(r.ingested_at));
        hypeByDate[d] = (hypeByDate[d] || 0) + 1;
      });
      const realityByDate = {};
      (ghRes.data || []).forEach(r => {
        const d = isoDate(new Date(r.captured_at));
        realityByDate[d] = Math.max(realityByDate[d] || 0, r.stars_this_week || 0);
      });

      // Build a continuous date axis so gaps are zeros, not missing points.
      const dates = [];
      for (let i = 0; i < WINDOW_DAYS; i++) {
        const d = new Date(start);
        d.setDate(d.getDate() + i);
        dates.push(isoDate(d));
      }
      const hypeSeries = dates.map(d => ({ d, v: hypeByDate[d] || 0 }));
      const realitySeries = dates.map(d => ({ d, v: realityByDate[d] || 0 }));

      const hypeZ = zscore(hypeSeries);
      const realityZ = zscore(realitySeries);

      const merged = dates.map((d, i) => ({
        date: d.slice(5),  // MM-DD for axis
        hype: Number(hypeZ[i]?.z?.toFixed(2) ?? 0),
        reality: Number(realityZ[i]?.z?.toFixed(2) ?? 0),
      }));

      // Verdict — compare the latest 7-day average of each z-series.
      const last7 = merged.slice(-7);
      const avgHype = last7.reduce((a, b) => a + b.hype, 0) / (last7.length || 1);
      const avgReality = last7.reduce((a, b) => a + b.reality, 0) / (last7.length || 1);
      let v;
      if (avgHype - avgReality > 1) v = { label: 'Overhyped (last 7d)', color: 'var(--accent-amber)' };
      else if (avgReality - avgHype > 1) v = { label: 'Underrated / High Traction (last 7d)', color: 'var(--accent-green)' };
      else v = { label: 'Balanced (last 7d)', color: 'var(--text-secondary)' };

      setData(merged);
      setVerdict(v);
      setLoading(false);
    };
    run();
  }, [company]);

  if (loading) return <div className="skeleton skeleton-card" style={{ height: '260px' }} />;

  const hasData = data.some(d => d.hype !== 0 || d.reality !== 0);
  if (!hasData) {
    return (
      <div className="text-xs text-muted">
        Not enough 30-day data yet. Hype/Reality trend will populate as news + GitHub signals accumulate.
      </div>
    );
  }

  return (
    <div>
      <div className="text-xs font-bold mb-2" style={{ color: verdict?.color }}>
        {verdict?.label}
      </div>
      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: -16 }}>
            <XAxis dataKey="date" stroke="var(--text-secondary)" fontSize={10} interval={4} />
            <YAxis stroke="var(--text-secondary)" fontSize={10} domain={[-3, 3]} />
            <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <ReferenceLine y={0} stroke="var(--border-color)" strokeDasharray="3 3" />
            <Line type="monotone" dataKey="hype" name="Hype (news z-score)" stroke="var(--accent-amber)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="reality" name="Reality (GitHub z-score)" stroke="var(--accent-green)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="text-xs text-muted mt-1">
        Z-score vs 30-day baseline · Hype = news mentions/day · Reality = max GitHub stars-this-week/day
      </div>
    </div>
  );
}
