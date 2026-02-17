import type { EventItem } from '../api';

interface EvidencePanelProps {
  events: EventItem[];
  loading: boolean;
  country: string | null;
  category: string | null;
  onCountryChange: (v: string) => void;
  onCategoryChange: (v: string) => void;
  countryOptions: string[];
}

const CATEGORIES = [
  'Armed Conflict',
  'Civil Unrest',
  'Diplomacy/Sanctions',
  'Economic Disruption',
  'Infrastructure/Energy',
  'Crime/Terror',
];

export default function EvidencePanel({
  events,
  loading,
  country,
  category,
  onCountryChange,
  onCategoryChange,
  countryOptions,
}: EvidencePanelProps) {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-200">Evidence (events)</h2>
      <p className="mb-4 text-sm text-slate-400">Filter by country/category. Click source URL to open.</p>
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <label className="mr-2 text-sm text-slate-400">Country</label>
          <select
            value={country ?? ''}
            onChange={(e) => onCountryChange(e.target.value)}
            className="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-slate-200"
          >
            <option value="">All</option>
            {countryOptions.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mr-2 text-sm text-slate-400">Category</label>
          <select
            value={category ?? ''}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-slate-200"
          >
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>
      {loading && <p className="text-sm text-slate-400">Loading…</p>}
      {!loading && (
        <ul className="space-y-2 text-sm">
          {events.slice(0, 50).map((e) => (
            <li key={e.id} className="rounded border border-slate-700/50 bg-slate-800/30 p-2">
              <div className="flex flex-wrap items-center gap-2 text-slate-300">
                <span>{e.date}</span>
                <span>{e.country ?? 'XX'}</span>
                <span>{e.category ?? '—'}</span>
                {e.avg_tone != null && <span>tone: {e.avg_tone.toFixed(2)}</span>}
              </div>
              {e.source_url ? (
                <a
                  href={e.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 block truncate text-cyan-400 hover:underline"
                >
                  {e.source_url}
                </a>
              ) : (
                <span className="mt-1 block text-slate-500">No URL</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {!loading && events.length === 0 && <p className="text-slate-500">No events match filters.</p>}
    </div>
  );
}
