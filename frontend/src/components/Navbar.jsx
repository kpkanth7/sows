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
    <nav className={`navbar ${scrolled ? 'glass-panel navbar-scrolled' : ''}`}>
      <div className="nav-brand">
        Tech<span className="accent">Intel</span>
        <div className="live-indicator">
          <div className="live-dot"></div>
          LIVE
        </div>
      </div>
      
      <div className="nav-links" role="tablist" aria-label="Primary views">
        <button 
          className={`nav-link tab-button ${activeTab === 'news' ? 'active' : ''}`} 
          onClick={() => setActiveTab('news')}
          role="tab"
          aria-selected={activeTab === 'news'}
        >
          News & Signals
        </button>
        <button 
          className={`nav-link tab-button ${activeTab === 'companies' ? 'active' : ''}`} 
          onClick={() => setActiveTab('companies')}
          role="tab"
          aria-selected={activeTab === 'companies'}
        >
          Market Map
        </button>
        <button 
          className={`nav-link tab-button ${activeTab === 'investors' ? 'active' : ''}`} 
          onClick={() => setActiveTab('investors')}
          role="tab"
          aria-selected={activeTab === 'investors'}
        >
          Investor Hub
        </button>
        <button
          className={`nav-link tab-button ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
          role="tab"
          aria-selected={activeTab === 'status'}
        >
          Status
        </button>
      </div>

      <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
      </button>
    </nav>
  );
}
