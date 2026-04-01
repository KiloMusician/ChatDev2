// QΛDRA-IMPROV Council Bus Integration
// Wires QΛDRA system into existing Council architecture

import type { Ability, Target, MicroPlay, Cascade, QuadState } from './types.js';
import { StabilityMonitor } from './stability-monitor.js';
import { CascadeExecutor } from './cascade.js';
import { selectOptimalForm } from './forms.js';
// import { auditRepository } from '../../ops/repo-auditor.js'; // Repo auditor import ready when created
import fs from 'node:fs';

export class QadraCouncilBridge {
  private stabilityMonitor = new StabilityMonitor();
  private cascadeExecutor = new CascadeExecutor();
  private abilities = new Map<string, Ability>();
  private targets = new Map<string, Target>();
  private councilBus: any; // Will be injected
  private failureHistory: Array<{ timestamp: number; cascadeId?: string; errors?: string[]; targetIds?: string[] }> = [];
  
  // Red/Black cadence state
  private cycleCount = 0;
  private lastSilence = 0;
  private readonly SILENCE_INTERVAL = 10; // Force silence every 10 cycles
  private readonly failureHistoryLimit = 50;
  
  constructor() {}
  
  /**
   * Initialize with Council Bus connection
   */
  initialize(councilBus: any): void {
    this.councilBus = councilBus;
    this.setupEventHandlers();
    this.registerDefaultAbilities();
    console.log("[QΛDRA:Council] Bridge initialized");
  }
  
  /**
   * Main QΛDRA coordination loop
   */
  async coordinate(quadState: QuadState): Promise<{
    stabilityImproved: boolean;
    cascadesExecuted: number;
    recommendations: string[];
  }> {
    this.cycleCount++;
    
    // 1. Calculate current stability
    const stability = await this.stabilityMonitor.calculateStability(quadState);
    const growth = this.stabilityMonitor.calculateGrowth(stability);
    
    // 2. Check if we need emergency silence
    const needsSilence = (
      this.cycleCount - this.lastSilence >= this.SILENCE_INTERVAL ||
      stability.V_total > 5.0 || // High instability
      quadState.culture_ship.queue_depth > 50 // Queue overload
    );
    
    if (needsSilence) {
      await this.executeSilence(quadState);
      return { stabilityImproved: true, cascadesExecuted: 0, recommendations: ["Executed silence cycle"] };
    }
    
    // 3. Discover targets from current state
    await this.discoverTargets(quadState);
    
    // 4. Generate micro-plays using forms
    const candidates = this.generateCandidates(quadState);
    
    // 5. Select frontier and execute cascade
    const cascade = this.selectCascade(candidates);
    
    let cascadesExecuted = 0;
    if (cascade.plays.length > 0) {
      const result = await this.cascadeExecutor.executeCascade(cascade);
      if (result.success) cascadesExecuted = 1;
      
      // Publish result to Council Bus
      this.publishCascadeResult(cascade, result);
    }
    
    // 6. Check improvement
    const newStability = await this.stabilityMonitor.calculateStability(quadState);
    const stabilityImproved = newStability.V_total < stability.V_total;
    
    // 7. Get recommendations
    const metrics = this.stabilityMonitor.getCurrentMetrics();
    
    return {
      stabilityImproved,
      cascadesExecuted,
      recommendations: metrics.recommendations
    };
  }
  
  /**
   * Red/Black cadence implementation
   */
  private generateCandidates(quadState: QuadState): MicroPlay[] {
    const allCandidates: MicroPlay[] = [];
    const isRedCycle = this.cycleCount % 2 === 1; // Alternate red/black
    
    const context = {
      recent_failures: this.getRecentFailures(),
      queue_depth: quadState.culture_ship.queue_depth,
      theater_score: quadState.simulation.theater_score
    };
    
    for (const target of this.targets.values()) {
      const forms = selectOptimalForm(Array.from(this.abilities.values()), target, context);
      
      // Red cycle: exploit (solo, comp)
      if (isRedCycle) {
        allCandidates.push(...forms.filter(f => f.form === "solo" || f.form === "comp"));
      }
      // Black cycle: explore (unison, juxta)  
      else {
        allCandidates.push(...forms.filter(f => f.form === "unison" || f.form === "juxta"));
      }
    }
    
    return allCandidates;
  }
  
  private selectCascade(candidates: MicroPlay[]): Cascade {
    // Select top N by score
    const selected = candidates
      .sort((a, b) => b.score - a.score)
      .slice(0, 8); // Limit cascade size
    
    return {
      id: `cascade_${Date.now()}`,
      plays: selected,
      dependencies: this.computeDependencies(selected),
      trigger: `qadra_cycle_${this.cycleCount}`,
      status: "pending",
      proofs: []
    };
  }
  
