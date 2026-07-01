export function daysFromToday(dateString) {
  if (!dateString) return null;
  const today = new Date(new Date().toISOString().slice(0, 10));
  const target = new Date(dateString);
  return Math.round((target - today) / 86400000);
}

function eventMatchesCompany(eventRow, company) {
  const ids = Array.isArray(eventRow.company_ids) ? eventRow.company_ids : [];
  const names = Array.isArray(eventRow.company_names) ? eventRow.company_names : [];
  return (
    ids.includes(company.id) ||
    names.includes(company.name) ||
    (company.ticker && names.includes(company.ticker))
  );
}

export function buildEventMap(rows, companies) {
  const map = new Map();
  for (const company of companies || []) {
    const matches = (rows || [])
      .filter((row) => eventMatchesCompany(row, company))
      .sort((a, b) => new Date(a.event_date) - new Date(b.event_date));
    if (matches.length > 0) {
      map.set(company.id, matches);
    }
  }
  return map;
}

export function getUpcomingCatalyst({ company, eventMap, earnings = [] }) {
  const eventRows = eventMap.get(company.id) || [];
  const nextEvent = eventRows.find((row) => daysFromToday(row.event_date) >= 0) || null;
  if (nextEvent) {
    return {
      kind: 'event',
      date: nextEvent.event_date,
      type: nextEvent.event_type,
      label: `${nextEvent.event_type.replace(/_/g, ' ')} · ${nextEvent.event_date}`,
      scoreBoost: 22,
    };
  }

  const nextEarnings = (earnings || []).find((row) => daysFromToday(row.earnings_date) >= 0) || null;
  if (nextEarnings) {
    return {
      kind: 'earnings',
      date: nextEarnings.earnings_date,
      type: 'earnings',
      label: `Earnings · ${nextEarnings.earnings_date}`,
      scoreBoost: 0,
    };
  }

  if (company.recent_event && company.recent_event_date && daysFromToday(company.recent_event_date) >= 0) {
    return {
      kind: 'recent_event',
      date: company.recent_event_date,
      type: company.recent_event,
      label: `${company.recent_event.replace(/_/g, ' ')} · ${company.recent_event_date}`,
      scoreBoost: 14,
    };
  }

  return null;
}
