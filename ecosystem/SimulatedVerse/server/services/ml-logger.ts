import fs from "node:fs";
import path from "node:path";

const TRACE_DIR = "ml/data/traces";
fs.mkdirSync(TRACE_DIR, { recursive: true });

export function logPUEvent(pu: any, accepted: boolean) {
  const line = JSON.stringify({
    kind: "PU",
    ts: Date.now(),
    title: pu.title, 
    desc: pu.desc,
    priority: pu.priority, 
    type: pu.type,
    accepted
  }) + "\n";
  
  const dateString = new Date().toISOString().slice(0,10);
  const filePath = path.join(TRACE_DIR, `${dateString}.jsonl`);
  
  fs.appendFile(filePath, line, (err) => {
    if (err) {
      console.warn('[ML-LOGGER] Failed to log PU event:', err);
    }
  });
}

export function logUserInteraction(interaction: {
  type: string;
  target: string;
  outcome: string;
  metadata?: any;
}) {
  const line = JSON.stringify({
    kind: "INTERACTION",
    ts: Date.now(),
    ...interaction
  }) + "\n";
  
  const dateString = new Date().toISOString().slice(0,10);
  const filePath = path.join(TRACE_DIR, `${dateString}.jsonl`);
  
  fs.appendFile(filePath, line, (err) => {
    if (err) {
      console.warn('[ML-LOGGER] Failed to log interaction:', err);
    }
  });
}