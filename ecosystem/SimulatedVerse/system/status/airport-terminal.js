#!/usr/bin/env node
// Airport Terminal Style Live Status Display
// Updates in real-time like arrival/departure boards

import fs from 'fs';

function displayLiveTerminal() {
  console.clear();
  console.log("📺 CORELINK FOUNDATION - LIVE STATUS TERMINAL");
  console.log("━".repeat(65));
  console.log(`🕐 ${new Date().toLocaleTimeString()} - Live Update Every 5 Seconds`);
  console.log("");
  
  // Read live status
  if (fs.existsSync("data/status/live-terminal.json")) {
    const status = JSON.parse(fs.readFileSync("data/status/live-terminal.json", 'utf-8'));
    
    console.log("🤖 AUTONOMOUS SYSTEM STATUS:");
    console.log(`   ├─ ${status.puQueue.status}`);
    console.log(`   ├─ Tasks Completed: ${status.puQueue.completedCount}`);
    console.log(`   └─ Current Activity: ${status.puQueue.recentTasks}`);
    console.log("");
    
    console.log("📁 FILE SYSTEM HEALTH:");
    console.log(`   ├─ ${status.fileSystem.status}`);
    console.log(`   ├─ Active Files: ${status.fileSystem.totalFiles}`);
    console.log(`   └─ Quarantined: ${status.fileSystem.quarantinedFiles}`);
    console.log("");
    
    console.log("🎮 GAME ENGINE:");
    console.log(`   ├─ ${status.system.health}`);
    console.log(`   ├─ System Entropy: ${status.system.entropy}`);
    console.log(`   └─ ${status.system.autoplay}`);
    console.log("");
  }
  
  // Show recent PUQueue activity (last 5 tasks)
  console.log("📊 RECENT AUTONOMOUS ACTIVITY:");
  if (fs.existsSync("data/pu_queue.ndjson")) {
    const lines = fs.readFileSync("data/pu_queue.ndjson", 'utf-8').split('\n').filter(l => l.trim());
    const recent = lines.slice(-5);
    
    recent.forEach(line => {
      try {
        const task = JSON.parse(line);
        const kind = task.kind.replace('PU', '');
        const status = task.status === 'done' ? '✅' : '🔄';
        console.log(`   ${status} ${kind}: ${task.id.substring(0,8)}... (${task.cost} cost)`);
      } catch {}
    });
  }
  
  console.log("━".repeat(65));
  console.log("🔄 System auto-updating... Press Ctrl+C to stop");
}

// Run terminal display
displayLiveTerminal();

// Auto-refresh every 5 seconds like real airport terminals
setInterval(displayLiveTerminal, 5000);