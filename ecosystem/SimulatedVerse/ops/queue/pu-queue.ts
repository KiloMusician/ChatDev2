#!/usr/bin/env tsx
/**
 * Minimal, durable PU queue:
 * - Loads tasks from ops/queue/pus.ndjson (one JSON per line)
 * - Persists state to ops/queue/state.json
 * - Processes with p-queue concurrency + backoff
 * - Emits live metrics to /public/system-status.json
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, appendFileSync } from "node:fs";
import { join } from "node:path";
import PQueue from "p-queue";

const ROOT = "ops/queue";
const FILE = join(ROOT, "pus.ndjson");
const STATE = join(ROOT, "state.json");
const PUB = "public/system-status.json";

type PU = { id: string; type: string; priority?: number; payload?: any; status?: "queued"|"running"|"done"|"error"; tries?: number; lastError?: string; };
type State = { completed: number; failed: number; running: number; backlog: number; last?: string; };

mkdirSync(ROOT, { recursive: true });
mkdirSync("public", { recursive: true });
if (!existsSync(FILE)) writeFileSync(FILE, "");
if (!existsSync(STATE)) writeFileSync(STATE, JSON.stringify({ completed:0, failed:0, running:0, backlog:0 }, null, 2));

function readPUs(): PU[] {
  const lines = readFileSync(FILE, "utf-8").split("\n").filter(Boolean);
  return lines.map(l => JSON.parse(l));
}

function loadState(): State { return JSON.parse(readFileSync(STATE, "utf-8")); }
function saveState(s: State) { writeFileSync(STATE, JSON.stringify(s, null, 2)); }
function writeStatus(partial:any) {
  let prev={}; try{ prev = JSON.parse(readFileSync(PUB,"utf-8")); }catch{}
  writeFileSync(PUB, JSON.stringify({ ...prev, pu_queue: partial, timestamp: Date.now() }, null, 2));
}

// Example handlers registry — extend freely
const handlers: Record<string, (pu: PU) => Promise<void>> = {
  "verify:ollama": async () => { await fetch("http://127.0.0.1:11434/api/tags").then(r=>r.text()); },
  "audit:packages": async () => { await import("../pkg-audit.ts"); },
  "refresh:provision": async () => { /* your provisioner write here; or import live fn */ },
  "noop": async () => {}
};

async function processPU(pu: PU) {
  const fn = handlers[pu.type] ?? handlers["noop"];
  await fn(pu);
}

// Priority queue + backoff
const q = new PQueue({ concurrency: 2, autoStart: true, interval: 1000, intervalCap: 10 });

async function main() {
  const all = readPUs();
  const state = loadState();
  const backlog = all.filter(p=>p.status!=="done").length;
  writeStatus({ total: all.length, completed: state.completed, failed: state.failed, next_task: all.find(p=>p.status!=="done")?.type ?? null });

  for (const pu of all) {
    if (pu.status === "done") continue;
    q.add(async () => {
      const st = loadState();
      st.running++; saveState(st);
      try {
        pu.status = "running"; pu.tries = (pu.tries ?? 0) + 1;
        await processPU(pu);
        pu.status = "done";
        const st2 = loadState(); st2.running--; st2.completed++; st2.last = pu.id; st2.backlog = Math.max(0, st2.backlog-1); saveState(st2);
      } catch (e:any) {
        pu.status = "error"; pu.lastError = String(e.message ?? e);
        const st2 = loadState(); st2.running--; st2.failed++; st2.last = pu.id; saveState(st2);
        // naive backoff requeue (max 3 tries)
        if ((pu.tries ?? 0) < 3) {
          setTimeout(()=> q.add(()=> processPU(pu)), 1000 * (pu.tries ?? 1));
        }
      } finally {
        writeStatus({ total: all.length, completed: loadState().completed, failed: loadState().failed, running: loadState().running, next_task: all.find(p=>p.status!=="done")?.type ?? null });
      }
    }, { priority: pu.priority ?? 0 });
  }
}

main().catch(e=>console.error(e));