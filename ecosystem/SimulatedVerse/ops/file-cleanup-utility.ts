// Automated File Cleanup Utility for CoreLink Foundation
// Implements aggressive timestamp artifact cleanup with safety checks

import fs from "node:fs";
import path from "node:path";
import { fileLifecycleManager } from "./file-lifecycle-manager.js";
// import { obsidianVaultManager } from "./obsidian-vault-manager.js";

interface CleanupReport {
  timestampArtifactsRemoved: number;
  spaceReclaimed: number;
  savesOptimized: number;
  vaultSynced: boolean;
}

// Recommended retention limits based on system analysis
const SYSTEM_LIMITS = {
  maxGameSaves: 5,        // Keep last 5 saves only
  maxReports: 3,          // Keep last 3 reports per type
  maxLogs: 2,             // Keep last 2 log files
  maxPlans: 10,           // Keep last 10 cascade plans
  maxArtifacts: 0,        // Zero tolerance for random artifacts
};

export async function performSystemCleanup(): Promise<CleanupReport> {
  console.log("🧹 Starting comprehensive file lifecycle cleanup...");
  
  const report: CleanupReport = {
    timestampArtifactsRemoved: 0,
    spaceReclaimed: 0,
    savesOptimized: 0,
    vaultSynced: false
  };
  
  // 1. Clean up game saves (biggest space hog)
  console.log("📁 Cleaning game saves directory...");
  if (!fs.existsSync("saves")) {
    console.log("📁 No saves directory found, skipping...");
    return report;
  }
  const saveFiles = fs.readdirSync("saves").filter(f => f.endsWith('.json'));
  const sortedSaves = saveFiles
    .map(f => ({ name: f, path: path.join("saves", f), stats: fs.statSync(path.join("saves", f)) }))
    .sort((a, b) => b.stats.mtime.getTime() - a.stats.mtime.getTime());
  
  // Keep only the latest 5 saves, remove the rest
  const savesToRemove = sortedSaves.slice(SYSTEM_LIMITS.maxGameSaves);
  for (const save of savesToRemove) {
    report.spaceReclaimed += save.stats.size;
    fs.unlinkSync(save.path);
    report.timestampArtifactsRemoved++;
  }
  report.savesOptimized = SYSTEM_LIMITS.maxGameSaves;
  
  // 2. Apply retention policies through lifecycle manager
  console.log("⚙️ Applying retention policies...");
  const optimizationResults = await fileLifecycleManager.applyRetentionPolicies();
  report.timestampArtifactsRemoved += optimizationResults.length;
  report.spaceReclaimed += optimizationResults.reduce(
    (sum, result) => sum + (result.originalSize - result.optimizedSize), 0
  );
  
  // 3. Sync to Obsidian vault for better knowledge management
  console.log("📚 Syncing to Obsidian vault...");
  try {
    // await obsidianVaultManager.syncToVault();
    console.log("📚 Vault sync disabled - module not available");
    report.vaultSynced = false;
  } catch (error) {
    console.warn("⚠️ Vault sync failed:", error);
  }
  
  console.log("✅ Cleanup completed!");
  console.log(`📊 Results: ${report.timestampArtifactsRemoved} files removed, ${Math.round(report.spaceReclaimed/1024)}KB reclaimed`);
  
  return report;
}

// CLI interface for manual cleanup
export async function runCleanupCLI() {
  const report = await performSystemCleanup();
  
  console.log("\n" + "=".repeat(60));
  console.log("FILE LIFECYCLE CLEANUP REPORT");
  console.log("=".repeat(60));
  console.log(`Timestamp artifacts removed: ${report.timestampArtifactsRemoved}`);
  console.log(`Space reclaimed: ${Math.round(report.spaceReclaimed/1024)}KB`);
  console.log(`Game saves optimized: ${report.savesOptimized}`);
  console.log(`Obsidian vault synced: ${report.vaultSynced ? 'Yes' : 'No'}`);
  console.log("=".repeat(60));
}

// For direct execution
async function main() {
  await runCleanupCLI();
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}