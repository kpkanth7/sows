import { useEffect, useState } from 'react';
import { Calendar, Clock3, Sparkles } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { safeUrl } from '../lib/urls';

function startOfToday() {
  return new Date().toISOString().split('T')[0];
}

function daysUntil(dateString) {
  const today = new Date(startOfToday());
  const target = new Date(dateString);
  return Math.round((target - today) / 86400000);
}

function formatRelative(dateString) {
  const delta = daysUntil(dateString);
  if (delta <= 0) return 'Today';
  if (delta === 1) return 'Tomorrow';
  return `In ${delta} days`;
}

function eventTypeTone(type) {
  const map = {
    conference: 'is-conference',
    earnings: 'is-earnings',
    product_launch: 'is-product-launch',
    ipo: 'is-ipo',
    acquisition: 'is-ipo',
    funding: 'is-default',
  };
  return map[type] || 'is-default';
}

function normalizeEventRow(row) {
  const official = row.is_official ? 'Official event page' : 'Tracked event';
  return {
    id: `event-${row.id}`,
    date: row.event_date,
    title: row.event_name,
    description: row.description,
    type: row.event_type,
    companyNames: Array.isArray(row.company_names) ? row.company_names : [],
    url: row.url,
    sourceLabel: row.source ? `${official} · ${row.source}` : official,
    confidence: row.confidence,
  };
}

export default function ConferenceCalendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadEvents() {
      const today = startOfToday();
      const { data: eventsData } = await supabase
        .from('events_calendar')
        .select('*')
        .gte('event_date', today)
        .order('event_date', { ascending: true })
        .limit(20);

      const merged = (eventsData || []).map(normalizeEventRow)
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(0, 8);

      setEvents(merged);
      setLoading(false);
    }

    loadEvents();
  }, []);

  return (
    <div className="card glass-panel">
      <div className="comparison-header">
        <Calendar size={20} className="text-accent-blue" />
        <div>
          <h3>Upcoming Events</h3>
          <p>Actual conference, IPO, product, acquisition, and funding dates only. No announcement headlines.</p>
        </div>
      </div>

      {loading ? (
        <div className="text-muted text-sm text-center py-4">Loading upcoming catalysts…</div>
      ) : events.length === 0 ? (
        <div className="text-muted text-sm text-center py-4">No upcoming events scheduled.</div>
      ) : (
        <div className="flex-col gap-4">
          {events.map((event) => (
            <div key={event.id} className="conference-event-row">
              <div className="flex-col items-center min-w-[58px]">
                <div className="text-xs text-muted font-bold uppercase">
                  {new Date(event.date).toLocaleString('default', { month: 'short' })}
                </div>
                <div className="font-bold text-lg">{new Date(event.date).getDate()}</div>
                <div className="conference-event-relative">{formatRelative(event.date)}</div>
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`conference-event-dot ${eventTypeTone(event.type)}`}></span>
                  {event.url ? (
                    <a
                      href={safeUrl(event.url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold text-sm hover:underline"
                    >
                      {event.title}
                    </a>
                  ) : (
                    <span className="font-bold text-sm">{event.title}</span>
                  )}
                </div>

                <div className="conference-event-meta">
                  <span className="badge badge-gray">{event.sourceLabel}</span>
                  {event.confidence != null && <span className="badge badge-blue">{Math.round(event.confidence)}% conf</span>}
                  <span className="conference-event-meta-inline">
                    <Clock3 size={12} />
                    {event.type.replace('_', ' ')}
                  </span>
                </div>

                {event.description && <p className="text-xs text-muted m-0 mt-2">{event.description}</p>}

                {event.companyNames.length > 0 && (
                  <div className="flex gap-2 mt-2 flex-wrap">
                    {event.companyNames.map((name) => (
                      <span key={name} className="badge badge-gray">{name}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          <div className="conference-event-footer">
            <Sparkles size={12} />
            Actual event dates only. Use other panels for releases and news.
          </div>
        </div>
      )}
    </div>
  );
}
