/**
 * RouteEnforcer — all user/agent actions must pass through Culture-Ship pipelines.
 * If a tool tries to bypass, we wrap & re-route (or block with guidance).
 */
import { planCascade } from "../planners/cascade_event.mjs";
import { tokenGovernor } from "../planners/token_governor.mjs";
import { enqueue, MegaTask } from "../queue/mega_queue.js";
import { ShipMemory } from "../memory/ship_memory.js";

export type ActionCtx = {
  actor: "replit-agent" | "chatdev" | "pilot" | "taskmaster" | "intermediary" | "librarian" | "council" | "system";
  intent: string;
  costPreference: "zero" | "low" | "any";
  allowExternalCalls?: boolean;
  payload?: Record<string, unknown>;
};

export async function routeAction(ctx: ActionCtx): Promise<{accepted:boolean; reason?:string}> {
  // 1) Hard guard: blocked states (soft-lock, runaway, duplicate spam)
  const mem = await ShipMemory.load();
  if (mem.softLock.active) {
    await enqueue<MegaTask>({ kind:"softlock.recover", priority:0, data:{hint:"route_action"} });
    return { accepted:false, reason:"Soft-lock recovery engaged. Action queued via Ship." };
  }

  // 2) Cost governor: prefer zero/low-token ops unless explicit
  const budget = tokenGovernor.currentBudget();
  if ((ctx.costPreference ?? "zero") !== "any" && budget.enforceFrugality) {
    ctx.allowExternalCalls = false; // clamp
  }

  // 3) Normalize into a Ship task so every path is observable & reversible
  await enqueue<MegaTask>({
    kind: "action.routed",
    priority: 5,
    data: { ctx, ts: Date.now() },
    tags: ["routed","observed","reversible"]
  });

  // 4) Plan a small cascade around the action (prep/validate/post)
  await planCascade({ trigger:"routeAction", ctx });

  return { accepted:true };
}