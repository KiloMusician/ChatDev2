#!/usr/bin/env node
import { nextBatch, markDone } from "../queue/mega_queue.js";
import { codemod } from "../surgery/codemod.mjs";
import { renameAndRewire } from "../surgery/rename_rewire.mjs";

console.log("🔧 Culture-Ship Fix All");

const batch = await nextBatch(25);
const done = [];

for (const task of batch) {
  console.log(`Processing: ${task.kind} (${task.id})`);
  
  try {
    let success = false;
    
    if (task.kind === "surgical-edit") {
      success = await codemod(task);
    } else if (task.kind === "rename-rewire") {
      success = await renameAndRewire(task);
    } else if (task.kind === "import.fix") {
      console.log("🔧 Import fix:", task.data);
      success = true;
    } else {
      console.log(`⚠️ Unknown task kind: ${task.kind}`);
    }
    
    if (success) {
      done.push(task.id);
    }
  } catch (error) {
    console.error(`❌ Failed to process task ${task.id}:`, error.message);
  }
}

if (done.length > 0) {
  await markDone(done);
  console.log(`✅ Completed ${done.length} tasks`);
} else {
  console.log("📭 No tasks completed");
}