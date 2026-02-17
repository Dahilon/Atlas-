import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import type { Metric, Spike } from '../api';

interface CountryDrilldownProps {
  country: string | null;
  metrics: Metric[];
  spikes: Spike[];
}

export default function CountryDrilldown({ country, metrics, spikes }: CountryDrilldownProps) {
  const countryMetrics = useMemo(
    () => (country ? metrics.filter((m) => m.country === country) : []),
    [country, metrics]
  );
  const countrySpikes = useMemo(
    () => (country ? spikes.filter((s) => s.country === country) : []),
    [country, spikes]
  );

  const riskOverTime = useMemo(() => {
    const byDate = new Map<string, { date: string; risk: number; events: number }>();
    for (const m of countryMetrics) {
      const d = m.date;
      const cur = byDate.get(d);
      const risk = m.risk_score ?? 0;
      const events = m.event_count ?? 0;
      if (!cur) {
        byDate.set(d, { date: d, risk, events });
      } else {
        byDate.set(d, { date: d, risk: Math.max(cur.risk, risk), events: cur.events + events });
      }
    }
    return Array.from(byDate.values()).sort((a, b) => a.date.localeCompare(b.date));
  }, [countryMetrics]);

  const categoryBreakdown = useMemo(() => {
    const latest = riskOverTime.length ? riskOverTime[riskOverTime.length - 1].date : null;
    if (!latest) return [];
    const rows = countryMetrics.filter((m) => m.date === latest);
    return rows.map((m) => ({ name: m.category, risk: m.risk_score ?? 0, events: m.event_count }));
  }, [countryMetrics, riskOverTime]);

  if (!country) {
    return (
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-6 text-center text-slate-400">
        Select a country from the map or risk movers table to see drill-down.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
        <h2 className="mb-3 text-lg font-semibold text-slate-200">Country: {country}</h2>
        <h3 className="mb-2 text-sm font-medium text-slate-400">Risk over time</h3>
        <div className="h-64">
          {riskOverTime.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={riskOverTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
                <Line type="monotone" dataKey="risk" stroke="#38bdf8" name="Risk score" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-slate-500">No time series data</p>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
        <h3 className="mb-2 text-sm font-medium text-slate-400">Category breakdown (latest date)</h3>
        <div className="h-56">
          {categoryBreakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryBreakdown} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={75} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
                <Legend />
                <Bar dataKey="risk" fill="#38bdf8" name="Risk score" radius={[0, 4, 4, 0]} />
                <Bar dataKey="events" fill="#64748b" name="Event count" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-slate-500">No category data</p>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
        <h3 className="mb-2 text-sm font-medium text-slate-400">Recent spikes</h3>
        {countrySpikes.length > 0 ? (
          <ul className="space-y-1 text-sm">
            {countrySpikes.slice(0, 10).map((s) => (
              <li key={s.id} className="flex justify-between text-slate-300">
                <span>{s.date} — {s.category}</span>
                <span>z_used: {s.z_used != null ? s.z_used.toFixed(2) : s.z_score?.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">No spikes for this country</p>
        )}
      </div>
    </div>
  );
}