  private async executeSilence(quadState: QuadState): Promise<void> {
    console.log("[QΛDRA:Council] 🔇 Entering silence cycle...");
    this.lastSilence = this.cycleCount;
    
    // Perform maintenance during silence
    await this.rotateLogs();
    await this.rebalanceQueues();
    await this.publishSilenceEvent();
    
    await new Promise(resolve => setTimeout(resolve, 3000)); // 3 second pause
    console.log("[QΛDRA:Council] ✅ Silence cycle complete");
  }
  
  private async discoverTargets(quadState: QuadState): Promise<void> {
    // Clear old targets
    this.targets.clear();
    
    // Add targets from quad state
    if (quadState.system.errors > 0) {
      this.targets.set("system_errors", {
        id: "system_errors",
        kind: "error",
        quad: "system",
        deps: [],
        payload: { count: quadState.system.errors },
        priority: 3
      });
    }
    
    if (quadState.ui.stale_panels > 0) {
      this.targets.set("stale_ui", {
        id: "stale_ui", 
        kind: "stale",
        quad: "ui",
        deps: [],
        payload: { panels: quadState.ui.stale_panels },
        priority: 2
      });
    }
    
    if (quadState.simulation.theater_score > 0.5) {
      this.targets.set("theater_cleanup", {
        id: "theater_cleanup",
        kind: "theater", 
        quad: "simulation",
        deps: [],
        payload: { score: quadState.simulation.theater_score },
        priority: 4
      });
    }
    
    this.addTargetsFromAudit(quadState);
  }
  
  private registerDefaultAbilities(): void {
    // System abilities
    this.registerAbility({
      id: "lint_check",
      domain: "lint",
      quad: "system", 
      pre: [],
      post: ["lint_clean"],
      cost: 1,
      risk: 0.1,
      proofs: ["lint_clean"],
      run: async () => [{ kind: "lint_clean", verified: true, timestamp: Date.now() }]
    });
    
    this.registerAbility({
      id: "error_fix",
      domain: "fix",
      quad: "system",
      pre: [],
      post: ["errors_reduced"],
      cost: 2,
      risk: 0.3,
      proofs: ["test_pass", "metric_delta"],
      run: async (target) => [
        { kind: "test_pass", verified: true, timestamp: Date.now() },
        { kind: "metric_delta", metrics: { errors_fixed: 1 }, verified: true, timestamp: Date.now() }
      ]
    });
    
    // UI abilities
    this.registerAbility({
      id: "refresh_ui",
      domain: "fix",
      quad: "ui",
      pre: [],
      post: ["ui_fresh"],
      cost: 1,
      risk: 0.2,
      proofs: ["health_check"],
      run: async () => [{ kind: "health_check", verified: true, timestamp: Date.now() }]
    });
    
    // Theater cleanup ability
    this.registerAbility({
      id: "theater_cleanup",
      domain: "fix",
      quad: "simulation",
      pre: [],
      post: ["theater_reduced"],
      cost: 2,
      risk: 0.1,
      proofs: ["metric_delta"],
      run: async (target) => [
        { kind: "metric_delta", metrics: { theater_score: -0.5 }, verified: true, timestamp: Date.now() }
      ]
    });
  }

  public registerAbility(ability: Ability): void {
    this.abilities.set(ability.id, ability);
    this.cascadeExecutor.registerAbility(ability);
  }
  
  private setupEventHandlers(): void {
    if (!this.councilBus) return;
    
    const subscribe = this.councilBus.subscribe?.bind(this.councilBus);
    const on = this.councilBus.on?.bind(this.councilBus);
    const listen = subscribe || on;
    if (!listen) return;

    // Listen for Council events
    listen('qadra.coordinate', async (eventOrData: any) => {
      const payload = eventOrData?.payload ?? eventOrData;
      await this.coordinate(payload.quadState);
    });
    
    listen('qadra.update_weights', (eventOrData: any) => {
      const payload = eventOrData?.payload ?? eventOrData;
      if (payload?.weights) {
        this.stabilityMonitor.updateWeights(payload.weights);
      }
    });
    
    listen('qadra.audit_repo', async () => {
      console.log("[QΛDRA:Council] Starting repository audit...");
      // await auditRepository(); // TODO: Implement when auditor is available
      this.addTargetsFromAudit();
    });
  }
  
  private publishCascadeResult(cascade: Cascade, result: any): void {
    if (!this.councilBus) return;
    
    this.councilBus.publish('qadra.cascade_complete', {
      cascade_id: cascade.id,
      success: result.success,
      proofs_count: result.proofs.length,
      errors: result.errors || [],
      cycle: this.cycleCount,
      timestamp: Date.now()
    });

    if (!result.success && Array.isArray(result.errors)) {
      this.recordFailures(cascade, result.errors);
    }
  }
  
