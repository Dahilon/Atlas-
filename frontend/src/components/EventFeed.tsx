import { useMemo } from 'react';
import { useEventsStore, applyFiltersToEvents } from '../stores/events-store';
import FeedFilters from './FeedFilters';
import EventCard from './EventCard';

export default function EventFeed() {
  const events = useEventsStore((s) => s.events);
  const filters = useEventsStore((s) => s.filters);
  const filteredEvents = useMemo(() => applyFiltersToEvents(events, filters), [events, filters]);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-700 px-3 py-2">
        <h3 className="font-semibold text-slate-200">Event Feed</h3>
        <p className="text-xs text-slate-500">{filteredEvents.length} events</p>
      </div>
      <div className="border-b border-slate-700 px-3 py-2">
        <FeedFilters />
      </div>
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <div className="space-y-2">
          {filteredEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
        {filteredEvents.length === 0 && (
          <p className="py-4 text-center text-sm text-slate-500">No events match filters.</p>
        )}
      </div>
    </div>
  );
}
