import React, { useEffect, useState } from "react";

type AgentsRes = { agents: string[] };
type TurnReq = { agent: string; input: string; json?: boolean };
type TurnRes = { backend: "ollama" | "openai"; output: string };

const CHATDEV_URL = (import.meta as any).env?.VITE_CHATDEV_URL || "http://127.0.0.1:4466";

export default function ChatDevPane() {
  const [agents, setAgents] = useState<string[]>([]);
  const [agent, setAgent] = useState<string>("");
  const [input, setInput] = useState("");
  const [resp, setResp] = useState<TurnRes | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${CHATDEV_URL}/chatdev/agents`).then(r=>r.json()).then((j:AgentsRes)=>{
      setAgents(j.agents || []); if (j.agents?.length) setAgent(j.agents[0]);
    }).catch(() => setErr("ChatDev unreachable"));
  }, []);

  async function send() {
    if (!input.trim()) return;
    setLoading(true);
    setErr(null); 
    setResp(null);
    try {
      const r = await fetch(`${CHATDEV_URL}/chatdev/turn`, {
        method:"POST",
        headers:{"content-type":"application/json"},
        body: JSON.stringify({ agent, input } as TurnReq)
      });
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json() as TurnRes;
      setResp(j);
      setInput(""); // Clear input after successful response
    } catch (e:any) {
      setErr(String(e?.message||e));
    }
    setLoading(false);
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      send();
    }
  };

  return (
    <div className="p-4 rounded-xl bg-zinc-900/40 space-y-3">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold text-white">🧠 ChatDev Console</h2>
        <div className={`w-2 h-2 rounded-full ${agents.length ? 'bg-green-400' : 'bg-red-400'}`} />
      </div>
      
      <div className="flex items-center gap-2">
        <label className="text-sm text-zinc-300">Agent</label>
        <select 
          className="bg-zinc-800 border border-zinc-600 rounded px-2 py-1 text-white text-sm"
          value={agent} 
          onChange={e=>setAgent(e.target.value)}
          disabled={!agents.length}
        >
          {agents.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <span className="text-xs text-zinc-500">({agents.length} available)</span>
      </div>
      
      <textarea
        className="w-full bg-zinc-800 border border-zinc-600 rounded p-2 h-24 text-white text-sm resize-none"
        placeholder="Ask the agent to perform an action… (Ctrl+Enter to send)"
        value={input}
        onChange={e=>setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={loading || !agents.length}
      />
      
      <button 
        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
          loading ? 'bg-zinc-600 text-zinc-400 cursor-not-allowed' : 
          'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
        onClick={send}
        disabled={loading || !agents.length || !input.trim()}
      >
        {loading ? 'Processing...' : 'Send'}
      </button>
      
      {resp && (
        <div className="text-sm border border-zinc-600 rounded p-3">
          <div className="flex items-center gap-2 text-zinc-400 mb-2">
            <span>Backend:</span>
            <span className={`px-1 rounded text-xs ${
              resp.backend === 'ollama' ? 'bg-green-900 text-green-300' : 'bg-blue-900 text-blue-300'
            }`}>
              {resp.backend}
            </span>
          </div>
          <pre className="whitespace-pre-wrap text-zinc-200 text-xs bg-zinc-800 p-2 rounded overflow-auto max-h-48">
            {resp.output}
          </pre>
        </div>
      )}
      
      {err && (
        <div className="text-red-400 text-sm bg-red-900/20 border border-red-800 rounded p-2">
          ⚠️ {err}
        </div>
      )}
    </div>
  );
}