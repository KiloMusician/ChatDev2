/* 
OWNERS: ai/raven, team/infrastructure
TAGS: ops:worker, queue:processor, execution:loop
STABILITY: critical
HEALTH: implementing
INTEGRATIONS: ops/queue, agent-gateway, proof-gate
*/

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import fetch from "node-fetch";
import { log } from "./log.js";

type WorkerState = {
  running: boolean;
  concurrency: number;
  last_dequeue_at?: string;
  dequeue_rate?: number;
  jobs_completed_today?: number;
  success_rate?: number;
};

const STATE_FILE = "ops/worker/state.json";
const QUEUE_FILE = "data/pu_queue.ndjson";

let state: WorkerState = { 
  running: false, // THEATER PERMANENTLY DISABLED - sophisticated fake progress eliminated
  concurrency: Number(process.env.PU_CONCURRENCY || 2),
  jobs_completed_today: 0,
  success_rate: 0
};

function saveState() {
  mkdirSync("ops/worker", { recursive: true });
  writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

export function getWorkerState(): WorkerState {
  if (existsSync(STATE_FILE)) {
    try { 
      const loaded = JSON.parse(readFileSync(STATE_FILE, "utf8"));
      state = { ...state, ...loaded };
    } catch {
      // Use defaults
    }
  }
  return state;
}

export function setWorkerState(patch: Partial<WorkerState>) {
  state = { ...getWorkerState(), ...patch };
  saveState();
  log.info(state, "[WORKER] State updated");
}

async function dequeueOne() {
  if (!existsSync(QUEUE_FILE)) return null;
  
  try {
    const content = readFileSync(QUEUE_FILE, "utf8");
    const lines = content.split("\n").filter(Boolean);
    if (lines.length === 0) return null;
    
    const firstLine = lines[0];
    if (!firstLine) return null;
    const head = JSON.parse(firstLine);
    // Remove processed item from queue  
    const remainingContent = lines.slice(1).join("\n");
    writeFileSync(QUEUE_FILE, remainingContent + (remainingContent ? "\n" : ""));
    
    state.last_dequeue_at = new Date().toISOString();
    state.dequeue_rate = (state.dequeue_rate || 0) * 0.9 + 0.1; // Moving average
    saveState();
    
    return head;
  } catch (error) {
    log.error({ error }, "[WORKER] Dequeue error");
    return null;
  }
}

export async function callAgent(agent: string, job: any): Promise<any> {
  const body = {
    input: job.input || { goal: job.summary || job.title || "unspecified task" },
    proof_kind: job.proof?.kind || "file",
    expect: job.expect || {}
  };
  
  try {
    const resp = await fetch(`http://127.0.0.1:5000/api/agent/${agent}/execute`, {
      method: "POST", 
      headers: { "content-type": "application/json" }, 
      body: JSON.stringify(body)
    });
    
    return await resp.json();
  } catch (error) {
    return { ok: false, error: String(error) };
  }
}

async function ingestProof(jobId: string, agent: string, artifactPath: string) {
  try {
    const resp = await fetch("http://127.0.0.1:5000/api/proofs/ingest", {
      method: "POST", 
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ 
        job_id: jobId, 
        agent, 
        artifact: { path: artifactPath } 
      })
    });
    
    return await resp.json();
  } catch (error) {
    log.error({ error }, "[WORKER] Proof ingest failed");
    return { ok: false, error: String(error) };
  }
}

export async function workerLoop() {
  log.warn({}, "[WORKER] Worker loop disabled to prevent server blocking");
  // THEATER DISABLED: while(true) loop blocks server event loop
  return;
}

// THEATER DISABLED - Watchdog eliminated 
export function startWatchdog() {
  log.warn({}, "[WATCHDOG] Auto-restart watchdog eliminated");
  return;
}
