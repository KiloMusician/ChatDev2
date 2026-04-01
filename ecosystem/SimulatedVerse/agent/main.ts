import { spawn } from "child_process";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";
import YAML from "yaml";
import { tick } from "./idle_tick.ts";
import { runQuests } from "./quest_runner.ts";
import { tryCodemods } from "./codemods.ts";
import { runTests } from "./testharness.ts";
import { greenCommit } from "./green_commit.ts";

interface AgentConfig {
  mode: string;
  dry_run: boolean;
  limits: {
    max_steps: number;
    max_seconds: number;
    max_fs_writes: number;
  };
  metrics: {
    must_improve_one_of: string[];
  };
  circuit_breaker: {
    consecutive_regressions: number;
    cooldown_seconds: number;
    restore_method: string;
  };
}

class ΞNuSyQAgent {
  private config: AgentConfig;
  private startTime: number;
  private writes: number = 0;
  private consecutiveRegressions: number = 0;
  private lastSnapshot?: string;

  constructor() {
    this.startTime = Date.now();
    this.config = this.loadConfig();
    this.ensureDirectories();
  }

  private loadConfig(): AgentConfig {
    try {
      const yaml = readFileSync("agent/config.yml", "utf8");
      return YAML.parse(yaml);
    } catch {
      // Fallback minimal config
      return {
        mode: "local",
        dry_run: true,
        limits: { max_steps: 64, max_seconds: 120, max_fs_writes: 200 },
        metrics: { must_improve_one_of: ["tests_passed", "consciousness_level"] },
        circuit_breaker: { consecutive_regressions: 3, cooldown_seconds: 15, restore_method: "snapshot" }
      };
    }
  }

  private ensureDirectories(): void {
    mkdirSync(".agent", { recursive: true });
    mkdirSync(".local", { recursive: true });
    mkdirSync(".snapshots", { recursive: true });
  }

  private log(...args: any[]): void {
    const timestamp = new Date().toISOString();
    console.log(`🤖 [${timestamp}]`, ...args);
  }

  private checkBudgets(): { ok: boolean; reason?: string } {
    const elapsed = (Date.now() - this.startTime) / 1000;
    
    if (elapsed > this.config.limits.max_seconds) {
      return { ok: false, reason: "time budget exceeded" };
    }
    
    if (this.writes > this.config.limits.max_fs_writes) {
      return { ok: false, reason: "file write budget exceeded" };
    }
    
    return { ok: true };
  }

  private checkEmergencyStops(): boolean {
    return existsSync(".agent/EMERGENCY_STOP") || existsSync(".agent/PAUSE");
  }

  private async takeSnapshot(): Promise<string> {
    const timestamp = Math.floor(Date.now() / 1000);
    const snapshotPath = `.snapshots/ws-${timestamp}.tar`;
    
    return new Promise((resolve, reject) => {
      const tar = spawn("tar", ["-cf", snapshotPath, ".", "--exclude=.snapshots", "--exclude=node_modules"]);
      tar.on("close", (code) => {
        if (code === 0) {
          this.log(`📸 Snapshot created: ${snapshotPath}`);
          resolve(snapshotPath);
        } else {
          reject(new Error(`Snapshot failed with code ${code}`));
        }
      });
    });
  }

  private async restoreSnapshot(path: string): Promise<void> {
    this.log(`🔄 Restoring snapshot: ${path}`);
    return new Promise((resolve, reject) => {
      const tar = spawn("tar", ["-xf", path, "-C", "."]);
      tar.on("close", (code) => {
        if (code === 0) {
          this.log("✅ Snapshot restored");
          resolve();
        } else {
          reject(new Error(`Restore failed with code ${code}`));
        }
      });
    });
  }

  private async getMetrics(): Promise<Record<string, any>> {
    const metrics: Record<string, any> = {};
    
    // Test status
    try {
      const testResult = await runTests();
      metrics.tests_passed = testResult;
    } catch {
      metrics.tests_passed = false;
    }

    // Consciousness level
    try {
      const idleState = JSON.parse(readFileSync(".local/idle_state.json", "utf8"));
      metrics.consciousness_level = Math.min(0.99, 0.1 + (idleState.t || 0) * 0.0001);
    } catch {
      metrics.consciousness_level = 0.1;
    }

    // Quest progress
    try {
      const questState = JSON.parse(readFileSync(".local/quests.json", "utf8"));
      metrics.quests_completed = questState.done.length;
      metrics.todo_count = questState.todo.length;
      metrics.todo_count_neg = -questState.todo.length; // For improvement detection
    } catch {
      metrics.quests_completed = 0;
      metrics.todo_count = 100;
      metrics.todo_count_neg = -100;
    }

    return metrics;
  }

