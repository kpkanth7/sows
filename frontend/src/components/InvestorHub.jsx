import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import ForecastBadge from './ForecastBadge';
import { Target, Users, AlertOctagon, TrendingUp, ShieldCheck } from 'lucide-react';

export default function InvestorHub() {
  const [activeTab, setActiveTab] = useState('forecasts'); // 'forecasts', 'influencers', 'disputes'
  const [forecastSubTab, setForecastSubTab] = useState('Best Bets'); // 'Best Bets', 'Risk Radar', 'IPO Watch'
  const [data, setData] = useState({ bestBets: [], risks: [], ipos: [], influencers: [], disputes: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHubData() {
      const cached = cache.get('investor_hub_all');
      if (cached) {
        setData(cached);
        setLoading(false);
        return;
      }

      setLoading(true);

      // 1. Fetch Forecasts: Best bets (strong bullish or bullish)
      const { data: best } = await supabase.from('companies')
        .select('id, name, ticker, forecast_direction, forecast_confidence, investor_brief')
        .in('forecast_direction', ['strong_bullish', 'bullish'])
        .order('forecast_confidence', { ascending: false }).limit(6);
        
      // 2. Fetch Forecasts: Risks (bearish, high controversy)
      const { data: risks } = await supabase.from('companies')
        .select('id, name, ticker, forecast_direction, forecast_confidence, controversy_score, investor_brief')
        .or('forecast_direction.eq.bearish,forecast_direction.eq.high_risk,controversy_score.gt.50')
        .order('controversy_score', { ascending: false }).limit(6);

      // 3. Fetch Forecasts: IPO Watch (private companies with high valuation or recent funding event)
      const { data: ipos } = await supabase.from('companies')
        .select('id, name, ticker, last_valuation, valuation_source, sector, investor_brief')
        .eq('is_private', true)
        .order('last_valuation', { ascending: false, nullsFirst: false }).limit(6);

      // 4. Fetch Influencer Trust Index
      const { data: influencers } = await supabase.from('influencers')
        .select('*')
        .order('trust_score', { ascending: false });

      // 5. Fetch Disputes
      const { data: disputes } = await supabase.from('news_items')
        .select('id, title, url, source, dispute_claim_a, dispute_confidence_a, dispute_claim_b, dispute_confidence_b, dispute_brief')
        .eq('is_disputed', true)
        .order('ingested_at', { ascending: false }).limit(10);

      const result = {
        bestBets: best || [],
        risks: risks || [],
        ipos: ipos || [],
        influencers: influencers || [],
        disputes: disputes || []
      };

      setData(result);
      cache.set('investor_hub_all', result, 15);
      setLoading(false);
    }
    fetchHubData();
  }, [activeTab]);

  return (
    <section id="investors" style={{ width: '100%', padding: '4rem 0' }}>
      <div className="section-header">
        <h2 className="section-title"><Target className="text-accent-red" /> Investor & Intelligence Hub</h2>
        <p className="text-muted">AI-synthesized forecasts, dispute resolution, and influencer tracking</p>
      </div>

      <div className="card glass-panel p-0 overflow-hidden" style={{ width: '100%' }}>
        {/* Main Tab Headers */}
        <div className="tabs-header p-4 pb-0 mb-0 flex gap-6" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <button 
            className={`tab-button ${activeTab === 'forecasts' ? 'active' : ''}`} 
            onClick={() => setActiveTab('forecasts')}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <TrendingUp size={16} /> Forecasts & Radar
          </button>
          <button 
            className={`tab-button ${activeTab === 'influencers' ? 'active' : ''}`} 
            onClick={() => setActiveTab('influencers')}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Users size={16} /> Influencer Trust Index
          </button>
          <button 
            className={`tab-button ${activeTab === 'disputes' ? 'active' : ''}`} 
            onClick={() => setActiveTab('disputes')}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <AlertOctagon size={16} /> Consensus & Disputes
          </button>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="skeleton skeleton-card" style={{ height: '300px' }}></div>
          ) : (
            <>
              {/* TAB 1: FORECASTS & RADAR */}
              {activeTab === 'forecasts' && (
                <div>
                  {/* Sub-tabs */}
                  <div className="category-pills mb-4">
                    {['Best Bets', 'Risk Radar', 'IPO Watch'].map(tab => (
                      <button 
                        key={tab} 
                        className={`pill ${forecastSubTab === tab ? 'active' : ''}`} 
                        onClick={() => setForecastSubTab(tab)}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>

                  <div className="flex-col gap-4">
                    {forecastSubTab === 'Best Bets' && (
                      data.bestBets.length === 0 ? (
                        <div className="empty-state"><p>No active bullish forecasts.</p></div>
                      ) : (
                        <div className="grid-cols-2">
                          {data.bestBets.map(item => (
                            <div key={item.id} className="card p-4" style={{ background: 'var(--bg-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                              <div>
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{item.name}</h3>
                                    <span className="text-xs text-muted font-bold">{item.ticker || 'PRIVATE'}</span>
                                  </div>
                                  <ForecastBadge direction={item.forecast_direction} confidence={item.forecast_confidence} />
                                </div>
                                <p className="text-sm text-muted" style={{ lineBreak: 'anywhere' }}>{item.investor_brief}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    )}

                    {forecastSubTab === 'Risk Radar' && (
                      data.risks.length === 0 ? (
                        <div className="empty-state"><p>No active risk signals detected.</p></div>
                      ) : (
                        <div className="grid-cols-2">
                          {data.risks.map(item => (
                            <div key={item.id} className="card p-4" style={{ background: 'var(--bg-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                              <div>
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{item.name}</h3>
                                    <span className="text-xs text-muted font-bold">{item.ticker || 'PRIVATE'}</span>
                                  </div>
                                  <ForecastBadge direction={item.forecast_direction} confidence={item.forecast_confidence} />
                                </div>
                                {item.controversy_score > 50 && (
                                  <div className="badge badge-danger mb-2" style={{ fontSize: '0.7rem' }}>CONTROVERSY SCORE: {Math.round(item.controversy_score)}/100</div>
                                )}
                                <p className="text-sm text-muted">{item.investor_brief}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    )}

                    {forecastSubTab === 'IPO Watch' && (
                      data.ipos.length === 0 ? (
                        <div className="empty-state"><p>No private tech valuations recorded.</p></div>
                      ) : (
                        <div className="grid-cols-2">
                          {data.ipos.map(item => (
                            <div key={item.id} className="card p-4" style={{ background: 'var(--bg-color)' }}>
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{item.name}</h3>
                                  <span className="badge badge-blue text-xs mt-1">{item.sector}</span>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                                    ${(item.last_valuation / 1e9).toFixed(1)}B
                                  </div>
                                  <div className="text-muted" style={{ fontSize: '0.65rem', fontWeight: 'bold' }}>{item.valuation_source}</div>
                                </div>
                              </div>
                              <p className="text-sm text-muted mt-2">{item.investor_brief || "Tracking private market signaling and funding events."}</p>
                            </div>
                          ))}
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: INFLUENCER TRUST INDEX */}
              {activeTab === 'influencers' && (
                <div>
                  <p className="text-muted text-sm mb-4">
                    Tracks commentator track records across platforms. Accuracy metrics automatically decay trust weightings from 0.60 to 0.05 when claims are refuted.
                  </p>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Influencer</th>
                          <th>Platform</th>
                          <th>Trust Score</th>
                          <th>Accuracy Metric</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.influencers.map(inf => {
                          const accuracy = inf.total_claims > 0 ? (inf.correct_claims / inf.total_claims * 100).toFixed(0) + '%' : 'N/A';
                          return (
                            <tr key={inf.id}>
                              <td className="font-bold">{inf.name}</td>
                              <td>
                                <span className="badge badge-gray" style={{ textTransform: 'uppercase' }}>{inf.platform}</span>
                              </td>
                              <td className="font-bold" style={{ color: inf.trust_score > 0.4 ? 'var(--accent-green)' : inf.trust_score > 0.2 ? 'var(--accent-amber)' : 'var(--accent-red)' }}>
                                {parseFloat(inf.trust_score).toFixed(3)}
                              </td>
                              <td className="font-bold">{accuracy} ({inf.correct_claims}/{inf.total_claims})</td>
                              <td>
                                {inf.trust_score > 0.4 ? (
                                  <span className="badge badge-blue flex items-center gap-1 w-fit"><ShieldCheck size={12}/> HIGH TRUST</span>
                                ) : inf.trust_score > 0.15 ? (
                                  <span className="badge badge-gold w-fit">STANDARD</span>
                                ) : (
                                  <span className="badge badge-danger w-fit">DEGRADED</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 3: CONSENSUS & DISPUTES */}
              {activeTab === 'disputes' && (
                <div>
                  <p className="text-muted text-sm mb-6">
                    Real-time claims conflicts automatically flagged by the consensus engine and reconciled via unbiased, cited briefs.
                  </p>
                  {data.disputes.length === 0 ? (
                    <div className="empty-state py-8">
                      <p>No active disputes flagged in the last 72 hours.</p>
                    </div>
                  ) : (
                    <div className="flex-col gap-6">
                      {data.disputes.map(disp => (
                        <div key={disp.id} className="card p-5" style={{ background: 'var(--bg-color)', borderLeft: '4px solid var(--accent-amber)' }}>
                          <h3 style={{ margin: '0 0 1rem', fontSize: '1.1rem' }}>
                            <a href={disp.url} target="_blank" className="hover:underline flex items-center gap-2">
                              {disp.title}
                            </a>
                          </h3>
                          <div className="grid-cols-2 mb-4" style={{ gap: '1rem' }}>
                            <div className="p-3 rounded" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)' }}>
                              <span className="badge badge-gray mb-1" style={{ fontSize: '0.65rem' }}>Source Claim A</span>
                              <p className="text-sm font-bold m-0" style={{ color: 'var(--text-primary)' }}>"{disp.dispute_claim_a}"</p>
                              <div className="text-muted mt-2" style={{ fontSize: '0.7rem' }}>Confidence Weight: {disp.dispute_confidence_a}%</div>
                            </div>
                            <div className="p-3 rounded" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)' }}>
                              <span className="badge badge-gray mb-1" style={{ fontSize: '0.65rem' }}>Source Claim B</span>
                              <p className="text-sm font-bold m-0" style={{ color: 'var(--text-primary)' }}>"{disp.dispute_claim_b}"</p>
                              <div className="text-muted mt-2" style={{ fontSize: '0.7rem' }}>Confidence Weight: {disp.dispute_confidence_b}%</div>
                            </div>
                          </div>
                          <div className="dispute-panel mt-3">
                            <span className="text-xs text-accent-amber font-bold flex items-center gap-1"><ShieldCheck size={14}/> AI CONSENSUS RESOLUTION BRIEF:</span>
                            <p className="dispute-brief m-0" style={{ fontSize: '0.9rem', lineHeight: '1.4' }}>{disp.dispute_brief}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
