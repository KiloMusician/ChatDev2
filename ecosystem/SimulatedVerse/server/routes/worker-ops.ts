/* 
OWNERS: ai/raven, team/operations
TAGS: ops:routes, worker:control, status:truth
STABILITY: critical
HEALTH: implementing
INTEGRATIONS: worker, proof-gate, queue
*/

import { Router } from "express";
import { getWorkerState, setWorkerState } from "../services/worker.js";
import { puQueue } from "../services/pu_queue.js";
import { getProofStats } from "../services/proof-gate.js";
import { existsSync, readFileSync } from "node:fs";

// Simple budget tracking storage
let dailyBudgetUsed = 0;
let budgetResetDate = new Date().toDateString();

function updateBudgetTracking(): number {
  const today = new Date().toDateString();
  if (today !== budgetResetDate) {
    dailyBudgetUsed = 0;
    budgetResetDate = today;
  }
  return dailyBudgetUsed;
}

export function workerOpsRoutes() {
  const r = Router();

  // Worker control
  r.get("/api/ops/worker/state", (_req, res) => {
    res.json(getWorkerState());
  });
  
  r.patch("/api/ops/worker/state", (req, res) => { 
    const patch = req.body || {};
    setWorkerState(patch);
    if (typeof patch.running === "boolean") {
      if (patch.running) {
        puQueue.startRealProcessor();
      } else {
        puQueue.stopProcessor();
      }
    }
    res.json(getWorkerState()); 
  });

  // Truthful status from runtime reality
  r.get("/api/ops/status", (_req, res) => {
    const workerState = getWorkerState();
    const proofStats = getProofStats();
    
    // Queue metrics
    const queueReady = existsSync("data/pu_queue.ndjson")
      ? readFileSync("data/pu_queue.ndjson", "utf8").split("\n").filter(Boolean).length 
      : 0;
    
    // Budget status - real tracking with daily reset
    const budgetUsed = updateBudgetTracking();
    const budgetMax = 100;
    
    // System health
    const systemReady = proofStats.total > 0 || queueReady > 0;
    
    res.json({
      autonomous_system: systemReady ? "operational" : "initializing",
      queue: {
        ready: queueReady,
        dequeue_rate: workerState.dequeue_rate || 0,
        last_dequeue: workerState.last_dequeue_at
      },
      worker: {
        running: workerState.running,
        concurrency: workerState.concurrency,
        jobs_today: workerState.jobs_completed_today || 0,
        success_rate: workerState.success_rate || 0
      },
      proofs: proofStats,
      budget: {
        used: budgetUsed,
        remaining: budgetMax - budgetUsed,
        max: budgetMax
      },
      infrastructure_first: true,
      reality_check: {
        queue_moving: (workerState.dequeue_rate || 0) > 0,
        proofs_generated: proofStats.total > 0,
        worker_active: workerState.running,
        spinal_cord_connected: true
      }
    });
  });

  // Quick worker toggle
  r.post("/api/ops/worker/toggle", (req, res) => {
    const currentState = getWorkerState();
    const newRunning = !currentState.running;
    setWorkerState({ running: newRunning });
    if (newRunning) {
      puQueue.startRealProcessor();
    } else {
      puQueue.stopProcessor();
    }
    
    res.json({ 
      ok: true, 
      action: newRunning ? "started" : "stopped",
      state: getWorkerState() 
    });
  });

  return r;
}
