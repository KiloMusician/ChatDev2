// client/src/council/YapPaneProvisioned.tsx
// Read-only YapPane using provisioned state (tripartite architecture)
import React from "react";
import { useProvisionedStateETag } from "../lib/useProvisionedStateETag";
import StatusGrid from "../components/StatusGrid";

export default function YapPaneProvisioned() {
  const { data: s, meta } = useProvisionedStateETag();

  if (!s) {
    return (
      <div className="rounded-2xl shadow p-4 bg-gray-900/20 border border-gray-600/30">
        <h2 className="text-xl font-semibold mb-2 text-green-400">System Dashboard</h2>
        <div className="text-sm text-yellow-700 bg-yellow-900/20 border border-yellow-500/30 p-3 rounded">
          ⏳ Loading system state from provisioner...
          <div className="text-xs mt-1">
            ETag: {meta.etag || "none"} • Last checked: {meta.lastChecked ? new Date(meta.lastChecked).toLocaleTimeString() : "never"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl shadow p-4 bg-gray-900/20 border border-green-400/30">
      <h2 className="text-xl font-semibold mb-2 text-green-400">🏗️ System Dashboard</h2>
      <StatusGrid s={s} />
      
      {/* Recent Activity Summary */}
      <div className="mt-4 p-3 bg-green-400/5 rounded border border-green-400/20">
        <div className="text-sm text-green-300 mb-2">⚡ Recent Activity</div>
        <div className="text-xs space-y-1 text-gray-300">
          <div>Last action: <span className="text-blue-400">{s.recent?.last_action || "—"}</span></div>
          <div>Agent: <span className="text-yellow-400">{s.recent?.last_agent || "—"}</span></div>
          {s.recent?.last_consciousness_task && (
            <div>Consciousness: <span className="text-purple-400">{s.recent.last_consciousness_task}</span></div>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-3 text-xs text-gray-500 border-t border-gray-600/30 pt-2">
        Last updated: {s.timestamp ? new Date(s.timestamp).toLocaleTimeString() : "unknown"} • 
        ETag: {meta.etag || "none"} • 
        Data source: Provisioned JSON (read-only)
      </div>
    </div>
  );
}