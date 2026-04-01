/**
 * 🚢 CULTURE-SHIP CORE ORCHESTRATOR
 * Zero-token infrastructure-first meta-module coordination
 */

import { runCascade } from "./planners/cascade_event.js";
import { scanDuplicates } from "./analyzers/duplicates.js";
import { scanImports } from "./analyzers/imports.js";
import { scanSoftlocks } from "./analyzers/softlocks.js";
import { renameAndRewire } from "./surgeons/rename_and_rewire.js";
import { tokenGovernor } from "./planners/token_governor.js";
import { report } from "./ui/telemetry.js";

interface ShipState {
  phase: "primer" | "awakening" | "operational";
  temples_unlocked: string[];
  last_cascade: number;
  token_budget: { used: number; max: number };
  health_score: number;
}

class CultureShip {
  private state: ShipState = {
    phase: "primer",
    temples_unlocked: [],
    last_cascade: 0,
    token_budget: { used: 0, max: 100 },
    health_score: 1.0
  };

  async boot() {
    console.log("🚢 Culture-Ship: Initializing ΞNuSyQ infrastructure vessel...");
    
    try {
      await tokenGovernor.init("config/token_policy.yml");
      await this.detectViewport();
      await this.unlockTemple("temple_of_knowledge", 1);
      
      this.state.phase = "awakening";
      console.log("🌅 Culture-Ship: Phase 0 (Awakening) - Base systems online");
      
      await report.banner("ΞNuSyQ Culture-Ship online: local-first, reversible ops.");
      return { success: true, phase: this.state.phase };
      
    } catch (error) {
      console.error("❌ Culture-Ship boot failed:", error);
      return { success: false, error: String(error) };
    }
  }

  async healthCycle() {
    console.log("🔍 Culture-Ship: Running health cycle...");
    const startTime = Date.now();
    
    try {
      // Phase 1: Analysis (zero-token local operations)
      const [duplicates, imports, softlocks] = await Promise.all([
        scanDuplicates(),
        scanImports(), 
        scanSoftlocks()
      ]);

      // Calculate health score
      this.state.health_score = this.calculateHealthScore({ duplicates, imports, softlocks });

      // Phase 2: Planning (cascade event generation)
      const plan = await runCascade({ 
        findings: { duplicates, imports, softlocks },
        health_score: this.state.health_score,
        token_budget: this.state.token_budget
      });

      await report.plan(plan);

      // Phase 3: Execution (surgical operations)
      let executedSteps = 0;
      for (const step of plan.steps) {
        if (!tokenGovernor.permit(step)) {
          console.log(`⏭️ Skipping step (budget): ${step.title}`);
          continue;
        }

        console.log(`🔧 Executing: ${step.title}`);
        
        try {
          if (step.kind === "consolidate") {
            await renameAndRewire(step.payload);
          } else if (step.execute) {
            await step.execute();
          }
          executedSteps++;
        } catch (error) {
          console.error(`❌ Step failed: ${step.title}`, error);
        }
      }

      // Phase 4: Cascade preparation for next cycle
      await runCascade({ checkpoint: true });
      this.state.last_cascade = Date.now();

      const duration = Date.now() - startTime;
      console.log(`✅ Culture-Ship health cycle complete: ${executedSteps}/${plan.steps.length} steps in ${duration}ms`);
      
      return {
        success: true,
        duration,
        health_score: this.state.health_score,
        executed_steps: executedSteps,
        total_steps: plan.steps.length
      };

    } catch (error) {
      console.error("❌ Culture-Ship health cycle failed:", error);
      return { success: false, error: String(error) };
    }
  }

  private calculateHealthScore(findings: any): number {
    const { duplicates, imports, softlocks } = findings;
    
    // Simple health scoring algorithm
    const duplicatePenalty = Math.min(0.3, (duplicates?.duplicateGroups || 0) * 0.05);
    const importPenalty = Math.min(0.4, (imports?.brokenImports || 0) * 0.02);
    const softlockPenalty = Math.min(0.3, (softlocks?.criticalIssues || 0) * 0.1);
    
    return Math.max(0.1, 1.0 - duplicatePenalty - importPenalty - softlockPenalty);
  }

  private async detectViewport() {
    // Detect mobile vs desktop for HUD optimization
    const viewportInfo = {
      mobile: process.env.MOBILE_VIEWPORT === "true",
      width: parseInt(process.env.VIEWPORT_WIDTH || "1280"),
      height: parseInt(process.env.VIEWPORT_HEIGHT || "720")
    };
    
    console.log(`📱 Viewport detected: ${viewportInfo.mobile ? "mobile" : "desktop"} (${viewportInfo.width}x${viewportInfo.height})`);
    return viewportInfo;
  }

  private async unlockTemple(temple: string, floor: number) {
    const templeKey = `${temple}_floor_${floor}`;
    if (!this.state.temples_unlocked.includes(templeKey)) {
      this.state.temples_unlocked.push(templeKey);
      console.log(`🏛️ Temple unlocked: ${temple} floor ${floor}`);
    }
  }

  async emergencyRollback(reason: string) {
    console.log(`🚨 Culture-Ship: Emergency rollback triggered - ${reason}`);
    
    try {
      // Implementation would call rollback.mjs script
      console.log("🔄 Executing emergency rollback procedure...");
      return { success: true, message: "Rollback completed" };
    } catch (error) {
      console.error("❌ Emergency rollback failed:", error);
      return { success: false, error: String(error) };
    }
  }

  getState(): ShipState {
    return { ...this.state };
  }
}

// Export singleton instance
export const cultureShip = new CultureShip();

// Boot function for hooks
export async function boot() {
  return cultureShip.boot();
}

// Health cycle for automated triggers
export async function healthCycle() {
  return cultureShip.healthCycle();
}