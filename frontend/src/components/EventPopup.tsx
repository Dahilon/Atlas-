import type { MapEvent } from '../api';
import { threatLevelColors } from '../constants/colors';

interface EventPopupProps {
  event: MapEvent;
}

export default function EventPopup({ event }: EventPopupProps) {
  const color = threatLevelColors[event.threatLevel] ?? threatLevelColors.info;
  const locationLabel =
    event.location?.placeName ||
    event.location?.country ||
    [event.location?.latitude?.toFixed(2), event.location?.longitude?.toFixed(2)].filter(Boolean).join(', ') ||
    '—';

  return (
    <div className="min-w-[200px] max-w-[320px] rounded-lg border border-slate-600 bg-slate-900 p-3 shadow-xl">
      <div className="mb-1 flex items-center gap-2">
        <span
          className="rounded px-1.5 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: color }}
        >
          {event.threatLevel}
        </span>
        {event.category && (
          <span className="text-xs text-slate-400">{event.category}</span>
        )}
      </div>
      <h3 className="font-semibold text-slate-100">
        {event.sourceUrl ? (
          <a
            href={event.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:underline"
          >
            {event.title}
          </a>
        ) : (
          event.title
        )}
      </h3>
      {event.summary && (
        <p className="mt-1 line-clamp-3 text-sm text-slate-300">{event.summary}</p>
      )}
      <p className="mt-1 text-xs text-slate-500">
        {locationLabel} · {event.timestamp?.slice(0, 10) || '—'}
      </p>
    </div>
  );
}
