import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { X, Github, ExternalLink, Activity } from 'lucide-react';
import HypeRealityMeter from './HypeRealityMeter';
import HypeRealityChart from './HypeRealityChart';
import BenchmarkLeaderboard from './BenchmarkLeaderboard';

export default function CompanyDetailPanel({ company, onClose }) {
  const [activeTab, setActiveTab] = useState('Overview');
  const [stockHistory, setStockHistory] = useState([]);
  
  useEffect(() => {
    if (activeTab === 'Charts' && !company.is_private) {
      supabase.from('stock_snapshots').select('price, captured_at').eq('company_id', company.id).order('captured_at', { ascending: true }).limit(30)
        .then(({data}) => {
          if (data) setStockHistory(data.map(d => ({ ...d, date: new Date(d.captured_at).toLocaleDateString() })));
        });
    }
  }, [activeTab, company]);

  if (!company) return null;

  return (
    <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(600px, 100vw)', background: 'var(--surface-color)', backdropFilter: 'blur(20px)', zIndex: 2000, boxShadow: '-10px 0 30px rgba(0,0,0,0.5)', borderLeft: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', animation: 'fadeIn 0.3s ease' }}>
      <div className="p-4 flex justify-between items-center" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <div className="flex items-center gap-3">
          {company.logo_url && <img src={company.logo_url} width={32} height={32} style={{ borderRadius: 6 }} />}
          <h2 style={{ margin: 0 }}>{company.name}</h2>
          <span className="badge badge-gray">{company.ticker || 'PRIVATE'}</span>
        </div>
        <button className="theme-toggle" onClick={onClose}><X size={24} /></button>
      </div>
      
      <div className="p-4 flex gap-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
        {['Overview', 'Charts', 'Benchmarks', 'News'].map(tab => (
          <button key={tab} className={`tab-button ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>
      
      <div className="p-4" style={{ flex: 1, overflowY: 'auto' }}>
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
                <div className="font-bold mt-1"><a href={company.website} target="_blank" className="flex items-center gap-1"><ExternalLink size={14}/> Visit</a></div>
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
              <div className="card glass-panel mt-4" style={{ background: 'rgba(0,212,255,0.05)', borderLeft: '3px solid var(--accent-blue)' }}>
                <div className="text-xs text-muted font-bold mb-2">AI INVESTOR BRIEF</div>
                <p className="text-sm m-0 italic">{company.investor_brief}</p>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'Charts' && (
          <div className="card glass-panel" style={{ height: '400px' }}>
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
        
        {activeTab === 'News' && (
          <div className="empty-state">
            <Activity className="empty-icon" />
            <p>Recent news loading...</p>
          </div>
        )}
      </div>
    </div>
  );
}
