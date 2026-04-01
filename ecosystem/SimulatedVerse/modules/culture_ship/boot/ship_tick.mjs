import { getState, saveState, nowISO } from "../core/state.mjs";
import { queuePlan } from "../ops/queue_planner.mjs";
import { runQueue } from "../ops/queue_runner.mjs";
import { budgetGuard } from "../policies/budget_guard.mjs";
import { scanAll } from "../ops/scan_all.mjs";

export async function tick({ mode = "manual" } = {}) {
  const s = await getState();
  const ok = await budgetGuard();
  if (!ok) {
    console.log("💳 TokenGuard: zero/minimal budget mode ON. Local tools only.");
  }
  const scan = await scanAll({ fast: mode === "boot" });
  const plan = await queuePlan({ scan, budget: ok ? "normal" : "local" });
  const result = await runQueue({ plan, budget: ok ? "normal" : "local" });

  s.lastTick = { when: nowISO(), mode, stats: { queued: plan.items?.length || 0, done: result.done || 0 } };
  await saveState(s);
  console.log("✅ Ship tick complete:", s.lastTick);
}