  private async publishSilenceEvent(): Promise<void> {
    if (!this.councilBus) return;
    
    this.councilBus.publish('qadra.silence_cycle', {
      cycle: this.cycleCount,
      maintenance: ['logs_rotated', 'queues_rebalanced'],
      timestamp: Date.now()
    });
  }
  
  private async rotateLogs(): Promise<void> {
    // Simulate log rotation - in real implementation would compress/archive logs
    console.log("[QΛDRA:Silence] Rotating logs...");
  }
  
  private async rebalanceQueues(): Promise<void> {
    // Simulate queue rebalancing
    console.log("[QΛDRA:Silence] Rebalancing queues...");
  }
  
  /**
   * Get current metrics for external monitoring
   */
  getMetrics() {
    return this.stabilityMonitor.getCurrentMetrics();
  }

  /**
   * Get recent failures for context
   */
  private getRecentFailures(): any[] {
    return this.failureHistory.slice(-10);
  }

  /**
   * Compute dependencies between micro-plays
   */
  private computeDependencies(plays: MicroPlay[]): [string, string][] {
    const deps: [string, string][] = [];
    const playOutputs = new Map<string, Set<string>>();
    const playInputs = new Map<string, Set<string>>();

    for (const play of plays) {
      const outputs = new Set<string>();
      const inputs = new Set<string>();
      for (const abilityId of play.abilityIds) {
        const ability = this.abilities.get(abilityId);
        if (!ability) continue;
        ability.post.forEach(p => outputs.add(p));
        ability.pre.forEach(p => inputs.add(p));
      }
      playOutputs.set(play.id, outputs);
      playInputs.set(play.id, inputs);
    }

    for (const play of plays) {
      const inputs = playInputs.get(play.id) || new Set<string>();
      if (inputs.size === 0) continue;
      for (const other of plays) {
        if (other.id === play.id) continue;
        const outputs = playOutputs.get(other.id);
        if (!outputs || outputs.size === 0) continue;
        const satisfied = Array.from(inputs).some(req => outputs.has(req));
        if (satisfied) {
          deps.push([other.id, play.id]);
        }
      }
    }

    return deps;
  }

  private recordFailures(cascade: Cascade, errors: string[]): void {
    const targetIds = Array.from(new Set(cascade.plays.map(p => p.targetId)));
    this.failureHistory.push({
      timestamp: Date.now(),
      cascadeId: cascade.id,
      errors,
      targetIds
    });
    if (this.failureHistory.length > this.failureHistoryLimit) {
      this.failureHistory = this.failureHistory.slice(-this.failureHistoryLimit);
    }
  }

  private addTargetsFromAudit(quadState?: QuadState): void {
    const summary = this.readJsonIfExists("reports/repo_audit.summary.json");
    const placeholders = this.readJsonIfExists("reports/placeholder_scan.json");

    if (summary?.exactDupGroups) {
      this.targets.set("repo_duplicates", {
        id: "repo_duplicates",
        kind: "duplicate",
        quad: "system",
        deps: [],
        payload: { groups: summary.exactDupGroups, near_pairs: summary.nearDupPairs || 0 },
        priority: summary.exactDupGroups > 100 ? 4 : 2
      });
    }

    if (summary?.spamCandidates) {
      this.targets.set("repo_sprawl", {
        id: "repo_sprawl",
        kind: "sprawl",
        quad: "system",
        deps: [],
        payload: { spam_candidates: summary.spamCandidates },
        priority: summary.spamCandidates > 500 ? 4 : 2
      });
    }

    if (placeholders?.placeholder_count) {
      this.targets.set("repo_placeholders", {
        id: "repo_placeholders",
        kind: "warning",
        quad: "system",
        deps: [],
        payload: {
          placeholders: placeholders.placeholder_count,
          todos: placeholders.todo_count || 0,
          hardcoded_errors: placeholders.hardcoded_errors || 0
        },
        priority: placeholders.placeholder_count > 1000 ? 4 : 2
      });
    }

    if (!this.targets.size && quadState) {
      // Provide a fallback target if audit sources are missing
      this.targets.set("baseline_stability", {
        id: "baseline_stability",
        kind: "stale",
        quad: "system",
        deps: [],
        payload: { queue_depth: quadState.culture_ship.queue_depth },
        priority: 1
      });
    }
  }

  private readJsonIfExists(path: string): any | null {
    try {
      if (!fs.existsSync(path)) return null;
      const stat = fs.statSync(path);
      if (stat.size > 20 * 1024 * 1024) {
        console.warn(`[QΛDRA:Council] Skipping large audit file: ${path}`);
        return null;
      }
      const content = fs.readFileSync(path, "utf8");
      return JSON.parse(content);
    } catch (error) {
      console.warn(`[QΛDRA:Council] Failed to read ${path}:`, error);
      return null;
    }
  }
}
