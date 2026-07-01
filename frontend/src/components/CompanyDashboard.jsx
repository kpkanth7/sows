import { useState, useEffect, useMemo } from 'react';
import { ResponsiveContainer, Treemap } from 'recharts';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import CompanyDetailPanel from './CompanyDetailPanel';
import { ArrowLeft, Briefcase, Grid2X2, Layers3, List } from 'lucide-react';

// Phase 3.10: Market Map redesigned from flat grid → recharts Treemap.
// Tiles SIZED by market_cap (public) or last_valuation (private) — privates
// with a real valuation now rank by that valuation instead of being shoved
// to the end. Tiles COLORED by 24h change (green/red, neutral gray for null).
// Filters: sector pills + region pills + public/private toggle, AND-combined.

const VISIBLE_TILE_COUNT = 4;
const MISC_VISUAL_SHARE = 0.125;
const SIZE_COMPRESSION_POWER = 1.05;
const SIZE_OFFSET = 1;

// Map a 24h % change to a richer market-map color. Magnitude is clamped so
// outliers stay readable while still showing direction clearly.
function changeToColor(pct) {
  if (pct === null || pct === undefined || Number.isNaN(pct)) return '#253955';
  if (pct === 0) return '#253955';
  const mag = Math.min(Math.abs(pct), 10) / 10; // 0..1
  const lerp = (a, b, t) => Math.round(a + (b - a) * t);
  if (pct > 0) {
    const r = lerp(28, 13, mag);
    const g = lerp(83, 178, mag);
    const b = lerp(96, 100, mag);
    return `rgb(${r},${g},${b})`;
  }
  const r = lerp(77, 205, mag);
  const g = lerp(63, 55, mag);
  const b = lerp(98, 88, mag);
  return `rgb(${r},${g},${b})`;
}

function privateValuationColor(value) {
  if (!value) return '#253955';
  const mag = Math.min(Math.log10(value) - 9, 3) / 3;
  const t = Math.max(0, Math.min(1, mag));
  const lerp = (a, b, pct) => Math.round(a + (b - a) * pct);
  return `rgb(${lerp(31, 72, t)},${lerp(56, 126, t)},${lerp(91, 178, t)})`;
}

function fmtMoney(value) {
  if (!value) return '—';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  return `$${Math.round(value).toLocaleString()}`;
}

function compressMapSize(value) {
  if (!value || Number.isNaN(value) || value <= 0) return 0;
  return Math.pow(Math.log10(value + SIZE_OFFSET), SIZE_COMPRESSION_POWER);
}

function buildMapLevel(items, depth) {
  const start = depth * VISIBLE_TILE_COUNT;
  const levelItems = items.slice(start);
  const visible = levelItems.slice(0, VISIBLE_TILE_COUNT);
  const tail = levelItems.slice(VISIBLE_TILE_COUNT);

  const visibleSized = visible.map(item => ({
    ...item,
    size: compressMapSize(item.rawSize || item.size),
  }));

  if (!tail.length) return visibleSized;

  const tailSize = tail.reduce((sum, item) => sum + (item.rawSize || item.size || 0), 0);
  const visibleSize = visibleSized.reduce((sum, item) => sum + item.size, 0);
  const tailVisualSize = visibleSize
    ? Math.max(visibleSize * (MISC_VISUAL_SHARE / (1 - MISC_VISUAL_SHARE)), 0.001)
    : 1;
  const gainers = tail.filter(item => item.change > 0).length;
  const losers = tail.filter(item => item.change < 0).length;
  const avgChangeValues = tail
    .map(item => item.change)
    .filter(change => change !== null && change !== undefined && !Number.isNaN(change));
  const avgChange = avgChangeValues.length
    ? avgChangeValues.reduce((sum, change) => sum + change, 0) / avgChangeValues.length
    : null;
  const clusterSummary = avgChangeValues.length
    ? `${gainers} up / ${losers} down`
    : `${fmtMoney(tailSize)} combined`;

  return [
    ...visibleSized,
    {
      name: 'Miscellaneous',
      size: tailVisualSize,
      rawSize: tailSize,
      change: avgChange,
      color: '#33415f',
      isCluster: true,
      clusterCount: tail.length,
      clusterDepth: depth + 1,
      clusterSummary,
      fullName: `${tail.length} smaller companies`,
      metricLabel: `${fmtMoney(tailSize)} combined`,
      hoverDetail: `${fmtMoney(tailSize)} combined value · click to drill in`,
    },
  ];
}

