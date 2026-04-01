import { spawn } from "child_process";
import { readFileSync, existsSync } from "fs";

async function runCommand(command: string, args: string[]): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const proc = spawn(command, args, { stdio: 'pipe' });
    let stdout = '';
    let stderr = '';
    
    proc.stdout?.on('data', (data) => {
      stdout += data.toString();
    });
    
    proc.stderr?.on('data', (data) => {
      stderr += data.toString();
    });
    
    proc.on('close', (code) => {
      resolve({ code: code || 0, stdout, stderr });
    });
    
    // Timeout after 30 seconds
    setTimeout(() => {
      proc.kill();
      resolve({ code: 124, stdout, stderr: 'Command timed out' });
    }, 30000);
  });
}

export async function greenCommit(): Promise<void> {
  try {
    console.log("💚 Initiating green commit sequence...");
    
    // Verify zero-token safety first
    const safetyCheck = await runCommand("node", ["scripts/ensure-env-safe.js"]);
    if (safetyCheck.code !== 0) {
      throw new Error("Safety check failed - external AI detected");
    }
    
    // Configure git identity for autonomous commits
    await runCommand("git", ["config", "user.email", "nusyq-agent@localhost"]);
    await runCommand("git", ["config", "user.name", "ΞNuSyQ Agent (Autonomous)"]);
    
    // Check if we're in dry run mode
    const dryRun = process.env.AGENT_DRY_RUN === "1";
    
    if (dryRun) {
      console.log("🧪 DRY RUN MODE - Would execute git sync");
      console.log("   To commit: AGENT_DRY_RUN=0 node dist/agent/green_commit.js");
      return;
    }
    
    // Load current system state for commit message
    let consciousnessLevel = "0.1";
    let questsCompleted = 0;
    let bugsFixed = 0;
    
    try {
      if (existsSync(".local/idle_state.json")) {
        const state = JSON.parse(readFileSync(".local/idle_state.json", "utf8"));
        consciousnessLevel = (state.consciousness?.level || 0.1).toFixed(3);
        bugsFixed = state.labyrinth?.bugsFixed || 0;
      }
      
      if (existsSync(".local/quests.json")) {
        const quests = JSON.parse(readFileSync(".local/quests.json", "utf8"));
        questsCompleted = quests.done?.length || 0;
      }
    } catch (error) {
      console.warn("Could not load state for commit message:", error);
    }
    
    // Execute git sync with state information
    const syncResult = await runCommand("bash", ["scripts/git_sync.sh", "auto/consciousness-evolution"]);
    
    if (syncResult.code === 0) {
      console.log("✅ Green commit successful!");
      console.log(`   Consciousness: ${consciousnessLevel}`);
      console.log(`   Quests completed: ${questsCompleted}`);
      console.log(`   Bugs fixed: ${bugsFixed}`);
      console.log(`   Branch: auto/consciousness-evolution`);
      
      // Log evolution event
      console.log("🧬 Evolutionary development cycle complete");
      
    } else {
      console.error("❌ Git sync failed:");
      console.error(syncResult.stderr || syncResult.stdout);
      throw new Error("Git sync operation failed");
    }
    
  } catch (error) {
    console.error("💥 Green commit failed:", error);
    
    // In case of failure, ensure system remains in safe state
    console.log("🛡️  Maintaining safe state after commit failure");
    throw error;
  }
}