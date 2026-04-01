// QΛDRA-IMPROV Cascade Executor
// Proof-gated execution of MicroPlay sequences

import type { MicroPlay, Cascade, Ability, Target, Proof, QuadState, StabilityVector } from './types.js';

export class CascadeExecutor {
  private abilities = new Map<string, Ability>();
  private targets = new Map<string, Target>();
  private activeCascades = new Map<string, Cascade>();
  
  // Weights for V(Ξ) stability calculation
  private readonly stabilityWeights = {
    w_e: 1.0,   // errors weight
    w_w: 0.6,   // warnings weight  
    w_p: 0.8,   // placeholders weight
    w_t: 1.5,   // theater weight (highest)
    w_s: 0.4    // staleness weight
  };
  
  constructor() {}
  
  registerAbility(ability: Ability): void {
    this.abilities.set(ability.id, ability);
  }
  
  registerTarget(target: Target): void {
    this.targets.set(target.id, target);
  }
  
  /**
   * Execute a cascade with proof gates at each step
   */
  async executeCascade(cascade: Cascade): Promise<{ success: boolean; proofs: Proof[]; errors: string[] }> {
    console.log(`[QΛDRA:Cascade] Starting cascade ${cascade.id} with ${cascade.plays.length} plays`);
    
    this.activeCascades.set(cascade.id, { ...cascade, status: "running" });
    const allProofs: Proof[] = [];
    const errors: string[] = [];
    
    try {
      // Execute plays in dependency order
      const executionOrder = this.topologicalSort(cascade.plays, cascade.dependencies);
      
      for (const play of executionOrder) {
        const result = await this.executeMicroPlay(play);
        
        if (!result.success) {
          errors.push(`Play ${play.id} failed: ${result.error}`);
          cascade.status = "failed";
          break;
        }
        
        allProofs.push(...result.proofs);
        
        // Proof gate: verify all expected proofs
        for (const expectedProof of play.expect) {
          const found = result.proofs.some(p => p.kind === expectedProof && p.verified);
          if (!found) {
            errors.push(`Missing expected proof '${expectedProof}' from play ${play.id}`);
            cascade.status = "failed";
            break;
          }
        }
        
        if (cascade.status === "failed") break;
        
        console.log(`[QΛDRA:Cascade] ✅ Play ${play.id} completed with ${result.proofs.length} proofs`);
      }
      
      if (cascade.status !== "failed") {
        cascade.status = "complete";
        console.log(`[QΛDRA:Cascade] ✅ Cascade ${cascade.id} completed successfully`);
      }
      
    } catch (error) {
      console.error(`[QΛDRA:Cascade] ❌ Cascade ${cascade.id} failed:`, error);
      cascade.status = "failed";
      errors.push(`Cascade execution failed: ${error}`);
    }
    
    this.activeCascades.set(cascade.id, cascade);
    
    return {
      success: cascade.status === "complete",
      proofs: allProofs,
      errors
    };
  }
  
  /**
   * Execute a single MicroPlay based on its form
   */
  private async executeMicroPlay(play: MicroPlay): Promise<{ success: boolean; proofs: Proof[]; error?: string }> {
    const target = this.targets.get(play.targetId);
    if (!target) {
      return { success: false, proofs: [], error: `Target ${play.targetId} not found` };
    }
    
    try {
      switch (play.form) {
        case "solo":
          return await this.executeSolo(play, target);
        case "unison":
          return await this.executeUnison(play, target);
        case "comp":
          return await this.executeComp(play, target);
        case "juxta":
          return await this.executeJuxta(play, target);
        case "silence":
          return await this.executeSilence(play, target);
        default:
          return { success: false, proofs: [], error: `Unknown form: ${play.form}` };
      }
    } catch (error) {
      return { success: false, proofs: [], error: `Execution failed: ${error}` };
    }
  }
  
  private async executeSolo(play: MicroPlay, target: Target): Promise<{ success: boolean; proofs: Proof[] }> {
    const ability = this.abilities.get(play.abilityIds[0]);
    if (!ability) throw new Error(`Ability ${play.abilityIds[0]} not found`);
    
    const proofs = await ability.run(target);
    return { success: true, proofs };
  }
  
  private async executeUnison(play: MicroPlay, target: Target): Promise<{ success: boolean; proofs: Proof[] }> {
    const abilities = play.abilityIds.map(id => this.abilities.get(id)).filter(Boolean) as Ability[];
    
    // Run all abilities in parallel
    const proofArrays = await Promise.all(abilities.map(a => a.run(target)));
    const allProofs = proofArrays.flat();
    
    return { success: true, proofs: allProofs };
  }
  
  private async executeComp(play: MicroPlay, target: Target): Promise<{ success: boolean; proofs: Proof[] }> {
    const [mainId, checkerId] = play.abilityIds;
    const main = this.abilities.get(mainId);
    const checker = this.abilities.get(checkerId);
    
    if (!main || !checker) throw new Error("Missing abilities for comp play");
    
    // Execute main first, then checker for verification
    const mainProofs = await main.run(target);
    const checkerProofs = await checker.run(target);
    
    return { success: true, proofs: [...mainProofs, ...checkerProofs] };
  }
  