function splitTileLabel(label) {
  const words = String(label || '').trim().split(/\s+/).filter(Boolean);
  if (words.length <= 1) return [label];

  const lines = [];
  let current = '';
  words.forEach(word => {
    const next = current ? `${current} ${word}` : word;
    if (!current || next.length <= 14) {
      current = next;
    } else {
      lines.push(current);
      current = word;
    }
  });
  if (current) lines.push(current);

  if (lines.length <= 2) return lines;
  return [words.slice(0, -1).join(' '), words[words.length - 1]];
}

function ColorSwatch({ color, className }) {
  return (
    <svg className={className} viewBox="0 0 12 12" aria-hidden="true">
      <rect x="0" y="0" width="12" height="12" rx="3" fill={color} />
    </svg>
  );
}

// Custom recharts Treemap tile renderer. Hides label on tiny tiles to avoid
// crowding. Click bubbles up via onClick prop the parent wires to set state.
function TreemapTile(props) {
  const { x, y, width, height, name, change, color, onTileClick, onClusterClick, onTileHover, payload } = props;
  if (width <= 0 || height <= 0) return null;
  const data = payload || props;
  const isCluster = Boolean(data.isCluster);
  const fontSize = Math.min(18, Math.max(12, Math.min(width / 8, height / 4)));
  const labelText = String(name || '');
  const labelLines = splitTileLabel(labelText);
  const longestLine = Math.max(...labelLines.map(line => line.length), 1);
  const labelFontSize = isCluster
    ? Math.min(24, Math.max(16, width / 11))
    : Math.max(9.5, Math.min(fontSize, (width - 24) / (longestLine * 0.62), height / (labelLines.length * 3.1)));
  const showLabel = isCluster || (width > 56 && height > 40);
  const showDetails = isCluster ? width > 120 && height > 76 : width > 84 && height > 64;
  const showFullName = !isCluster && showDetails && data.fullName && data.fullName !== name;
  const handleClick = () => {
    if (isCluster) {
      onClusterClick && onClusterClick(data.clusterDepth);
      return;
    }
    onTileClick && data.company && onTileClick(data.company);
  };

  return (
    <g
      className={`market-tile market-tile-clickable ${isCluster ? 'market-tile-cluster' : ''} ${data.isPendingCap ? 'market-tile-pending-cap' : ''}`}
      onClick={handleClick}
      onMouseEnter={() => onTileHover && onTileHover(data)}
      onMouseLeave={() => onTileHover && onTileHover(null)}
    >
      <title>{data.tooltip}</title>
      <rect
        className="market-tile-rect"
        x={x + 1}
        y={y + 1}
        width={Math.max(0, width - 2)}
        height={Math.max(0, height - 2)}
        rx={Math.min(10, Math.max(3, Math.min(width, height) / 12))}
        fill={color}
      />
      {showLabel && (
        <>
          {isCluster && (
            <text
              x={x + width / 2}
              y={y + height / 2 - 32}
              fill="rgba(255,255,255,0.72)"
              fontSize={12}
              textAnchor="middle"
              pointerEvents="none"
            >
              {data.clusterCount} companies
            </text>
          )}
          <text
            x={x + width / 2}
            y={isCluster ? y + height / 2 - 8 : y + height / 2 - (showDetails ? 14 : 0) - ((labelLines.length - 1) * labelFontSize * 0.56)}
            textAnchor="middle"
            fill="#f8fbff"
            fontSize={labelFontSize}
            fontWeight={800}
            pointerEvents="none"
            fontFamily="var(--font-heading)"
            paintOrder="stroke"
            stroke="rgba(4, 8, 18, 0.72)"
            strokeWidth={2}
          >
            {isCluster ? name : labelLines.map((line, index) => (
              <tspan key={line} x={x + width / 2} dy={index === 0 ? 0 : labelFontSize * 1.08}>
                {line}
              </tspan>
            ))}
          </text>
          {showFullName && (
            <text
              x={x + width / 2}
              y={y + height / 2 + 4 + ((labelLines.length - 1) * labelFontSize * 0.5)}
              textAnchor="middle"
              fill="rgba(255,255,255,0.72)"
              fontSize={Math.min(12, Math.max(9, width / 13))}
              fontWeight={600}
              pointerEvents="none"
              paintOrder="stroke"
              stroke="rgba(4, 8, 18, 0.65)"
              strokeWidth={2}
            >
              {data.fullName}
            </text>
          )}
        </>
      )}
      {showDetails && (
        <text
          x={x + width / 2}
          y={isCluster ? y + height / 2 + 20 : y + height / 2 + 22 + ((labelLines.length - 1) * labelFontSize * 0.5)}
          textAnchor="middle"
          fill="rgba(255,255,255,0.85)"
          fontSize={11}
          fontWeight={700}
          pointerEvents="none"
          paintOrder="stroke"
          stroke="rgba(4, 8, 18, 0.6)"
          strokeWidth={2}
        >
          {isCluster ? data.clusterSummary : data.metricLabel}
        </text>
      )}
      {isCluster && width > 120 && height > 86 && (
        <text
          x={x + width / 2}
          y={y + height - 18}
          fill="rgba(255,255,255,0.7)"
          fontSize={11}
          fontWeight={700}
          textAnchor="middle"
          pointerEvents="none"
        >
          Click to drill in
        </text>
      )}
    </g>
  );
}

