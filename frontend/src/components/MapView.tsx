import { useMemo } from 'react';
import type { Metric } from '../api';

// Build country -> max risk for latest dates from metrics
function countryRiskFromMetrics(metrics: Metric[]): Array<{ country: string; risk: number }> {
  const byCountry = new Map<string, number>();
  const withScore = metrics.filter((m) => m.risk_score != null && m.risk_score > 0);
  for (const m of withScore) {
    const cur = byCountry.get(m.country);
    const score = m.risk_score ?? 0;
    if (cur == null || score > cur) byCountry.set(m.country, score);
  }
  return Array.from(byCountry.entries())
    .map(([country, risk]) => ({ country, risk }))
    .sort((a, b) => b.risk - a.risk);
}

function riskColor(score: number): string {
  if (score >= 70) return 'bg-red-600/80 hover:bg-red-500';
  if (score >= 40) return 'bg-amber-600/80 hover:bg-amber-500';
  if (score >= 20) return 'bg-yellow-600/80 hover:bg-yellow-500';
  return 'bg-emerald-600/80 hover:bg-emerald-500';
}

interface MapViewProps {
  metrics: Metric[];
  onSelectCountry: (country: string) => void;
}

export default function MapView({ metrics, onSelectCountry }: MapViewProps) {
  const countryRisk = useMemo(() => countryRiskFromMetrics(metrics), [metrics]);

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-200">Global risk hotspots</h2>
      <p className="mb-4 text-sm text-slate-400">
        Click a country to drill down. Color = max risk score (green &lt; 20, yellow &lt; 40, orange &lt; 70, red ≥ 70).
      </p>
      <div className="flex flex-wrap gap-2">
        {countryRisk.map(({ country, risk }) => (
          <button
            key={country}
            type="button"
            onClick={() => onSelectCountry(country)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium text-white transition ${riskColor(risk)}`}
          >
            {country} {risk.toFixed(0)}
          </button>
        ))}
      </div>
      {countryRisk.length === 0 && (
        <p className="text-sm text-slate-500">No risk data yet. Run Day 2 pipeline and ensure metrics have risk_score.</p>
      )}
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
        <span className="rounded bg-emerald-900/50 px-2 py-0.5 text-emerald-300">Low (&lt;20)</span>
        <span className="rounded bg-amber-900/50 px-2 py-0.5 text-amber-300">Medium (20–40)</span>
        <span className="rounded bg-orange-900/50 px-2 py-0.5 text-orange-300">High (40–70)</span>
        <span className="rounded bg-red-900/50 px-2 py-0.5 text-red-300">Critical (≥70)</span>
      </div>
    </div>
  );
}
