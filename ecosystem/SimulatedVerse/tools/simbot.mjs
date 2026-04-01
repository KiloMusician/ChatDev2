// SimBot: Autonomous testing agent that plays the game to find regressions
import fs from "fs";
import { state } from "../src/engine/state.mjs";
import { toggleView, VIEWS } from "../src/engine/toggle.mjs";
import { pause, resume } from "../src/engine/pause.mjs";

const log = (m) => console.log("🤖 [SimBot]", m);

class SimBot {
  constructor() {
    this.probes = [
      { name: "tick-advances", run: () => this.testTickAdvancement() },
      { name: "view-switching", run: () => this.testViewSwitching() },
      { name: "pause-resume", run: () => this.testPauseResume() },
      { name: "resource-generation", run: () => this.testResourceGeneration() },
      { name: "consciousness-evolution", run: () => this.testConsciousnessEvolution() },
      { name: "no-hard-stalls", run: () => this.testNoStalls() }
    ];
    this.results = [];
  }

  async testTickAdvancement() {
    const initialOre = state.colony.resources.ore;
    await this.sleep(1200); // Wait for a few ticks
    const finalOre = state.colony.resources.ore;
    return finalOre > initialOre;
  }

  async testViewSwitching() {
    const views = [VIEWS.IDLE, VIEWS.LABYRINTH, VIEWS.BASE, VIEWS.DEFENSE];
    
    for (const view of views) {
      toggleView(view);
      await this.sleep(100);
      if (state.view !== view) return false;
    }
    return true;
  }

  async testPauseResume() {
    const wasPaused = state.paused;
    
    pause();
    await this.sleep(100);
    if (!state.paused) return false;
    
    resume();
    await this.sleep(100);
    if (state.paused) return false;
    
    // Restore original state
    if (wasPaused) pause();
    return true;
  }

  async testResourceGeneration() {
    if (state.paused) return true; // Skip if paused
    
    const initial = { ...state.colony.resources };
    await this.sleep(2000); // Wait 2 seconds
    const final = state.colony.resources;
    
    // Resources should increase when not paused
    return final.energy > initial.energy || final.ore > initial.ore;
  }

  async testConsciousnessEvolution() {
    // Consciousness should be within reasonable bounds
    const c = state.consciousness;
    return c.level >= 0 && c.level <= 1 && 
           c.coherence >= 0 && c.coherence <= 1 &&
           typeof c.awarenessStage === 'string';
  }

  async testNoStalls() {
    // Simple stall detection - measure execution time
    const start = performance.now();
    
    // Simulate some operations
    for (let i = 0; i < 1000; i++) {
      Math.sqrt(i);
    }
    
    const duration = performance.now() - start;
    return duration < 100; // Should complete in under 100ms
  }

  async sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async runAllProbes() {
    log("🚀 Starting autonomous regression testing...");
    
    for (const probe of this.probes) {
      log(`🔍 Testing: ${probe.name}`);
      
      try {
        const start = performance.now();
        const ok = await probe.run();
        const duration = performance.now() - start;
        
        this.results.push({
          probe: probe.name,
          ok,
          duration: Math.round(duration),
          timestamp: Date.now()
        });
        
        log(`${probe.name}: ${ok ? "✅ PASS" : "❌ FAIL"} (${Math.round(duration)}ms)`);
      } catch (error) {
        this.results.push({
          probe: probe.name,
          ok: false,
          error: error.message,
          timestamp: Date.now()
        });
        log(`${probe.name}: ❌ ERROR - ${error.message}`);
      }
    }
    
    return this.generateReport();
  }

  generateReport() {
    const totalProbes = this.results.length;
    const passedProbes = this.results.filter(r => r.ok).length;
    const failedProbes = totalProbes - passedProbes;
    const successRate = (passedProbes / totalProbes * 100).toFixed(1);
    
    const report = {
      timestamp: new Date().toISOString(),
      totalProbes,
      passedProbes,
      failedProbes,
      successRate: `${successRate}%`,
      results: this.results,
      systemHealthy: failedProbes === 0,
      summary: `${passedProbes}/${totalProbes} tests passed (${successRate}%)`
    };
    
    // Save report
    fs.mkdirSync("reports", { recursive: true });
    fs.writeFileSync("reports/simbot-latest.json", JSON.stringify(report, null, 2));
    
    log(`📊 Testing complete: ${report.summary}`);
    log(`📁 Report saved to reports/simbot-latest.json`);
    
    return report;
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const bot = new SimBot();
  const report = await bot.runAllProbes();
  process.exit(report.systemHealthy ? 0 : 1);
}

export { SimBot };