function MarketListView({ data, isPrivate, setSelectedCompany }) {
  return (
    <div className="market-map-list-view">
      <div className="market-map-list-head">
        <span>Company</span>
        <span>{isPrivate ? 'Valuation' : 'Market Cap'}</span>
        <span>{isPrivate ? 'Status' : '24h Move'}</span>
        <span>Region</span>
        <span>Sector</span>
      </div>
      <div className="market-map-list-rows">
        {data.map(item => {
          const company = item.company || {};
          const move = company.change_pct_24h;
          const moveLabel = move === null || move === undefined || Number.isNaN(move)
            ? '—'
            : `${move > 0 ? '+' : ''}${move.toFixed(2)}%`;
          return (
            <button
              key={company.id || item.name}
              className="market-map-list-row"
              onClick={() => setSelectedCompany(company)}
              aria-label={`Open ${item.fullName || item.name} details`}
            >
              <span className="market-map-list-company">
                <ColorSwatch color={item.color} className="market-map-list-swatch" />
                <span>
                  <strong>{item.fullName || item.name}</strong>
                  <small>{company.ticker || (company.is_private ? 'Private' : 'Public')}</small>
                </span>
              </span>
              <span>{isPrivate ? fmtMoney(company.last_valuation) : fmtMoney(company.market_cap)}</span>
              <span className={!isPrivate && move > 0 ? 'text-accent-green' : !isPrivate && move < 0 ? 'text-accent-red' : 'text-muted'}>
                {isPrivate ? 'Private' : moveLabel}
              </span>
              <span>{company.region || '—'}</span>
              <span>{company.sector || '—'}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function MarketMapPanel({ title, subtitle, data, depth, setDepth, setSelectedCompany, emptyText }) {
  const [hoveredTile, setHoveredTile] = useState(null);
  const [view, setView] = useState('map');
  const treemapData = useMemo(() => buildMapLevel(data, depth), [data, depth]);
  const canGoBack = depth > 0;
  const depthStart = depth * VISIBLE_TILE_COUNT + 1;
  const depthEnd = Math.min(data.length, (depth + 1) * VISIBLE_TILE_COUNT);
  const isPrivate = title.toLowerCase().includes('private');
  const isListView = view === 'list';

  return (
    <div className="market-map-panel">
      <div className="market-map-panel-header">
        <div>
          <div className="market-map-title-row">
            <h3>{title}</h3>
            <button
              className="market-map-view-button"
              onClick={() => setView(isListView ? 'map' : 'list')}
              type="button"
              aria-pressed={isListView}
            >
              {isListView ? <Grid2X2 size={14} /> : <List size={14} />}
              {isListView ? 'Map' : 'List'}
            </button>
          </div>
          <p>{subtitle}</p>
        </div>
        <div className="market-map-hover-card">
          {hoveredTile ? (
            <>
              <strong>{hoveredTile.fullName || hoveredTile.name}</strong>
              <span>{hoveredTile.hoverDetail || hoveredTile.metricLabel || hoveredTile.clusterSummary}</span>
            </>
          ) : (
            <>
              <strong>Hover a tile</strong>
              <span>Full company name, value, and move appear here.</span>
            </>
          )}
        </div>
      </div>

      <div className="market-map-toolbar">
        <div>
          <span className="market-map-kicker">Showing</span>
          <strong>{isListView ? `All ${data.length}` : `${data.length ? `${depthStart}-${depthEnd}` : '0'} of ${data.length}`}</strong>
        </div>
        {isListView ? (
          <span className="market-map-hint"><List size={15} /> Click any row to open details</span>
        ) : canGoBack ? (
          <button className="market-map-back" onClick={() => setDepth(current => Math.max(0, current - 1))}>
            <ArrowLeft size={16} /> Back to larger tiles
          </button>
        ) : (
          <span className="market-map-hint"><Layers3 size={15} /> Click Miscellaneous to drill into smaller companies</span>
        )}
      </div>

      {treemapData.length === 0 ? (
        <div className="card glass-panel market-map-empty">
          <p className="text-muted">{emptyText}</p>
        </div>
      ) : isListView ? (
        <MarketListView data={data} isPrivate={isPrivate} setSelectedCompany={setSelectedCompany} />
      ) : (
        <>
          <div className="market-map-canvas">
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={treemapData}
                dataKey="size"
                stroke="transparent"
                isAnimationActive={false}
                content={<TreemapTile onTileClick={setSelectedCompany} onClusterClick={setDepth} onTileHover={setHoveredTile} />}
              />
            </ResponsiveContainer>
          </div>
          <div className="market-map-mobile-list">
            {treemapData.map(item => (
              <button
                key={`${item.name}-${item.clusterDepth || item.company?.id || item.size}`}
                className={`market-map-mobile-row ${item.isCluster ? 'is-cluster' : ''}`}
                onClick={() => item.isCluster ? setDepth(item.clusterDepth) : setSelectedCompany(item.company)}
                aria-label={item.isCluster ? `Open miscellaneous cluster with ${item.clusterCount} companies` : `Open ${item.fullName || item.name} details`}
              >
                <ColorSwatch color={item.color} className="market-map-mobile-swatch" />
                <span className="market-map-mobile-name">
                  <strong>{item.fullName || item.name}</strong>
                  <small>{item.isCluster ? item.clusterSummary : item.hoverDetail}</small>
                </span>
                <span className="market-map-mobile-value">{item.metricLabel}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default function CompanyDashboard() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [sector, setSector] = useState('All');
  const [region, setRegion] = useState('All');
  const [publicDepth, setPublicDepth] = useState(0);
  const [privateDepth, setPrivateDepth] = useState(0);

  useEffect(() => {
    async function fetchCompanies() {
      const cached = cache.get('companies-market-map-v4');
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
        cache.set('companies-market-map-v4', data, 5);
      }
      setLoading(false);
    }
    fetchCompanies();
  }, []);

  useEffect(() => {
    setPublicDepth(0);
    setPrivateDepth(0);
  }, [sector, region]);

  // Distinct sectors/regions derived from the fetched rows. Null/empty dropped.
  const sectors = useMemo(() => {
    const s = new Set(companies.map(c => c.sector).filter(Boolean));
    return ['All', ...Array.from(s).sort()];
  }, [companies]);

  const regions = useMemo(() => {
    const r = new Set(companies.map(c => c.region).filter(Boolean));
    return ['All', ...Array.from(r).sort()];
  }, [companies]);

  const filteredCompanies = useMemo(() => {
    return companies
      .filter(c => sector === 'All' || c.sector === sector)
      .filter(c => region === 'All' || c.region === region);
  }, [companies, sector, region]);

  const publicTreemapData = useMemo(() => {
    const publicCompanies = filteredCompanies.filter(c => !c.is_private && c.ticker);
    const realCaps = publicCompanies
      .map(c => c.market_cap)
      .filter(Boolean)
      .sort((a, b) => a - b);
    const pendingSize = realCaps.length ? Math.max(realCaps[0] * 0.7, 2_000_000_000) : 2_000_000_000;

    return publicCompanies
      .map(c => {
        const metricLabel = c.change_pct_24h === null || c.change_pct_24h === undefined
          ? 'No 24h move'
          : `${c.change_pct_24h > 0 ? '+' : ''}${c.change_pct_24h.toFixed(2)}%`;
        const fullName = c.name || c.ticker;
        const hasMarketCap = Boolean(c.market_cap);
        return {
          name: c.ticker || c.name,
          fullName,
          size: c.market_cap || pendingSize,
          rawSize: c.market_cap || pendingSize,
          change: c.change_pct_24h,
          color: changeToColor(c.change_pct_24h),
          company: c,
          metricLabel: hasMarketCap ? metricLabel : 'Market cap pending',
          listDetail: hasMarketCap ? `${fmtMoney(c.market_cap)} market cap` : 'Market cap pending',
          hoverDetail: hasMarketCap
            ? `${fmtMoney(c.market_cap)} market cap · ${metricLabel}`
            : `Market cap pending · ${metricLabel}`,
          tooltip: hasMarketCap
            ? `${fullName} (${c.ticker})\nMarket cap: ${fmtMoney(c.market_cap)}\n24h move: ${metricLabel}`
            : `${fullName} (${c.ticker})\nMarket cap: pending\n24h move: ${metricLabel}`,
          isPendingCap: !hasMarketCap,
        };
      })
      .filter(d => d.size > 0)
      .sort((a, b) => {
        if (a.isPendingCap !== b.isPendingCap) return a.isPendingCap ? 1 : -1;
        return b.size - a.size;
      });
  }, [filteredCompanies]);

  const privateTreemapData = useMemo(() => {
    return filteredCompanies
      .filter(c => c.is_private && c.last_valuation)
      .map(c => {
        const fullName = c.name || c.ticker;
        return {
          name: c.name,
          fullName,
          size: c.last_valuation,
          rawSize: c.last_valuation,
          change: null,
          color: privateValuationColor(c.last_valuation),
          company: c,
          metricLabel: fmtMoney(c.last_valuation),
          listDetail: 'Private valuation',
          hoverDetail: `${fmtMoney(c.last_valuation)} private valuation · no public 24h move`,
          tooltip: `${fullName}\nPrivate valuation: ${fmtMoney(c.last_valuation)}\n24h move: not publicly traded`,
        };
      })
      .filter(d => d.size > 0)
      .sort((a, b) => b.size - a.size);
  }, [filteredCompanies]);

  return (
    <section id="companies" className="market-map-section">
      <div className="section-header">
        <h2 className="section-title"><Briefcase className="text-accent-amber" /> Market Map</h2>
        <p className="text-muted">
          Public companies are sized by market cap and colored by 24h move. Private companies are shown separately by last valuation.
        </p>
      </div>

      {/* Filter stack — sector + region pills apply to both maps. */}
      <div className="market-map-filter-stack">
        <div className="category-pills market-map-filter-row">
          {sectors.map(s => (
            <button key={s} className={`pill ${sector === s ? 'active' : ''}`} onClick={() => setSector(s)}>{s}</button>
          ))}
        </div>
        <div className="category-pills market-map-filter-row">
          {regions.map(r => (
            <button key={r} className={`pill ${region === r ? 'active' : ''}`} onClick={() => setRegion(r)}>{r}</button>
          ))}
        </div>
        <div className="category-pills market-map-filter-row">
          <span className="badge badge-gray market-map-filter-badge">{publicTreemapData.length} public stocks</span>
          <span className="badge badge-gray market-map-filter-badge">{privateTreemapData.length} private valuations</span>
        </div>
      </div>

      {loading ? (
        <div className="skeleton card market-map-loading" />
      ) : (
        <div className="market-map-stack">
          <MarketMapPanel
            title="Public Markets"
            subtitle="Sized by actual market cap. Color shows latest 24h price move when available."
            data={publicTreemapData}
            depth={publicDepth}
            setDepth={setPublicDepth}
            setSelectedCompany={setSelectedCompany}
            emptyText="No public companies with market cap match the current filters."
          />
          <MarketMapPanel
            title="Private Valuations"
            subtitle="Sized by latest known private valuation. Private companies do not have public 24h price moves."
            data={privateTreemapData}
            depth={privateDepth}
            setDepth={setPrivateDepth}
            setSelectedCompany={setSelectedCompany}
            emptyText="No private companies with valuation match the current filters."
          />
        </div>
      )}

      {selectedCompany && (
        <CompanyDetailPanel company={selectedCompany} onClose={() => setSelectedCompany(null)} />
      )}
    </section>
  );
}
