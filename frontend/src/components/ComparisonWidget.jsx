import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { GitCompare } from 'lucide-react';
import ForecastBadge from './ForecastBadge';

export default function ComparisonWidget() {
  const [companies, setCompanies] = useState([]);
  const [idA, setIdA] = useState('');
  const [idB, setIdB] = useState('');

  useEffect(() => {
    supabase.from('companies').select('id, name, ticker, hype_score, reality_score, sentiment_score, buzz_score, forecast_direction, forecast_confidence').order('name')
      .then(({data}) => {
        if (data) {
          setCompanies(data);
          if (data.length > 1) {
            setIdA(data[0].id);
            setIdB(data[1].id);
          }
        }
      });
  }, []);

  const compA = companies.find(c => c.id === idA);
  const compB = companies.find(c => c.id === idB);

  if (!compA || !compB) return null;

  return (
    <div className="card glass-panel mt-6">
      <h3 className="flex items-center gap-2 mb-4"><GitCompare size={20} className="text-accent-amber" /> Head-to-Head</h3>
      
      <div className="flex gap-4 mb-6">
        <select value={idA} onChange={e => setIdA(e.target.value)} className="flex-1" style={{ background: 'var(--bg-color)' }}>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <div className="font-bold text-muted flex items-center justify-center px-2">VS</div>
        <select value={idB} onChange={e => setIdB(e.target.value)} className="flex-1" style={{ background: 'var(--bg-color)' }}>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      <div className="grid-cols-2" style={{ gap: 0 }}>
        {/* Company A */}
        <div className="p-4" style={{ borderRight: '1px solid var(--border-color)' }}>
          <div className="flex justify-between text-xs font-bold mb-1"><span>HYPE</span><span>{Math.round(compA.hype_score)}</span></div>
          <div className="progress-container mb-4"><div className="progress-bar blue" style={{ width: `${compA.hype_score}%` }}></div></div>

          <div className="flex justify-between text-xs font-bold mb-1"><span>SENTIMENT</span><span>{Math.round(compA.sentiment_score)}</span></div>
          <div className="progress-container mb-4"><div className={`progress-bar ${compA.sentiment_score > 50 ? 'green' : 'red'}`} style={{ width: `${compA.sentiment_score}%` }}></div></div>

          <div className="mt-4"><ForecastBadge direction={compA.forecast_direction} confidence={compA.forecast_confidence} /></div>
        </div>
        
        {/* Company B */}
        <div className="p-4 text-right">
          <div className="flex justify-between text-xs font-bold mb-1 flex-row-reverse"><span>HYPE</span><span>{Math.round(compB.hype_score)}</span></div>
          <div className="progress-container mb-4" style={{ transform: 'rotate(180deg)' }}><div className="progress-bar blue" style={{ width: `${compB.hype_score}%` }}></div></div>

          <div className="flex justify-between text-xs font-bold mb-1 flex-row-reverse"><span>SENTIMENT</span><span>{Math.round(compB.sentiment_score)}</span></div>
          <div className="progress-container mb-4" style={{ transform: 'rotate(180deg)' }}><div className={`progress-bar ${compB.sentiment_score > 50 ? 'green' : 'red'}`} style={{ width: `${compB.sentiment_score}%` }}></div></div>

          <div className="mt-4 flex justify-end"><ForecastBadge direction={compB.forecast_direction} confidence={compB.forecast_confidence} /></div>
        </div>
      </div>
    </div>
  );
}
