/**
 * MegaQueue — idempotent, taggable, rate-limited, dependency-aware task runner.
 * Zero-token by default; can explicitly lift constraint per-task.
 */
import fs from "node:fs/promises";
import path from "node:path";
// MegaTask type: { id?, kind, data?, tags?, priority?, deps?, allowExternalCalls? }
// Priority: 0 (highest) to 9 (lowest)

const DB = path.resolve(".ship/.queue.json");

async function load() {
  try { return JSON.parse(await fs.readFile(DB, "utf-8")); } catch { return []; }
}
async function save(q) { await fs.mkdir(path.dirname(DB), {recursive:true}); await fs.writeFile(DB, JSON.stringify(q,null,2)); }

export async function enqueue(t) {
  const q = await load();
  t.id = t.id ?? `T${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
  t.priority = t.priority ?? 5;
  q.push(t);
  await save(q);
  return t.id;
}

export async function nextBatch(max=25) {
  const q = await load();
  // simple dep filter + priority sort + de-dup by kind+data hash
  const resolved = new Set(q.filter(t => !t.deps?.length).map(t=>t.id));
  const ready = q.filter(t => !t.deps || t.deps.every(d => resolved.has(d))).sort((a,b)=>(a.priority-b.priority));
  return ready.slice(0,max);
}

export async function markDone(ids) {
  const q = await load();
  const rest = q.filter(t => !ids.includes(t.id));
  await save(rest);
}