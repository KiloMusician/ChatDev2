// Smart Task Organizer with DAG-based prioritization
import fs from "fs";
import { execSync } from "child_process";

function parseYAML(yamlText) {
  // Simple YAML parser for our task format
  const lines = yamlText.split("\n");
  const result = { version: 1, heuristics: { weights: {}, caps: {} }, tasks: [] };
  let currentTask = null;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("version:")) {
      result.version = parseInt(trimmed.split(":")[1].trim());
    } else if (trimmed.includes("weights:")) {
      // Parse weights section
    } else if (trimmed.startsWith("- id:")) {
      if (currentTask) result.tasks.push(currentTask);
      currentTask = { 
        id: trimmed.split(":")[1].trim(),
        depends_on: [],
        impact: 5,
        runtime_cost: 1,
        token_cost: 0
      };
    } else if (trimmed.startsWith("title:") && currentTask) {
      currentTask.title = trimmed.split(":")[1].trim().replace(/"/g, "");
    } else if (trimmed.startsWith("script:") && currentTask) {
      currentTask.script = trimmed.split(":")[1].trim().replace(/"/g, "");
    } else if (trimmed.startsWith("impact:") && currentTask) {
      currentTask.impact = parseInt(trimmed.split(":")[1].trim());
    } else if (trimmed.startsWith("token_cost:") && currentTask) {
      currentTask.token_cost = parseInt(trimmed.split(":")[1].trim());
    } else if (trimmed.startsWith("depends_on:") && currentTask) {
      const deps = trimmed.split(":")[1].trim();
      if (deps !== "[]") {
        currentTask.depends_on = deps.replace(/[\[\]]/g, "").split(",").map(s => s.trim());
      }
    }
  }
  if (currentTask) result.tasks.push(currentTask);
  return result;
}

const file = process.argv[2] || "ops/tasks.yaml";
if (!fs.existsSync(file)) {
  console.log("❌ Task file not found:", file);
  process.exit(1);
}

const doc = parseYAML(fs.readFileSync(file, "utf8"));
const done = new Set(process.env.DONE?.split(",").filter(Boolean) ?? []);
const active = new Set(process.env.ACTIVE?.split(",").filter(Boolean) ?? []);

function ready(task) {
  return task.depends_on.every(d => done.has(d) || doc.tasks.find(x => x.id === d) === undefined);
}

function score(task) {
  const baseScore = (task.impact || 5) * 2; // Prioritize high impact
  const tokenPenalty = (task.token_cost || 0) * -4; // Heavy bias against token usage
  const readyBonus = ready(task) ? 10 : -20; // Can't do unready tasks
  const diversityBonus = Math.random() * 2; // Small randomization
  
  return baseScore + tokenPenalty + readyBonus + diversityBonus;
}

const ranked = doc.tasks
  .filter(t => !done.has(t.id) && !active.has(t.id))
  .map(t => ({ ...t, score: score(t) }))
  .sort((a, b) => b.score - a.score);

console.log("🧠 ΞNuSyQ Smart Task Organizer");
console.log("═══════════════════════════════");
console.log(`📊 ${ranked.length} tasks in queue, ${done.size} completed, ${active.size} active\n`);

console.log("🎯 Next 5 priority tasks:");
ranked.slice(0, 5).forEach((t, i) => {
  const status = ready(t) ? "✅ READY" : "⏳ WAITING";
  console.log(`${i + 1}. ${t.id.padEnd(20)} score=${t.score.toFixed(1)} ${status}`);
  console.log(`   "${t.title}"`);
});

if (process.env.RUN_FIRST === "1" && ranked[0] && ready(ranked[0])) {
  console.log(`\n🚀 Executing highest priority task: ${ranked[0].id}`);
  console.log(`📝 Command: ${ranked[0].script}\n`);
  try {
    execSync(ranked[0].script, { stdio: "inherit" });
    console.log(`✅ Task completed: ${ranked[0].id}`);
  } catch (error) {
    console.log(`❌ Task failed: ${ranked[0].id} - ${error.message}`);
    process.exit(1);
  }
}

console.log(`\n💡 Usage: RUN_FIRST=1 node tools/taskOrganizer.mjs to execute top task`);
console.log(`💡 Usage: DONE=task1,task2 node tools/taskOrganizer.mjs to mark tasks done`);