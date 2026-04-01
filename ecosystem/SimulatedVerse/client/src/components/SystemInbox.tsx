import React, { useEffect, useState } from "react";
import { POLLING_INTERVALS } from "@/config/polling";

type SpeakMsg = { ts:number; from:string; level?:string; title:string; text:string; tags?:Record<string,any> };

export default function SystemInbox(){
  const [items, setItems] = useState<SpeakMsg[]|null>(null);
  const [reply, setReply] = useState("");
  const [replyTo, setReplyTo] = useState<string>("any");

  const fetchInbox = async () => {
    try {
      const r = await fetch("/inbox.json", { cache:"no-store" });
      if (!r.ok) throw new Error(`${r.status}`);
      setItems(await r.json());
    } catch (e) { /* swallow; show stale */ }
  };

  useEffect(()=>{ fetchInbox(); const t = setInterval(fetchInbox, POLLING_INTERVALS.standard); return ()=>clearInterval(t); },[]);

  async function sendReply(){
    if (!reply.trim()) return;
    const r = await fetch("/api/inbox/reply", { method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ reply, to: replyTo }) });
    if (r.ok) setReply("");
  }

  if (!items) return <div className="p-4 text-sm">Loading messages…</div>;
  return (
    <div className="rounded-2xl shadow p-4 space-y-3">
      <h2 className="text-xl font-semibold">System Inbox</h2>
      <div className="flex gap-2">
        <input className="border rounded px-2 py-1 flex-1" placeholder="Reply to the system…" value={reply} onChange={e=>setReply(e.target.value)} />
        <select className="border rounded px-2 py-1" value={replyTo} onChange={e=>setReplyTo(e.target.value)}>
          <option value="any">Any Agent</option>
          <option value="skeptic">Skeptic</option>
          <option value="raven">Raven</option>
          <option value="mladenc">Mladenč</option>
          <option value="librarian">Librarian</option>
          <option value="artificer">Artificer</option>
          <option value="alchemist">Alchemist</option>
          <option value="protagonist">Protagonist</option>
          <option value="culture-ship">Culture-Ship</option>
        </select>
        <button className="border rounded px-3 py-1" onClick={sendReply}>Send</button>
      </div>
      <div className="max-h-96 overflow-auto space-y-2 text-sm">
        {items.map((m,i)=>(
          <div key={i} className="border rounded p-2">
            <div className="text-xs opacity-70">{new Date(m.ts).toLocaleString()} • {m.from} • {m.level ?? "info"}</div>
            <div className="font-semibold">{m.title}</div>
            <div className="whitespace-pre-wrap">{m.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
