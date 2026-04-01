// server/services/raven/core.ts
import { randomUUID } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

export type RavenJob = {
  id: string;
  kind: "plan" | "refactor" | "doc" | "test" | "migrate" | "balance" | "ops" | "fix";
  title: string;
  files?: Array<{ path: string; content: string; mode?: "100644" | "100755" }>;
  meta?: Record<string, any>;
  budget?: { tokens?: number; seconds?: number };
  priority?: "low" | "normal" | "high" | "critical";
};

export type RavenResult = {
  id: string; ok: boolean; logs?: string; diffSummary?: string; prUrl?: string; cost?: number;
};

type Lease = {
  leaseId: string;
  items: RavenJob[];
  remaining: number;        // ← was missing — caused --undefined = NaN
  expiresAt: number;
};

const q: RavenJob[] = [];
const inFlight = new Map<string, Lease>();
const QUEUE_PERSIST_PATH = path.join(process.cwd(), "ops/queue/raven-queue.ndjson");
const LEASE_TTL_MS = 120_000; // 2 minutes

// ── Boot: restore queue from disk if server restarted mid-run ────────────────
(function restorePersistedQueue() {
  try {
    if (fs.existsSync(QUEUE_PERSIST_PATH)) {
      const jobs: RavenJob[] = fs.readFileSync(QUEUE_PERSIST_PATH, "utf-8")
        .split("\n").filter(Boolean).map(l => JSON.parse(l));
      q.push(...jobs);
      if (jobs.length) console.log(`[Raven] 🔄 Restored ${jobs.length} jobs from persisted queue`);
    }
  } catch { /* non-fatal */ }
})();

// ── Expiry watchdog: re-queue expired leases every 30s ───────────────────────
setInterval(() => {
  const now = Date.now();
  for (const [leaseId, lease] of inFlight) {
    if (now > lease.expiresAt) {
      console.log(`[Raven] ⏰ Lease ${leaseId} expired — re-queuing ${lease.items.length} jobs`);
      // Re-insert at front so high-priority work isn't lost
      q.unshift(...lease.items);
      inFlight.delete(leaseId);
    }
  }
}, 30_000).unref(); // .unref() so it doesn't prevent process exit

// ── SIGTERM / SIGINT: flush queue to disk before shutdown ────────────────────
function persistQueueToDisk() {
  try {
    const all = [...q, ...Array.from(inFlight.values()).flatMap(l => l.items)];
    if (all.length === 0) { try { fs.unlinkSync(QUEUE_PERSIST_PATH); } catch {} return; }
    fs.mkdirSync(path.dirname(QUEUE_PERSIST_PATH), { recursive: true });
    fs.writeFileSync(QUEUE_PERSIST_PATH, all.map(j => JSON.stringify(j)).join("\n") + "\n");
    console.log(`[Raven] 💾 Persisted ${all.length} jobs to disk`);
  } catch (e) { console.warn("[Raven] Failed to persist queue:", e); }
}
process.on("SIGTERM", () => { persistQueueToDisk(); process.exit(0); });
process.on("SIGINT",  () => { persistQueueToDisk(); process.exit(0); });

// ── Public API ────────────────────────────────────────────────────────────────

export function queueRavenJobs(jobs: RavenJob[]) {
  for (const j of jobs) {
    const id = j.id || randomUUID();
    // dedup by id
    if (!q.find(e => e.id === id) && !Array.from(inFlight.values()).some(l => l.items.find(i => i.id === id))) {
      q.push({ ...j, id, priority: j.priority || "normal" });
    }
  }
  return { queued: jobs.length, size: q.length };
}

export function leaseRavenJobs(n = 3): Lease {
  if (q.length === 0) {
    // Return empty lease rather than crashing
    return { leaseId: randomUUID(), items: [], remaining: 0, expiresAt: Date.now() };
  }
  const count = Math.max(1, Math.min(n, q.length));
  const items = q.splice(0, count);
  const lease: Lease = {
    leaseId: randomUUID(),
    items,
    remaining: items.length,   // ← properly initialised
    expiresAt: Date.now() + LEASE_TTL_MS,
  };
  inFlight.set(lease.leaseId, lease);
  return lease;
}

export function ackRavenJob(leaseId: string, result: RavenResult) {
  const lease = inFlight.get(leaseId);
  if (!lease) return { ok: false, error: "lease-not-found" };

  lease.remaining = Math.max(0, lease.remaining - 1);

  try {
    console.log(`[Raven] 📋 Job completed: ${result.id} (${result.ok ? "success" : "failed"})`);
    if (result.logs) console.log(`[Raven] 📝 ${result.logs.slice(0, 200)}`);

    // Emit to event bus (optional, non-blocking)
    import("../../services/msg.js").then(({ emitMsg }) =>
      emitMsg({ rune: "RAVEN_JOB_COMPLETE", data: { jobId: result.id, success: result.ok } })
    ).catch(() => {});
  } catch { /* non-fatal logging failure */ }

  if (lease.remaining === 0) inFlight.delete(leaseId);

  return { ok: true, result };
}

/** Read-only snapshot of live queue state — safe to call from router */
export function getRavenStatus() {
  return {
    queue_depth: q.length,
    in_flight: inFlight.size,
    in_flight_jobs: Array.from(inFlight.values()).reduce((s, l) => s + l.remaining, 0),
    raven_enabled: ["1","true","yes"].includes(
      ((process.env.RAVEN_ENABLED || "").split("#")[0] ?? "").trim().toLowerCase()
    ),
  };
}

// simple caps (extend: real budget/entropy gates)
export const ravenCaps = {
  allowPaidFallback: process.env.PAID_FALLBACK === "1",
  localOllamaUrl: process.env.OLLAMA_URL || "",
  dailyAllowance: Number(process.env.DAILY_ALLOWANCE || 5000),
};
