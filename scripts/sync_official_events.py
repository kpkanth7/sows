import logging
from datetime import date

from companies_config import OFFICIAL_EVENT_CATALOG
from db import get_client, record_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _company_lookup(sb):
    rows = sb.table('companies').select('id, name, ticker').execute().data or []
    lookup = {}
    for row in rows:
        if row.get('name'):
            lookup[row['name']] = row['id']
        if row.get('ticker'):
            lookup[str(row['ticker']).upper()] = row['id']
    return lookup


def main():
    sb = get_client()
    lookup = _company_lookup(sb)
    today = date.today().isoformat()
    payload = []

    for spec in OFFICIAL_EVENT_CATALOG:
        event_date = spec['event_date']
        if event_date < today:
            continue

        company_names = list(spec.get('company_names') or [])
        company_ids = []
        for name in company_names:
            company_id = lookup.get(name) or lookup.get(str(name).upper())
            if company_id:
                company_ids.append(company_id)

        payload.append({
            'event_name': spec['event_name'],
            'company_ids': company_ids,
            'company_names': company_names,
            'event_date': event_date,
            'event_type': spec['event_type'],
            'description': spec.get('description'),
            'url': spec.get('url'),
            'source': spec.get('source'),
            'source_kind': spec.get('source_kind', 'official_event_page'),
            'source_priority': spec.get('source_priority', 1),
            'source_region': spec.get('source_region'),
            'confidence': spec.get('confidence', 95),
            'is_official': spec.get('is_official', True),
            'is_upcoming': True,
        })

    for row in payload:
        sb.table('events_calendar').delete().eq('event_name', row['event_name']).eq('event_date', row['event_date']).execute()
        sb.table('events_calendar').insert(row).execute()

    logger.info(f"synced {len(payload)} official events")


if __name__ == '__main__':
    try:
        main()
        record_health(get_client(), 'sync_official_events', 'ok')
    except Exception as e:
        record_health(get_client(), 'sync_official_events', 'error', str(e))
        raise
