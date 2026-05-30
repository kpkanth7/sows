import { useState, useEffect, useRef } from 'react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import CategoryPills from './CategoryPills';
import NewsCard from './NewsCard';
import { Activity } from 'lucide-react';

const CATEGORIES = ['All', 'AI', 'Releases', 'M&A', 'IPO', 'Controversy', 'Conferences', 'Open Source', 'Earnings', 'Filings'];

const mapCategory = (uiCat) => {
  const map = {
    'AI': 'ai',
    'Releases': 'release',
    'M&A': 'ma',
    'IPO': 'ipo',
    'Controversy': 'controversy',
    'Conferences': 'conference',
    'Open Source': 'opensource',
    'Earnings': 'earnings'
  };
  return map[uiCat] || null;
};

// Phase 3.1: Filings pill filters by `source` (precise ingestor name) rather
// than the LLM `category` — surfaces SEC 8-K material events (exec changes,
// M&A, breaches, bankruptcies, etc.) as their own stream regardless of how
// the LLM labeled the headline. Uses `source` not `source_type` because
// `source_type` is a coarse bucket ('news'/'social'/'research').
const SOURCE_FILTER = {
  'Filings': 'sec_edgar',
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

    let query = supabase.from('news_items')
      .select('*')
      .gte('ingested_at', threeDaysAgo.toISOString())
      // Phase 2.13: rank by LLM-rated composite buzz_v2 first (nulls last for
      // not-yet-processed items), then fall back to recency for stability.
      .order('buzz_v2', { ascending: false, nullsFirst: false })
      .order('ingested_at', { ascending: false })
      .range(pageNum * 20, (pageNum + 1) * 20 - 1);
    
    const sourceFilter = SOURCE_FILTER[cat];
    if (sourceFilter) {
      query = query.eq('source', sourceFilter);
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

  const hero = news.length > 0 ? [...news].sort((a,b) => b.buzz_score - a.buzz_score)[0] : null;
  const gridItems = news.filter(n => n.id !== hero?.id).slice(0, 6);
  const feedItems = news.filter(n => n.id !== hero?.id).slice(6);

  return (
    <section id="news">
      <div className="section-header flex justify-between items-end">
        <div>
          <h2 className="section-title"><Activity className="text-accent-blue" /> News & Signals</h2>
          <p className="text-muted">Real-time parsed intelligence from 10+ sources</p>
        </div>
      </div>
      
      <CategoryPills categories={CATEGORIES} activeCategory={activeCategory} onSelect={setActiveCategory} />
      
      {loading && news.length === 0 ? (
        <div className="grid-cols-2">
          <div className="skeleton skeleton-card" style={{ gridColumn: '1 / -1', height: '300px' }}></div>
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
          <div className="grid-cols-2" style={{ marginBottom: '2rem' }}>
            {hero && <NewsCard item={hero} isHero={true} />}
            {gridItems.map(item => <NewsCard key={item.id} item={item} />)}
          </div>
          
          <div className="flex-col gap-4">
            {feedItems.map(item => <NewsCard key={item.id} item={item} />)}
          </div>
          
          <div ref={observerTarget} style={{ height: '20px', margin: '2rem 0' }}>
            {loading && <div className="text-center text-muted font-bold">Loading more signals...</div>}
          </div>
        </>
      )}
    </section>
  );
}
