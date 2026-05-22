import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';

export default function LiveTicker() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    let mounted = true;
    
    async function fetchTicker() {
      const cached = cache.get('ticker');
      if (cached) {
        if (mounted) setItems(cached);
        return;
      }
      
      const { data, error } = await supabase
        .from('news_items')
        .select('title, buzz_score, entity_names')
        .order('buzz_score', { ascending: false })
        .limit(15);
        
      if (!error && data) {
        if (mounted) setItems(data);
        cache.set('ticker', data, 5); // 5 min cache
      }
    }
    
    fetchTicker();
    
    // Auto refresh every 5 min
    const interval = setInterval(fetchTicker, 5 * 60 * 1000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (items.length === 0) return null;

  return (
    <div className="ticker-wrapper" style={{ marginTop: '70px' }}>
      <div className="ticker-track">
        {/* Duplicate items for seamless scroll */}
        {[...items, ...items, ...items].map((item, i) => (
          <div key={i} className="ticker-item">
            <span className="buzz">{(item.buzz_score || 0).toFixed(0)} BUZZ</span>
            <span>{item.title}</span>
            {item.entity_names && item.entity_names.length > 0 && (
              <span className="text-muted text-xs" style={{ marginLeft: '8px' }}>
                [{item.entity_names.join(', ')}]
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
