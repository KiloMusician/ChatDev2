// client/src/components/OpsPane.tsx
// Ops monitoring pane - shows chug system reports in real-time
import React, { useEffect, useState } from "react";
import { safeMap } from "@/lib/guardedOps";
import { POLLING_INTERVALS } from "@/config/polling";

type ChugReport = {
  timestamp: number;
  iteration: number;
  ui_assumption: string;
  checks: {
    typescript: { ok: boolean; errors?: string[] };
    eslint: { ok: boolean; warnings?: string[] };
    map_footguns: { count: number; files: Array<{ file: string; mapLines: Array<{ line: string; num: number }> }> };
    routes: { ok: boolean; found?: string[]; missing?: string[]; reason?: string };
    consciousness?: { ok: boolean; issue?: string; details?: string[] };
  };
  duplicates: {
    count: number;
    details: Array<{ hash: string; files: string[]; core: string; size: number }>;
    alias_suggestions: Array<{ core: string; duplicate: string; suggestedAlias: string; strategy: string }>;
  };
  next_actions: string[];
};

type UnstickStatus = {
  timestamp: number;
  iteration: number;
  last_result: {
    rebuilt: boolean;
    reason?: string;
    error?: string;
  };
  watching: string;
  target: string;
};

export default function OpsPane() {
  const [chugReport, setChugReport] = useState<ChugReport | null>(null);
  const [unstickStatus, setUnstickStatus] = useState<UnstickStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    
    const fetchReports = async () => {
      try {
        // Fetch chug report
        const chugRes = await fetch("/ops-report/report.json", { cache: "no-store" });
        if (chugRes.ok && alive) {
          const chugData = await chugRes.json();
          setChugReport(chugData);
        }
        
        // Fetch unstick status
        const unstickRes = await fetch("/unstick-status.json", { cache: "no-store" });
        if (unstickRes.ok && alive) {
          const unstickData = await unstickRes.json();
          setUnstickStatus(unstickData);
        }
        
        setError(null);
      } catch (e: any) {
        if (alive) {
          setError(String(e?.message || e));
        }
      }
    };

    fetchReports();
    const interval = setInterval(fetchReports, POLLING_INTERVALS.critical);
    
    return () => { 
      alive = false; 
      clearInterval(interval); 
    };
  }, []);

  if (error && !chugReport) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 p-4">
        <div className="text-red-800 dark:text-red-200">
          📡 Ops reports not ready: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg shadow-lg bg-white dark:bg-gray-800 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          🚀 Chug Mode Status
        </h2>
        {chugReport && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Iteration {chugReport.iteration} • {new Date(chugReport.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* System Health Checks */}
      {chugReport && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatusBadge 
            ok={chugReport.checks.typescript?.ok} 
            label="TypeScript" 
            detail={chugReport.checks.typescript?.errors?.[0]}
          />
          <StatusBadge 
            ok={chugReport.checks.eslint?.ok} 
            label="ESLint" 
            detail={chugReport.checks.eslint?.warnings?.[0]}
          />
          <StatusBadge 
            ok={chugReport.checks.map_footguns.count === 0} 
            label=".map Guards" 
            detail={`${chugReport.checks.map_footguns.count} footguns`}
          />
          <StatusBadge 
            ok={chugReport.checks.routes?.ok} 
            label="Routes" 
            detail={chugReport.checks.routes?.found?.join(", ") || chugReport.checks.routes?.reason}
          />
        </div>
      )}

      {/* UI Build Status */}
      {unstickStatus && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-gray-900 dark:text-white">UI Build Status</h3>
            <span className="text-xs text-gray-500">
              Iteration {unstickStatus.iteration}
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-600 dark:text-gray-300">Watching:</div>
              <div className="font-mono text-xs">{unstickStatus.watching}</div>
            </div>
            <div>
              <div className="text-gray-600 dark:text-gray-300">Status:</div>
              <div className={`font-medium ${
                unstickStatus.last_result.rebuilt ? 'text-green-600 dark:text-green-400' :
                unstickStatus.last_result.error ? 'text-red-600 dark:text-red-400' :
                'text-gray-600 dark:text-gray-400'
              }`}>
                {unstickStatus.last_result.rebuilt ? '✅ Rebuilt' :
                 unstickStatus.last_result.error ? '❌ Build failed' :
                 unstickStatus.last_result.reason || 'Monitoring'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Map Footguns */}
      {chugReport && chugReport.checks.map_footguns.count > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h3 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">
            🚨 Map Footguns Detected ({chugReport.checks.map_footguns.count})
          </h3>
          <div className="space-y-2 max-h-32 overflow-auto">
            {safeMap(chugReport.checks.map_footguns.files.slice(0, 3), (fileInfo, i) => (
              <div key={i} className="text-sm">
                <div className="font-mono text-xs text-yellow-700 dark:text-yellow-300">
                  {fileInfo.file}
                </div>
                {safeMap(fileInfo.mapLines.slice(0, 2), (mapLine, j) => (
                  <div key={j} className="text-xs text-yellow-600 dark:text-yellow-400 ml-4">
                    Line {mapLine.num}: {mapLine.line.slice(0, 60)}...
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="text-xs text-yellow-700 dark:text-yellow-300 mt-2">
            💡 Use safeMap() from @/lib/guardedOps to prevent m.map errors
          </div>
        </div>
      )}

      {/* Duplicates */}
      {chugReport && chugReport.duplicates.count > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
            📦 Duplicate Files ({chugReport.duplicates.count})
          </h3>
          <div className="space-y-2 max-h-32 overflow-auto">
            {safeMap(chugReport.duplicates.details.slice(0, 3), (dup, i) => (
              <div key={i} className="text-sm">
                <div className="font-medium text-blue-700 dark:text-blue-300">
                  Core: {dup.core}
                </div>
                <div className="text-xs text-blue-600 dark:text-blue-400 ml-4">
                  Duplicates: {dup.files.filter(f => f !== dup.core).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Actions */}
      {chugReport && chugReport.next_actions.length > 0 && (
        <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-2">🎯 Next Actions</h3>
          <ul className="space-y-1">
            {safeMap(chugReport.next_actions.slice(0, 5), (action, i) => (
              <li key={i} className="text-sm text-gray-700 dark:text-gray-300">
                • {action}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600">
        <span>{chugReport?.ui_assumption || "UI status unknown"}</span>
        <span id="build-id" title="Click to refresh">
          Build loading...
        </span>
      </div>
    </div>
  );
}

function StatusBadge({ ok, label, detail }: { ok?: boolean; label: string; detail?: string }) {
  return (
    <div className={`px-3 py-2 rounded-lg text-center border transition-colors ${
      ok === true ? 
        "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200" :
      ok === false ?
        "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200" :
        "bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-200"
    }`}>
      <div className="font-medium text-sm">{label}</div>
      {detail && (
        <div className="text-xs opacity-75 mt-1" title={detail}>
          {detail.length > 20 ? detail.slice(0, 20) + "..." : detail}
        </div>
      )}
    </div>
  );
}
