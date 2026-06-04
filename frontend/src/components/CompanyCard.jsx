import { TrendingUp, TrendingDown } from 'lucide-react';
import ProgressBar from './ProgressBar';

export default function CompanyCard({ company, onClick }) {
  const isUp = company.change_pct_24h > 0;
  
  return (
    <div className="card glass-panel cursor-pointer company-card" onClick={() => onClick(company)}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          {company.logo_url ? (
            <img src={company.logo_url} alt={company.name} className="company-card-logo" />
          ) : (
            <div className="company-card-logo-fallback">
              {company.name.substring(0,2).toUpperCase()}
            </div>
          )}
          <div>
            <h3 className="company-card-title">{company.name}</h3>
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
          <div className="company-card-price">
            ${company.is_private ? (company.last_valuation / 1e9).toFixed(1) + 'B' : company.stock_price}
          </div>
        </div>
        {!company.is_private && (
          <div className={`flex items-center gap-1 font-bold company-card-change ${isUp ? 'is-up' : 'is-down'}`}>
            {isUp ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            {Math.abs(company.change_pct_24h)}%
          </div>
        )}
      </div>
      
      <div className="flex items-center justify-between mt-auto pt-4 company-card-footer">
        <div className="flex-col gap-1 w-full max-w-[45%]">
          <span className="text-xs text-muted font-bold">HYPE</span>
          <ProgressBar value={company.hype_score} tone="blue" />
        </div>
        <div className="flex-col gap-1 w-full max-w-[45%] text-right">
          <span className="text-xs text-muted font-bold">SENTIMENT</span>
          <ProgressBar value={company.sentiment_score} tone={company.sentiment_score > 50 ? 'green' : 'red'} reversed />
        </div>
      </div>
    </div>
  );
}
