import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import ForecastBadge from './ForecastBadge';
import { Target } from 'lucide-react';

export default function InvestorHub() {
  const [activeTab, setActiveTab] = useState('Best Bets');
  const [data, setData] = useState({ bestBets: [], risks: [], ipos: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHub() {
      const cached = cache.get('investor_hub');
      if (cached) {
        setData(cached);
        setLoading(false);
        return;
      }

      // Best bets (strong bullish or bullish)
      const { data: best } = await supabase.from('companies')
        .select('id, name, ticker, forecast_direction, forecast_confidence, investor_brief')
        .in('forecast_direction', ['strong_bullish', 'bullish'])
        .order('forecast_confidence', { ascending: false }).limit(5);
        
      // Risks (bearish or high controversy)
      const { data: risks } = await supabase.from('companies')
        .select('id, name, ticker, forecast_direction, forecast_confidence, controversy_score, investor_brief')
        .or('forecast_direction.eq.bearish,forecast_direction.eq.high_risk,controversy_score.gt.60')
        .order('controversy_score', { ascending: false }).limit(5);

      const result = { bestBets: best || [], risks: risks || [], ipos: [] };
      setData(result);
      cache.set('investor_hub', result, 30);
      setLoading(false);
    }
    fetchHub();
  }, []);

  const items = activeTab === 'Best Bets' ? data.bestBets : activeTab === 'Risk Radar' ? data.risks : data.ipos;

  return (
    <section id="investors">
      <div className="section-header">
        <h2 className="section-title"><Target className="text-accent-red" /> Investor Hub</h2>
        <p className="text-muted">AI-synthesized forecasts and risk modeling</p>
      </div>

      <div className="card glass-panel p-0 overflow-hidden">
        <div className="tabs-header p-4 pb-0 mb-0">
          {['Best Bets', 'Risk Radar', 'IPO Watch'].map(tab => (
            <button key={tab} className={`tab-button ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab}
            </button>
          ))}
        </div>
        
        <div className="p-4 flex-col gap-4">
          {loading ? (
            <div className="skeleton skeleton-card" style={{ height: '150px' }}></div>
          ) : items.length === 0 ? (
            <div className="empty-state py-8">
              <p>No active signals for this category.</p>
            </div>
          ) : (
            items.map(item => (
              <div key={item.id} className="card p-4" style={{ background: 'var(--bg-color)' }}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="m-0 text-lg">{item.name}</h3>
                    <span className="text-xs text-muted font-bold">{item.ticker || 'PRIVATE'}</span>
                  </div>
                  <ForecastBadge direction={item.forecast_direction} confidence={item.forecast_confidence} />
                </div>
                {item.controversy_score > 60 && (
                  <div className="badge badge-danger mb-2">HIGH CONTROVERSY: {item.controversy_score}</div>
                )}
                <p className="text-sm text-muted m-0">{item.investor_brief}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
