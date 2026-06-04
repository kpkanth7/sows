import { useState, useEffect, useRef } from 'react';
import { supabase } from '../lib/supabase';
import CategoryPills from './CategoryPills';
import NewsCard from './NewsCard';
import EarningsStrip from './EarningsStrip';
import { Activity } from 'lucide-react';

const CATEGORIES = ['All', 'Influencers', 'Social', 'AI', 'Releases', 'M&A', 'IPO', 'Controversy', 'Conferences', 'Open Source', 'Earnings', 'Filings', 'Research'];

const mapCategory = (uiCat) => {
  const map = {
    'AI': 'ai',
    'Releases': 'release',
    'M&A': 'ma',
    'IPO': 'ipo',
    'Controversy': 'controversy',
    'Conferences': 'conference',
    'Open Source': 'opensource',
    'Earnings': 'earnings',
  };
  return map[uiCat] || null;
};

const SOURCE_FILTER = {
  'Filings': 'sec_edgar',
  'Influencers': 'influencer',
  'Social': 'community',
  'Research': 'arxiv',
};

const getItemBuzz = (item) => item?.buzz_v2 ?? item?.buzz_score ?? 0;
const SOCIAL_SUBREDDIT_ALLOWLIST = new Set([
  'reddit_r_MachineLearning',
  'reddit_r_singularity',
  'reddit_r_LocalLLaMA',
  'reddit_r_OpenAI',
  'reddit_r_SaaS',
  'reddit_r_devops',
  'reddit_r_softwaredevelopment',
  'reddit_r_ClaudeAI',
  'reddit_r_Anthropic',
]);

const mapCommunitySignalsToFeed = (rows) => {
  const grouped = new Map();
  for (const row of rows || []) {
    if (!SOCIAL_SUBREDDIT_ALLOWLIST.has(row.source)) continue;
    const key = row.post_url || `${row.source}::${row.post_title}`;
    const existing = grouped.get(key);
    const entity = row.entity_name;
    if (!existing) {
      grouped.set(key, {
        id: key,
        title: row.post_title,
        summary: `Community discussion from ${row.source.replace(/^reddit_r_/, 'r/')} about ${entity}. Treat as sentiment signal, not confirmed reporting.`,
        url: row.post_url,
        source: row.source.replace(/^reddit_r_/, 'r/'),
        source_type: 'community',
        source_credibility_tier: 4,
        entity_names: entity ? [entity] : [],
        sentiment: row.sentiment ?? 0,
        buzz_score: Math.min(100, 12 + Math.abs(row.sentiment ?? 0) * 22),
        category: 'social',
        published_at: row.captured_at,
        ingested_at: row.captured_at,
      });
      continue;
    }

    if (entity && !existing.entity_names.includes(entity)) {
      existing.entity_names.push(entity);
      existing.buzz_score = Math.min(100, existing.buzz_score + 8);
      existing.summary = `Community discussion from ${existing.source} about ${existing.entity_names.join(', ')}. Treat as sentiment signal, not confirmed reporting.`;
    }
    if (typeof row.sentiment === 'number') {
      existing.sentiment = (existing.sentiment + row.sentiment) / 2;
    }
  }
  return Array.from(grouped.values()).sort((a, b) => new Date(b.published_at || b.ingested_at) - new Date(a.published_at || a.ingested_at));
};

