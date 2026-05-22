import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';

export default function ForecastBadge({ direction, confidence }) {
  const config = {
    strong_bullish: { color: 'var(--accent-green)', icon: <><TrendingUp size={14}/><TrendingUp size={14}/></>, label: 'Strong Bullish' },
    bullish: { color: 'var(--accent-green)', icon: <TrendingUp size={14}/>, label: 'Bullish' },
    neutral: { color: 'var(--text-secondary)', icon: <Minus size={14}/>, label: 'Neutral' },
    caution: { color: 'var(--accent-amber)', icon: <AlertTriangle size={14}/>, label: 'Caution' },
    bearish: { color: 'var(--accent-red)', icon: <TrendingDown size={14}/>, label: 'Bearish' },
    high_risk: { color: 'var(--accent-red)', icon: <><TrendingDown size={14}/><TrendingDown size={14}/></>, label: 'High Risk' }
  };

  const badgeConfig = config[direction] || config.neutral;

  return (
    <div className="flex items-center gap-2" style={{ color: badgeConfig.color, fontSize: '0.85rem', fontWeight: 600 }}>
      <div className="flex items-center">{badgeConfig.icon}</div>
      <span>{badgeConfig.label} {confidence ? `(${confidence}%)` : ''}</span>
    </div>
  );
}
