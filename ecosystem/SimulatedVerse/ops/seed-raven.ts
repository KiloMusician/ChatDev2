#!/usr/bin/env tsx
/**
 * ops/seed-raven.ts — ΞNuSyQ RAVEN Job Seeder
 * Reads all backlog sources and POSTs jobs to /api/raven/queue
 * Sources: next_steps.todo.ndjson, goals.yaml horizons, ops/proofs gaps, scan results
 * Run: npx tsx ops/seed-raven.ts
 *    or: npm run seed
 */
import fs from "node:fs";
import path from "node:path";

const BASE  = process.env.BASE_URL    || "http://127.0.0.1:5000";
const TOKEN = process.env.ADMIN_TOKEN || "";
const ROOT  = process.cwd();

type RavenJob = {
  id?: string; kind: string; title: string; priority?: string; meta?: any;
};

const jobs: RavenJob[] = [];

function addJob(j: RavenJob) {
  // dedup by title
  if (!jobs.find(e => e.title === j.title)) jobs.push(j);
}

// ── Source 1: next_steps.todo.ndjson ────────────────────────────────────────
const nextStepsFile = path.join(ROOT, "reports/next_steps.todo.ndjson");
if (fs.existsSync(nextStepsFile)) {
  const lines = fs.readFileSync(nextStepsFile, "utf-8").split("\n").filter(Boolean);
  for (const l of lines) {
    try {
      const t: any = JSON.parse(l);
      addJob({
        kind: "plan",
        title: t.task || t.title || String(l).slice(0, 80),
        priority: t.priority === 1 ? "critical" : t.priority === 2 ? "high" : "normal",
        meta: { source: "next_steps", owner: t.owner, proof: t.proof }
      });
    } catch { /* skip malformed */ }
  }
  console.log(`[seed] next_steps: ${lines.length} tasks loaded`);
}

// ── Source 2: reports/backlog_synthesis.json ─────────────────────────────────
const backlogFile = path.join(ROOT, "reports/backlog_synthesis.json");
if (fs.existsSync(backlogFile)) {
  try {
    const b = JSON.parse(fs.readFileSync(backlogFile, "utf-8"));
    (b.tasks || []).forEach((t: any) => addJob({
      kind: "ops",
      title: t.task || t.title || JSON.stringify(t).slice(0,80),
      priority: "normal",
      meta: { source: "backlog_synthesis", owner: t.owner }
    }));
    console.log(`[seed] backlog_synthesis: ${(b.tasks||[]).length} tasks`);
  } catch { /* skip */ }
}

// ── Source 3: ops/goals.yaml horizon tasks ───────────────────────────────────
const goalsFile = path.join(ROOT, "ops/goals.yaml");
if (fs.existsSync(goalsFile)) {
  const raw = fs.readFileSync(goalsFile, "utf-8");
  const ids = [...raw.matchAll(/id: "([^"]+)"/g)].map(m => m[1]);
  const titles = [...raw.matchAll(/title: "([^"]+)"/g)].map(m => m[1]);
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i], title = titles[i] || ids[i];
    // Skip already-gated ones (st.001, st.003 are done)
    if (["st.001", "st.003"].some(done => id.startsWith(done))) continue;
    addJob({
      id: `raven.goal.${id}`,
      kind: "plan",
      title: `Goal: ${title}`,
      priority: id.startsWith("st.") ? "high" : id.startsWith("mt.") ? "normal" : "low",
      meta: { source: "goals.yaml", goal_id: id }
    });
  }
  console.log(`[seed] goals.yaml: ${ids.length} goals processed`);
}

// ── Source 4: TypeScript files with FIXME/TODO comments ─────────────────────
// Already clean per theater audit — skip to avoid false positives

