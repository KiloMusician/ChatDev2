// Task Processor - Watches tasks/ directory and executes agents
import fs from "node:fs";
import path from "node:path";
import { loadAgents } from "./agents/registry.js";

const TASKS_DIR = path.resolve("tasks");
const RESULTS_DIR = path.resolve("results");
const POLL_INTERVAL = 1000; // 1 second

// Ensure directories exist
fs.mkdirSync(TASKS_DIR, { recursive: true });
fs.mkdirSync(RESULTS_DIR, { recursive: true });

console.log("🤖 SimulatedVerse Task Processor");
console.log(`📂 Tasks directory: ${TASKS_DIR}`);
console.log(`📂 Results directory: ${RESULTS_DIR}`);
console.log("⏳ Loading agents...\n");

const agents = await loadAgents();
const agentMap = new Map(agents.map(a => [a.id, a]));

console.log(`✅ Loaded ${agents.length} agents:`, agents.map(a => a.id).join(", "));
console.log("\n🔍 Watching for tasks...\n");

// Process task files
async function processTask(taskFile: string) {
  const taskPath = path.join(TASKS_DIR, taskFile);
  
  try {
    const taskData = JSON.parse(fs.readFileSync(taskPath, "utf-8"));
    
    // Validate task format
    if (!taskData.task_id || !taskData.agent_id) {
      console.warn(`⚠️  Invalid task format in ${taskFile} - archiving`);
      const archiveDir = path.join(TASKS_DIR, "invalid");
      fs.mkdirSync(archiveDir, { recursive: true });
      fs.renameSync(taskPath, path.join(archiveDir, taskFile));
      return;
    }
    
    console.log(`📥 New task: ${taskData.task_id} for agent: ${taskData.agent_id}`);
    
    const agent = agentMap.get(taskData.agent_id);
    if (!agent) {
      console.error(`❌ Agent not found: ${taskData.agent_id} - archiving task`);
      const errorDir = path.join(TASKS_DIR, "errors");
      fs.mkdirSync(errorDir, { recursive: true });
      fs.renameSync(taskPath, path.join(errorDir, taskFile));
      return;
    }
    
    // Execute agent
    console.log(`🚀 Executing ${taskData.agent_id}...`);
    const result = await agent.impl.run(taskData);
    
    // Write result
    const resultFile = path.join(RESULTS_DIR, `${taskData.task_id}_result.json`);
    fs.writeFileSync(resultFile, JSON.stringify({
      task_id: taskData.task_id,
      agent_id: taskData.agent_id,
      result: result,
      completed_at: new Date().toISOString()
    }, null, 2));
    
    console.log(`✅ Task completed: ${resultFile}\n`);
    
    // Archive task file
    const doneDir = path.join(TASKS_DIR, "completed");
    fs.mkdirSync(doneDir, { recursive: true });
    fs.renameSync(taskPath, path.join(doneDir, taskFile));
    
  } catch (error: any) {
    console.error(`❌ Error processing ${taskFile}:`, error.message);
    // Move to errors directory
    try {
      const errorDir = path.join(TASKS_DIR, "errors");
      fs.mkdirSync(errorDir, { recursive: true });
      fs.renameSync(taskPath, path.join(errorDir, taskFile));
    } catch (moveError) {
      console.error(`❌ Could not archive error file: ${taskFile}`);
    }
  }
}

// Watch loop
setInterval(() => {
  const files = fs.readdirSync(TASKS_DIR)
    .filter(f => f.endsWith('.json'));
  
  for (const file of files) {
    processTask(file);
  }
}, POLL_INTERVAL);

console.log("✅ Task processor running. Press Ctrl+C to stop.\n");
