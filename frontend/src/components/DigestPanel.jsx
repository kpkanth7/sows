import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Newspaper } from 'lucide-react';

// Phase 3.12: Daily Digest tab inside InvestorHub. Renders the latest digest
// row (also surfaced as the dashboard banner via DailyDigestBanner) plus the
// previous 6 days of summaries so investors can scan recent narrative shifts.

export default function DigestPanel() {
  const [digests, setDigests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      const { data, error } = await supabase
        .from('daily_digests')
        .select('digest_date, summary, top_tickers, source_count, generated_at')
        .order('digest_date', { ascending: false })
        .limit(7);
      if (!error) setDigests(data || []);
      setLoading(false);
    };
    run();
  }, []);

  if (loading) return <div className="skeleton skeleton-card digest-panel-skeleton" />;
  if (digests.length === 0) {
    return (
      <div className="empty-state">
        <p>No daily digest yet. First digest is generated at 02:00 UTC.</p>
      </div>
    );
  }

  const [latest, ...history] = digests;

  return (
    <div>
      <p className="text-muted text-sm mb-6">
        LLM-synthesized "what an investor should know" — built daily from last-24h news, SEC 8-Ks,
        insider trades, and earnings signals.
      </p>

      <div className="card glass-panel mb-6 digest-panel-latest">
        <div className="flex items-center gap-2 mb-2">
          <Newspaper size={16} className="text-accent-amber" />
          <span className="font-bold text-sm">Today · {latest.digest_date}</span>
          <span className="text-xs text-muted">· {latest.source_count} signals</span>
        </div>
        <p className="text-sm m-0 digest-panel-summary">{latest.summary}</p>
        {(latest.top_tickers || []).length > 0 && (
          <div className="flex gap-2 flex-wrap mt-3">
            {latest.top_tickers.map(t => (
              <span key={t} className="badge badge-gold digest-panel-top-ticker">{t}</span>
            ))}
          </div>
        )}
      </div>

      {history.length > 0 && (
        <>
          <h4 className="text-xs text-muted font-bold mb-3">PAST 6 DAYS</h4>
          <div className="flex-col gap-3">
            {history.map(d => (
              <div key={d.digest_date} className="card glass-panel digest-panel-history-card">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-muted font-bold">{d.digest_date}</span>
                  <span className="text-xs text-muted">{d.source_count} signals</span>
                </div>
                <p className="text-sm m-0 digest-panel-summary">{d.summary}</p>
                {(d.top_tickers || []).length > 0 && (
                  <div className="flex gap-1 flex-wrap mt-2">
                    {d.top_tickers.map(t => (
                      <span key={t} className="badge badge-gray digest-panel-history-ticker">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
