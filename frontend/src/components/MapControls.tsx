import { useMapStore } from '../stores/map-store';

export default function MapControls() {
  const {
    showHeatmap,
    showClusters,
    showMilitaryBases,
    setShowHeatmap,
    setShowClusters,
    setShowMilitaryBases,
  } = useMapStore();

  return (
    <div className="absolute right-3 top-3 z-10 flex flex-col gap-2 rounded-lg border border-slate-600 bg-slate-900/90 px-3 py-2 shadow-lg">
      <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-200">
        <input
          type="checkbox"
          checked={showClusters}
          onChange={(e) => setShowClusters(e.target.checked)}
          className="rounded"
        />
        Clusters
      </label>
      <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-200">
        <input
          type="checkbox"
          checked={showHeatmap}
          onChange={(e) => setShowHeatmap(e.target.checked)}
          className="rounded"
        />
        Heatmap
      </label>
      <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-200">
        <input
          type="checkbox"
          checked={showMilitaryBases}
          onChange={(e) => setShowMilitaryBases(e.target.checked)}
          className="rounded"
        />
        Military bases
      </label>
    </div>
  );
}
