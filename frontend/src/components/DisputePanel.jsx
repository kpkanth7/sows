import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

export default function DisputePanel({ item }) {
  const [expanded, setExpanded] = useState(false);

  if (!item.is_disputed) return null;

  return (
    <div className="dispute-panel">
      <div className="flex justify-between items-center cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2 font-bold" style={{ color: 'var(--accent-amber)' }}>
          <AlertCircle size={18} />
          CONTESTED CLAIM DETECTED
        </div>
        <button className="theme-toggle">
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {expanded && (
        <div style={{ animation: 'fadeIn 0.3s ease' }}>
          <div className="grid-cols-2" style={{ marginBottom: '1rem' }}>
            <div className="card" style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem' }}>
              <div className="text-sm text-muted font-bold mb-2">CLAIM A (Confidence: {item.dispute_confidence_a}%)</div>
              <p className="text-sm">{item.dispute_claim_a}</p>
              <div className="text-xs text-muted mt-2">Sources: {(item.dispute_sources_a || []).join(', ')}</div>
            </div>
            
            <div className="card" style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem' }}>
              <div className="text-sm text-muted font-bold mb-2">CLAIM B (Confidence: {item.dispute_confidence_b}%)</div>
              <p className="text-sm">{item.dispute_claim_b}</p>
              <div className="text-xs text-muted mt-2">Sources: {(item.dispute_sources_b || []).join(', ')}</div>
            </div>
          </div>
          
          <div className="text-sm text-muted font-bold mb-2">AI RECONCILIATION BRIEF</div>
          <blockquote className="dispute-brief text-sm">
            {item.dispute_brief || 'Analysis pending...'}
          </blockquote>
        </div>
      )}
    </div>
  );
}
