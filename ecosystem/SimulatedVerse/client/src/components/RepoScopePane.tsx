import React from "react";

export function RepoScopePane({ stats }: { stats?: { total:number; signal:number; noise:number; growthPerMin:number } }) {
  const s = stats ?? { total: 0, signal: 0, noise: 0, growthPerMin: 0 };
  return (
    <div className="p-3 rounded-xl border">
      <div className="text-sm opacity-70">Repo Scope</div>
      <div className="text-xl font-semibold">{s.signal} files (signal)</div>
      <div className="text-sm">Noise fenced: {s.noise} / Total: {s.total}</div>
      <div className={`text-sm mt-2 ${s.growthPerMin > 25 ? 'text-red-600' : 'text-emerald-600'}`}>
        Growth: {s.growthPerMin.toFixed(2)}/min
      </div>
      <div className="text-xs opacity-60 mt-2">Source: ops/repo-targets.yaml · git tracked</div>
    </div>
  );
}