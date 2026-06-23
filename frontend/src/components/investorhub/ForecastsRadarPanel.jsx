import ForecastBadge from '../ForecastBadge';

function metricLabel(item) {
  if (item.priority != null) return `Priority ${item.priority}`;
  if (item.score != null) return `Score ${Math.round(item.score)}`;
  if (item.rank != null) return `Rank #${item.rank}`;
  if (item.watch_priority != null) return `Priority ${item.watch_priority}`;
  return null;
}

function summaryText(item) {
  return item.summary || item.brief || item.explanation || item.description || null;
}

function reasonChips(item) {
  if (Array.isArray(item.reasons) && item.reasons.length > 0) return item.reasons;
  if (Array.isArray(item.explanation_chips) && item.explanation_chips.length > 0) return item.explanation_chips;
  if (Array.isArray(item.highlights) && item.highlights.length > 0) return item.highlights;
  if (typeof item.explanation === 'string' && item.explanation.trim()) return [item.explanation.trim()];
  return [];
}

function forecastProps(item) {
  if (item.forecast && typeof item.forecast === 'object') {
    return {
      direction: item.forecast.direction,
      confidence: item.forecast.confidence,
    };
  }

  return {
    direction: item.forecast_direction || item.forecastDirection,
    confidence: item.forecast_confidence || item.forecastConfidence,
  };
}

function CompanyCard({ item, emptyCopy }) {
  const chips = reasonChips(item);
  const summary = summaryText(item);
  const forecast = forecastProps(item);

  return (
    <div className="card glass-panel p-4 investor-hub-forecast-card">
      <div className="flex justify-between items-start gap-3 mb-3">
        <div>
          <h3 className="investor-hub-card-title">{item.name || item.company_name || 'Unnamed company'}</h3>
          <div className="flex items-center gap-2 flex-wrap mt-1">
            <span className={`badge ${item.ticker ? 'badge-gray' : 'badge-blue'}`}>
              {item.ticker || 'PRIVATE'}
            </span>
            {item.nextEventLabel ? <span className="badge badge-gray">{item.nextEventLabel}</span> : null}
            {metricLabel(item) && <span className="badge badge-gold">{metricLabel(item)}</span>}
          </div>
        </div>
        {forecast.direction ? (
          <ForecastBadge direction={forecast.direction} confidence={forecast.confidence} />
        ) : null}
      </div>

      {summary ? <p className="text-sm text-muted investor-hub-brief-anywhere">{summary}</p> : null}

      {chips.length > 0 ? (
        <div
          className="flex gap-2 flex-wrap mt-3"
          style={{ alignItems: 'flex-start' }}
        >
          {chips.slice(0, 4).map((chip, index) => (
            <span key={`${item.id || item.name || 'company'}-${index}`} className="badge badge-blue">
              {chip}
            </span>
          ))}
        </div>
      ) : !summary ? (
        <p className="text-sm text-muted m-0">{emptyCopy}</p>
      ) : null}
    </div>
  );
}

function Section({ title, rows, emptyCopy }) {
  return (
    <section>
      <div className="flex items-center justify-between gap-3 mb-3">
        <h3 className="font-bold">{title}</h3>
        <span className="badge badge-gray">{rows.length}</span>
      </div>

      {rows.length === 0 ? (
        <div className="empty-state">
          <p>{emptyCopy}</p>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gap: '1rem',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          }}
        >
          {rows.map((item, index) => (
            <CompanyCard
              key={item.id || `${title}-${item.ticker || item.name || index}`}
              item={item}
              emptyCopy={emptyCopy}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default function ForecastsRadarPanel({
  momentumLeaders = [],
  riskBuildUp = [],
  catalystsAhead = [],
  privateWatchlist = [],
}) {
  return (
    <div className="flex-col gap-6">
      <Section
        title="Momentum Leaders"
        rows={momentumLeaders}
        emptyCopy="No momentum leaders supplied."
      />
      <Section
        title="Risk Build-Up"
        rows={riskBuildUp}
        emptyCopy="No risk build-up entries supplied."
      />
      <Section
        title="Catalysts Ahead"
        rows={catalystsAhead}
        emptyCopy="No upcoming catalysts supplied."
      />
      <Section
        title="Private Watchlist"
        rows={privateWatchlist}
        emptyCopy="No private watchlist entries supplied."
      />
    </div>
  );
}
