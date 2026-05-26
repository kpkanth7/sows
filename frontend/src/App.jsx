import { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import LiveTicker from "./components/LiveTicker";
import NewsSection from "./components/NewsSection";
import CompanyDashboard from "./components/CompanyDashboard";
import InvestorHub from "./components/InvestorHub";
import ConferenceCalendar from "./components/ConferenceCalendar";
import ComparisonWidget from "./components/ComparisonWidget";
import { supabase } from "./lib/supabase";

export default function App() {
  const [theme, setTheme] = useState("dark");
  const [activeTab, setActiveTab] = useState("news");

  useEffect(() => {
    const savedTheme = localStorage.getItem("techintel-theme") || "dark";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("techintel-theme", next);
    document.documentElement.setAttribute("data-theme", next);
  };

  return (
    <div className="app-container">
      <Navbar theme={theme} toggleTheme={toggleTheme} activeTab={activeTab} setActiveTab={setActiveTab} />
      <LiveTicker />
      
      <main className="main-content" style={{ width: '100%', padding: 0, overflow: 'hidden' }}>
        <div className="tab-content" style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
          {activeTab === 'news' && <NewsSection />}
          
          {activeTab === 'companies' && <CompanyDashboard />}
          
          {activeTab === 'investors' && (
            <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', padding: '0 2rem' }}>
              <InvestorHub />
              <aside style={{ paddingTop: '4rem' }}>
                <ConferenceCalendar />
                <ComparisonWidget />
              </aside>
            </div>
          )}
        </div>
      </main>

      <footer style={{ textAlign: 'center', padding: '2rem', borderTop: '1px solid var(--border-color)', marginTop: '4rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        &copy; {new Date().getFullYear()} Tech-Intel AI. Real-time Bloomberg Terminal alternative.
      </footer>
    </div>
  );
}
