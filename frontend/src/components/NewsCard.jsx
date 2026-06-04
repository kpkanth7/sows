import { Clock, TrendingUp, AlertTriangle, FileText, Scale, BookOpen, Mic2 } from 'lucide-react';
import DisputePanel from './DisputePanel';
import { safeUrl } from '../lib/urls';
import ProgressBar from './ProgressBar';

function isSocialCommunityItem(item) {
  return item?.category === 'social' || String(item?.source || '').startsWith('r/');
}

function getTierClass(tier, item) {
  if (item?.source_type === 'influencer') return 'badge-blue';
  if (isSocialCommunityItem(item)) return 'badge-danger';
  switch(tier) {
    case 1: return 'badge-gold';
    case 2: return 'badge-blue';
    case 3: return 'badge-gray';
    case 4: return 'badge-danger';
    default: return 'badge-gray';
  }
}

function getTierLabel(tier, item) {
  if (item?.source_type === 'influencer') return 'Creator Insight';
  if (isSocialCommunityItem(item)) return 'Community Signal';
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
    ai: 'news-card-category-ai',
    release: 'news-card-category-release',
    ma: 'news-card-category-ma',
    ipo: 'news-card-category-ipo',
    controversy: 'news-card-category-controversy',
    conference: 'news-card-category-conference',
    social: 'news-card-category-social'
  };
  return map[cat] || 'news-card-category-default';
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
  const displayBuzz = item.buzz_v2 ?? item.buzz_score ?? 0;
  const categoryColor = getCategoryColor(item.category);
  const sentimentValue = Math.max(10, Math.min(100, (item.sentiment + 1) * 50));

  return (
    <article className={`card glass-panel flex-col news-card ${categoryColor} ${isHero ? 'news-hero' : ''}`}>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <span className={`badge ${getTierClass(item.source_credibility_tier, item)}`}>
            {item.source_type === 'influencer' && <Mic2 size={10} />}
            {getTierLabel(item.source_credibility_tier, item)}
          </span>
          {item.source_type === 'influencer' && (
            <span className="badge badge-gray">{item.source}</span>
          )}
          {isSocialCommunityItem(item) && (
            <span className="badge badge-gray">{item.source}</span>
          )}
          {/* Phase 3.1: explicit SEC 8-K badge so material filings stand out
              even when listed inside All / category pills. */}
          {item.source === 'sec_edgar' && (
            <span className="badge badge-gold flex items-center gap-1">
              <FileText size={10} /> SEC 8-K
            </span>
          )}
          {/* Surprise-ticker tag: SEC 8-K with no tracked entity match — a
              filing from outside our 120-company universe that hit the
              tech-keyword whitelist. Flags it as "watch this one". */}
          {item.source === 'sec_edgar' && (!item.entity_names || item.entity_names.length === 0) && (
            <span className="badge badge-blue">NEW TICKER</span>
          )}
          {/* Phase 3.5: CourtListener docket / lawsuit filing. */}
          {item.source === 'courtlistener' && (
            <span className="badge badge-danger flex items-center gap-1">
              <Scale size={10} /> LAWSUIT
            </span>
          )}
          {/* Phase 3.6: arXiv research paper (forward-looking R&D signal). */}
          {item.source === 'arxiv' && (
            <span className="badge badge-blue flex items-center gap-1">
              <BookOpen size={10} /> arXiv
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted font-bold">
          <Clock size={12} />
          {timeAgo(item.published_at || item.ingested_at)}
        </div>
      </div>
      
      <h3 className={`news-card-title ${isHero ? 'news-card-title-hero' : ''}`}>
        <a href={safeUrl(item.url)} target="_blank" rel="noopener noreferrer">{item.title}</a>
      </h3>
      
      <p className="text-muted text-sm mb-4 news-card-summary">{item.summary}</p>
      
      {item.entity_names && item.entity_names.length > 0 && (
        <div className="flex gap-2 flex-wrap mb-4">
          {item.entity_names.map((e, i) => (
            <span key={i} className="badge badge-gray">{e}</span>
          ))}
        </div>
      )}
      
      <div className="flex items-center gap-4 text-xs font-bold mt-auto pt-4 news-card-footer">
        <div className="flex items-center gap-1">
          <TrendingUp size={14} className="text-muted" />
          <span className="news-card-buzz">{Math.round(displayBuzz)} BUZZ</span>
        </div>
        
        <div className="flex items-center gap-2 flex-1">
          <span className="text-muted">SENTIMENT</span>
          <ProgressBar value={sentimentValue} tone={sentimentColor} className="news-card-sentiment" />
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
