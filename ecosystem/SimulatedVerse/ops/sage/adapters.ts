import { spawn } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import YAML from "yaml";

const POL = YAML.parse(readFileSync("ops/sage/policies.yaml","utf8"));

function run(cmd: string, args: string[] = [], name = cmd) {
  const child = spawn(cmd, args, { stdio: "inherit", env: process.env });
  child.on("exit", (c)=> console.log(`[sage] ${name} exited code=${c}`));
  return child;
}

// ---- Culture Ship ("cascade events", parties, etc.) ----
export function cultureCascade(tag: string, payload: Record<string, any> = {}) {
  if (!POL.ops.allow_cascade_events) return;
  // Convention: council bus shim via ops/ or packages/council
  run("node", ["-e", `
    (async () => {
      try {
        const { councilBus } = require('./packages/council/events/eventBus.js');
        councilBus.publish('culture.cascade', { tag: '${tag}', payload: ${JSON.stringify(payload)} });
        console.log('[sage:cascade] published ${tag}');
      } catch (e) { console.error(e); }
    })();`], "culture-cascade");
}

// ---- Auditor / Annealer (dup/TODO/placeholder scans) ----
export function runAuditor(reason = "periodic") {
  if (existsSync("ops/repo-auditor.ts")) return run("npx", ["tsx", "ops/repo-auditor.ts", "--reason", reason], "auditor");
  return run("node", ["-e", `console.log('[sage] auditor missing - skip')`], "auditor-skip");
}

// ---- PU Runner (proof-gated queue) ----
export function runChugRunner() {
  if (existsSync("ops/chug-runner.ts")) return run("npx", ["tsx", "ops/chug-runner.ts"], "chug");
  return run("node", ["-e", `console.log('[sage] chug-runner missing - skip')`], "chug-skip");
}

// ---- Ollama watch/gateway (from your earlier step) ----
export function ensureOllamaStack() {
  if (existsSync("ops/ollama/watchdog.ts")) run("npx", ["tsx", "ops/ollama/watchdog.ts"], "ollama-watch");
  if (existsSync("ops/ollama/gateway.ts")) run("npx", ["tsx", "ops/ollama/gateway.ts"], "llm-gateway");
}

// ---- UI Refresh (provisioner timestamp stale?) ----
export function nudgeProvisioner() {
  if (existsSync("ops/system-provisioner.js")) return run("node", ["ops/system-provisioner.js"], "provisioner");
}

// ---- Code hygiene (topology / dead) — reports only, no deletes ----
export function runTopology() {
  return run("npx", ["madge","--circular","apps","packages"], "topology");
}
export function runKnip() {
  return run("npx", ["knip","--include","apps/**,packages/**","--reporter","compact"], "knip");
}

// ---- UI conflict/integration pass (legacy vs new) ----
export function uiFixPass() {
  // You can point this at a codemod or a safeMap replacement pass.
  return run("node", ["-e", "console.log('[sage] UI fix pass placeholder (safeMap / feature flags)')"], "ui-fix");
}