import React from "react";
import { useProvision } from "../hooks/useProvision";

export const QueueCard = () => {
  const { data } = useProvision();
  const q = data?.pu_queue;
  const oll = data?.ollama;
  return (
    <div className="rounded-xl border p-3 text-sm">
      <div className="font-semibold mb-1">System Status</div>
      <div>Ollama: <span className={oll?.status==="up"?"text-green-600":"text-red-600"}>{oll?.status ?? "unknown"}</span> {oll?.model ? `(${oll.model})` : ""}</div>
      <div>Packages: ok {data?.packages?.ok ?? 0} / {data?.packages?.total ?? 0} | tested ok {data?.packages?.tested_ok ?? 0}</div>
      <div>PU Queue: {q?.completed ?? 0} / {q?.total ?? 0} done | running {q?.running ?? 0} | failed {q?.failed ?? 0}</div>
      <div>Next: {q?.next_task ?? "—"}</div>
      <div className="text-xs text-gray-500 mt-1">Last update: {data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "—"}</div>
    </div>
  );
};