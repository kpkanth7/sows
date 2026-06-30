import { ExternalLink, ShieldCheck } from 'lucide-react';
import { safeUrl } from '../../lib/urls';

function formatDate(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}

function trustTone(score) {
  if (score == null || Number.isNaN(Number(score))) return 'badge-gray';
  if (Number(score) > 0.4) return 'badge-blue';
  if (Number(score) > 0.15) return 'badge-gold';
  return 'badge-danger';
}

function accuracyText(row) {
  if (row.accuracy != null) return `${Math.round(Number(row.accuracy))}%`;
  if (row.accuracy_pct != null) return `${Math.round(Number(row.accuracy_pct))}%`;
  if (row.total_claims > 0 && row.correct_claims != null) {
    return `${Math.round((row.correct_claims / row.total_claims) * 100)}% (${row.correct_claims}/${row.total_claims})`;
  }
  if (row.validated_predictions > 0 && row.correct_predictions != null) {
    return `${Math.round((row.correct_predictions / row.validated_predictions) * 100)}% (${row.correct_predictions}/${row.validated_predictions})`;
  }
  return null;
}

function activityForRow(row, recentActivity) {
  if (!recentActivity) return [];

  if (!Array.isArray(recentActivity)) {
    return recentActivity[row.id] || recentActivity[row.name] || recentActivity[row.handle] || [];
  }

  return recentActivity.filter((item) => (
    item.influencer_id === row.id ||
    item.influencer === row.name ||
    item.influencer_name === row.name ||
    item.handle === row.handle
  ));
}

function entityList(row, activity) {
  if (Array.isArray(row.recent_entities) && row.recent_entities.length > 0) return row.recent_entities;
  if (Array.isArray(row.entities) && row.entities.length > 0) return row.entities;

  const seen = new Set();
  activity.forEach((item) => {
    const values = Array.isArray(item.entities)
      ? item.entities
      : Array.isArray(item.entity_names)
        ? item.entity_names
        : [];
    values.forEach((value) => {
      if (value) seen.add(value);
    });
  });
  return Array.from(seen);
}

function linkedItems(activity) {
  return activity
    .map((item) => ({
      label: item.title || item.caption || item.platform_label || item.url || 'Linked post',
      url: item.url || item.post_url || item.video_url,
      date: item.published_at || item.created_at || item.posted_at,
    }))
    .filter((item) => item.url)
    .slice(0, 3);
}

function categoryLabel(category) {
  if (!category) return 'uncategorized';
  return category.replaceAll('_', ' ');
}

export default function InfluencerTrustPanel({ rows = [], recentActivity = [] }) {
  if (rows.length === 0) {
    return (
      <div className="empty-state">
        <p>No influencer trust rows supplied.</p>
      </div>
    );
  }

  return (
    <div className="flex-col gap-4">
      {rows.map((row, index) => {
        const accuracy = accuracyText(row);
        const activity = activityForRow(row, recentActivity);
        const entities = entityList(row, activity);
        const links = row.recentTitles?.length
          ? row.recentTitles.map((item) => ({
              label: item.title,
              url: item.url,
              date: item.publishedAt,
            }))
          : linkedItems(activity);
        const trustNumber = row.trust_score != null ? Number(row.trust_score) : null;
        const trustScore = trustNumber != null && !Number.isNaN(trustNumber) ? trustNumber.toFixed(3) : 'N/A';
        const checkedLabel = formatDate(row.last_checked || row.updated_at);
        const activeLabel = formatDate(row.last_active || activity[0]?.published_at || activity[0]?.created_at);

        return (
          <div
            key={row.id || row.handle || row.name || index}
            className="card glass-panel p-4"
          >
            <div className="flex justify-between items-start gap-3 flex-wrap mb-4">
              <div>
                <h3 className="investor-hub-card-title">{row.name || row.handle || 'Unknown influencer'}</h3>
                <div className="flex items-center gap-2 flex-wrap mt-1">
                  {row.platform ? <span className="badge badge-gray">{row.platform}</span> : null}
                  {row.category ? <span className="badge badge-gray">{categoryLabel(row.category)}</span> : null}
                  {row.handle ? <span className="badge badge-gray">@{row.handle.replace(/^@/, '')}</span> : null}
                  <span className={`badge ${trustTone(row.trust_score)}`}>Trust {trustScore}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {trustNumber == null || Number.isNaN(trustNumber) ? (
                  <span className="badge badge-gray">Unscored</span>
                ) : trustNumber > 0.4 ? (
                  <span className="badge badge-blue flex items-center gap-1">
                    <ShieldCheck size={12} />
                    High Trust
                  </span>
                ) : trustNumber > 0.15 ? (
                  <span className="badge badge-gold">Standard</span>
                ) : (
                  <span className="badge badge-danger">Degraded</span>
                )}
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gap: '1rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              }}
            >
              <div>
                <div className="text-xs text-muted font-bold mb-2">TRACK RECORD</div>
                <div className="flex gap-2 flex-wrap mb-2">
                  {accuracy ? (
                    <span className="badge badge-blue">Accuracy {accuracy}</span>
                  ) : (
                    <span className="badge badge-gray">Validation history limited</span>
                  )}
                  {checkedLabel ? <span className="badge badge-gray">Last checked {checkedLabel}</span> : null}
                  {typeof row.recentSignalCount === 'number' ? (
                    <span className="badge badge-gray">{row.recentSignalCount} recent signals</span>
                  ) : null}
                </div>
                <p className="text-sm text-muted m-0">
                  {accuracy
                    ? 'Accuracy shown only where validation history was supplied by the parent.'
                    : 'No validated history was supplied for this row yet, so this panel does not infer a trend.'}
                </p>
              </div>

              <div>
                <div className="text-xs text-muted font-bold mb-2">RECENT ACTIVITY</div>
                <div className="flex gap-2 flex-wrap mb-2">
                  {activeLabel ? <span className="badge badge-gray">Last active {activeLabel}</span> : null}
                  {entities.slice(0, 4).map((entity) => (
                    <span key={`${row.id || row.name}-${entity}`} className="badge badge-blue">
                      {entity}
                    </span>
                  ))}
                </div>

                {links.length > 0 ? (
                  <div className="flex-col gap-2">
                    {links.map((link, linkIndex) => (
                      <a
                        key={`${row.id || row.name}-link-${linkIndex}`}
                        href={safeUrl(link.url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm flex items-center gap-2"
                      >
                        <ExternalLink size={14} />
                        <span>{link.label}</span>
                        {link.date ? <span className="text-muted">· {formatDate(link.date)}</span> : null}
                      </a>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted m-0">No recent linked posts or videos supplied.</p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
