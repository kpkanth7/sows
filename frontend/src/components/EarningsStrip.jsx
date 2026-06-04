import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Calendar, TrendingUp, TrendingDown, Minus } from 'lucide-react';

// Phase 3.2: earnings countdown + post-earnings sentiment delta strip.
// Renders inside NewsSection above the news feed when the Earnings pill is
// active. Two row groups:
//   1. Upcoming (next 7d) — countdown card per ticker with date + BMO/AMC tag.
//   2. Recent (past 7d) — sentiment_delta chip showing narrative shift.
// All data comes from earnings_calendar JOIN companies; delta is computed by
// scripts/compute_earnings_delta.py (daily, idempotent).

const WINDOW_DAYS = 7;
const isoDate = (d) => d.toISOString().slice(0, 10);

function fmtDaysAway(dateStr) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const e = new Date(dateStr);
  const diff = Math.round((e - today) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff < 0) return `${-diff}d ago`;
  return `in ${diff}d`;
}

function hourLabel(h) {
  if (h === 'bmo') return 'Before open';
  if (h === 'amc') return 'After close';
  if (h === 'dmh') return 'Intraday';
  return null;
}

function DeltaChip({ delta }) {
  if (delta === null || delta === undefined) return null;
  const v = Number(delta);
  const Icon = v > 0.05 ? TrendingUp : v < -0.05 ? TrendingDown : Minus;
  const colorClass = v > 0.05 ? 'is-positive' : v < -0.05 ? 'is-negative' : 'is-neutral';
  return (
    <span className={`flex items-center gap-1 text-xs font-bold earnings-delta-chip ${colorClass}`}>
      <Icon size={12} /> {v >= 0 ? '+' : ''}{v.toFixed(2)} Δ
    </span>
  );
}

export default function EarningsStrip() {
  const [upcoming, setUpcoming] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const future = new Date(today);
      future.setDate(future.getDate() + WINDOW_DAYS);
      const past = new Date(today);
      past.setDate(past.getDate() - WINDOW_DAYS);

      // earnings_calendar references companies via company_id — pull both via
      // Supabase's foreign-table syntax: companies(name, ticker).
      const upRes = await supabase
        .from('earnings_calendar')
        .select('id, earnings_date, hour, eps_estimate, companies(name, ticker)')
        .gte('earnings_date', isoDate(today))
        .lte('earnings_date', isoDate(future))
        .order('earnings_date', { ascending: true })
        .limit(30);

      const recRes = await supabase
        .from('earnings_calendar')
        .select('id, earnings_date, hour, eps_estimate, eps_actual, sentiment_delta, companies(name, ticker)')
        .gte('earnings_date', isoDate(past))
        .lt('earnings_date', isoDate(today))
        .order('earnings_date', { ascending: false })
        .limit(30);

      if (!upRes.error) setUpcoming(upRes.data || []);
      if (!recRes.error) setRecent(recRes.data || []);
      setLoading(false);
    };
    run();
  }, []);

  if (loading) return <div className="skeleton skeleton-card earnings-strip-skeleton" />;
  if (upcoming.length === 0 && recent.length === 0) return null;

  return (
    <div className="glass-panel earnings-strip">
      {upcoming.length > 0 && (
        <>
          <h3 className="text-sm font-bold mb-2 flex items-center gap-2">
            <Calendar size={14} /> Earnings — Next 7 Days
          </h3>
          <div className="flex gap-3 overflow-x-auto pb-2 earnings-strip-row">
            {upcoming.map(e => (
              <div key={e.id} className="card glass-panel earnings-strip-card earnings-strip-card-upcoming">
                <div className="font-bold text-base">{e.companies?.ticker || e.companies?.name}</div>
                <div className="text-xs text-muted">{e.companies?.name}</div>
                <div className="text-sm font-bold mt-2 earnings-strip-countdown">
                  {fmtDaysAway(e.earnings_date)}
                </div>
                <div className="text-xs text-muted">
                  {e.earnings_date}{hourLabel(e.hour) ? ` · ${hourLabel(e.hour)}` : ''}
                </div>
                {e.eps_estimate != null && (
                  <div className="text-xs text-muted mt-1">est EPS {Number(e.eps_estimate).toFixed(2)}</div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {recent.length > 0 && (
        <>
          <h3 className="text-sm font-bold mb-2 flex items-center gap-2">
            <Calendar size={14} /> Past 7 Days — Sentiment Delta
          </h3>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {recent.map(e => {
              const beat = e.eps_actual != null && e.eps_estimate != null
                ? Number(e.eps_actual) - Number(e.eps_estimate) : null;
              return (
                <div key={e.id} className="card glass-panel earnings-strip-card earnings-strip-card-recent">
                  <div className="font-bold text-base">{e.companies?.ticker || e.companies?.name}</div>
                  <div className="text-xs text-muted">{e.companies?.name}</div>
                  <div className="text-xs text-muted mt-2">Reported {e.earnings_date}</div>
                  {beat !== null && (
                    <div className={`text-xs font-bold mt-1 earnings-strip-beat ${beat >= 0 ? 'is-positive' : 'is-negative'}`}>
                      EPS {beat >= 0 ? 'beat' : 'miss'} {Math.abs(beat).toFixed(2)}
                    </div>
                  )}
                  <div className="mt-2"><DeltaChip delta={e.sentiment_delta} /></div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
