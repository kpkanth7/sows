export default function HypeRealityMeter({ hype = 50, reality = 50 }) {
  let analysis = 'Balanced';
  let hypeColor = 'blue';
  
  if (hype - reality > 20) {
    analysis = 'Potentially Overhyped';
    hypeColor = 'amber';
  } else if (reality - hype > 20) {
    analysis = 'Underrated / High Traction';
  }

  return (
    <div className="hype-reality-meter flex-col gap-2 mt-4">
      <div className="flex justify-between text-xs text-muted font-bold">
        <span>HYPE SCORE</span>
        <span>{Math.round(hype)}</span>
      </div>
      <div className="progress-container">
        <div className={`progress-bar ${hypeColor}`} style={{ width: `${Math.min(hype, 100)}%` }}></div>
      </div>
      
      <div className="flex justify-between text-xs text-muted font-bold mt-2">
        <span>REALITY SCORE (Traction)</span>
        <span>{Math.round(reality)}</span>
      </div>
      <div className="progress-container">
        <div className="progress-bar green" style={{ width: `${Math.min(reality, 100)}%` }}></div>
      </div>

      <div className="text-xs mt-2 font-bold" style={{ color: analysis.includes('Overhyped') ? 'var(--accent-amber)' : (analysis.includes('Underrated') ? 'var(--accent-green)' : 'var(--text-secondary)') }}>
        {analysis}
      </div>
    </div>
  );
}