// ── Source 5: Reports gap analysis ──────────────────────────────────────────
const requiredReports = [
  { file: "reports/autonomy_metrics.json",  title: "Generate autonomy metrics report", kind: "ops" },
  { file: "reports/uptime_log.json",        title: "Generate uptime log",             kind: "ops" },
  { file: "reports/agent_productivity.json",title: "Measure agent productivity (mt.011)", kind: "ops" },
  { file: "reports/godot_bridge_status.json",title: "Check Godot bridge status",      kind: "ops" },
  { file: "reports/ui_console.ndjson",      title: "Collect UI console errors",       kind: "ops" },
];
for (const r of requiredReports) {
  const p = path.join(ROOT, r.file);
  if (!fs.existsSync(p)) {
    addJob({ kind: r.kind, title: r.title, priority: "normal",
             meta: { source: "reports_gap", target_file: r.file } });
  }
}

// ── Source 6: Known open issues from culture_ship memory ────────────────────
const knownTasks = [
  { title: "Wire ops/autonomous-loop.js imports (councilBusShim, zeta-driver)",   kind: "fix",  priority: "high"  },
  { title: "Enable database persistence (DATABASE_URL config + migration)",         kind: "plan", priority: "high"  },
  { title: "Wire heartbeat.ts councilBus to event bus",                            kind: "fix",  priority: "normal"},
  { title: "Add RAVEN job persistence (persist queue to disk on shutdown)",         kind: "refactor", priority: "normal" },
  { title: "Wire mt.011 agent productivity metrics to reports/agent_productivity.json", kind: "ops", priority: "normal" },
  { title: "Reduce ESLint no-console warnings by adding logger abstraction",        kind: "refactor", priority: "low" },
  { title: "Add /api/raven/status endpoint showing queue depth",                   kind: "fix",  priority: "normal"},
  { title: "Wire ops/chug-runner watchdogs to seed RAVEN on stagnation",           kind: "fix",  priority: "normal"},
];
knownTasks.forEach(t => addJob({ ...t, meta: { source: "known_tasks" } }));

// ── Emit ────────────────────────────────────────────────────────────────────
console.log(`\n[seed] Total jobs to queue: ${jobs.length}`);

async function seed() {
  let ok = 0, fail = 0;
  try {
    const r = await fetch(`${BASE}/api/raven/queue`, {
      method: "POST",
      headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify(jobs),
    });
    if (r.ok) {
      const d: any = await r.json();
      console.log(`[seed] ✅ Queued ${d.queued} jobs — queue size: ${d.size}`);
      ok = d.queued;
    } else {
      // Non-OK (wrong server / route missing) → fall back to disk
      console.warn(`[seed] ⚠  Server returned ${r.status} — falling back to disk`);
      const pending = path.join(ROOT, "ops/queue/raven-pending.ndjson");
      fs.mkdirSync(path.dirname(pending), { recursive: true });
      fs.writeFileSync(pending, jobs.map(j => JSON.stringify(j)).join("\n") + "\n");
      console.log(`[seed] 💾 ${jobs.length} jobs written to ${pending}`);
      fail = jobs.length;
    }
  } catch (e: any) {
    // Connection refused — server not running
    const pending = path.join(ROOT, "ops/queue/raven-pending.ndjson");
    fs.mkdirSync(path.dirname(pending), { recursive: true });
    fs.writeFileSync(pending, jobs.map(j => JSON.stringify(j)).join("\n") + "\n");
    console.log(`[seed] Server offline — ${jobs.length} jobs written to ${pending}`);
    console.log(`[seed] They will be loaded when the server starts.`);
    fail = jobs.length;
  }

  // Write seed receipt
  const receipt = {
    timestamp: new Date().toISOString(),
    jobs_seeded: ok,
    jobs_pending: fail,
    sources: ["next_steps.todo.ndjson","backlog_synthesis.json","goals.yaml","reports_gap","known_tasks"],
    total: jobs.length,
    job_ids: jobs.map(j => j.id || j.title.slice(0, 40)),
  };
  fs.writeFileSync(path.join(ROOT, "reports/raven_seed_receipt.json"), JSON.stringify(receipt, null, 2));
  console.log(`[seed] Receipt written: reports/raven_seed_receipt.json`);
}

seed();
