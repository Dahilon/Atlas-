import { useMemo, useState } from 'react';
import type { Metric } from '../api';

type SortKey = 'country' | 'category' | 'risk_score' | 'event_count' | 'z_score' | 'date';

interface MoversTableProps {
  metrics: Metric[];
  onSelectCountry?: (country: string) => void;
}

export default function MoversTable({ metrics, onSelectCountry }: MoversTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('risk_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sorted = useMemo(() => {
    const list = [...metrics];
    list.sort((a, b) => {
      let va: number | string = a[sortKey] ?? '';
      let vb: number | string = b[sortKey] ?? '';
      if (sortKey === 'date') {
        va = String(va);
        vb = String(vb);
      }
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortDir === 'asc' ? va - vb : vb - va;
      }
      const cmp = String(va).localeCompare(String(vb));
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list.slice(0, 100);
  }, [metrics, sortKey, sortDir]);

  const toggle = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDir(key === 'country' || key === 'category' || key === 'date' ? 'asc' : 'desc');
    }
  };

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-200">Risk movers</h2>
      <p className="mb-4 text-sm text-slate-400">Sortable table (top 100). Click column headers to sort.</p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-600 text-slate-400">
              {(['date', 'country', 'category', 'risk_score', 'event_count', 'z_score'] as const).map((key) => (
                <th key={key} className="cursor-pointer py-2 pr-4 hover:text-slate-200" onClick={() => toggle(key)}>
                  {key.replace('_', ' ')} {sortKey === key && (sortDir === 'asc' ? '↑' : '↓')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((m, i) => (
              <tr
                key={`${m.date}-${m.country}-${m.category}-${i}`}
                className="border-b border-slate-700/50 hover:bg-slate-800/50"
              >
                <td className="py-1.5 pr-4 text-slate-300">{m.date}</td>
                <td className="py-1.5 pr-4">
                  {onSelectCountry ? (
                    <button type="button" className="text-cyan-400 hover:underline" onClick={() => onSelectCountry(m.country)}>
                      {m.country}
                    </button>
                  ) : (
                    <span className="text-slate-300">{m.country}</span>
                  )}
                </td>
                <td className="py-1.5 pr-4 text-slate-300">{m.category}</td>
                <td className="py-1.5 pr-4 font-medium text-slate-200">{m.risk_score != null ? m.risk_score.toFixed(1) : '—'}</td>
                <td className="py-1.5 pr-4 text-slate-300">{m.event_count}</td>
                <td className="py-1.5 pr-4 text-slate-300">{m.z_score != null ? m.z_score.toFixed(2) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sorted.length === 0 && <p className="py-4 text-sm text-slate-500">No metrics to show.</p>}
    </div>
  );
}
