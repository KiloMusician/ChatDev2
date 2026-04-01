// server/router/raven.ts
import { Router } from "express";
import fs from "node:fs";
import path from "node:path";
import { queueRavenJobs, leaseRavenJobs, ackRavenJob, ravenCaps, getRavenStatus } from "../services/raven/core.js";

// ── Boot: load jobs seeded while server was offline ──────────────────────────
const PENDING_FILE = path.join(process.cwd(), "ops/queue/raven-pending.ndjson");
if (fs.existsSync(PENDING_FILE)) {
  try {
    const lines = fs.readFileSync(PENDING_FILE, "utf-8").split("\n").filter(Boolean);
    const jobs = lines.map(l => JSON.parse(l));
    if (jobs.length) {
      queueRavenJobs(jobs);
      fs.unlinkSync(PENDING_FILE);
      console.log(`[Raven] 📥 Loaded ${jobs.length} pending jobs from disk`);
    }
  } catch (e) {
    console.warn("[Raven] Failed to load pending jobs:", e);
  }
}

// ── Budget helper (reads ops/state/budget.json if present) ───────────────────
function getBudgetConsumption(): number {
  try {
    const budgetPath = path.join(process.cwd(), "data/state/budget.json");
    if (fs.existsSync(budgetPath)) {
      const b = JSON.parse(fs.readFileSync(budgetPath, "utf-8"));
      return b.consumed || 0;
    }
  } catch { /* ignore */ }
  return 0;
}

export const raven = Router();

// ── Admin guard — strips inline dotenv comments and whitespace ────────────────
const adminGuard = (req: any, res: any, next: any) => {
  const token = (req.headers.authorization || "").replace(/^Bearer\s+/, "").trim();
  const expected = ((process.env.ADMIN_TOKEN || "").split("#")[0] ?? "").trim();
  if (!token || !expected || token !== expected) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
};

// ── GET /api/raven/health ─────────────────────────────────────────────────────
raven.get("/health", (_req, res) => {
  res.json({
    ok: true,
    caps: {
      local: !!ravenCaps.localOllamaUrl,
      paid: ravenCaps.allowPaidFallback,
    },
    budget: {
      allowance: ravenCaps.dailyAllowance,
      consumed: getBudgetConsumption(),
    },
  });
});

// ── GET /api/raven/status — live queue snapshot ───────────────────────────────
raven.get("/status", (_req, res) => {
  res.json(getRavenStatus());
});

// ── POST /api/raven/queue — seed jobs ────────────────────────────────────────
raven.post("/queue", adminGuard, (req, res) => {
  const arr = Array.isArray(req.body) ? req.body : [req.body];
  const r = queueRavenJobs(arr);
  res.json({ ok: true, ...r });
});

// ── POST /api/raven/lease — worker pulls next batch ──────────────────────────
raven.post("/lease", adminGuard, (req, res) => {
  const n = Number(req.query.n || 3);
  res.json(leaseRavenJobs(n));
});

// ── POST /api/raven/ack — worker reports result ───────────────────────────────
raven.post("/ack", adminGuard, (req, res) => {
  const { leaseId, result } = req.body || {};
  res.json(ackRavenJob(String(leaseId), result));
});
