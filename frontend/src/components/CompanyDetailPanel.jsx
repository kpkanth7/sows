import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { X, Github, ExternalLink, Activity } from 'lucide-react';
import HypeRealityMeter from './HypeRealityMeter';
import HypeRealityChart from './HypeRealityChart';
import BenchmarkLeaderboard from './BenchmarkLeaderboard';
import InsiderTradesPanel from './InsiderTradesPanel';
import NewsCard from './NewsCard';
import { safeUrl } from '../lib/urls';

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000);
  if (diff < 60) return `${diff}m ago`;
  const hours = Math.floor(diff / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function CompanyDetailPanel({ company, onClose }) {
  const [activeTab, setActiveTab] = useState('Overview');
  const [stockHistory, setStockHistory] = useState([]);
  const [companyNews, setCompanyNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsError, setNewsError] = useState(null);
  
  useEffect(() => {
    if (activeTab === 'Charts' && !company.is_private) {
      supabase.from('stock_snapshots').select('price, captured_at').eq('company_id', company.id).order('captured_at', { ascending: true }).limit(30)
        .then(({data}) => {
          if (data) setStockHistory(data.map(d => ({ ...d, date: new Date(d.captured_at).toLocaleDateString() })));
        });
    }
  }, [activeTab, company]);

  useEffect(() => {
    if (!company?.name) return;

    let cancelled = false;
    const fetchCompanyNews = async () => {
      setNewsLoading(true);
      setNewsError(null);

      const { data, error } = await supabase
        .from('news_items')
        .select('id, title, summary, url, source, source_type, category, source_credibility_tier, buzz_score, buzz_v2, sentiment, entity_names, published_at, ingested_at, is_disputed, dispute_claim_a, dispute_confidence_a, dispute_claim_b, dispute_confidence_b, dispute_brief')
        .contains('entity_names', JSON.stringify([company.name]))
        .order('ingested_at', { ascending: false })
        .limit(8);

      if (cancelled) return;
      if (error) {
        setNewsError(error.message);
        setCompanyNews([]);
      } else {
        setCompanyNews((data || []).map(item => ({
          ...item,
          buzz_score: item.buzz_v2 ?? item.buzz_score ?? 0,
        })));
      }
      setNewsLoading(false);
    };

    fetchCompanyNews();
    return () => {
      cancelled = true;
    };
  }, [company?.id, company?.name]);

  if (!company) return null;

  const latestSignal = companyNews[0];
  const signalCount = companyNews.length;

  return (
    <div className="company-detail-panel">
      <div className="company-detail-header">
        <div className="company-detail-title">
          {company.logo_url && <img src={company.logo_url} width={32} height={32} className="company-detail-logo" />}
          <h2 className="company-detail-name">{company.name}</h2>
          <span className="badge badge-gray">{company.ticker || 'PRIVATE'}</span>
        </div>
        <button className="theme-toggle" onClick={onClose} aria-label={`Close ${company.name} detail panel`}><X size={24} /></button>
      </div>
      
      <div className="company-detail-tabs" role="tablist" aria-label={`${company.name} detail sections`}>
        {['Overview', 'Charts', 'Benchmarks', 'Insider', 'News'].map(tab => (
          <button key={tab} className={`tab-button ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)} role="tab" aria-selected={activeTab === tab}>
            {tab}
          </button>
        ))}
      </div>
      
      <div className="company-detail-body">
        {activeTab === 'Overview' && (
          <div className="flex-col gap-4">
            <p className="text-muted">{company.description}</p>
            <div className="grid-cols-2">
              <div className="card glass-panel">
                <div className="text-xs text-muted font-bold">SECTOR</div>
                <div className="font-bold mt-1">{company.sector || 'Technology'}</div>
              </div>
              <div className="card glass-panel">
                <div className="text-xs text-muted font-bold">WEBSITE</div>
                <div className="font-bold mt-1"><a href={safeUrl(company.website)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1"><ExternalLink size={14}/> Visit</a></div>
              </div>
            </div>
            
            <div className="card glass-panel mt-4">
              <h3 className="flex items-center gap-2"><Activity size={18}/> Hype vs Reality</h3>
              <HypeRealityMeter hype={company.hype_score} reality={company.reality_score} />
              {/* Phase 3.3: real 30-day z-score trendline below the legacy
                  flat-bar meter. Two signals: news-volume (hype) vs
                  github-stars-this-week (reality). */}
              <div className="mt-4">
                <HypeRealityChart company={company} />
              </div>
            </div>
            
            {company.investor_brief && (
              <div className="card glass-panel investor-brief-card mt-4">
                <div className="investor-brief-header">
                  <div>
                    <div className="text-xs text-muted font-bold mb-2">AI INVESTOR BRIEF</div>
                    <div className="brief-meta-row">
                      <span className="badge badge-blue">{company.forecast_direction?.replace('_', ' ') || 'neutral'}</span>
                      <span className="badge badge-gray">{Math.round(company.forecast_confidence || 0)}% confidence</span>
                      <span className="badge badge-gray">{signalCount} recent signal{signalCount === 1 ? '' : 's'}</span>
                    </div>
                  </div>
                </div>
                <p className="text-sm m-0">{company.investor_brief}</p>
                {latestSignal && (
                  <div className="brief-latest-signal">
                    <span className="text-xs text-muted font-bold">LATEST TRACKED SIGNAL</span>
                    <strong>{latestSignal.title}</strong>
                    <span className="text-xs text-muted">{latestSignal.source} · {timeAgo(latestSignal.published_at || latestSignal.ingested_at)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'Charts' && (
          <div className="card glass-panel company-detail-chart-card">
            {company.is_private ? (
              <div className="empty-state">No public stock charts available for private companies.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stockHistory}>
                  <XAxis dataKey="date" stroke="var(--text-secondary)" fontSize={12} />
                  <YAxis domain={['auto', 'auto']} stroke="var(--text-secondary)" fontSize={12} />
                  <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="price" stroke="var(--accent-green)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
        
        {activeTab === 'Benchmarks' && (
          <BenchmarkLeaderboard companyId={company.id} />
        )}

        {/* Phase 3.4: per-company insider trades (last 30d, notable only). */}
        {activeTab === 'Insider' && (
          <InsiderTradesPanel companyId={company.id} />
        )}
        
        {activeTab === 'News' && (
          <div className="company-news-list">
            {newsLoading ? (
              <>
                <div className="skeleton skeleton-card" />
                <div className="skeleton skeleton-card" />
              </>
            ) : newsError ? (
              <div className="empty-state">
                <Activity className="empty-icon" />
                <p>Company news unavailable: {newsError}</p>
              </div>
            ) : companyNews.length === 0 ? (
              <div className="empty-state">
                <Activity className="empty-icon" />
                <p>No recent tracked news for {company.name} yet.</p>
              </div>
            ) : (
              companyNews.map(item => <NewsCard key={item.id} item={item} />)
            )}
          </div>
        )}
      </div>
    </div>
  );
}
