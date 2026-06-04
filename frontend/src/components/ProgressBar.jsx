export default function ProgressBar({ value = 0, tone = 'blue', thin = false, reversed = false, className = '' }) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  const x = reversed ? 100 - clamped : 0;
  const classes = ['progress-container', thin ? 'is-thin' : '', className].filter(Boolean).join(' ');

  return (
    <div className={classes} aria-hidden="true">
      <svg className="progress-svg" viewBox="0 0 100 10" preserveAspectRatio="none">
        <rect className={`progress-fill tone-${tone}`} x={x} y="0" width={clamped} height="10" rx="999" />
      </svg>
    </div>
  );
}
