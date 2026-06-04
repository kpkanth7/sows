import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

// Phase 3.4: insider transactions panel.
// Powered by `insider_transactions` (Finnhub, ingested in 2.5).
//
//   prop `companyId`  optional. If set, shows trades for that company only.
//                     If not, shows notable trades across all tracked cos.
//
// Filter: |change| >= NOTABLE_THRESHOLD shares to hide tiny routine grants.
// Window: last LOOKBACK_DAYS days.

const NOTABLE_THRESHOLD = 10000;
const LOOKBACK_DAYS = 30;

function fmtShares(n) {
  if (n == null) return '';
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export default function InsiderTradesPanel({ companyId = null }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      const since = new Date();
      since.setDate(since.getDate() - LOOKBACK_DAYS);

      // Fetch notable trades. Two paths: per-company (uses indexed company_id)
      // vs global (broader — query against transaction_date directly).
      let q = supabase
        .from('insider_transactions')
        .select('id, person, position, transaction_type, share, change, transaction_date, filing_date, companies(name, ticker)')
        .gte('transaction_date', since.toISOString().slice(0, 10))
        .order('transaction_date', { ascending: false })
        .limit(companyId ? 50 : 25);

      if (companyId) q = q.eq('company_id', companyId);

      const { data, error } = await q;
      if (error || !data) {
        setRows([]);
        setLoading(false);
        return;
      }
      // Notable filter applied client-side so we keep one query path.
      const filtered = data.filter(r => Math.abs(r.change || 0) >= NOTABLE_THRESHOLD);
      setRows(filtered);
      setLoading(false);
    };
    run();
  }, [companyId]);

  if (loading) return <div className="skeleton skeleton-card insider-trades-skeleton" />;
  if (rows.length === 0) {
    return (
      <div className="text-xs text-muted">
        No notable insider trades (|change| ≥ {fmtShares(NOTABLE_THRESHOLD)}) in the last {LOOKBACK_DAYS} days.
      </div>
    );
  }

  return (
    <div className="flex-col gap-2">
      {rows.map(r => {
        const isBuy = (r.change || 0) > 0;
        const Icon = isBuy ? ArrowUpRight : ArrowDownRight;
        return (
          <div key={r.id} className="card glass-panel flex items-center justify-between insider-trades-row">
            <div className="insider-trades-meta">
              <div className="font-bold text-sm insider-trades-person">
                {r.person || 'Unknown'} {r.position ? <span className="text-muted text-xs">· {r.position}</span> : null}
              </div>
              <div className="text-xs text-muted">
                {!companyId && r.companies?.ticker ? `${r.companies.ticker} · ` : ''}
                {r.transaction_date} · {r.transaction_type || 'trade'}
              </div>
            </div>
            <div className={`flex items-center gap-1 font-bold text-sm insider-trades-change ${isBuy ? 'is-buy' : 'is-sell'}`}>
              <Icon size={14} />
              {isBuy ? '+' : ''}{fmtShares(r.change)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
