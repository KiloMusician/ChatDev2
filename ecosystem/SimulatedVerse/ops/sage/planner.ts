import { readFileSync, existsSync } from "node:fs";
import YAML from "yaml";
import * as adapters from "./adapters.js";

type Action = { name: string; run: () => void; proof?: () => Promise<boolean> };
export type Plan = Action[];

export function buildPlan(ctx: {
  staleUI: boolean;
  noPUms: number;
  llmHealth: { ollama: boolean; openai: boolean; ok: boolean };
  theaterScore: number | null;
}) : Plan {
  const pol = YAML.parse(readFileSync("ops/sage/policies.yaml","utf8"));

  const actions: Plan = [];

  // 1) Fix errors / theater first
  if (ctx.theaterScore !== null && ctx.theaterScore > 0.2) {
    actions.push({ name: "audit-theater", run: () => adapters.runAuditor("theater") });
  }

  // 2) Unblock UI if stale or no PUs finishing
  if (ctx.staleUI || ctx.noPUms > pol.idle.max_no_pu_complete_ms) {
    actions.push({ name: "nudge-provisioner", run: () => adapters.nudgeProvisioner() });
    actions.push({ name: "ui-fix-pass", run: () => adapters.uiFixPass() });
  }

  // 3) Ensure Ollama is healthy
  if (!ctx.llmHealth.ok || !ctx.llmHealth.ollama) {
    actions.push({ name: "ensure-ollama", run: () => adapters.ensureOllamaStack() });
  }

  // 4) Reduce sprawl, no deletions — reports only
  actions.push({ name: "topology", run: () => adapters.runTopology() });
  actions.push({ name: "knip-report", run: () => adapters.runKnip() });

  // 5) Keep chug running
  if (existsSync("ops/chug-runner.ts")) actions.push({ name: "chug-runner", run: () => adapters.runChugRunner() });

  // 6) Culture-Ship cascade when we are stagnant (party missions / quests)
  if (ctx.noPUms > pol.idle.max_no_pu_complete_ms) {
    actions.push({ name: "culture-cascade", run: () => adapters.cultureCascade("sage.nudge", { reason:"stagnation" }) });
  }

  return actions;
}