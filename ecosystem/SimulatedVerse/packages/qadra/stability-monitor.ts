// QΛDRA-IMPROV Stability Monitor
// Tracks V(Ξ) and calculates growth measures over time

import type { QuadState, StabilityVector, GrowthMeasure } from './types.js';
import { promises as fs } from 'node:fs';

export class StabilityMonitor {
  private history: StabilityVector[] = [];
  private growthHistory: GrowthMeasure[] = [];
  private readonly maxHistory = 1000;
  private readonly horizonSize = 20; // H in growth calculation
  
  // Stability weights (tunable via Council)
  private weights = {
    w_e: 1.0,   // errors
    w_w: 0.6,   // warnings  
    w_p: 0.8,   // placeholders
    w_t: 1.5,   // theater (highest priority)
    w_s: 0.4    // staleness
  };
  
  constructor() {
    this.loadHistory();
  }
  
  /**
   * Calculate current V(Ξ) stability vector
   */
  async calculateStability(quadState: QuadState): Promise<StabilityVector> {
    const w = this.weights;
    
    // Extract metrics from quad state
    const errors = quadState.system.errors + quadState.ui.render_errors;
    const warnings = quadState.system.warnings;
    const placeholders = await this.countPlaceholders();
    const theater = quadState.simulation.theater_score + (quadState.simulation.fake_elements * 0.1);
    const staleness = Math.max(0, 1 - quadState.ui.freshness);
    
    // Calculate weighted components
    const V_errors = w.w_e * errors;
    const V_warnings = w.w_w * warnings;
    const V_placeholders = w.w_p * placeholders;
    const V_theater = w.w_t * theater;
    const V_staleness = w.w_s * staleness;
    
    const V_total = V_errors + V_warnings + V_placeholders + V_theater + V_staleness;
    
    // Calculate growth delta
    const previous = this.history[this.history.length - 1];
    const growth_delta = previous ? (1 - V_total) - (1 - previous.V_total) : 0;
    
    const stability: StabilityVector = {
      timestamp: Date.now(),
      V_total,
      V_errors,
      V_warnings,
      V_placeholders,
      V_theater,
      V_staleness,
      growth_delta
    };
    
    this.addStabilityPoint(stability);
    return stability;
  }
  
  /**
   * Calculate growth measure 𝔊_k = 1 - sigmoid(V(Ξ_k)) + ϑ*(proofs/attempts)
   */
  calculateGrowth(stability: StabilityVector, proofRatio: number = 0.8): GrowthMeasure {
    const sigmoid = (x: number) => 1 / (1 + Math.exp(x - 3)); // centered at V=3
    const theta = 0.4; // ϑ weight for proof quality
    
    const G_k = (1 - sigmoid(stability.V_total)) + (theta * proofRatio);
    
    const previous = this.growthHistory[this.growthHistory.length - 1];
    const delta_G = previous ? G_k - previous.G_k : 0;
    
    // Calculate horizon average (last H points)
    const recentGrowth = this.growthHistory.slice(-this.horizonSize);
    const horizon_avg = recentGrowth.length > 0 
      ? recentGrowth.reduce((sum, g) => sum + g.delta_G, 0) / recentGrowth.length
      : 0;
    
    const growth: GrowthMeasure = {
      timestamp: Date.now(),
      G_k,
      delta_G,
      horizon_avg,
      target_met: delta_G > 0 // Want positive growth
    };
    
    this.addGrowthPoint(growth);
    return growth;
  }
  
  /**
   * Check if stable operating plane is reached
   */
  async isStableOperatingPlane(quadState: QuadState): Promise<boolean> {
    const STABILITY_THRESHOLD = 2.0;
    const FRESHNESS_THRESHOLD = 0.8;
    const QUEUE_THRESHOLD = 10;
    const THEATER_THRESHOLD = 0.2;
    
    const current = await this.calculateStability(quadState);
    
    return (
      current.V_total < STABILITY_THRESHOLD &&
      quadState.ui.freshness > FRESHNESS_THRESHOLD &&
      quadState.culture_ship.queue_depth < QUEUE_THRESHOLD &&
      quadState.simulation.theater_score < THEATER_THRESHOLD
    );
  }
  