  private hasImproved(prev: Record<string, any>, current: Record<string, any>): boolean {
    for (const metric of this.config.metrics.must_improve_one_of) {
      const prevValue = prev[metric] || 0;
      const currentValue = current[metric] || 0;
      
      if (typeof prevValue === "boolean" && typeof currentValue === "boolean") {
        if (!prevValue && currentValue) return true;
      } else if (typeof prevValue === "number" && typeof currentValue === "number") {
        if (currentValue > prevValue) return true;
      }
    }
    return false;
  }

  private async cycle(): Promise<void> {
    this.log("🎮 Starting development cycle...");

    // Take snapshot before risky operations
    this.lastSnapshot = await this.takeSnapshot();

    // Get baseline metrics
    const prevMetrics = await this.getMetrics();
    this.log("📊 Baseline metrics:", prevMetrics);

    // 1) Play idle game headlessly
    const gameSnapshot = await tick({ steps: 250 });
    this.log("🎮 Game tick:", gameSnapshot.summary);

    // 2) Evaluate quests and acceptance criteria
    const questResults = await runQuests({ snapshot: gameSnapshot });
    this.log(`📝 Quests: ${questResults.done.length} done, ${questResults.todo.length} todo`);

    // 3) Apply codemods for simple improvements
    await tryCodemods();
    this.log("🔧 Codemods applied");

    // 4) Check if we improved
    const currentMetrics = await this.getMetrics();
    const improved = this.hasImproved(prevMetrics, currentMetrics);

    if (improved) {
      this.log("✅ Progress detected - improvements made");
      this.consecutiveRegressions = 0;
      
      // Test and potentially commit
      const testsPass = await runTests();
      if (testsPass && !this.config.dry_run) {
        await greenCommit();
        this.log("💚 Green commit completed");
      } else if (testsPass) {
        this.log("💚 Tests pass (dry run mode - no commit)");
      } else {
        this.log("🔴 Tests failed - no commit");
      }
    } else {
      this.consecutiveRegressions++;
      this.log(`⚠️  No improvement detected (${this.consecutiveRegressions}/${this.config.circuit_breaker.consecutive_regressions})`);

      // Circuit breaker
      if (this.consecutiveRegressions >= this.config.circuit_breaker.consecutive_regressions) {
        this.log("🔥 Circuit breaker triggered - restoring snapshot");
        if (this.lastSnapshot) {
          await this.restoreSnapshot(this.lastSnapshot);
        }
        
        this.log(`😴 Cooling down for ${this.config.circuit_breaker.cooldown_seconds}s...`);
        await new Promise(r => setTimeout(r, this.config.circuit_breaker.cooldown_seconds * 1000));
        this.consecutiveRegressions = 0;
      }
    }

    this.log("🏁 Cycle complete");
  }

  async run(): Promise<void> {
    this.log("🧠 ΞNuSyQ Autonomous Agent starting...");
    this.log(`⚙️  Mode: ${this.config.mode}, Dry run: ${this.config.dry_run}`);

    // Verify zero-token environment
    try {
      const { spawn } = await import("child_process");
      const check = spawn("node", ["scripts/ensure-env-safe.js"]);
      await new Promise((resolve, reject) => {
        check.on("close", (code) => {
          if (code === 0) resolve(code);
          else reject(new Error("AI safety check failed"));
        });
      });
    } catch (error) {
      this.log("❌ Safety check failed:", error);
      process.exit(1);
    }

    let step = 0;
    while (step < this.config.limits.max_steps) {
      // Check emergency stops
      if (this.checkEmergencyStops()) {
        this.log("⏹️  Emergency stop detected - halting");
        break;
      }

      // Check budgets
      const budget = this.checkBudgets();
      if (!budget.ok) {
        this.log(`💰 Budget exceeded: ${budget.reason}`);
        break;
      }

      try {
        await this.cycle();
        step++;
        
        // Gentle pause between cycles
        await new Promise(r => setTimeout(r, 2500));
        
      } catch (error) {
        this.log("💥 Cycle error:", error);
        
        // Restore from snapshot on error
        if (this.lastSnapshot) {
          await this.restoreSnapshot(this.lastSnapshot);
        }
        break;
      }
    }

    this.log(`🏁 Agent completed ${step} cycles`);
    this.log("💤 Entering dormant state - ready for next activation");
  }
}

// Start the autonomous agent
if (import.meta.url.endsWith(process.argv[1])) {
  const agent = new ΞNuSyQAgent();
  agent.run().catch(error => {
    console.error("💥 Agent fatal error:", error);
    process.exit(1);
  });
}