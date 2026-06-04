import { useEffect, useMemo, useState } from 'react';
import { Activity, CheckCircle2, Clock, Server, TriangleAlert } from 'lucide-react';
import { supabase } from '../lib/supabase';

const WARNING_AFTER_HOURS = 8;
const STALE_AFTER_HOURS = 24;

function timeAgo(iso) {
  if (!iso) return 'never';
  const minutes = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function getState(row) {
  const status = (row.status || '').toLowerCase();
  const hours = row.last_run ? (Date.now() - new Date(row.last_run).getTime()) / 36e5 : Infinity;
  if (status === 'error') return 'red';
  if (status === 'partial' || hours > STALE_AFTER_HOURS) return 'yellow';
  if (hours > WARNING_AFTER_HOURS) return 'yellow';
  return 'green';
}

function stateMeta(state) {
  if (state === 'red') return { label: 'Needs attention', icon: TriangleAlert, className: 'badge-danger' };
  if (state === 'yellow') return { label: 'Watch', icon: Clock, className: 'badge-gold' };
  return { label: 'Healthy', icon: CheckCircle2, className: 'badge-blue' };
}

export default function StatusPanel() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      const { data, error: queryError } = await supabase
        .from('health_checks')
        .select('job_name, status, detail, last_run')
        .order('job_name');

      if (queryError) {
        setError(queryError.message);
        setRows([]);
      } else {
        setRows(data || []);
        setError(null);
      }
      setLoading(false);
    };
    run();
  }, []);

  const summary = useMemo(() => {
    const counts = { green: 0, yellow: 0, red: 0 };
    rows.forEach(row => {
      counts[getState(row)] += 1;
    });
    return counts;
  }, [rows]);

  return (
    <section id="status">
      <div className="section-header flex justify-between items-end">
        <div>
          <h2 className="section-title"><Server className="text-accent-green" /> Pipeline Status</h2>
          <p className="text-muted">Last-run health from scheduled ingestion and processing jobs</p>
        </div>
      </div>

      {loading ? (
        <div className="status-grid">
          {[...Array(8)].map((_, i) => <div key={i} className="skeleton skeleton-card" />)}
        </div>
      ) : error ? (
        <div className="error-boundary glass-panel">
          <TriangleAlert size={20} className="text-accent-amber" />
          <div>
            <div className="font-bold">Status data unavailable</div>
            <p className="text-sm text-muted m-0">{error}</p>
          </div>
        </div>
      ) : rows.length === 0 ? (
        <div className="empty-state glass-panel">
          <Activity className="empty-icon" />
          <p>No health checks have been written yet.</p>
        </div>
      ) : (
        <>
          <div className="status-summary">
            <div className="glass-panel status-summary-card">
              <span className="text-xs text-muted font-bold">HEALTHY</span>
              <strong>{summary.green}</strong>
            </div>
            <div className="glass-panel status-summary-card">
              <span className="text-xs text-muted font-bold">WATCH</span>
              <strong>{summary.yellow}</strong>
            </div>
            <div className="glass-panel status-summary-card">
              <span className="text-xs text-muted font-bold">ATTENTION</span>
              <strong>{summary.red}</strong>
            </div>
          </div>

          <div className="status-grid">
            {rows.map(row => {
              const state = getState(row);
              const meta = stateMeta(state);
              const Icon = meta.icon;
              return (
                <article key={row.job_name} className="card glass-panel status-card">
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <h3>{row.job_name.replaceAll('_', ' ')}</h3>
                      <span className={`badge ${meta.className} flex items-center gap-2`}>
                        <Icon size={12} /> {meta.label}
                      </span>
                    </div>
                    <span className="text-xs text-muted font-bold">{timeAgo(row.last_run)}</span>
                  </div>
                  {row.detail && <p className="text-sm text-muted">{row.detail}</p>}
                </article>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
