import { loopOrchestrator, type LoopDecision } from "./loop_orchestrator.js";
import { puQueue } from "./pu_queue.js";
import { LOOP_CONFIG } from "../config/constants.js";
import { log } from "./log.js";

const LOG_AUTONOMOUS_LOOP = process.env.LOG_AUTONOMOUS_LOOP === '1';

function logLoopInfo(message: string, data?: any) {
  if (!LOG_AUTONOMOUS_LOOP) return;
  log.info(data, message);
}

/**
 * Autonomous Loop Runner
 * 
 * Continuously evaluates system state and makes intelligent decisions
 * about loop handling without requiring user confirmation.
 * 
 * This replaces hardcoded loop behaviors with contextual AI Council decisions.
 */
export class AutonomousLoopRunner {
  private isRunning = false;
  private currentDecision: LoopDecision | null = null;
  private evaluationTimer: NodeJS.Timeout | null = null;
  private loopCounter = 0;

  /**
   * Start the autonomous loop system
   */
  start() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.loopCounter = 0;
    
    logLoopInfo("[AUTONOMOUS-LOOP] Starting real autonomous loop");
    
    // Start with a longer interval to prevent overwhelming the system
    this.scheduleNextEvaluation(LOOP_CONFIG.EVALUATION_INTERVAL_MS);
  }

  /**
   * Stop the autonomous loop system
   */
  stop() {
    if (!this.isRunning) return;

    this.isRunning = false;
    if (this.evaluationTimer) {
      clearTimeout(this.evaluationTimer);
      this.evaluationTimer = null;
    }
    
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous loop system stopped");
  }

  /**
   * Schedule the next loop evaluation
   */
  private scheduleNextEvaluation(delayMs: number) {
    if (!this.isRunning) return;

    this.evaluationTimer = setTimeout(() => {
      this.evaluateAndAct();
    }, delayMs);
  }

  /**
   * Core evaluation and action cycle
   */
  private async evaluateAndAct() {
    if (!this.isRunning) return;

    try {
      this.loopCounter++;
      logLoopInfo(`[AUTONOMOUS-LOOP] Evaluation cycle ${this.loopCounter}`);

      // Get AI Council decision on loop action
      const decision = await loopOrchestrator.decideLoopAction();
      this.currentDecision = decision;

      // Execute the decided action autonomously
      await loopOrchestrator.executeLoopAction(decision);

      // Log decision for transparency
      logLoopInfo(`[AUTONOMOUS-LOOP] Decision executed: ${decision.action} (${Math.round(decision.confidence * 100)}%)`);
      logLoopInfo(`[AUTONOMOUS-LOOP] Reasoning: ${decision.reasoning}`);

      // Additional autonomous actions based on decision
      await this.executeAutonomousActions(decision);

      // Schedule next evaluation based on decision
      this.scheduleNextEvaluation(decision.next_evaluation_ms);

    } catch (error) {
      log.error({ error }, "[AUTONOMOUS-LOOP] Evaluation failed");
      // Fallback to safe default interval
      this.scheduleNextEvaluation(LOOP_CONFIG.EVALUATION_INTERVAL_MS);
    }
  }

  /**
   * Execute additional autonomous actions based on AI Council decision
   */
  private async executeAutonomousActions(decision: LoopDecision) {
    switch (decision.action) {
      case "proceed":
        await this.accelerateProcessing();
        break;
        
      case "optimize":
        await this.optimizeSystemPerformance();
        break;
        
      case "research":
        await this.initiateResearchProtocols();
        break;
        
      case "fix":
        await this.deployFixProtocols();
        break;
        
      case "repeat":
        await this.repeatSuccessfulPatterns();
        break;
        
      case "escalate":
        await this.escalateToHigherAutonomyLevel();
        break;
    }
  }

  /**
   * Autonomous action implementations
   */
  private async accelerateProcessing() {
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous acceleration: Reducing processing intervals");
    // Could temporarily increase processing speed
  }

  private async optimizeSystemPerformance() {
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous optimization: Queuing performance enhancements");
    
    // Queue optimization tasks
    puQueue.enqueue({
      kind: "PerfPU",
      summary: "Autonomous optimization: Memory usage optimization",
      cost: 2,
      payload: { autonomous: true, source: "loop_runner" }
    });

    puQueue.enqueue({
      kind: "PerfPU", 
      summary: "Autonomous optimization: Task batching efficiency",
      cost: 3,
      payload: { autonomous: true, source: "loop_runner" }
    });
  }

  private async initiateResearchProtocols() {
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous research: Analyzing patterns and documentation");
    
    puQueue.enqueue({
      kind: "DocPU",
      summary: "Autonomous research: Pattern analysis and optimization insights",
      cost: 4,
      payload: { autonomous: true, source: "loop_runner", type: "research" }
    });
  }

  private async deployFixProtocols() {
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous fixes: Deploying error correction protocols");
    
    puQueue.enqueue({
      kind: "FixPU",
      summary: "Autonomous fix: Error pattern correction and prevention",
      cost: 3,
      payload: { autonomous: true, source: "loop_runner", priority: "high" }
    });
  }

  private async repeatSuccessfulPatterns() {
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous repeat: Reinforcing successful patterns");
    // Could analyze and repeat recently successful task patterns
  }

  private async escalateToHigherAutonomyLevel() {
    logLoopInfo("[AUTONOMOUS-LOOP] Autonomous escalation: Engaging higher-level optimization");
    
    // Queue meta-optimization tasks
    puQueue.enqueue({
      kind: "MLPU",
      summary: "Autonomous escalation: Meta-level system optimization",
      cost: 5,
      payload: { autonomous: true, source: "loop_runner", level: "meta" }
    });
  }

  /**
   * Get current loop status for monitoring
   */
  getStatus() {
    return {
      running: this.isRunning,
      loop_count: this.loopCounter,
      current_decision: this.currentDecision,
      next_evaluation: this.evaluationTimer ? "scheduled" : "none",
      autonomous_mode: true
    };
  }

  /**
   * Force immediate evaluation (for external triggers)
   */
  async forceEvaluation() {
    if (!this.isRunning) return;
    
    logLoopInfo("[AUTONOMOUS-LOOP] Forced evaluation triggered");
    if (this.evaluationTimer) {
      clearTimeout(this.evaluationTimer);
    }
    await this.evaluateAndAct();
  }
}

export const autonomousLoopRunner = new AutonomousLoopRunner();
