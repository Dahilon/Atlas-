import { useEventsStore } from '../stores/events-store';
import { threatLevelColors } from '../constants/colors';

const THREAT_LEVELS = ['critical', 'high', 'medium', 'low', 'info'] as const;
const SOURCES = ['gdelt', 'valyu'] as const;

export default function FeedFilters() {
  const filters = useEventsStore((s) => s.filters);
  const setSearchQuery = useEventsStore((s) => s.setSearchQuery);
  const toggleThreatLevel = useEventsStore((s) => s.toggleThreatLevel);
  const toggleSource = useEventsStore((s) => s.toggleSource);
  const clearFilters = useEventsStore((s) => s.clearFilters);

  return (
    <div className="space-y-2">
      <input
        type="search"
        placeholder="Search events..."
        value={filters.searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500"
      />
      <div className="flex flex-wrap gap-1">
        {THREAT_LEVELS.map((level) => (
          <button
            key={level}
            type="button"
            onClick={() => toggleThreatLevel(level)}
            className={`rounded px-2 py-0.5 text-xs font-medium text-white ${
              filters.threatLevels.has(level) ? 'ring-1 ring-white' : 'opacity-70'
            }`}
            style={{ backgroundColor: threatLevelColors[level] }}
          >
            {level}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-1">
        {SOURCES.map((src) => (
          <button
            key={src}
            type="button"
            onClick={() => toggleSource(src)}
            className={`rounded border px-2 py-0.5 text-xs ${
              filters.sources.has(src)
                ? 'border-cyan-500 bg-cyan-900/50 text-cyan-200'
                : 'border-slate-600 text-slate-400'
            }`}
          >
            {src}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={clearFilters}
        className="text-xs text-slate-500 hover:text-slate-300"
      >
        Clear filters
      </button>
    </div>
  );
}
