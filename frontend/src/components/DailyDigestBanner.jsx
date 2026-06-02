import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Newspaper, ChevronDown, ChevronUp } from 'lucide-react';

// Phase 3.7: hero banner above the dashboard. Pulls the most recent row from
// `daily_digests` (written daily by scripts/generate_daily_digest.py).
// Collapsible on mobile to stay out of the way.

export default function DailyDigestBanner() {
  const [digest, setDigest] = useState(null);
  const [open, setOpen] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      const { data, error } = await supabase
        .from('daily_digests')
        .select('digest_date, summary, top_tickers, source_count, generated_at')
        .order('digest_date', { ascending: false })
        .limit(1)
        .maybeSingle();
      if (!error && data) setDigest(data);
      setLoading(false);
    };
    run();
  }, []);

  if (loading || !digest) return null;

  const dateStr = digest.digest_date;
  const tickers = digest.top_tickers || [];

  return (
    <div
      className="digest-banner"
    >
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Newspaper size={16} className="text-accent-amber" />
          <span className="font-bold text-sm">Today's Tech-Investor Digest</span>
          <span className="text-xs text-muted">· {dateStr} · {digest.source_count} signals</span>
        </div>
        <button
          className="theme-toggle"
          onClick={() => setOpen(o => !o)}
          aria-label={open ? 'Collapse digest' : 'Expand digest'}
          style={{ padding: '4px' }}
        >
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>
      {open && (
        <div className="mt-2">
          <p className="text-sm m-0" style={{ lineHeight: 1.5 }}>{digest.summary}</p>
          {tickers.length > 0 && (
            <div className="flex gap-2 flex-wrap mt-3">
              {tickers.map(t => (
                <span key={t} className="badge badge-gold" style={{ fontSize: '0.7rem' }}>{t}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
