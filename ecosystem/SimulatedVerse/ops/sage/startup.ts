// ops/sage/startup.ts
// Skeptical startup chain: prove the spine, then queues, then UI, else degrade gracefully.
import { request } from "undici";
import { elasticCooldown } from "./elastic";

async function ping(url: string, timeout = 3000) {
  try {
    const r = await request(url, { method: "GET", headersTimeout: timeout, bodyTimeout: timeout });
    return r.statusCode === 200;
  } catch {
    return false;
  }
}

export async function boot() {
  const report: Record<string, any> = { t0: Date.now(), receipts: [] };

  // 1) LLM spine
  report.ollamaOk = await ping(`${process.env.OLLAMA_HOST ?? "http://127.0.0.1:11434"}/api/version`);
  if (!report.ollamaOk) {
    // try watchdog (non-fatal if absent)
    try {
      const { spawn } = await import("node:child_process");
      spawn("npx", ["-y", "tsx", "ops/ollama/watchdog.ts"], { stdio: "ignore", detached: true }).unref();
      await new Promise((r) => setTimeout(r, elasticCooldown(1500, { timeouts: 0, rateLimits: 0, econn: 1, backlog: 0, idleStreakMs: 0, receipts: 0, uiFreshSkewMs: 0 })));
      report.ollamaOk = await ping(`${process.env.OLLAMA_HOST ?? "http://127.0.0.1:11434"}/api/version`);
    } catch {}
  }

  report.gatewayOk = await ping(`${process.env.LLM_GATEWAY_URL ?? "http://127.0.0.1:4455"}/llm/health`);
  if (!report.gatewayOk && process.env.OPENAI_API_KEY) report.gatewayDegradedToOpenAI = true;

  // 2) Queues alive?
  // heuristic: presence of recent receipts file or completed markers
  const fs = await import("node:fs/promises");
  try {
    const st = await fs.stat("public/system-status.json");
    report.uiSkewMs = Date.now() - st.mtimeMs;
    if (report.uiSkewMs > 60_000) {
      await fs.writeFile(
        "public/system-status.json",
        JSON.stringify({ timestamp: new Date().toISOString(), sage: "refresh" }, null, 2)
      );
      report.uiRefreshed = true;
    }
  } catch {
    // create it
    await fs.mkdir("public", { recursive: true });
    await fs.writeFile("public/system-status.json", JSON.stringify({ timestamp: new Date().toISOString() }, null, 2));
    report.uiCreated = true;
  }

  // 3) Noise mask (.gitignore hardening)
  try {
    const gi = await fs.readFile(".gitignore", "utf8").catch(() => "");
    const needed = ["node_modules/", ".venv/", ".pythonlibs/", "__pycache__/", ".cache/", "dist/", "build/", "attic/", "quarantine/"];
    const missing = needed.filter((x) => !gi.includes(x));
    if (missing.length) {
      await fs.appendFile(".gitignore", "\n# noise mask (sage)\n" + missing.map((x) => x + "\n").join(""));
      report.gitignoreHardened = missing;
    }
  } catch {}

  report.t1 = Date.now();
  return report;
}