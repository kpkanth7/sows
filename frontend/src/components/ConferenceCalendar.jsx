import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { Calendar } from 'lucide-react';

export default function ConferenceCalendar() {
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    supabase.from('events_calendar').select('*').gte('event_date', new Date().toISOString().split('T')[0]).order('event_date', { ascending: true }).limit(8)
      .then(({data}) => {
        if (data) setEvents(data);
      });
  }, []);

  const getTypeColor = (type) => {
    const map = {
      conference: 'var(--accent-blue)',
      earnings: 'var(--accent-green)',
      product_launch: 'var(--accent-amber)',
      ipo: 'var(--accent-red)'
    };
    return map[type] || 'var(--text-secondary)';
  };

  return (
    <div className="card glass-panel">
      <h3 className="flex items-center gap-2 mb-4"><Calendar size={20} className="text-accent-blue" /> Upcoming Events</h3>
      {events.length === 0 ? (
        <div className="text-muted text-sm text-center py-4">No upcoming events scheduled.</div>
      ) : (
        <div className="flex-col gap-4">
          {events.map(ev => (
            <div key={ev.id} className="flex gap-4 items-start" style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
              <div className="flex-col items-center min-w-[50px]">
                <div className="text-xs text-muted font-bold uppercase">{new Date(ev.event_date).toLocaleString('default', { month: 'short' })}</div>
                <div className="font-bold text-lg">{new Date(ev.event_date).getDate()}</div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: getTypeColor(ev.event_type) }}></div>
                  <a href={ev.url} target="_blank" className="font-bold text-sm hover:underline">{ev.event_name}</a>
                </div>
                <p className="text-xs text-muted m-0">{ev.description}</p>
                {ev.company_names && ev.company_names.length > 0 && (
                  <div className="flex gap-2 mt-2">
                    {ev.company_names.map(name => <span key={name} className="badge badge-gray">{name}</span>)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
