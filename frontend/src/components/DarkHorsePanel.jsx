import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Rocket } from 'lucide-react';
import ProgressBar from './ProgressBar';

// Phase 3.12: Dark-Horse Movers panel. Reads from `dark_horse_movers` (top 20)
// written daily by scripts/compute_dark_horses.py (Phase 3.11). Equal-weight
// composite of 5 signals: GH stars z-score, news volume z-score, analyst
// upgrade momentum, insider+market combined, and catalyst/release heat. Reasons array surfaces the
// drivers (e.g. "GitHub stars surging").

function ComponentBar({ label, value }) {
  // Bars colored by intensity; midpoint 50 = neutral.
  const v = Math.max(0, Math.min(100, value));
  const tone = v >= 70 ? 'green' : v <= 30 ? 'red' : 'amber';
  return (
    <div className="dark-horse-component-bar">
      <div className="text-xs text-muted dark-horse-component-label">{label}</div>
      <ProgressBar value={v} tone={tone} thin />
    </div>
  );
}

export default function DarkHorsePanel() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      const { data, error } = await supabase
        .from('dark_horse_movers')
        .select('rank, score, components, reasons, companies(name, ticker, sector, region)')
        .order('rank', { ascending: true })
        .limit(20);
      if (!error) setRows(data || []);
      setLoading(false);
    };
    run();
  }, []);

  if (loading) return <div className="skeleton skeleton-card dark-horse-skeleton" />;
  if (rows.length === 0) {
    return (
      <div className="empty-state">
        <p>No dark-horse movers yet. Rankings populate after the first compute_dark_horses run.</p>
      </div>
    );
  }

  return (
    <div>
        <p className="text-muted text-sm mb-6">
        Tracked companies punching above their weight. Equal-weight composite of GitHub stars z-score,
        news volume z-score, analyst upgrade momentum, combined insider + 7d stock momentum, and catalyst/release heat —
        chosen to dilute single-source bias. This is a sample of the tracked universe, not the full market.
      </p>
      <div className="flex-col gap-3">
        {rows.map(r => {
          const co = r.companies || {};
          const c = r.components || {};
          return (
            <div key={r.rank} className="card glass-panel dark-horse-card">
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-3">
                  <span className="badge badge-gold dark-horse-rank-badge">
                    #{r.rank}
                  </span>
                  <div>
                    <div className="font-bold text-base">{co.ticker || co.name}</div>
                    <div className="text-xs text-muted">
                      {co.name}{co.sector ? ` · ${co.sector}` : ''}{co.region ? ` · ${co.region}` : ''}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Rocket size={14} className="text-accent-amber" />
                  <span className="font-bold dark-horse-score">
                    {Math.round(r.score)}
                  </span>
                </div>
              </div>
              <div className="flex gap-3 flex-wrap mb-2">
                <ComponentBar label="GH" value={c.gh ?? 50} />
                <ComponentBar label="NEWS" value={c.news ?? 50} />
                <ComponentBar label="ANALYST" value={c.analyst ?? 50} />
                <ComponentBar label="INSIDER+MKT" value={c.market ?? 50} />
                <ComponentBar label="CATALYST" value={c.catalyst ?? 50} />
              </div>
              {(r.reasons || []).length > 0 && (
                <div className="flex gap-1 flex-wrap mt-1">
                  {r.reasons.map((reason, i) => (
                    <span key={i} className="badge badge-blue dark-horse-reason">
                      {reason}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
