#!/usr/bin/env tsx
// Smart File Operations CLI - Leverage Autonomous System Instead of Creating from Scratch
// Usage: tsx system/ops/smart-file-ops.ts [command] [args]

import { smartMove, organizeDirectory, triggerAutonomousOptimization } from './file-lifecycle-manager.js';

const commands = {
  
  async move(oldPath: string, newPath: string) {
    console.log("📦 Smart Move with Reference Updates");
    console.log("━".repeat(50));
    await smartMove(oldPath, newPath);
    console.log("✅ Move completed with all references updated!");
  },
  
  async organize(dirPath: string) {
    console.log("🗂️ Intelligent Directory Organization");
    console.log("━".repeat(50));
    await organizeDirectory(dirPath);
    console.log("✅ Directory organized with meaningful names!");
  },
  
  async optimize() {
    console.log("🤖 Triggering Autonomous PUQueue Optimization");
    console.log("━".repeat(50));
    await triggerAutonomousOptimization();
    console.log("✅ Autonomous system will handle the optimization!");
    console.log("🎯 Watch the PUQueue logs for progress...");
  },
  
  help() {
    console.log("🛠️ Smart File Operations - Infrastructure-First Approach");
    console.log("━".repeat(60));
    console.log("COMMANDS:");
    console.log("  move <old> <new>  - Move file and update all references");
    console.log("  organize <dir>    - Organize directory with smart naming");
    console.log("  optimize          - Trigger autonomous PUQueue optimization");
    console.log("  help              - Show this help");
    console.log("");
    console.log("💡 TIP: Use file operations instead of creating from scratch!");
    console.log("🤖 TIP: Let the PUQueue autonomous system do the heavy lifting!");
    console.log("━".repeat(60));
  }
};

// CLI Interface
async function main() {
  const [command, ...args] = process.argv.slice(2);
  
  if (!command || command === 'help') {
    commands.help();
    return;
  }
  
  if (command in commands && typeof commands[command] === 'function') {
    await commands[command](...args);
  } else {
    console.log(`❌ Unknown command: ${command}`);
    commands.help();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { commands as smartFileOps };