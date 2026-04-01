#!/usr/bin/env tsx
/**
 * Replit-friendly Ollama watchdog:
 * - Pings /api/tags and /api/generate
 * - If down: attempts start (nix/shell) or logs actionable hint
 * - Preloads models + verifies a tiny JSON response
 * - Emits health to /public/system-status.json (no UI entanglement)
 */
import { execSync, spawn } from "node:child_process";
import { writeFileSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const HOST = process.env.OLLAMA_HOST ?? "http://127.0.0.1:11434";
const OUT = join("public", "system-status.json");
const MODEL = process.env.OLLAMA_MODEL ?? "llama3"; // swap to your default
const GEN_PROMPT = `{"model":"${MODEL}","prompt":"Return JSON: {\\"ok\\":true}","stream":false}`;

type Health = { ok: boolean; reason?: string; tags?: string[]; model?: string; ts: number };

async function httpJson(path: string, init?: RequestInit) {
  const r = await fetch(`${HOST}${path}`, init);
  if (!r.ok) throw new Error(`${path} => ${r.status}`);
  return r.json();
}

async function ping(): Promise<Health> {
  try {
    const tags = await httpJson("/api/tags");
    const gen = await httpJson("/api/generate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: GEN_PROMPT
    }) as any;
    const ok = !!gen?.response?.includes?.(`"ok":true`) || gen?.response?.trim()?.startsWith("{");
    return { ok, tags: (tags?.models ?? []).map((m:any)=>m.name), model: MODEL, ts: Date.now() };
  } catch (e:any) {
    return { ok: false, reason: e.message, ts: Date.now() };
  }
}

function writeStatus(partial: Record<string, any>) {
  try {
    mkdirSync("public", { recursive: true });
    // merge with prior content if present
    let prev: any = {};
    try { prev = JSON.parse(readFileSync(OUT, "utf-8")); } catch {}
    const merged = { ...prev, ...partial, timestamp: Date.now() };
    writeFileSync(OUT, JSON.stringify(merged, null, 2));
  } catch {}
}

async function heal() {
  const h = await ping();
  if (h.ok) {
    writeStatus({ ollama: { status: "up", model: h.model, tags: h.tags ?? [] } });
    return;
  }

  // Try to start Ollama (best-effort, adjust for your env)
  writeStatus({ ollama: { status: "down", reason: h.reason ?? "unknown" } });
  console.log("[ollama] down -> attempting to start (best effort)");

  try {
    // If Ollama is available on Replit Nix, you could attempt: `execSync("ollama serve &", {stdio:"ignore"})`
    // We use a conservative attempt; if not present, log clear hint.
    execSync("pgrep ollama || (command -v ollama && (nohup ollama serve >/dev/null 2>&1 &) || true)", { stdio: "ignore" });
  } catch {}

  // pre-pull model if missing
  try {
    execSync(`ollama pull ${MODEL}`, { stdio: "inherit" });
  } catch (e) {
    console.log("[ollama] pull skipped or unavailable:", (e as Error).message);
  }

  // recheck
  const h2 = await ping();
  writeStatus({ ollama: { status: h2.ok ? "up" : "down", reason: h2.reason ?? null, model: h2.model, tags: h2.tags ?? [] } });
  console.log("[ollama] health:", h2);
}

// run forever (lightweight)
(async () => {
  await heal();
  setInterval(heal, 15000); // every 15s
})();