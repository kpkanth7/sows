import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { FileText, ExternalLink } from 'lucide-react';
import { safeUrl } from '../lib/urls';

// Phase 3.12: Material Events (SEC 8-K) tab inside InvestorHub. Mirrors the
// Filings pill in NewsSection but with an investor-centric layout — tracked
// tickers first, then surprise tickers (no entity match) tagged separately.

const LOOKBACK_HOURS = 72;

function timeAgo(iso) {
  if (!iso) return '';
  const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 60) return `${m}m ago`;
  if (m < 1440) return `${Math.floor(m / 60)}h ago`;
  return `${Math.floor(m / 1440)}d ago`;
}

export default function MaterialEventsPanel() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      const since = new Date(Date.now() - LOOKBACK_HOURS * 3600 * 1000).toISOString();
      const { data, error } = await supabase
        .from('news_items')
        .select('id, title, url, entity_names, published_at, ingested_at')
        .eq('source', 'sec_edgar')
        .gte('ingested_at', since)
        .order('ingested_at', { ascending: false })
        .limit(50);
      if (!error) setItems(data || []);
      setLoading(false);
    };
    run();
  }, []);

  if (loading) return <div className="skeleton skeleton-card material-events-skeleton" />;
  if (items.length === 0) {
    return (
      <div className="empty-state">
        <p>No SEC 8-K filings in the last {LOOKBACK_HOURS} hours.</p>
      </div>
    );
  }

  const tracked = items.filter(i => (i.entity_names || []).length > 0);
  const surprise = items.filter(i => (i.entity_names || []).length === 0);

  const Card = ({ it, surprise = false }) => (
    <a
      key={it.id}
      href={safeUrl(it.url)}
      target="_blank"
      rel="noopener noreferrer"
      className="card glass-panel material-events-card"
    >
      <div className="flex justify-between items-start gap-3">
        <div className="material-events-copy">
          <div className="flex items-center gap-2 mb-1">
            <span className="badge badge-gold flex items-center gap-1">
              <FileText size={10} /> 8-K
            </span>
            {surprise && <span className="badge badge-blue">NEW TICKER</span>}
            {!surprise && (it.entity_names || []).slice(0, 3).map(e => (
              <span key={e} className="badge badge-gray">{e}</span>
            ))}
            <span className="text-xs text-muted">{timeAgo(it.published_at || it.ingested_at)}</span>
          </div>
          <div className="text-sm font-bold material-events-title">{it.title}</div>
        </div>
        <ExternalLink size={14} className="text-muted material-events-link-icon" />
      </div>
    </a>
  );

  return (
    <div>
      <p className="text-muted text-sm mb-6">
        SEC 8-K material events (M&A, exec departures, breaches, bankruptcies, etc.) from the last {LOOKBACK_HOURS}h.
        Tracked companies first, then surprise tickers caught by the tech-keyword whitelist.
      </p>
      {tracked.length > 0 && (
        <div className="flex-col gap-2 mb-6">
          <h4 className="text-xs text-muted font-bold mb-1">TRACKED</h4>
          {tracked.map(it => <Card key={it.id} it={it} />)}
        </div>
      )}
      {surprise.length > 0 && (
        <div className="flex-col gap-2">
          <h4 className="text-xs text-muted font-bold mb-1">SURPRISE TICKERS</h4>
          {surprise.map(it => <Card key={it.id} it={it} surprise />)}
        </div>
      )}
    </div>
  );
}
