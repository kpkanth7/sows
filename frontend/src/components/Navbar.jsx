import { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';

export default function Navbar({ theme, toggleTheme }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) {
      window.scrollTo({ top: el.offsetTop - 80, behavior: 'smooth' });
    }
  };

  return (
    <nav className={`navbar ${scrolled ? 'glass-panel' : ''}`} style={scrolled ? { top: '10px', width: 'calc(100% - 4rem)', left: '2rem', borderRadius: '12px', borderBottom: 'none' } : {}}>
      <div className="nav-brand">
        Tech<span className="accent">Intel</span>
        <div className="live-indicator">
          <div className="live-dot"></div>
          LIVE
        </div>
      </div>
      
      <div className="nav-links">
        <button className="nav-link tab-button" onClick={() => scrollTo('news')}>News & Signals</button>
        <button className="nav-link tab-button" onClick={() => scrollTo('companies')}>Market Map</button>
        <button className="nav-link tab-button" onClick={() => scrollTo('investors')}>Investor Hub</button>
      </div>

      <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
      </button>
    </nav>
  );
}
