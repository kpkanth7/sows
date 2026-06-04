import ProgressBar from './ProgressBar';

export default function HypeRealityMeter({ hype = 50, reality = 50 }) {
  let analysis = 'Balanced';
  let hypeColor = 'blue';
  let analysisClass = 'is-balanced';
  
  if (hype - reality > 20) {
    analysis = 'Potentially Overhyped';
    hypeColor = 'amber';
    analysisClass = 'is-overhyped';
  } else if (reality - hype > 20) {
    analysis = 'Underrated / High Traction';
    analysisClass = 'is-underrated';
  }

  return (
    <div className="hype-reality-meter flex-col gap-2 mt-4">
      <div className="flex justify-between text-xs text-muted font-bold">
        <span>HYPE SCORE</span>
        <span>{Math.round(hype)}</span>
      </div>
      <ProgressBar value={hype} tone={hypeColor} />
      
      <div className="flex justify-between text-xs text-muted font-bold mt-2">
        <span>REALITY SCORE (Traction)</span>
        <span>{Math.round(reality)}</span>
      </div>
      <ProgressBar value={reality} tone="green" />

      <div className={`text-xs mt-2 font-bold hype-reality-analysis ${analysisClass}`}>
        {analysis}
      </div>
    </div>
  );
}