export default function NewsSection() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const observerTarget = useRef(null);

  const fetchNews = async (pageNum, cat, append = false) => {
    setLoading(true);
    const threeDaysAgo = new Date();
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

    if (cat === 'Social') {
      const { data, error } = await supabase
        .from('community_signals')
        .select('source, entity_name, post_title, post_url, sentiment, captured_at')
        .gte('captured_at', threeDaysAgo.toISOString())
        .order('captured_at', { ascending: false })
        .range(pageNum * 60, (pageNum + 1) * 60 - 1);

      if (!error && data) {
        const mapped = mapCommunitySignalsToFeed(data);
        if (mapped.length < 20) {
          setHasMore(false);
        }
        if (append) {
          setNews(prev => [...prev, ...mapped]);
        } else {
          setNews(mapped);
        }
      } else {
        setHasMore(false);
      }
      setLoading(false);
      return;
    }

    let query = supabase.from('news_items')
      .select('*')
      .gte('ingested_at', threeDaysAgo.toISOString())
      .order('buzz_v2', { ascending: false, nullsFirst: false })
      .order('ingested_at', { ascending: false })
      .range(pageNum * 20, (pageNum + 1) * 20 - 1);

    const sourceFilter = SOURCE_FILTER[cat];
    if (sourceFilter) {
      if (cat === 'Influencers') {
        query = query.eq('source_type', sourceFilter);
      } else {
        query = query.eq('source', sourceFilter);
      }
    } else {
      const mappedCat = mapCategory(cat);
      if (mappedCat) {
        query = query.eq('category', mappedCat);
      }
    }

    const { data, error } = await query;
    if (!error && data) {
      if (data.length < 20) {
        setHasMore(false);
      }
      if (append) {
        setNews(prev => [...prev, ...data]);
      } else {
        setNews(data);
      }
    } else {
      setHasMore(false);
    }
    setLoading(false);
  };

  useEffect(() => {
    setHasMore(true);
    fetchNews(0, activeCategory, false);
    setPage(0);
  }, [activeCategory]);

  useEffect(() => {
    const threeDaysAgoMs = Date.now() - 3 * 24 * 60 * 60 * 1000;
    const channel = supabase
      .channel('news_inserts')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'news_items' },
        (payload) => {
          const row = payload.new;
          if (!row) return;

          const sourceFilter = SOURCE_FILTER[activeCategory];
          if (sourceFilter) {
            if (activeCategory === 'Social') return;
            if (activeCategory === 'Influencers') {
              if (row.source_type !== sourceFilter) return;
            } else if (row.source !== sourceFilter) {
              return;
            }
          } else {
            const mappedCat = mapCategory(activeCategory);
            if (mappedCat && row.category !== mappedCat) return;
          }

          if (row.ingested_at && new Date(row.ingested_at).getTime() < threeDaysAgoMs) return;

          setNews(prev => {
            if (prev.some(item => item.id === row.id)) return prev;
            return [row, ...prev];
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [activeCategory]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && !loading && news.length > 0 && hasMore) {
          const nextPage = page + 1;
          setPage(nextPage);
          fetchNews(nextPage, activeCategory, true);
        }
      },
      { threshold: 1.0 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }
    return () => observer.disconnect();
  }, [page, loading, news.length, activeCategory, hasMore]);

  const hero = news.length > 0 ? [...news].sort((a, b) => getItemBuzz(b) - getItemBuzz(a))[0] : null;
  const gridItems = news.filter(item => item.id !== hero?.id).slice(0, 6);
  const feedItems = news.filter(item => item.id !== hero?.id).slice(6);

  return (
    <section id="news">
      <div className="section-header flex justify-between items-end">
        <div>
          <h2 className="section-title"><Activity className="text-accent-blue" /> News & Signals</h2>
          <p className="text-muted">Real-time parsed intelligence from 10+ sources</p>
        </div>
      </div>

      <CategoryPills categories={CATEGORIES} activeCategory={activeCategory} onSelect={setActiveCategory} />

      {activeCategory === 'Earnings' && <EarningsStrip />}

      {loading && news.length === 0 ? (
        <div className="grid-cols-2">
          <div className="skeleton skeleton-card news-section-hero-skeleton"></div>
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton skeleton-card"></div>)}
        </div>
      ) : news.length === 0 ? (
        <div className="empty-state glass-panel">
          <Activity className="empty-icon" />
          <h3>No signals found</h3>
          <p>Try selecting a different category or check back later.</p>
        </div>
      ) : (
        <>
          <div className="grid-cols-2 news-grid-top">
            {hero && <NewsCard item={hero} isHero={true} />}
            {gridItems.map(item => <NewsCard key={item.id} item={item} />)}
          </div>

          <div className="flex-col gap-4">
            {feedItems.map(item => <NewsCard key={item.id} item={item} />)}
          </div>

          <div ref={observerTarget} className="news-scroll-anchor">
            {loading && <div className="text-center text-muted font-bold">Loading more signals...</div>}
          </div>
        </>
      )}
    </section>
  );
}
