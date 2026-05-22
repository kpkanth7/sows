import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { cache } from '../services/cache';
import CompanyCard from './CompanyCard';
import CompanyDetailPanel from './CompanyDetailPanel';
import { Briefcase } from 'lucide-react';

export default function CompanyDashboard() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [view, setView] = useState('all');

  useEffect(() => {
    async function fetchCompanies() {
      const cached = cache.get('companies');
      if (cached) {
        setCompanies(cached);
        setLoading(false);
        return;
      }
      
      const { data, error } = await supabase
        .from('companies')
        .select('*')
        .order('market_cap', { ascending: false, nullsFirst: false });
        
      if (!error && data) {
        setCompanies(data);
        cache.set('companies', data, 15);
      }
      setLoading(false);
    }
    fetchCompanies();
  }, []);

  const filtered = view === 'public' ? companies.filter(c => !c.is_private) 
                 : view === 'private' ? companies.filter(c => c.is_private)
                 : companies;

  return (
    <section id="companies" style={{ background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
      <div className="section-header flex justify-between items-end">
        <div>
          <h2 className="section-title"><Briefcase className="text-accent-amber" /> Market Map</h2>
          <p className="text-muted">Top tracked public & private tech entities</p>
        </div>
        <div className="category-pills" style={{ marginBottom: 0 }}>
          <button className={`pill ${view === 'all' ? 'active' : ''}`} onClick={() => setView('all')}>All</button>
          <button className={`pill ${view === 'public' ? 'active' : ''}`} onClick={() => setView('public')}>Public</button>
          <button className={`pill ${view === 'private' ? 'active' : ''}`} onClick={() => setView('private')}>Private</button>
        </div>
      </div>

      {loading ? (
        <div className="horizontal-strip">
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton strip-card" style={{ height: '220px' }}></div>)}
        </div>
      ) : (
        <div className="horizontal-strip">
          {filtered.map(company => (
            <CompanyCard key={company.id} company={company} onClick={setSelectedCompany} />
          ))}
        </div>
      )}

      {selectedCompany && (
        <CompanyDetailPanel company={selectedCompany} onClose={() => setSelectedCompany(null)} />
      )}
    </section>
  );
}
