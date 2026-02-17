import type { MapEvent } from '../api';
import { threatLevelColors } from '../constants/colors';
import { useMapStore } from '../stores/map-store';
import { useEventsStore } from '../stores/events-store';

interface EventCardProps {
  event: MapEvent;
}

export default function EventCard({ event }: EventCardProps) {
  const flyTo = useMapStore((s) => s.flyTo);
  const selectEvent = useEventsStore((s) => s.selectEvent);
  const selectedEvent = useEventsStore((s) => s.selectedEvent);

  const isSelected = selectedEvent?.id === event.id;
  const color = threatLevelColors[event.threatLevel] ?? threatLevelColors.info;

  const handleClick = () => {
    selectEvent(event);
    const lat = event.location?.latitude ?? 0;
    const lon = event.location?.longitude ?? 0;
    if (lat !== 0 || lon !== 0) flyTo(lon, lat, 8);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`w-full rounded-lg border px-3 py-2 text-left transition ${
        isSelected
          ? 'border-cyan-500 bg-slate-800'
          : 'border-slate-700 bg-slate-800/50 hover:border-slate-600 hover:bg-slate-800'
      }`}
    >
      <div className="flex items-center gap-2">
        <span
          className="rounded px-1.5 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: color }}
        >
          {event.threatLevel}
        </span>
        {event.category && (
          <span className="text-xs text-slate-500">{event.category}</span>
        )}
        {event.source && (
          <span className="text-xs text-slate-500">{event.source}</span>
        )}
      </div>
      <h4 className="mt-1 font-medium text-slate-200 line-clamp-2">{event.title}</h4>
      {event.summary && (
        <p className="mt-0.5 line-clamp-2 text-sm text-slate-400">{event.summary}</p>
      )}
      <p className="mt-1 text-xs text-slate-500">
        {event.location?.country || event.location?.placeName || '—'} ·{' '}
        {event.timestamp?.slice(0, 10) || '—'}
      </p>
    </button>
  );
}
