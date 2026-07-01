import { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import LiveTicker from "./components/LiveTicker";
import DailyDigestBanner from "./components/DailyDigestBanner";
import NewsSection from "./components/NewsSection";
import CompanyDashboard from "./components/CompanyDashboard";
import InvestorHub from "./components/InvestorHub";
import ConferenceCalendar from "./components/ConferenceCalendar";
import ComparisonWidget from "./components/ComparisonWidget";
import ErrorBoundary from "./components/ErrorBoundary";

const ROOT_TITLE = "Tech-Intel | Technology Company Intelligence";
const ROOT_DESCRIPTION =
  "Tech-Intel tracks public and private technology companies across news, filings, research, GitHub momentum, earnings, insider trades, and investor signals.";
const TOP_TAB_META = {
  news: {
    label: "News & Signals",
    description: "Track live technology news, filings, research, and investor signals across the Tech-Intel coverage universe.",
  },
  companies: {
    label: "Market Map",
    description: "Explore public market caps, private valuations, and company-level investor intelligence across tracked technology companies.",
  },
  investors: {
    label: "Investor Hub",
    description: "Review investor forecasts, catalysts, influencer track records, insider activity, and daily digest signals in one place.",
  },
};

function setMetaContent(selector, content) {
  if (!content) return;
  const element = document.head.querySelector(selector);
  if (element) element.setAttribute("content", content);
}

function normalizeMetaUrl(pathname = "/") {
  const canonicalTag = document.head.querySelector('link[rel="canonical"]');
  const ogUrlTag = document.head.querySelector('meta[property="og:url"]');
  const baseUrl =
    canonicalTag?.getAttribute("data-base-url") ||
    ogUrlTag?.getAttribute("data-base-url") ||
    "";
  const origin =
    window.location.origin.startsWith("http://localhost") ||
    window.location.origin.startsWith("http://127.0.0.1")
      ? window.location.origin
      : baseUrl || window.location.origin;
  return new URL(pathname, `${origin.replace(/\/$/, "")}/`).toString();
}

function applySeoMetadata(activeTab) {
  const tabMeta = TOP_TAB_META[activeTab] || { label: "Dashboard", description: ROOT_DESCRIPTION };
  const companyName = document.querySelector(".company-detail-name")?.textContent?.trim();
  const companyTicker = document.querySelector(".company-detail-title .badge")?.textContent?.trim();
  const companyTab = document.querySelector(".company-detail-tabs .tab-button.active")?.textContent?.trim();
  const companyPath = companyName
    ? `/companies/${encodeURIComponent(companyName.toLowerCase().replace(/\s+/g, "-"))}`
    : `/${activeTab}`;

  const title = companyName
    ? `${companyName}${companyTab ? ` ${companyTab}` : ""} | ${tabMeta.label} | Tech-Intel`
    : activeTab
      ? `Tech-Intel | ${tabMeta.label}`
      : ROOT_TITLE;

  const description = companyName
    ? `${companyName}${companyTicker ? ` (${companyTicker})` : ""} on Tech-Intel: ${companyTab || "Overview"} covering news, benchmarks, insider activity, and investor signals.`
    : tabMeta.description;

  document.title = title;
  setMetaContent('meta[name="description"]', description);
  setMetaContent('meta[property="og:title"]', title);
  setMetaContent('meta[property="og:description"]', description);
  setMetaContent('meta[name="twitter:title"]', title);
  setMetaContent('meta[name="twitter:description"]', description);

  const canonicalHref = normalizeMetaUrl(companyPath);
  const canonicalTag = document.head.querySelector('link[rel="canonical"]');
  if (canonicalTag) canonicalTag.setAttribute("href", canonicalHref);
  setMetaContent('meta[property="og:url"]', canonicalHref);
}

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

  useEffect(() => {
    applySeoMetadata(activeTab);

    const observer = new MutationObserver(() => {
      applySeoMetadata(activeTab);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => observer.disconnect();
  }, [activeTab]);

  return (
    <div className="app-container">
      <Navbar theme={theme} toggleTheme={toggleTheme} activeTab={activeTab} setActiveTab={setActiveTab} />
      <LiveTicker />
      
      <main className="main-content app-main">
        {/* Phase 3.7: persistent hero digest banner above every tab. */}
        <DailyDigestBanner />
        <div className="tab-content tab-content-animated">
          {activeTab === 'news' && (
            <ErrorBoundary label="News & Signals failed to load.">
              <NewsSection />
            </ErrorBoundary>
          )}
          
          {activeTab === 'companies' && (
            <ErrorBoundary label="Market Map failed to load.">
              <CompanyDashboard />
            </ErrorBoundary>
          )}
          
          {activeTab === 'investors' && (
            <div className="investor-layout">
              <ErrorBoundary label="Investor Hub failed to load.">
                <InvestorHub />
              </ErrorBoundary>
              <aside className="investor-side-panel">
                <ErrorBoundary label="Investor side panel failed to load.">
                  <ConferenceCalendar />
                  <ComparisonWidget />
                </ErrorBoundary>
              </aside>
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        &copy; {new Date().getFullYear()} Tech-Intel AI. Real-time Bloomberg Terminal alternative.
      </footer>
    </div>
  );
}
