import React, { useEffect, useState } from "react";

export default function SageConsole() {
  const [ts, setTs] = useState<number>(Date.now());
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    const i = setInterval(async () => {
      setTs(Date.now());
      try {
        const r = await fetch("/llm/health").then(r=>r.json());
        setHealth(r);
      } catch { setHealth({ ok:false }); }
    }, 8000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="rounded-2xl border p-3 text-sm space-y-1">
      <div className="font-semibold">🧙 Wise Sage</div>
      <div>Tick: {new Date(ts).toLocaleTimeString()}</div>
      <div>LLM: {health?.ok ? "OK" : "DEGRADED"} {health?.ollama ? "• Ollama" : ""} {health?.openai ? "• OpenAI" : ""}</div>
      <div className="opacity-70">SAGE auto-nudges when UI is stale, PUs stall, or LLM fails.</div>
    </div>
  );
}