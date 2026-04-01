import React, { useEffect, useState } from "react";

type Growth = { prev:{count:number}, cur:{count:number}, growth:number, perMin:number, alert:string };
export default function RepoHealthPane() {
  const [g, setG] = useState<Growth | null>(null);
  useEffect(() => {
    const fetcher = () => fetch("/reports/repo_growth.json", { cache: "no-store" })
      .then(r => r.ok ? r.json() : null).then(setG).catch(()=>{});
    fetcher(); const id = setInterval(fetcher, 8000); return () => clearInterval(id);
  }, []);
  if (!g) return <div className="text-sm opacity-70">Repo health: loading…</div>;
  const color = g.alert.includes("🚨") ? "text-red-600" : g.alert.includes("⚠️") ? "text-amber-600" : "text-emerald-600";
  return (
    <div className="rounded-xl p-3 border">
      <div className="font-semibold">Repo Health</div>
      <div className={`text-sm ${color}`}>Status: {g.alert}</div>
      <div className="text-xs opacity-70">Files: {g.cur.count} (Δ{g.growth}, ~{g.perMin.toFixed(2)}/min)</div>
      <div className="text-xs opacity-70">Open <code>reports/repo_audit.summary.json</code> for full details</div>
    </div>
  );
}