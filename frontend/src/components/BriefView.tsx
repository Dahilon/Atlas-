import type { BriefResponse } from '../api';

interface BriefViewProps {
  brief: BriefResponse | null;
  briefDate: string;
  onDateChange: (date: string) => void;
  loading: boolean;
}

export default function BriefView({ brief, briefDate, onDateChange, loading }: BriefViewProps) {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-200">Daily intel brief</h2>
      <div className="mb-4 flex items-center gap-2">
        <label className="text-sm text-slate-400">Date</label>
        <input
          type="date"
          value={briefDate}
          onChange={(e) => onDateChange(e.target.value)}
          className="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-slate-200"
        />
      </div>
      {loading && <p className="text-sm text-slate-400">Loading…</p>}
      {!loading && brief && (
        <>
          <p className="mb-4 text-sm text-slate-300">{brief.summary}</p>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm font-medium text-slate-400">Top risk movers</h3>
              <ul className="space-y-1 text-sm">
                {brief.top_movers.map((m, i) => (
                  <li key={i} className="flex justify-between text-slate-300">
                    <span>{m.country} — {m.category}</span>
                    <span>risk: {m.risk_score != null ? m.risk_score.toFixed(1) : '—'}</span>
                  </li>
                ))}
                {brief.top_movers.length === 0 && <li className="text-slate-500">None</li>}
              </ul>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium text-slate-400">Top spikes (last 7 days)</h3>
              <ul className="space-y-1 text-sm">
                {brief.top_spikes.map((s, i) => (
                  <li key={i} className="flex justify-between text-slate-300">
                    <span>{s.date} {s.country} — {s.category}</span>
                    <span>z: {(s.z_used ?? s.z_score) != null ? Number(s.z_used ?? s.z_score).toFixed(2) : '—'}</span>
                  </li>
                ))}
                {brief.top_spikes.length === 0 && <li className="text-slate-500">None</li>}
              </ul>
            </div>
          </div>
        </>
      )}
      {!loading && !brief && <p className="text-sm text-slate-500">No brief data.</p>}
    </div>
  );
}
