// ops/raven-runner.ts — ΞNuSyQ Autonomous RAVEN Worker
// Polls /api/raven/lease, executes jobs via Ollama or file materialization
import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync, appendFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";

const BASE    = process.env.BASE_URL    || "http://127.0.0.1:5000";
const OLLAMA  = process.env.OLLAMA_URL  || "http://localhost:11434";
const MODEL   = process.env.RAVEN_MODEL || "llama3.1:8b";
const TOKEN   = process.env.ADMIN_TOKEN || "";
const LOG_DIR = "ops/logs/raven";
const H = { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" };

mkdirSync(LOG_DIR, { recursive: true });

function log(msg: string) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  appendFileSync(join(LOG_DIR, "run.log"), line + "\n");
}

async function api(url: string, opt: any = {}) {
  const r = await fetch(url, { ...opt, headers: { ...(opt.headers||{}), ...H } });
  return r.json();
}

// ── Ollama integration ──────────────────────────────────────────────────────
async function ollama(prompt: string, system = "You are a TypeScript/Python developer in the ΞNuSyQ ecosystem. Be concise and produce working code."): Promise<string> {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 90_000);
    const r = await fetch(`${OLLAMA}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: MODEL, stream: false, messages: [
        { role: "system", content: system },
        { role: "user",   content: prompt }
      ]}),
      signal: ctrl.signal,
    });
    const d: any = await r.json();
    return d.message?.content || "";
  } catch (e: any) {
    return `// Ollama unavailable: ${e.message}`;
  }
}

async function ollamaAvailable(): Promise<boolean> {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 2000);
    const r = await fetch(`${OLLAMA}/api/tags`, { signal: ctrl.signal });
    return r.ok;
  } catch { return false; }
}

// ── Job executor ────────────────────────────────────────────────────────────
async function executeJob(job: any): Promise<{ ok: boolean; logs: string }> {
  let logs = `[job:${job.id}] kind:${job.kind} title:${job.title}\n`;

  // 1. Pre-generated files → materialize and commit
  if (job.files?.length) {
    for (const f of job.files) {
      const dir = dirname(f.path);
      if (dir !== ".") mkdirSync(dir, { recursive: true });
      writeFileSync(f.path, f.content);
      logs += `written: ${f.path}\n`;
    }
    try {
      execSync("git add -A",                      { stdio: "pipe" });
      execSync(`git commit -m "raven: ${job.title.slice(0,72)}"`, { stdio: "pipe" });
      logs += `committed: ${job.title}\n`;
    } catch { logs += `git: no changes or skipped\n`; }
    return { ok: true, logs };
  }

  // 2. Ollama-driven jobs (plan / refactor / doc / test / ops)
  const llmAvail = await ollamaAvailable();
  if (!llmAvail) {
    logs += `ollama offline — job deferred\n`;
    return { ok: false, logs };
  }

  switch (job.kind) {
    case "plan": {
      const plan = await ollama(
        `Create a concise implementation plan for: "${job.title}"\nContext: ${JSON.stringify(job.meta || {})}\nOutput numbered steps only.`
      );
      const out = `ops/proofs/plan_${job.id}.md`;
      mkdirSync("ops/proofs", { recursive: true });
      writeFileSync(out, `# Plan: ${job.title}\n\n${plan}\n`);
      logs += `plan written: ${out}\n${plan.slice(0,200)}\n`;
      return { ok: true, logs };
    }
    case "refactor":
    case "fix": {
      if (!job.meta?.file) { logs += "no file specified\n"; return { ok: false, logs }; }
      if (!existsSync(job.meta.file)) { logs += `file not found: ${job.meta.file}\n`; return { ok: false, logs }; }
      const { readFileSync } = await import("node:fs");
      const src = readFileSync(job.meta.file, "utf-8").slice(0, 6000);
      const patched = await ollama(
        `Fix/refactor the following TypeScript code. Issue: "${job.title}"\n\nFile: ${job.meta.file}\n\`\`\`ts\n${src}\n\`\`\`\n\nReturn ONLY the complete fixed file content, no markdown fences.`
      );
      if (patched && patched.length > 50 && !patched.startsWith("// Ollama unavailable")) {
        writeFileSync(job.meta.file, patched);
        try {
          execSync("git add -A", { stdio: "pipe" });
          execSync(`git commit -m "raven-fix: ${job.title.slice(0,60)}"`, { stdio: "pipe" });
        } catch { /* ok */ }
        logs += `refactored: ${job.meta.file}\n`;
      }
      return { ok: true, logs };
    }
    case "doc": {
      const target = job.meta?.file;
      if (target && existsSync(target)) {
        const { readFileSync } = await import("node:fs");
        const src = readFileSync(target, "utf-8").slice(0, 4000);
        const doc = await ollama(`Add JSDoc comments to this TypeScript code. Return ONLY the complete file:\n${src}`);
        if (doc && doc.length > 50 && !doc.startsWith("// Ollama unavailable")) {
          writeFileSync(target, doc);
          logs += `documented: ${target}\n`;
        }
      }
      return { ok: true, logs };
    }
    case "test": {
      const testPlan = await ollama(
        `Write a concise test plan for: "${job.title}"\nFiles: ${JSON.stringify(job.meta?.files || [])}\nOutput as a checklist only.`
      );
      const out = `ops/proofs/test_plan_${job.id}.md`;
      mkdirSync("ops/proofs", { recursive: true });
      writeFileSync(out, `# Test Plan: ${job.title}\n\n${testPlan}\n`);
      logs += `test plan: ${out}\n`;
      return { ok: true, logs };
    }
    case "ops":
    default: {
      const analysis = await ollama(
        `Analyze and provide a solution for this ops task: "${job.title}"\nMeta: ${JSON.stringify(job.meta || {})}\nBe concise.`
      );
      const out = `ops/proofs/ops_${job.id}.md`;
      mkdirSync("ops/proofs", { recursive: true });
      writeFileSync(out, `# Ops Task: ${job.title}\n\n${analysis}\n`);
      logs += `ops artifact: ${out}\n${analysis.slice(0, 200)}\n`;
      return { ok: true, logs };
    }
  }
}

// ── Main loop ────────────────────────────────────────────────────────────────
async function main() {
  log("🐦‍⬛ RAVEN autonomous worker starting");
  log(`   server: ${BASE}  ollama: ${OLLAMA}  model: ${MODEL}`);

  let idle = 0;
  while (true) {
    try {
      const lease = await api(`${BASE}/api/raven/lease?n=5`, { method: "POST", body: "{}" });

      if (!lease.items?.length) {
        idle++;
        if (idle % 15 === 0) log(`⏸ queue empty (${idle * 4}s idle) — waiting for jobs`);
        await new Promise(r => setTimeout(r, 4000));
        continue;
      }
      idle = 0;
      log(`📋 Leased ${lease.items.length} jobs (lease ${lease.leaseId})`);

      for (const job of lease.items) {
        log(`🔨 ${job.id}: ${job.title}`);
        const { ok, logs } = await executeJob(job);
        log(ok ? `✅ ${job.id} done` : `⚠️ ${job.id} deferred`);
        await api(`${BASE}/api/raven/ack`, {
          method: "POST",
          body: JSON.stringify({ leaseId: lease.leaseId, result: { id: job.id, ok, logs } })
        });
      }
    } catch (_e) {
      log("⏸ Connection issue — server may be starting up, retrying...");
    }
    await new Promise(r => setTimeout(r, 4000));
  }
}

main();
