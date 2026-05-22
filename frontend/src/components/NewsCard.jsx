import { Clock, TrendingUp, AlertTriangle } from 'lucide-react';
import DisputePanel from './DisputePanel';

function getTierClass(tier) {
  switch(tier) {
    case 1: return 'badge-gold';
    case 2: return 'badge-blue';
    case 3: return 'badge-gray';
    case 4: return 'badge-danger';
    default: return 'badge-gray';
  }
}

function getTierLabel(tier) {
  switch(tier) {
    case 1: return 'Tier 1 (Official)';
    case 2: return 'Tier 2 (High Trust)';
    case 3: return 'Tier 3 (Rumor/Social)';
    case 4: return 'Tier 4 (Low Trust)';
    default: return 'Unknown Source';
  }
}

function getCategoryColor(cat) {
  const map = {
    ai: 'var(--accent-blue)',
    release: 'var(--accent-green)',
    ma: 'var(--accent-amber)',
    ipo: 'var(--accent-amber)',
    controversy: 'var(--accent-red)',
    conference: 'var(--accent-blue)'
  };
  return map[cat] || 'var(--border-color)';
}

export default function NewsCard({ item, isHero = false }) {
  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Math.floor((new Date() - new Date(dateStr)) / 60000); // in minutes
    if (diff < 60) return `${diff}m ago`;
    const hours = Math.floor(diff / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const sentimentColor = item.sentiment > 0.2 ? 'green' : item.sentiment < -0.2 ? 'red' : 'gray';

  return (
    <article className={`card glass-panel flex-col ${isHero ? 'news-hero' : ''}`} style={{ borderTop: `3px solid ${getCategoryColor(item.category)}` }}>
      <div className="flex justify-between items-center mb-4">
        <span className={`badge ${getTierClass(item.source_credibility_tier)}`}>
          {getTierLabel(item.source_credibility_tier)}
        </span>
        <div className="flex items-center gap-2 text-xs text-muted font-bold">
          <Clock size={12} />
          {timeAgo(item.published_at || item.ingested_at)}
        </div>
      </div>
      
      <h3 style={{ fontSize: isHero ? '1.75rem' : '1.1rem', marginBottom: '0.5rem' }}>
        <a href={item.url} target="_blank" rel="noopener noreferrer">{item.title}</a>
      </h3>
      
      <p className="text-muted text-sm mb-4" style={{ flex: 1 }}>{item.summary}</p>
      
      {item.entity_names && item.entity_names.length > 0 && (
        <div className="flex gap-2 flex-wrap mb-4">
          {item.entity_names.map((e, i) => (
            <span key={i} className="badge badge-gray">{e}</span>
          ))}
        </div>
      )}
      
      <div className="flex items-center gap-4 text-xs font-bold mt-auto pt-4" style={{ borderTop: '1px solid var(--glass-border)' }}>
        <div className="flex items-center gap-1">
          <TrendingUp size={14} className="text-muted" />
          <span style={{ color: 'var(--accent-amber)' }}>{Math.round(item.buzz_score)} BUZZ</span>
        </div>
        
        <div className="flex items-center gap-2 flex-1">
          <span className="text-muted">SENTIMENT</span>
          <div className="progress-container" style={{ width: '60px' }}>
            <div className={`progress-bar ${sentimentColor}`} style={{ width: `${Math.max(10, Math.min(100, (item.sentiment + 1) * 50))}%` }}></div>
          </div>
        </div>

        {item.is_disputed && (
          <span className="badge badge-danger flex items-center gap-1">
            <AlertTriangle size={12} /> DISPUTED
          </span>
        )}
      </div>

      <DisputePanel item={item} />
    </article>
  );
}
