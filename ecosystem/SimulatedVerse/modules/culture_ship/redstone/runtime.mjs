import { enqueue } from "../queue/mega_queue.mjs";
import { ShipMemory } from "../memory/ship_memory.mjs";
// Metric type: { metric?, event?, op?, value? }

export async function evalRule(r) {
  const mem = await ShipMemory.load();
  const now = { "imports.broken": mem.health.brokenImports, "cpu.softlock": mem.softLock.active, "tokens.left": process.env.TOKENS_LEFT ? Number(process.env.TOKENS_LEFT) : 999 };
  const pass = r.when.event ? true : compare(now[r.when.metric], r.when.op, r.when.value);
  if (pass) await enqueue({kind: r.do.task, data:r.do.data, priority: (r.do.priority ?? 5)});
}
function compare(a,op,b){return op==">"?a>b:op=="<"?a<b:op=="=="?a===b: a!==b;}