import { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';

export default function Navbar({ theme, toggleTheme, activeTab, setActiveTab }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

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
        <button 
          className={`nav-link tab-button ${activeTab === 'news' ? 'active' : ''}`} 
          onClick={() => setActiveTab('news')}
          style={activeTab === 'news' ? { color: 'var(--accent-blue)', borderBottom: '2px solid var(--accent-blue)' } : {}}
        >
          News & Signals
        </button>
        <button 
          className={`nav-link tab-button ${activeTab === 'companies' ? 'active' : ''}`} 
          onClick={() => setActiveTab('companies')}
          style={activeTab === 'companies' ? { color: 'var(--accent-blue)', borderBottom: '2px solid var(--accent-blue)' } : {}}
        >
          Market Map
        </button>
        <button 
          className={`nav-link tab-button ${activeTab === 'investors' ? 'active' : ''}`} 
          onClick={() => setActiveTab('investors')}
          style={activeTab === 'investors' ? { color: 'var(--accent-blue)', borderBottom: '2px solid var(--accent-blue)' } : {}}
        >
          Investor Hub
        </button>
      </div>

      <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
      </button>
    </nav>
  );
}