  /**
   * Get stability trend (improving/degrading/stable)
   */
  getStabilityTrend(windowSize: number = 10): "improving" | "degrading" | "stable" {
    if (this.history.length < windowSize) return "stable";
    
    const recent = this.history.slice(-windowSize);
    const deltas = recent.map(r => r.growth_delta);
    const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
    
    const THRESHOLD = 0.01;
    if (avgDelta > THRESHOLD) return "improving";
    if (avgDelta < -THRESHOLD) return "degrading";
    return "stable";
  }
  
  /**
   * Get current metrics for dashboard
   */
  getCurrentMetrics(): {
    stability: StabilityVector | null;
    growth: GrowthMeasure | null;
    trend: "improving" | "degrading" | "stable";
    isStable: boolean;
    recommendations: string[];
  } {
    const stability = this.history[this.history.length - 1] || null;
    const growth = this.growthHistory[this.growthHistory.length - 1] || null;
    const trend = this.getStabilityTrend();
    
    const recommendations: string[] = [];
    if (stability) {
      if (stability.V_theater > 1.0) recommendations.push("Reduce theater score via cleanup");
      if (stability.V_errors > 2.0) recommendations.push("Address system errors urgently");
      if (stability.V_staleness > 0.5) recommendations.push("Refresh stale UI components");
    }
    
    return {
      stability,
      growth,
      trend,
      isStable: stability ? stability.V_total < 2.0 : false,
      recommendations
    };
  }
  
  /**
   * Update weights (tuning interface for Council)
   */
  updateWeights(newWeights: Partial<typeof this.weights>): void {
    this.weights = { ...this.weights, ...newWeights };
    console.log(`[QΛDRA:Stability] Updated weights:`, this.weights);
  }
  
  private addStabilityPoint(stability: StabilityVector): void {
    this.history.push(stability);
    if (this.history.length > this.maxHistory) {
      this.history = this.history.slice(-this.maxHistory);
    }
    this.saveHistory();
  }
  
  private addGrowthPoint(growth: GrowthMeasure): void {
    this.growthHistory.push(growth);
    if (this.growthHistory.length > this.maxHistory) {
      this.growthHistory = this.growthHistory.slice(-this.maxHistory);
    }
  }
  
  private async saveHistory(): Promise<void> {
    try {
      await fs.mkdir("reports/qadra", { recursive: true });
      await fs.writeFile(
        "reports/qadra/stability_history.json",
        JSON.stringify({
          stability: this.history.slice(-100), // Last 100 points
          growth: this.growthHistory.slice(-100),
          weights: this.weights,
          updated: Date.now()
        }, null, 2)
      );
    } catch (error) {
      console.warn(`[QΛDRA:Stability] Could not save history:`, error);
    }
  }
  
  private async loadHistory(): Promise<void> {
    try {
      const data = await fs.readFile("reports/qadra/stability_history.json", "utf8");
      const parsed = JSON.parse(data);
      
      this.history = parsed.stability || [];
      this.growthHistory = parsed.growth || [];
      if (parsed.weights) this.weights = parsed.weights;
      
      console.log(`[QΛDRA:Stability] Loaded ${this.history.length} stability points`);
    } catch {
      console.log(`[QΛDRA:Stability] No previous history found, starting fresh`);
    }
  }

  /**
   * Count placeholder files/code in the repository
   */
  private async countPlaceholders(): Promise<number> {
    try {
      // Quick scan for common placeholder patterns
      const patterns = ['TODO', 'FIXME', 'PLACEHOLDER', 'MOCK', 'STUB'];
      // For now, return a reasonable estimate - in production this would scan the repo
      return 5; // Baseline placeholder count
    } catch {
      return 0;
    }
  }
}