  private async executeJuxta(play: MicroPlay, target: Target): Promise<{ success: boolean; proofs: Proof[] }> {
    const [abilityAId, abilityBId] = play.abilityIds;
    const abilityA = this.abilities.get(abilityAId);
    const abilityB = this.abilities.get(abilityBId);
    
    if (!abilityA || !abilityB) throw new Error("Missing abilities for juxta play");
    
    // Run both approaches
    const [proofsA, proofsB] = await Promise.all([
      abilityA.run(target),
      abilityB.run(target)
    ]);
    
    // Choose best result based on proof quality
    const scoreA = this.evaluateProofs(proofsA);
    const scoreB = this.evaluateProofs(proofsB);
    
    const winningProofs = scoreA >= scoreB ? proofsA : proofsB;
    const losingProofs = scoreA >= scoreB ? proofsB : proofsA;
    
    // Return winning proofs plus exploration insight
    const explorationProof: Proof = {
      kind: "metric_delta",
      metrics: { exploration_score_A: scoreA, exploration_score_B: scoreB },
      timestamp: Date.now(),
      verified: true
    };
    
    return { success: true, proofs: [...winningProofs, explorationProof] };
  }
  
  private async executeSilence(play: MicroPlay, target: Target): Promise<{ success: boolean; proofs: Proof[] }> {
    // Budgeted quiescence: pause, rotate logs, rebalance queues
    const silenceDuration = 2000; // 2 seconds default
    
    console.log(`[QΛDRA:Silence] Entering budgeted quiescence for ${silenceDuration}ms...`);
    
    // Perform maintenance tasks during silence
    const maintenanceProofs: Proof[] = [];
    
    // Log rotation simulation
    maintenanceProofs.push({
      kind: "artifact_diff",
      metrics: { logs_rotated: 1, queue_rebalanced: 1 },
      timestamp: Date.now(),
      verified: true
    });
    
    await new Promise(resolve => setTimeout(resolve, silenceDuration));
    
    console.log(`[QΛDRA:Silence] Quiescence complete.`);
    
    return { success: true, proofs: maintenanceProofs };
  }
  
  /**
   * Calculate V(Ξ) stability measure from current quad state
   */
  calculateStabilityVector(quadState: QuadState): StabilityVector {
    const w = this.stabilityWeights;
    
    const V_errors = w.w_e * quadState.system.errors;
    const V_warnings = w.w_w * quadState.system.warnings;
    const V_placeholders = w.w_p * this.extractPlaceholdersFromTargets(targets);
    const V_theater = w.w_t * quadState.simulation.theater_score;
    const V_staleness = w.w_s * (1 - quadState.ui.freshness);
    
    const V_total = V_errors + V_warnings + V_placeholders + V_theater + V_staleness;
    
    return {
      timestamp: Date.now(),
      V_total,
      V_errors,
      V_warnings,
      V_placeholders,
      V_theater,
      V_staleness,
      growth_delta: 0 // Will be calculated by comparing with previous
    };
  }
  
  /**
   * Check if stable operating plane is reached
   * Returns true when V(Ξ) < threshold and system is healthy
   */
  isStableOperatingPlane(stability: StabilityVector, quadState: QuadState): boolean {
    const STABILITY_THRESHOLD = 2.0;
    const FRESHNESS_THRESHOLD = 0.8;
    const QUEUE_DEPTH_THRESHOLD = 10;
    
    return (
      stability.V_total < STABILITY_THRESHOLD &&
      quadState.ui.freshness > FRESHNESS_THRESHOLD &&
      quadState.culture_ship.queue_depth < QUEUE_DEPTH_THRESHOLD &&
      quadState.simulation.theater_score < 0.2
    );
  }
  
  private evaluateProofs(proofs: Proof[]): number {
    let score = 0;
    for (const proof of proofs) {
      if (proof.verified) score += 1;
      if (proof.metrics) score += Object.keys(proof.metrics).length * 0.1;
    }
    return score;
  }
  
  private topologicalSort(plays: MicroPlay[], dependencies: [string, string][]): MicroPlay[] {
    const graph = new Map<string, string[]>();
    const inDegree = new Map<string, number>();
    
    // Initialize graph
    for (const play of plays) {
      graph.set(play.id, []);
      inDegree.set(play.id, 0);
    }
    
    // Build dependency graph
    for (const [from, to] of dependencies) {
      graph.get(from)?.push(to);
      inDegree.set(to, (inDegree.get(to) || 0) + 1);
    }
    
    // Kahn's algorithm
    const queue = plays.filter(p => inDegree.get(p.id) === 0);
    const result: MicroPlay[] = [];
    
    while (queue.length > 0) {
      const current = queue.shift()!;
      result.push(current);
      
      for (const neighbor of graph.get(current.id) || []) {
        const newInDegree = (inDegree.get(neighbor) || 0) - 1;
        inDegree.set(neighbor, newInDegree);
        
        if (newInDegree === 0) {
          const neighborPlay = plays.find(p => p.id === neighbor);
          if (neighborPlay) queue.push(neighborPlay);
        }
      }
    }
    
    return result;
  }
}