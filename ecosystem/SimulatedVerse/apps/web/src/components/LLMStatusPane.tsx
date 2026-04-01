import React, { useEffect, useState } from "react";

export default function LLMStatusPane() {
  const [status, setStatus] = useState<any>({ ok: false });

  async function refresh() {
    try {
      const response = await fetch("/api/llm/health", {
        cache: "no-store"
      });
      if (response.ok) {
        setStatus(await response.json());
      } else {
        setStatus({ ok: false, reason: "api_error" });
      }
    } catch (e) {
      setStatus({ ok: false, error: String(e) });
    }
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 8000); // poll every 8s
    return () => clearInterval(t);
  }, []);

  return (
    <div className="p-3 rounded-xl bg-zinc-900/40 text-sm">
      <div className="font-semibold mb-2 flex items-center gap-2">
        🧠 LLM Spine
        <span className={`w-2 h-2 rounded-full ${status.ok ? 'bg-green-400' : 'bg-red-400'}`} />
      </div>
      <div className="text-xs space-y-1 opacity-80">
        <div>Ollama: <b className={status.ollama ? 'text-green-400' : 'text-red-400'}>{String(status.ollama)}</b></div>
        <div>OpenAI: <b className={status.openai ? 'text-blue-400' : 'text-gray-400'}>{String(status.openai)}</b></div>
        {status.reason && <div className="text-yellow-400">Issue: {status.reason}</div>}
        {status.error && <div className="text-red-400">Error: {status.error.slice(0,30)}</div>}
      </div>
    </div>
  );
}