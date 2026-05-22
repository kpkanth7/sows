import { TrendingUp, TrendingDown, Star } from 'lucide-react';

export default function CompanyCard({ company, onClick }) {
  const isUp = company.change_pct_24h > 0;
  
  return (
    <div className="card glass-panel strip-card cursor-pointer" onClick={() => onClick(company)} style={{ cursor: 'pointer' }}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          {company.logo_url ? (
            <img src={company.logo_url} alt={company.name} style={{ width: 40, height: 40, borderRadius: 8, background: '#fff' }} />
          ) : (
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'var(--surface-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
              {company.name.substring(0,2).toUpperCase()}
            </div>
          )}
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{company.name}</h3>
            <div className="flex gap-2 items-center">
              <span className="text-muted text-xs font-bold">{company.ticker || 'PRIVATE'}</span>
              {company.is_ai_company && <span className="badge badge-blue">AI</span>}
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex justify-between items-end mb-4">
        <div>
          <div className="text-muted text-xs font-bold mb-1">{company.is_private ? 'VALUATION' : 'PRICE'}</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
            ${company.is_private ? (company.last_valuation / 1e9).toFixed(1) + 'B' : company.stock_price}
          </div>
        </div>
        {!company.is_private && (
          <div className={`flex items-center gap-1 font-bold ${isUp ? 'text-accent-green' : 'text-accent-red'}`} style={{ color: isUp ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {isUp ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            {Math.abs(company.change_pct_24h)}%
          </div>
        )}
      </div>
      
      <div className="flex items-center justify-between mt-auto pt-4" style={{ borderTop: '1px solid var(--glass-border)' }}>
        <div className="flex-col gap-1 w-full max-w-[45%]">
          <span className="text-xs text-muted font-bold">HYPE</span>
          <div className="progress-container">
            <div className="progress-bar blue" style={{ width: `${company.hype_score}%` }}></div>
          </div>
        </div>
        <div className="flex-col gap-1 w-full max-w-[45%] text-right">
          <span className="text-xs text-muted font-bold">SENTIMENT</span>
          <div className="progress-container" style={{ transform: 'rotate(180deg)' }}>
            <div className={`progress-bar ${company.sentiment_score > 50 ? 'green' : 'red'}`} style={{ width: `${company.sentiment_score}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
