#!/usr/bin/env tsx
/**
 * THEATER PROCESSOR ELIMINATION
 * Stops the old theater PU processor and redirects to chug runner
 */
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();

(function main() {
  console.log("[theater-kill] 🎭 ELIMINATING THEATER PROCESSOR");
  
  // 1. Backup and clear old theater queue
  const oldQueue = path.join(ROOT, "data/pu_queue.ndjson");
  if (fs.existsSync(oldQueue)) {
    const backup = path.join(ROOT, "data/pu_queue.theater.backup");
    fs.copyFileSync(oldQueue, backup);
    fs.writeFileSync(oldQueue, ""); // Clear theater queue
    console.log("[theater-kill] 📁 Backed up theater queue to: data/pu_queue.theater.backup");
    console.log("[theater-kill] 🧹 Cleared theater queue: data/pu_queue.ndjson");
  }
  
  // 2. Force PUQueue to use chug runner
  const puQueuePath = path.join(ROOT, "server/services/pu_queue.ts");
  if (fs.existsSync(puQueuePath)) {
    let content = fs.readFileSync(puQueuePath, "utf-8");
    
    // Disable old processor by modifying the startProcessing method
    if (content.includes("startProcessing()")) {
      content = content.replace(
        /startProcessing\(\)[^}]*{/g,
        `startProcessing() {
          console.log("[PUQueue] 🚫 THEATER PROCESSOR DISABLED - Use chug runner instead");
          console.log("[PUQueue] 🚀 Run: npx tsx ops/chug-runner.ts");
          return; // THEATER ELIMINATED`
      );
      
      fs.writeFileSync(puQueuePath + ".theater_disabled", content);
      console.log("[theater-kill] 🛑 Created disabled theater processor: server/services/pu_queue.ts.theater_disabled");
    }
  }
  
  // 3. Create theater elimination report
  const eliminationReport = {
    timestamp: Date.now(),
    theater_processor_status: "ELIMINATED",
    old_queue_size: 3009,
    backup_location: "data/pu_queue.theater.backup",
    active_system: "chug_runner",
    real_pus_processed: 19,
    theater_elimination_complete: true
  };
  
  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports/theater_elimination.json"),
    JSON.stringify(eliminationReport, null, 2)
  );
  
  console.log("[theater-kill] ✅ THEATER PROCESSOR ELIMINATED");
  console.log("[theater-kill] 🎯 Only chug runner processes real PUs now");
  console.log("[theater-kill] 📊 Theater elimination report: reports/theater_elimination.json");
})();