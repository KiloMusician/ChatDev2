#!/usr/bin/env node
import { nextBatch, markDone } from "../queue/mega_queue.mjs";
import { evalRule } from "../redstone/runtime.mjs";
import { ShipMemory } from "../memory/ship_memory.mjs";

const rules = {
  rules: [
    { when: {metric: "imports.broken", op: ">", value: 0}, do: {task:"import.fix", priority:1}},
    { when: {metric: "cpu.softlock", op: "==", value: true}, do: {task:"softlock.recover", priority:0}},
  ]
};

const batch = await nextBatch(50);
if (!batch.length) {
  // No tasks? Evaluate rules to seed work.
  for (const r of rules.rules) await evalRule(r);
}

const done = [];
for (const t of (batch.length ? batch : await nextBatch(50))) {
  // Handle kinds minimally (extend handlers as you grow)
  if (t.kind === "import.fix") { 
    console.log("🔧 Processing import.fix task");
    done.push(t.id);
  }
  if (t.kind === "rename.rewire") { 
    console.log("📁 Processing rename.rewire task");
    done.push(t.id);
  }
}

if (done.length) {
  await markDone(done);
  console.log(`✅ Completed ${done.length} tasks`);
} else {
  console.log("📭 No tasks to process");
}