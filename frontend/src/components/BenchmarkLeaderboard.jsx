import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { AlertCircle } from 'lucide-react';

export default function BenchmarkLeaderboard({ companyId }) {
  const [benchmarks, setBenchmarks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBench() {
      let query = supabase.from('benchmarks').select('*').order('benchmark_name', { ascending: true });
      if (companyId) {
        query = query.eq('company_id', companyId);
      }
      const { data, error } = await query;
      if (!error && data) setBenchmarks(data);
      setLoading(false);
    }
    fetchBench();
  }, [companyId]);

  if (loading) return <div className="skeleton skeleton-card benchmark-leaderboard-skeleton"></div>;
  if (benchmarks.length === 0) return <div className="empty-state">No benchmarks recorded.</div>;

  return (
    <div className="card glass-panel benchmark-leaderboard-card">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Benchmark</th>
              <th>Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {benchmarks.map(b => (
              <tr key={b.id} className={b.is_disputed ? 'disputed' : ''}>
                <td className="font-bold">{b.model_name}</td>
                <td>{b.benchmark_name}</td>
                <td className="font-bold benchmark-leaderboard-score">{b.score}{b.score_unit}</td>
                <td>
                  {b.is_disputed ? (
                    <span className="badge badge-danger flex items-center gap-1" title={b.dispute_brief}>
                      <AlertCircle size={12}/> DISPUTED
                    </span>
                  ) : b.is_self_reported ? (
                    <span className="badge badge-gray">SELF-REPORTED</span>
                  ) : (
                    <span className="badge badge-green">VERIFIED</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
