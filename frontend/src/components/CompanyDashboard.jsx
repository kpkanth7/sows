import { useState, useEffect, useMemo } from 'react';
import { ResponsiveContainer, Treemap } from 'recharts';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import CompanyDetailPanel from './CompanyDetailPanel';
import { Briefcase } from 'lucide-react';

// Phase 3.10: Market Map redesigned from flat grid → recharts Treemap.
// Tiles SIZED by market_cap (public) or last_valuation (private) — privates
// with a real valuation now rank by that valuation instead of being shoved
// to the end. Tiles COLORED by 24h change (green/red, neutral gray for null).
// Filters: sector pills + region pills + public/private toggle, AND-combined.

// Map a 24h % change to a hex color. Magnitude clamped at ±5% for intensity.
// Null/zero → neutral surface gray so privates (no daily price) don't fake red.
function changeToColor(pct) {
  if (pct === null || pct === undefined || Number.isNaN(pct)) return '#2a2d35';
  if (pct === 0) return '#2a2d35';
  const mag = Math.min(Math.abs(pct), 5) / 5; // 0..1
  // Blend from dark surface → vivid green/red
  const lerp = (a, b, t) => Math.round(a + (b - a) * t);
  if (pct > 0) {
    const r = lerp(42, 16, mag);
    const g = lerp(45, 160, mag);
    const b = lerp(53, 80, mag);
    return `rgb(${r},${g},${b})`;
  }
  const r = lerp(42, 200, mag);
  const g = lerp(45, 45, mag);
  const b = lerp(53, 60, mag);
  return `rgb(${r},${g},${b})`;
}

// Custom recharts Treemap tile renderer. Hides label on tiny tiles to avoid
// crowding. Click bubbles up via onClick prop the parent wires to set state.
function TreemapTile(props) {
  const { x, y, width, height, name, change, color, onTileClick, payload } = props;
  if (width <= 0 || height <= 0) return null;
  const showLabel = width > 60 && height > 30;
  const showChange = width > 80 && height > 48 && change !== null && change !== undefined;
  return (
    <g
      style={{ cursor: 'pointer' }}
      onClick={() => onTileClick && payload && onTileClick(payload.company)}
    >
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: color,
          stroke: 'rgba(0,0,0,0.4)',
          strokeWidth: 1,
        }}
      />
      {showLabel && (
        <text
          x={x + width / 2}
          y={y + height / 2 - (showChange ? 6 : 0)}
          textAnchor="middle"
          fill="#fff"
          fontSize={Math.min(16, Math.max(11, width / 8))}
          fontWeight={700}
          style={{ pointerEvents: 'none', fontFamily: 'var(--font-heading)' }}
        >
          {name}
        </text>
      )}
      {showChange && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 12}
          textAnchor="middle"
          fill="rgba(255,255,255,0.85)"
          fontSize={11}
          style={{ pointerEvents: 'none' }}
        >
          {change > 0 ? '+' : ''}{change.toFixed(2)}%
        </text>
      )}
    </g>
  );
}

export default function CompanyDashboard() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [view, setView] = useState('all');       // all | public | private
  const [sector, setSector] = useState('All');
  const [region, setRegion] = useState('All');

  useEffect(() => {
    async function fetchCompanies() {
      const cached = cache.get('companies');
      if (cached) {
        setCompanies(cached);
        setLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from('companies')
        .select('*')
        .order('market_cap', { ascending: false, nullsFirst: false });

      if (!error && data) {
        setCompanies(data);
        cache.set('companies', data, 15);
      }
      setLoading(false);
    }
    fetchCompanies();
  }, []);

  // Distinct sectors/regions derived from the fetched rows. Null/empty dropped.
  const sectors = useMemo(() => {
    const s = new Set(companies.map(c => c.sector).filter(Boolean));
    return ['All', ...Array.from(s).sort()];
  }, [companies]);

  const regions = useMemo(() => {
    const r = new Set(companies.map(c => c.region).filter(Boolean));
    return ['All', ...Array.from(r).sort()];
  }, [companies]);

  // AND-combined filters, then sort by effective value (mcap || valuation).
  // Privates with a valuation now slot in by size instead of being last.
  const treemapData = useMemo(() => {
    return companies
      .filter(c => view === 'all' || (view === 'public' ? !c.is_private : c.is_private))
      .filter(c => sector === 'All' || c.sector === sector)
      .filter(c => region === 'All' || c.region === region)
      .map(c => {
        const value = c.market_cap || c.last_valuation || 0;
        return {
          name: c.ticker || c.name,
          size: value,
          change: c.change_pct_24h,
          color: changeToColor(c.change_pct_24h),
          company: c,
        };
      })
      .filter(d => d.size > 0)
      .sort((a, b) => b.size - a.size);
  }, [companies, view, sector, region]);

  return (
    <section id="companies" style={{ background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
      <div className="section-header">
        <h2 className="section-title"><Briefcase className="text-accent-amber" /> Market Map</h2>
        <p className="text-muted">Tiles sized by market cap / valuation, colored by 24h move. Click any tile.</p>
      </div>

      {/* Filter stack — sector + region pills + public/private toggle. */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
        <div className="category-pills" style={{ marginBottom: 0 }}>
          {sectors.map(s => (
            <button key={s} className={`pill ${sector === s ? 'active' : ''}`} onClick={() => setSector(s)}>{s}</button>
          ))}
        </div>
        <div className="category-pills" style={{ marginBottom: 0 }}>
          {regions.map(r => (
            <button key={r} className={`pill ${region === r ? 'active' : ''}`} onClick={() => setRegion(r)}>{r}</button>
          ))}
        </div>
        <div className="category-pills" style={{ marginBottom: 0 }}>
          <button className={`pill ${view === 'all' ? 'active' : ''}`} onClick={() => setView('all')}>All</button>
          <button className={`pill ${view === 'public' ? 'active' : ''}`} onClick={() => setView('public')}>Public</button>
          <button className={`pill ${view === 'private' ? 'active' : ''}`} onClick={() => setView('private')}>Private</button>
        </div>
      </div>

      {loading ? (
        <div className="skeleton card" style={{ height: '650px' }}></div>
      ) : treemapData.length === 0 ? (
        <div className="card glass-panel" style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p className="text-muted">No companies match the current filters.</p>
        </div>
      ) : (
        <div style={{ width: '100%', height: 650 }}>
          <ResponsiveContainer width="100%" height="100%">
            <Treemap
              data={treemapData}
              dataKey="size"
              stroke="#000"
              isAnimationActive={false}
              content={<TreemapTile onTileClick={setSelectedCompany} />}
            />
          </ResponsiveContainer>
        </div>
      )}

      {selectedCompany && (
        <CompanyDetailPanel company={selectedCompany} onClose={() => setSelectedCompany(null)} />
      )}
    </section>
  );
}
