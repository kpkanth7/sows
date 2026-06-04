import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';

export default function ForecastBadge({ direction, confidence }) {
  const config = {
    strong_bullish: { tone: 'is-green', icon: <><TrendingUp size={14}/><TrendingUp size={14}/></>, label: 'Strong Bullish' },
    bullish: { tone: 'is-green', icon: <TrendingUp size={14}/>, label: 'Bullish' },
    neutral: { tone: 'is-neutral', icon: <Minus size={14}/>, label: 'Neutral' },
    caution: { tone: 'is-amber', icon: <AlertTriangle size={14}/>, label: 'Caution' },
    bearish: { tone: 'is-red', icon: <TrendingDown size={14}/>, label: 'Bearish' },
    high_risk: { tone: 'is-red', icon: <><TrendingDown size={14}/><TrendingDown size={14}/></>, label: 'High Risk' }
  };

  const badgeConfig = config[direction] || config.neutral;

  return (
    <div className={`flex items-center gap-2 forecast-badge ${badgeConfig.tone}`}>
      <div className="flex items-center">{badgeConfig.icon}</div>
      <span>{badgeConfig.label} {confidence ? `(${confidence}%)` : ''}</span>
    </div>
  );
}
