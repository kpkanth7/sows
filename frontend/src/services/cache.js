/**
 * Simple localStorage TTL cache
 */
const CACHE_PREFIX = 'techintel_';

export const cache = {
  set(key, data, ttlMinutes = 5) {
    const expiresAt = Date.now() + ttlMinutes * 60 * 1000;
    const record = { data, expiresAt };
    try {
      localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(record));
    } catch (e) {
      console.warn('Cache set failed', e);
    }
  },
  
  get(key) {
    try {
      const item = localStorage.getItem(CACHE_PREFIX + key);
      if (!item) return null;
      
      const record = JSON.parse(item);
      if (Date.now() > record.expiresAt) {
        localStorage.removeItem(CACHE_PREFIX + key);
        return null;
      }
      return record.data;
    } catch (e) {
      console.warn('Cache get failed', e);
      return null;
    }
  },
  
  clear() {
    Object.keys(localStorage)
      .filter(key => key.startsWith(CACHE_PREFIX))
      .forEach(key => localStorage.removeItem(key));
  }
};
