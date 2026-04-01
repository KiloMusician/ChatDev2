import React, { useEffect, useState } from "react";

type Summary = { files?: number; scanned?: number; ts?: number };

export default function QSAReportPane() {
  const [sum, setSum] = useState<Summary | null>(null);
  const [issues, setIssues] = useState<any[]>([]);
  const [dupes, setDupes] = useState<{ exact?: any[]; near?: any[] }>({});

  useEffect(() => {
    const fetchIt = async () => {
      try {
        const s = await fetch("/reports/qsa/repo_audit.json").then(r=>r.json());
        setSum(s);
      } catch {}
      try {
        const i = await fetch("/reports/qsa/issues.json").then(r=>r.json());
        setIssues(i.slice(0,30));
      } catch {}
      try {
        const d = await fetch("/reports/qsa/dupes.json").then(r=>r.json());
        setDupes({ exact: (d.exact||[]).slice(0,10), near: (d.near||[]).slice(0,10) });
      } catch {}
    };
    fetchIt();
    const t = setInterval(fetchIt, 10000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="rounded-2xl shadow p-4 space-y-3">
      <h3 className="text-lg font-semibold">QSA — Repo Audit</h3>
      {sum ? <p className="text-sm opacity-80">Files: {sum.files} • Scanned: {sum.scanned} • {new Date(sum.ts||0).toLocaleTimeString()}</p>
           : <p className="text-sm opacity-60">No report yet. Run <code>tsx ops/qsa/scan-repo.ts</code></p>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <h4 className="font-medium">Issues (sample)</h4>
          <ul className="text-xs space-y-1">
            {issues.map((x,i)=>(<li key={i}><code>{x.path}</code> {x.hardcoded ? "🔥" : x.placeholders ? "📝" : ""}</li>))}
          </ul>
        </div>
        <div>
          <h4 className="font-medium">Dupes (sample)</h4>
          <div className="text-xs">
            <p>Exact clusters: {dupes.exact?.length ?? 0}</p>
            <p>Near pairs: {dupes.near?.length ?? 0}</p>
          </div>
        </div>
      </div>
    </div>
  );
}