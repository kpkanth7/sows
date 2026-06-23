import { useEffect, useState } from 'react';
import { Target, Users, TrendingUp, DollarSign, Rocket, FileText, Newspaper } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import InsiderTradesPanel from './InsiderTradesPanel';
import DarkHorsePanel from './DarkHorsePanel';
import MaterialEventsPanel from './MaterialEventsPanel';
import DigestPanel from './DigestPanel';
import ForecastsRadarPanel from './investorhub/ForecastsRadarPanel';
import InfluencerTrustPanel from './investorhub/InfluencerTrustPanel';

const DEFAULT_DATA = {
  momentumLeaders: [],
  riskBuildUp: [],
  catalystsAhead: [],
  privateWatchlist: [],
  influencers: [],
};

const FORECAST_WEIGHT = {
  strong_bullish: 1.15,
  bullish: 0.9,
  neutral: 0.4,
  bearish: -0.7,
  high_risk: -1.0,
};

function daysFromToday(dateString) {
  if (!dateString) return null;
  const today = new Date(new Date().toISOString().slice(0, 10));
  const target = new Date(dateString);
  return Math.round((target - today) / 86400000);
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function formatHeadline(newsBucket) {
  return newsBucket?.latestSummary || newsBucket?.latestTitle || null;
}

function buildNewsMap(newsRows) {
  const buckets = new Map();
  for (const row of newsRows || []) {
    const names = Array.isArray(row.entity_names) ? row.entity_names : [];
    for (const name of names) {
      if (!buckets.has(name)) {
        buckets.set(name, {
          count: 0,
          buzzValues: [],
          sentimentValues: [],
          categories: new Set(),
          latestTitle: null,
          latestSummary: null,
        });
      }
      const bucket = buckets.get(name);
      bucket.count += 1;
      if (row.buzz_v2 != null) bucket.buzzValues.push(Number(row.buzz_v2));
      if (row.sentiment != null) bucket.sentimentValues.push(Number(row.sentiment));
      if (row.category) bucket.categories.add(row.category);
      if (!bucket.latestTitle) {
        bucket.latestTitle = row.title;
        bucket.latestSummary = row.summary;
      }
    }
  }

  return new Map(
    Array.from(buckets.entries()).map(([name, bucket]) => [
      name,
      {
        ...bucket,
        buzzAvg: average(bucket.buzzValues),
        sentimentAvg: average(bucket.sentimentValues),
        categories: Array.from(bucket.categories),
      },
    ]),
  );
}

function buildDarkHorseMap(rows) {
  const map = new Map();
  for (const row of rows || []) {
    map.set(row.company_id, row);
  }
  return map;
}

function buildEarningsMap(rows) {
  const map = new Map();
  for (const row of rows || []) {
    if (!map.has(row.company_id)) {
      map.set(row.company_id, []);
    }
    map.get(row.company_id).push(row);
  }
  for (const value of map.values()) {
    value.sort((a, b) => new Date(a.earnings_date) - new Date(b.earnings_date));
  }
  return map;
}

function buildUpgradeMap(rows) {
  const map = new Map();
  for (const row of rows || []) {
    const current = map.get(row.company_id) || { up: 0, down: 0 };
    if (row.action === 'up' || row.action === 'init') current.up += 1;
    if (row.action === 'down') current.down += 1;
    map.set(row.company_id, current);
  }
  return map;
}

function buildInsiderMap(rows) {
  const map = new Map();
  for (const row of rows || []) {
    const current = map.get(row.company_id) || { buys: 0, sells: 0 };
    const delta = Number(row.change || 0);
    if (delta > 0) current.buys += delta;
    if (delta < 0) current.sells += Math.abs(delta);
    map.set(row.company_id, current);
  }
  return map;
}

function buildForecastRows(companies, newsMap, darkHorseMap, earningsMap, upgradeMap, insiderMap) {
  const summaries = companies.map((company) => {
    const news = newsMap.get(company.name) || {
      count: 0,
      buzzAvg: 0,
      sentimentAvg: 0,
      categories: [],
      latestTitle: null,
      latestSummary: null,
    };
    const darkHorse = darkHorseMap.get(company.id);
    const earnings = earningsMap.get(company.id) || [];
    const nextEarnings = earnings.find((row) => daysFromToday(row.earnings_date) >= 0) || null;
    const upgrades = upgradeMap.get(company.id) || { up: 0, down: 0 };
    const insider = insiderMap.get(company.id) || { buys: 0, sells: 0 };
    const daysToEarnings = nextEarnings ? daysFromToday(nextEarnings.earnings_date) : null;
    const forecastConfidence = Number(company.forecast_confidence || 0);
    const forecastTilt = FORECAST_WEIGHT[company.forecast_direction] || 0;
    const sentimentAvg = Number(news.sentimentAvg || 0);
    const buzzAvg = Number(news.buzzAvg || 0);
    const articleCount = Number(news.count || 0);
    const darkHorseScore = Number(darkHorse?.score || 0);
    const upgradeDelta = upgrades.up - upgrades.down;
    const insiderBias = insider.buys - insider.sells;
    const upcomingCatalyst = daysToEarnings != null && daysToEarnings >= 0 && daysToEarnings <= 21;
    const recentEventCatalyst = company.recent_event && company.recent_event_date && daysFromToday(company.recent_event_date) != null && daysFromToday(company.recent_event_date) >= 0;

    const reasons = [];
    if (articleCount >= 4) reasons.push(`${articleCount} news items / 7d`);
    if (buzzAvg >= 35) reasons.push(`buzz ${Math.round(buzzAvg)}`);
    if (sentimentAvg >= 0.18) reasons.push('positive tone building');
    if (sentimentAvg <= -0.18) reasons.push('negative tone building');
    if (darkHorseScore >= 55) reasons.push(`dark-horse ${Math.round(darkHorseScore)}`);
    if (upgradeDelta > 0) reasons.push(`${upgrades.up} analyst upgrades`);
    if (upgradeDelta < 0) reasons.push(`${upgrades.down} analyst downgrades`);
    if (insiderBias > 0) reasons.push('net insider buying');
    if (insiderBias < 0) reasons.push('net insider selling');
    if (upcomingCatalyst) reasons.push(`earnings in ${daysToEarnings === 0 ? 'today' : `${daysToEarnings}d`}`);
    if (recentEventCatalyst) reasons.push(`${company.recent_event.replace('_', ' ')} ahead`);

    const momentumScore = clamp(
      forecastConfidence * Math.max(forecastTilt, 0) * 0.5 +
      articleCount * 7 +
      Math.max(sentimentAvg, 0) * 30 +
      buzzAvg * 0.45 +
      darkHorseScore * 0.35 +
      Math.max(upgradeDelta, 0) * 9 +
      (upcomingCatalyst ? 14 - Math.min(daysToEarnings, 14) : 0),
      0,
      100,
    );

    const riskScore = clamp(
      (company.forecast_direction === 'bearish' ? 24 : 0) +
      (company.forecast_direction === 'high_risk' ? 38 : 0) +
      Math.max(-sentimentAvg, 0) * 34 +
      Math.max(-upgradeDelta, 0) * 10 +
      Math.min((insider.sells / 50000), 24) +
      (Number(company.controversy_score || 0) * 0.25),
      0,
      100,
    );

    const catalystScore = clamp(
      (upcomingCatalyst ? 60 - Math.min(daysToEarnings * 2, 40) : 0) +
      (recentEventCatalyst ? 22 : 0) +
      articleCount * 3 +
      Math.max(buzzAvg - 20, 0) * 0.25,
      0,
      100,
    );

    const privateScore = clamp(
      company.is_private
        ? (Number(company.last_valuation || 0) / 1e10) +
          articleCount * 5 +
          Math.max(sentimentAvg, 0) * 25 +
          Math.max(forecastConfidence * Math.max(forecastTilt, 0) * 0.35, 0)
        : 0,
      0,
      100,
    );

    return {
      id: company.id,
      name: company.name,
      ticker: company.ticker,
      sector: company.sector,
      isPrivate: company.is_private,
      forecast_direction: company.forecast_direction,
      forecast_confidence: company.forecast_confidence,
      investorBrief: company.investor_brief,
      articleCount,
      buzzAvg,
      sentimentAvg,
      darkHorseScore,
      reasons: reasons.slice(0, 4),
      latestHeadline: formatHeadline(news),
      summary: company.investor_brief || formatHeadline(news) || null,
      nextEventLabel: nextEarnings ? `Earnings · ${nextEarnings.earnings_date}` : (company.recent_event ? `${company.recent_event.replace('_', ' ')} · ${company.recent_event_date || 'pending'}` : null),
      latestValuation: company.last_valuation,
      marketCap: company.market_cap,
      momentumScore,
      riskScore,
      catalystScore,
      privateScore,
    };
  });

  return {
    momentumLeaders: summaries
      .filter((row) => row.momentumScore > 0)
      .sort((a, b) => b.momentumScore - a.momentumScore)
      .slice(0, 6),
    riskBuildUp: summaries
      .filter((row) => row.riskScore > 0)
      .sort((a, b) => b.riskScore - a.riskScore)
      .slice(0, 6),
    catalystsAhead: summaries
      .filter((row) => row.catalystScore > 0)
      .sort((a, b) => b.catalystScore - a.catalystScore)
      .slice(0, 6),
    privateWatchlist: summaries
      .filter((row) => row.isPrivate)
      .sort((a, b) => b.privateScore - a.privateScore)
      .slice(0, 6),
  };
}

function buildInfluencerRows(influencers, recentSignals) {
  const byInfluencer = new Map();
  for (const signal of recentSignals || []) {
    if (!byInfluencer.has(signal.influencer_id)) {
      byInfluencer.set(signal.influencer_id, []);
    }
    byInfluencer.get(signal.influencer_id).push(signal);
  }

  return (influencers || []).map((inf) => {
    const signals = (byInfluencer.get(inf.id) || [])
      .sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
    const recentEntities = Array.from(
      new Set(signals.map((signal) => signal.entity_name).filter(Boolean)),
    ).slice(0, 5);
    const recentTitles = signals.slice(0, 3).map((signal) => ({
      title: signal.content_title,
      url: signal.content_url,
      publishedAt: signal.published_at,
    }));
    const accuracy = inf.total_claims > 0
      ? Math.round((inf.correct_claims / inf.total_claims) * 100)
      : null;

    return {
      id: inf.id,
      name: inf.name,
      platform: inf.platform,
      category: inf.category,
      trust_score: Number(inf.trust_score || 0),
      total_claims: inf.total_claims || 0,
      correct_claims: inf.correct_claims || 0,
      accuracy,
      last_checked: inf.last_checked,
      last_active: signals[0]?.published_at || null,
      recentSignalCount: signals.length,
      recent_entities: recentEntities,
      recentTitles,
    };
  }).sort((a, b) => {
    if (b.trust_score !== a.trust_score) return b.trust_score - a.trust_score;
    return b.recentSignalCount - a.recentSignalCount;
  });
}

export default function InvestorHub() {
  const [activeTab, setActiveTab] = useState('forecasts');
  const [data, setData] = useState(DEFAULT_DATA);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHubData() {
      const cached = cache.get('investor_hub_v2');
      if (cached) {
        setData(cached);
        setLoading(false);
        return;
      }

      setLoading(true);
      const newsSince = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
      const recent30Date = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
      const today = new Date().toISOString().slice(0, 10);

      const [
        companiesRes,
        newsRes,
        darkHorseRes,
        earningsRes,
        upgradeRes,
        insiderRes,
        influencersRes,
        influencerSignalsRes,
      ] = await Promise.all([
        supabase
          .from('companies')
          .select('id, name, ticker, is_private, sector, region, market_cap, last_valuation, valuation_source, controversy_score, forecast_direction, forecast_confidence, investor_brief, recent_event, recent_event_date')
          .order('name'),
        supabase
          .from('news_items')
          .select('title, summary, entity_names, buzz_v2, sentiment, category, published_at')
          .gte('published_at', newsSince)
          .order('published_at', { ascending: false })
          .limit(1000),
        supabase
          .from('dark_horse_movers')
          .select('company_id, rank, score, reasons, components')
          .limit(20),
        supabase
          .from('earnings_calendar')
          .select('company_id, earnings_date, sentiment_delta, eps_estimate, eps_actual, revenue_estimate, revenue_actual')
          .gte('earnings_date', today)
          .order('earnings_date', { ascending: true })
          .limit(200),
        supabase
          .from('upgrade_downgrade')
          .select('company_id, action, action_date')
          .gte('action_date', recent30Date)
          .limit(1000),
        supabase
          .from('insider_transactions')
          .select('company_id, change, transaction_date')
          .gte('transaction_date', recent30Date)
          .limit(1000),
        supabase
          .from('influencers')
          .select('*')
          .order('trust_score', { ascending: false }),
        supabase
          .from('influencer_signals')
          .select('influencer_id, entity_name, content_title, content_url, published_at')
          .gte('published_at', newsSince)
          .order('published_at', { ascending: false })
          .limit(200),
      ]);

      const companies = companiesRes.data || [];
      const forecastRows = buildForecastRows(
        companies,
        buildNewsMap(newsRes.data || []),
        buildDarkHorseMap(darkHorseRes.data || []),
        buildEarningsMap(earningsRes.data || []),
        buildUpgradeMap(upgradeRes.data || []),
        buildInsiderMap(insiderRes.data || []),
      );

      const result = {
        ...forecastRows,
        influencers: buildInfluencerRows(influencersRes.data || [], influencerSignalsRes.data || []),
      };

      setData(result);
      cache.set('investor_hub_v2', result, 15);
      setLoading(false);
    }

    fetchHubData();
  }, []);

  return (
    <section id="investors" className="investor-hub-section">
      <div className="section-header">
        <h2 className="section-title"><Target className="text-accent-red" /> Investor & Intelligence Hub</h2>
        <p className="text-muted">Ranked conviction, catalysts, insider signals, and creator track records.</p>
      </div>

      <div className="card glass-panel p-0 overflow-hidden investor-hub-shell">
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
            <Users size={16} /> Influencer Trust
          </button>
          <button
            className={`tab-button investor-hub-tab ${activeTab === 'insider' ? 'active' : ''}`}
            onClick={() => setActiveTab('insider')}
            role="tab"
            aria-selected={activeTab === 'insider'}
          >
            <DollarSign size={16} /> Insider Trades
          </button>
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
              {activeTab === 'forecasts' && (
                <ForecastsRadarPanel
                  momentumLeaders={data.momentumLeaders}
                  riskBuildUp={data.riskBuildUp}
                  catalystsAhead={data.catalystsAhead}
                  privateWatchlist={data.privateWatchlist}
                />
              )}

              {activeTab === 'influencers' && (
                <InfluencerTrustPanel rows={data.influencers} />
              )}

              {activeTab === 'insider' && (
                <div>
                  <p className="text-muted text-sm mb-6">
                    Notable insider transactions (|change| ≥ 10K shares) across tracked public companies in the last 30 days. Source: Finnhub filings refreshed on the scheduled pipeline.
                  </p>
                  <InsiderTradesPanel />
                </div>
              )}

              {activeTab === 'darkhorse' && <DarkHorsePanel />}

              {activeTab === 'material' && <MaterialEventsPanel />}

              {activeTab === 'digest' && <DigestPanel />}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
