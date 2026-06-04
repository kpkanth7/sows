import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import ForecastBadge from './ForecastBadge';
import { Target, Users, AlertOctagon, TrendingUp, ShieldCheck, DollarSign, Rocket, FileText, Newspaper } from 'lucide-react';
import InsiderTradesPanel from './InsiderTradesPanel';
import DarkHorsePanel from './DarkHorsePanel';
import MaterialEventsPanel from './MaterialEventsPanel';
import DigestPanel from './DigestPanel';
import { safeUrl } from '../lib/urls';

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

      // 5. Fetch Disputes — last 72h only (Phase 3.12 bug fix: label said
      // "last 72 hours" but no time filter existed, so old disputes leaked.)
      const since72h = new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString();
      const { data: disputes } = await supabase.from('news_items')
        .select('id, title, url, source, dispute_claim_a, dispute_confidence_a, dispute_claim_b, dispute_confidence_b, dispute_brief')
        .eq('is_disputed', true)
        .gte('ingested_at', since72h)
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
    <section id="investors" className="investor-hub-section">
      <div className="section-header">
        <h2 className="section-title"><Target className="text-accent-red" /> Investor & Intelligence Hub</h2>
        <p className="text-muted">AI-synthesized forecasts, dispute resolution, and influencer tracking</p>
      </div>

      <div className="card glass-panel p-0 overflow-hidden investor-hub-shell">
        {/* Main Tab Headers */}
        <div className="tabs-header p-4 pb-0 mb-0 flex gap-6 investor-hub-tabs" role="tablist" aria-label="Investor hub sections">
          <button 
            className={`tab-button investor-hub-tab ${activeTab === 'forecasts' ? 'active' : ''}`} 
            onClick={() => setActiveTab('forecasts')}
            role="tab"
            aria-selected={activeTab === 'forecasts'}
          >
            <TrendingUp size={16} /> Forecasts & Radar
          </button>
          <button 
            className={`tab-button investor-hub-tab ${activeTab === 'influencers' ? 'active' : ''}`} 
            onClick={() => setActiveTab('influencers')}
            role="tab"
            aria-selected={activeTab === 'influencers'}
          >
            <Users size={16} /> Influencer Trust Index
          </button>
          <button
            className={`tab-button investor-hub-tab ${activeTab === 'disputes' ? 'active' : ''}`}
            onClick={() => setActiveTab('disputes')}
            role="tab"
            aria-selected={activeTab === 'disputes'}
          >
            <AlertOctagon size={16} /> Consensus & Disputes
          </button>
          {/* Phase 3.4: notable insider trades across all tracked cos last 30d. */}
          <button
            className={`tab-button investor-hub-tab ${activeTab === 'insider' ? 'active' : ''}`}
            onClick={() => setActiveTab('insider')}
            role="tab"
            aria-selected={activeTab === 'insider'}
          >
            <DollarSign size={16} /> Insider Trades
          </button>
          {/* Phase 3.12 new tabs: Dark-Horse (3.11) · Material Events (3.1) · Digest (3.7). */}
          <button
            className={`tab-button investor-hub-tab ${activeTab === 'darkhorse' ? 'active' : ''}`}
            onClick={() => setActiveTab('darkhorse')}
            role="tab"
            aria-selected={activeTab === 'darkhorse'}
          >
            <Rocket size={16} /> Dark-Horse
          </button>
          <button
            className={`tab-button investor-hub-tab ${activeTab === 'material' ? 'active' : ''}`}
            onClick={() => setActiveTab('material')}
            role="tab"
            aria-selected={activeTab === 'material'}
          >
            <FileText size={16} /> Material Events
          </button>
          <button
            className={`tab-button investor-hub-tab ${activeTab === 'digest' ? 'active' : ''}`}
            onClick={() => setActiveTab('digest')}
            role="tab"
            aria-selected={activeTab === 'digest'}
          >
            <Newspaper size={16} /> Daily Digest
          </button>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="skeleton skeleton-card investor-hub-skeleton"></div>
          ) : (
            <>
              {/* TAB 1: FORECASTS & RADAR */}
              {activeTab === 'forecasts' && (
                <div>
                  {/* Sub-tabs */}
                  <div className="category-pills mb-4" role="tablist" aria-label="Forecast views">
                    {['Best Bets', 'Risk Radar', 'IPO Watch'].map(tab => (
                      <button 
                        key={tab} 
                        className={`pill ${forecastSubTab === tab ? 'active' : ''}`} 
                        onClick={() => setForecastSubTab(tab)}
                        role="tab"
                        aria-selected={forecastSubTab === tab}
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
                            <div key={item.id} className="card p-4 investor-hub-forecast-card">
                              <div>
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <h3 className="investor-hub-card-title">{item.name}</h3>
                                    <span className="text-xs text-muted font-bold">{item.ticker || 'PRIVATE'}</span>
                                  </div>
                                  <ForecastBadge direction={item.forecast_direction} confidence={item.forecast_confidence} />
                                </div>
                                <p className="text-sm text-muted investor-hub-brief-anywhere">{item.investor_brief}</p>
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
                            <div key={item.id} className="card p-4 investor-hub-forecast-card">
                              <div>
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <h3 className="investor-hub-card-title">{item.name}</h3>
                                    <span className="text-xs text-muted font-bold">{item.ticker || 'PRIVATE'}</span>
                                  </div>
                                  <ForecastBadge direction={item.forecast_direction} confidence={item.forecast_confidence} />
                                </div>
                                {item.controversy_score > 50 && (
                                  <div className="badge badge-danger mb-2 investor-hub-controversy-badge">CONTROVERSY SCORE: {Math.round(item.controversy_score)}/100</div>
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
                            <div key={item.id} className="card p-4 investor-hub-ipo-card">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <h3 className="investor-hub-card-title">{item.name}</h3>
                                  <span className="badge badge-blue text-xs mt-1">{item.sector}</span>
                                </div>
                                <div className="investor-hub-ipo-metric">
                                  <div className="investor-hub-ipo-value">
                                    ${(item.last_valuation / 1e9).toFixed(1)}B
                                  </div>
                                  <div className="text-muted investor-hub-ipo-source">{item.valuation_source}</div>
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
                                <span className="badge badge-gray investor-hub-platform-badge">{inf.platform}</span>
                              </td>
                              <td className={`font-bold investor-hub-trust-value ${inf.trust_score > 0.4 ? 'is-high' : inf.trust_score > 0.2 ? 'is-mid' : 'is-low'}`}>
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
                        <div key={disp.id} className="card p-5 investor-hub-dispute-card">
                          <h3 className="investor-hub-card-title investor-hub-dispute-title">
                            <a href={safeUrl(disp.url)} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-2">
                              {disp.title}
                            </a>
                          </h3>
                          <div className="grid-cols-2 mb-4 investor-hub-dispute-grid">
                            <div className="p-3 rounded investor-hub-dispute-claim">
                              <span className="badge badge-gray mb-1 investor-hub-dispute-label">Source Claim A</span>
                              <p className="text-sm font-bold m-0 investor-hub-dispute-text">"{disp.dispute_claim_a}"</p>
                              <div className="text-muted mt-2 investor-hub-dispute-confidence">Confidence Weight: {disp.dispute_confidence_a}%</div>
                            </div>
                            <div className="p-3 rounded investor-hub-dispute-claim">
                              <span className="badge badge-gray mb-1 investor-hub-dispute-label">Source Claim B</span>
                              <p className="text-sm font-bold m-0 investor-hub-dispute-text">"{disp.dispute_claim_b}"</p>
                              <div className="text-muted mt-2 investor-hub-dispute-confidence">Confidence Weight: {disp.dispute_confidence_b}%</div>
                            </div>
                          </div>
                          <div className="dispute-panel mt-3">
                            <span className="text-xs text-accent-amber font-bold flex items-center gap-1"><ShieldCheck size={14}/> AI CONSENSUS RESOLUTION BRIEF:</span>
                            <p className="dispute-brief m-0 investor-hub-dispute-brief">{disp.dispute_brief}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: INSIDER TRADES (Phase 3.4) — notable last 30d, all cos. */}
              {activeTab === 'insider' && (
                <div>
                  <p className="text-muted text-sm mb-6">
                    Notable insider transactions (|change| ≥ 10K shares) across all tracked companies in the last 30 days. Source: SEC Form 4 filings via Finnhub.
                  </p>
                  <InsiderTradesPanel />
                </div>
              )}

              {/* TAB 5: DARK-HORSE MOVERS (Phase 3.11). */}
              {activeTab === 'darkhorse' && <DarkHorsePanel />}

              {/* TAB 6: MATERIAL EVENTS (Phase 3.1 dataset). */}
              {activeTab === 'material' && <MaterialEventsPanel />}

              {/* TAB 7: DAILY DIGEST (Phase 3.7 dataset). */}
              {activeTab === 'digest' && <DigestPanel />}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
