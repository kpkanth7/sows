import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

export default function DisputePanel({ item }) {
  const [expanded, setExpanded] = useState(false);

  if (!item.is_disputed) return null;

  return (
    <div className="dispute-panel">
      <button
        type="button"
        className="dispute-panel-toggle"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={expanded ? 'Collapse disputed claim details' : 'Expand disputed claim details'}
      >
        <div className="flex items-center gap-2 font-bold dispute-panel-banner">
          <AlertCircle size={18} />
          CONTESTED CLAIM DETECTED
        </div>
        <span className="theme-toggle" aria-hidden="true">
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </span>
      </button>

      {expanded && (
        <div className="dispute-panel-expanded">
          <div className="grid-cols-2 dispute-panel-claims">
            <div className="card dispute-panel-claim-card">
              <div className="text-sm text-muted font-bold mb-2">CLAIM A (Confidence: {item.dispute_confidence_a}%)</div>
              <p className="text-sm">{item.dispute_claim_a}</p>
              <div className="text-xs text-muted mt-2">Sources: {(item.dispute_sources_a || []).join(', ')}</div>
            </div>
            
            <div className="card dispute-panel-claim-card">
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
