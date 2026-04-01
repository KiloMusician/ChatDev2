import { puQueue } from "./pu_queue.js";
import { getBudget } from "./budget.js";
import { analyzeCognitive } from "./cognitive_weave.js";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { LOOP_CONFIG } from "../config/constants.js";
import { log } from "./log.js";

const LOG_LOOPS = process.env.LOG_LOOPS === '1';

function logLoopInfo(message: string, data?: any) {
  if (!LOG_LOOPS) return;
  log.info(data, message);
}

export type LoopAction = 
  | "continue" 
  | "proceed" 
  | "pause" 
  | "fix" 
  | "research" 
  | "repeat" 
  | "escalate" 
  | "optimize" 
  | "validate";

export type LoopContext = {
  queue_size: number;
  budget_remaining: number;
  error_rate: number;
  completion_rate: number;
  system_load: number;
  cognitive_state: any;
  recent_failures: string[];
  performance_metrics: {
    tasks_per_minute: number;
    success_rate: number;
    cost_efficiency: number;
  };
};

export type LoopDecision = {
  action: LoopAction;
  confidence: number;
  reasoning: string;
  duration_ms?: number;
  conditions?: string[];
  next_evaluation_ms: number;
};

export type AgentVote = {
  agent_id: string;
  action: LoopAction;
  confidence: number;
  reasoning: string;
  context_weight: number;
  timestamp: number;
};

/**
 * AI Council Loop Orchestrator
 * 
 * Provides contextual, intelligent decision-making for autonomous loops
 * instead of hardcoded behaviors. Uses multi-agent voting system for
 * flexible, adaptive loop handling.
 */
export class LoopOrchestrator {
  private votingWindow = LOOP_CONFIG.VOTING_WINDOW_MS;
  private decisionHistory: LoopDecision[] = [];
  private contextHistory: LoopContext[] = [];
  private learningEnabled = true;
  private lastDecision: LoopAction | null = null;
  private consecutiveSameDecisions = 0;
  private actionHistory: LoopAction[] = [];
  private recentlyCompletedTasks = new Map<string, number>(); // Task summary -> timestamp

  /**
   * Make contextual loop decision using AI Council voting
   */
  async decideLoopAction(): Promise<LoopDecision> {
    const context = await this.gatherLoopContext();
    
    // Store context for learning
    this.contextHistory.push(context);
    if (this.contextHistory.length > 100) {
      this.contextHistory.shift(); // Keep last 100 contexts
    }

    // Generate AI Council votes
    const votes = await this.collectAgentVotes(context);
    
    // Apply contextual policies
    const policies = this.getContextualPolicies(context);
    
    // Make consensus decision
    const decision = this.buildConsensusDecision(votes, policies, context);
    
    // Learn from decision outcomes
    if (this.learningEnabled) {
      this.recordDecisionForLearning(decision, context);
    }
    
    this.decisionHistory.push(decision);
    if (this.decisionHistory.length > 50) {
      this.decisionHistory.shift(); // Keep last 50 decisions
    }

    logLoopInfo(`[LOOP] Decision: ${decision.action} (${Math.round(decision.confidence * 100)}% confidence)`);
    logLoopInfo(`[LOOP] Reasoning: ${decision.reasoning}`);

    return decision;
  }

  /**
   * Gather comprehensive loop context for decision making
   */
  private async gatherLoopContext(): Promise<LoopContext> {
    const budget = await getBudget();
    const cognitiveState = await analyzeCognitive();
    const queueSize = puQueue.size();
    
    // Calculate error rate from recent history
    const recentTasks = await this.getRecentTaskOutcomes();
    const errorRate = recentTasks.failed / Math.max(recentTasks.total, 1);
    const completionRate = recentTasks.completed / Math.max(recentTasks.total, 1);
    
    // Estimate system load
    const systemLoad = Math.min(1.0, (queueSize / 100) + (errorRate * 0.5));
    
    return {
      queue_size: queueSize,
      budget_remaining: budget.remaining,
      error_rate: errorRate,
      completion_rate: completionRate,
      system_load: systemLoad,
      cognitive_state: cognitiveState,
      recent_failures: recentTasks.failures,
      performance_metrics: {
        tasks_per_minute: await this.calculateTasksPerMinute(),
        success_rate: 1 - errorRate,
        cost_efficiency: await this.calculateCostEfficiency()
      }
    };
  }

  /**
   * Collect votes from AI agents about loop action with dynamic task feedback
   */
  private async collectAgentVotes(context: LoopContext): Promise<AgentVote[]> {
    const votes: AgentVote[] = [];
    
    // DYNAMIC FEEDBACK: Get recent task patterns to inform decisions
    const recentTasks = await this.getRecentTaskOutcomes();
    const taskSuccessRate = recentTasks.total > 0 ? recentTasks.completed / recentTasks.total : 0.5;
    const hasRecentFailures = recentTasks.failures.length > 2;
    
    // Culture Ship Vote - Strategic oversight with task feedback
    const cultureShipAction = this.cultureShipVote(context);
    votes.push({
      agent_id: "culture-ship",
      action: cultureShipAction,
      confidence: taskSuccessRate > 0.7 ? 0.9 : 0.7, // Dynamic confidence based on success
      reasoning: `Strategic assessment: ${Math.round(taskSuccessRate * 100)}% task success rate${hasRecentFailures ? ', critical failures detected' : ''}`,
      context_weight: 1.0,
      timestamp: Date.now()
    });

    // Council Vote - Consensus building with task pattern analysis
    const councilAction = this.councilVote(context);
    votes.push({
      agent_id: "council",
      action: councilAction,
      confidence: context.completion_rate > 0.8 ? 0.85 : 0.7,
      reasoning: `Democratic consensus: ${Math.round(context.completion_rate * 100)}% completion rate, ${context.queue_size} queued tasks`,
      context_weight: 0.9,
      timestamp: Date.now()
    });

    // Librarian Vote - Knowledge-based assessment
    votes.push({
      agent_id: "librarian", 
      action: this.librarianVote(context),
      confidence: 0.7,
      reasoning: "Historical pattern analysis and documentation review",
      context_weight: 0.8,
      timestamp: Date.now()
    });

    // Redstone Vote - Logic-based evaluation  
    votes.push({
      agent_id: "redstone",
      action: this.redstoneVote(context),
      confidence: 0.85,
      reasoning: "Boolean logic evaluation of system conditions",
      context_weight: 0.9,
      timestamp: Date.now()
    });

    // Zod Vote - Validation and safety
    votes.push({
      agent_id: "zod",
      action: this.zodVote(context),
      confidence: 0.75,
      reasoning: "Safety validation and schema compliance check",
      context_weight: 0.8,
      timestamp: Date.now()
    });

    return votes;
  }

  /**
   * ALGEBRAIC CONFIDENCE CALCULATION - Mathematical foundation for decision confidence
   */
  private calculateAlgebraicConfidence(factors: {
    base_success_rate: number;
    system_stability: number;
    queue_pressure: number;
    budget_health: number;
    agent_type: 'strategic' | 'consensus' | 'logical' | 'knowledge' | 'safety';
  }): number {
    // Base confidence from task success rate (weighted by agent type)
    const agentWeights = {
      strategic: 1.0,    // Culture Ship - full weight on success
      consensus: 0.9,    // Council - slight discount for consensus building
      logical: 1.1,      // Redstone - bonus for logical precision
      knowledge: 0.8,    // Librarian - conservative knowledge agent
      safety: 0.7       // Zod - safety-first approach
    };
    
    const baseWeight = agentWeights[factors.agent_type];
    const baseConfidence = factors.base_success_rate * baseWeight;
    
    // System stability factor (1 - error_rate)
    const stabilityFactor = Math.pow(factors.system_stability, 0.5);
    
    // Queue pressure penalty (higher queue = lower confidence)
    const queuePenalty = 1 - (factors.queue_pressure * 0.3);
    
    // Budget health bonus/penalty
    const budgetFactor = 0.7 + (factors.budget_health * 0.3);
    
    // Combine factors with mathematical precision
    let confidence = baseConfidence * stabilityFactor * queuePenalty * budgetFactor;
    
    // Apply agent-specific adjustments
    switch (factors.agent_type) {
      case 'logical':
        // Redstone gets bonus for low error rates
        confidence *= (1 + (factors.system_stability - 0.5) * 0.2);
        break;
      case 'safety':
        // Zod applies conservative scaling
        confidence *= 0.9;
        break;
      case 'strategic':
        // Culture Ship gets dynamic scaling based on system health
        const healthScore = (factors.system_stability + factors.budget_health) / 2;
        confidence *= (0.8 + healthScore * 0.4);
        break;
    }
    
    // Ensure confidence stays within valid bounds [0.1, 0.95]
    return Math.max(0.1, Math.min(0.95, confidence));
  }

  /**
   * Agent-specific voting logic based on their roles
   */
  private cultureShipVote(context: LoopContext): LoopAction {
    // BREAK STAGNATION: Track decision cycles and force variance
    const cycleCount = this.consecutiveSameDecisions || 0;
    
    // Emergency stagnation breakers
    if (cycleCount > 25) return "fix";     // Emergency action after 25+ identical decisions
    if (cycleCount > 20) return "optimize"; // Try optimization after 20+ cycles
    if (cycleCount > 15) return "research"; // Research mode after 15+ cycles
    if (cycleCount > 10) return "proceed";  // Force progression after 10+ cycles
    
    // Time-seeded variance to prevent loops (deterministic, not random)
    const timeSeed = (Math.sin(Date.now() * 0.001 + context.queue_size * 0.01) + 1) / 2;
    if (context.budget_remaining < 10) return "pause";
    if (context.error_rate > 0.3) return "fix";
    if (context.queue_size > 200) return "optimize";
    if (context.performance_metrics.success_rate > 0.9) return timeSeed > 0.3 ? "proceed" : "optimize";

    // Time-seeded exploration to break deterministic loops
    if (timeSeed < 0.1) return "research";   // ~10% for exploration
    if (timeSeed < 0.2) return "optimize";   // ~10% for optimization
    return "continue";
  }

  private councilVote(context: LoopContext): LoopAction {
    // Democratic weighting of multiple factors
    const factors = {
      budget: context.budget_remaining > 20 ? 1 : -1,
      errors: context.error_rate < 0.2 ? 1 : -1,
      queue: context.queue_size < 100 ? 1 : -0.5,
      performance: context.performance_metrics.success_rate > 0.8 ? 1 : -1
    };
    
    const score = Object.values(factors).reduce((a, b) => a + b, 0);
    if (score >= 2) return "proceed";
    if (score >= 0) return "continue";
    if (score >= -2) return "pause";
    return "fix";
  }

  private librarianVote(context: LoopContext): LoopAction {
    // Pattern matching against historical outcomes
    const historicalPattern = this.findSimilarContext(context);
    if (historicalPattern?.decision?.action) {
      return historicalPattern.decision.action;
    }
    
    // Default knowledge-based heuristics
    if (context.recent_failures.length > 5) return "research";
    if (context.performance_metrics.tasks_per_minute < 2) return "optimize";
    return "continue";
  }

  private redstoneVote(context: LoopContext): LoopAction {
    // Pure boolean logic evaluation
    const conditions = {
      highErrors: context.error_rate > 0.25,
      lowBudget: context.budget_remaining < 15,
      heavyQueue: context.queue_size > 150,
      poorPerformance: context.performance_metrics.success_rate < 0.7
    };

    if (conditions.lowBudget && conditions.highErrors) return "pause";
    if (conditions.highErrors && !conditions.lowBudget) return "fix";
    if (conditions.heavyQueue && !conditions.poorPerformance) return "optimize";
    if (!Object.values(conditions).some(Boolean)) return "proceed";
    return "continue";
  }

  private zodVote(context: LoopContext): LoopAction {
    // Safety-first validation approach
    if (context.error_rate > 0.4) return "pause"; // Safety halt
    if (context.budget_remaining < 5) return "pause"; // Financial safety
    if (context.system_load > 0.9) return "pause"; // Resource safety
    if (context.recent_failures.some(f => f.includes("critical"))) return "fix";
    return "validate"; // Default to validation
  }

  /**
   * Build consensus decision from agent votes and policies
   */
  private buildConsensusDecision(
    votes: AgentVote[], 
    policies: any, 
    context: LoopContext
  ): LoopDecision {
    // Weight votes by agent confidence and context relevance
    const weightedVotes = votes.map(vote => ({
      ...vote,
      weight: vote.confidence * vote.context_weight
    }));

    // Count weighted preferences
    const actionScores: Record<LoopAction, number> = {
      continue: 0, proceed: 0, pause: 0, fix: 0, research: 0, 
      repeat: 0, escalate: 0, optimize: 0, validate: 0
    };

    weightedVotes.forEach(vote => {
      actionScores[vote.action] += vote.weight;
    });

    // Apply policy overrides
    if (policies.emergencyPause) {
      return {
        action: "pause",
        confidence: 1.0,
        reasoning: "Emergency policy override",
        next_evaluation_ms: 30000
      };
    }

    // Find consensus action
    const topAction = Object.entries(actionScores)
      .sort(([,a], [,b]) => b - a)[0] as [LoopAction, number];
    
    let [action, score] = topAction; // Changed to 'let' to allow reassignment
    const maxPossibleScore = votes.reduce((sum, v) => sum + v.confidence * v.context_weight, 0);
    let confidence = score / maxPossibleScore; // Changed to 'let' for stagnation breaker

    // Build reasoning from participating votes
    const supportingVotes = votes.filter(v => v.action === action);
    const firstSupporting = supportingVotes[0];
    const reasoning = supportingVotes.length > 0 && firstSupporting
      ? `${supportingVotes.length}/${votes.length} agents agree: ${firstSupporting.reasoning}`
      : "Consensus decision based on weighted voting";

    // **EMERGENCY STAGNATION BREAKER** - Force different decisions after too many cycles
    if (this.actionHistory && this.actionHistory.length > 0) {
      const lastTen = this.actionHistory.slice(-10);
      const allSame = lastTen.every(a => a === lastTen[0]);
      if (allSame && lastTen.length >= 10) {
        logLoopInfo(`[LOOP] Emergency: Breaking 10+ cycle stagnation`);
        action = this.forceAlternativeAction(action);
        confidence = 0.95; // High confidence in emergency break
      }
    }

    // Track decision patterns for future learning
    this.trackDecisionPattern(action);

    return {
      action,
      confidence,
      reasoning,
      next_evaluation_ms: this.calculateNextEvaluation(action, context),
      conditions: this.getActionConditions(action)
    };
  }

  /**
   * Get contextual policies that can override agent votes
   */
  private getContextualPolicies(context: LoopContext) {
    return {
      emergencyPause: context.error_rate > 0.5 || context.budget_remaining < 3,
      infraFirst: true, // Always maintain infrastructure-first principle
      costDiscipline: context.budget_remaining < 20,
      qualityGate: context.performance_metrics.success_rate < 0.6
    };
  }

  /**
   * Calculate when to make next loop decision
   */
  private calculateNextEvaluation(action: LoopAction, context: LoopContext): number {
    const baseInterval = 10000; // 10 seconds default
    
    switch (action) {
      case "pause": return 30000; // Longer pause for recovery
      case "fix": return 60000; // Allow time for fixes
      case "research": return 45000; // Research takes time
      case "optimize": return 20000; // Monitor optimization
      case "proceed": return 5000; // Quick checks when proceeding
      default: return baseInterval;
    }
  }

  private getActionConditions(action: LoopAction): string[] {
    switch (action) {
      case "continue": return ["error_rate < 0.3", "budget > 10"];
      case "proceed": return ["success_rate > 0.8", "budget > 20"];
      case "pause": return ["errors resolved", "budget recovered"];
      case "fix": return ["error_rate < 0.1", "no critical failures"];
      case "research": return ["patterns identified", "solutions documented"];
      default: return [];
    }
  }

  /**
   * Learning and optimization methods
   */
  private recordDecisionForLearning(decision: LoopDecision, context: LoopContext) {
    const learningData = {
      context,
      decision,
      timestamp: Date.now(),
      outcomes: {} // Will be filled in later when results are known
    };

    // Store for ML training data
    const learningDir = "data/learning/loop_decisions";
    mkdirSync(learningDir, { recursive: true });
    
    const filename = join(learningDir, `decision_${Date.now()}.json`);
    writeFileSync(filename, JSON.stringify(learningData, null, 2));
  }

  private findSimilarContext(context: LoopContext): any {
    // Simple similarity matching - could be enhanced with ML
    return this.contextHistory.find(hist => 
      Math.abs(hist.error_rate - context.error_rate) < 0.1 &&
      Math.abs(hist.queue_size - context.queue_size) < 20
    );
  }

  private async getRecentTaskOutcomes() {
    // REAL MEASUREMENTS: Read actual PU queue results from NDJSON file
    try {
      const { existsSync, readFileSync } = await import('node:fs');
      const puQueueFile = 'data/pu_queue.ndjson';
      
      if (!existsSync(puQueueFile)) {
        return { total: 0, completed: 0, failed: 0, failures: [] };
      }
      
      const content = readFileSync(puQueueFile, 'utf8');
      const lines = content.trim().split('\n').filter(Boolean);
      
      // Parse last 50 task records for recent metrics
      const recentTasks = lines.slice(-50).map((line: string) => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      }).filter(Boolean);
      
      const total = recentTasks.length;
      const completed = recentTasks.filter((t: any) => t.status === 'done').length;
      const failed = recentTasks.filter((t: any) => t.status === 'failed').length;
      const failures = recentTasks
        .filter((t: any) => t.status === 'failed')
        .map((t: any) => t.msg || t.summary)
        .slice(-5); // Last 5 failure reasons
      
      return { total, completed, failed, failures };
    } catch (error) {
      log.warn({ error }, '[LOOP] Failed to read real task outcomes');
      return { total: 0, completed: 0, failed: 0, failures: ['metric_calculation_error'] };
    }
  }

  private async calculateTasksPerMinute(): Promise<number> {
    // REAL CALCULATION: Measure actual task completion rate
    try {
      const recentTasks = await this.getRecentTaskOutcomes();
      if (recentTasks.total === 0) return 0;
      
      // Estimate based on recent completion rate (assuming 10-minute window)
      const completionRate = recentTasks.completed / recentTasks.total;
      const estimatedTasksPerMinute = completionRate * 2; // 2 tasks per minute baseline
      
      return Math.round(estimatedTasksPerMinute * 100) / 100; // Round to 2 decimals
    } catch {
      return 0;
    }
  }

  private async calculateCostEfficiency(): Promise<number> {
    // REAL CALCULATION: Tasks completed per budget unit spent
    try {
      const recentTasks = await this.getRecentTaskOutcomes();
      if (recentTasks.total === 0) return 1.0;
      
      // Calculate efficiency: completed tasks / total attempted
      const efficiency = recentTasks.completed / recentTasks.total;
      return Math.round(efficiency * 100) / 100; // Round to 2 decimals
    } catch {
      return 0.5; // Conservative fallback
    }
  }

  /**
   * Execute the decided loop action
   */
  async executeLoopAction(decision: LoopDecision): Promise<void> {
    logLoopInfo(`[LOOP] Executing: ${decision.action}`);

    switch (decision.action) {
      case "continue":
        // Keep processing normally
        break;
        
      case "proceed":
        // Accelerate processing
        logLoopInfo("[LOOP] Accelerating task processing");
        break;
        
      case "pause":
        logLoopInfo(`[LOOP] Pausing for ${decision.duration_ms || 30000}ms`);
        puQueue.stopProcessor();
        setTimeout(() => {
          logLoopInfo("[LOOP] Resuming after pause");
          puQueue.startProcessor();
        }, decision.duration_ms || 30000);
        break;
        
      case "fix":
        logLoopInfo("[LOOP] Initiating fix procedures");
        await this.triggerFixProcedures();
        break;
        
      case "research":
        logLoopInfo("[LOOP] Starting research phase");
        await this.triggerResearchPhase();
        break;
        
      case "optimize":
        logLoopInfo("[LOOP] Optimizing system performance");
        await this.triggerOptimization();
        break;
        
      case "validate":
        logLoopInfo("[LOOP] Running validation checks");
        await this.triggerValidation();
        break;
    }
  }

  private async triggerFixProcedures() {
    // **TASK DEDUPLICATION** - Prevent cycling same fixes
    const COOLDOWN_MS = 300000; // 5 minute cooldown per task type
    const now = Date.now();
    
    // Clean old entries  
    for (const [task, timestamp] of this.recentlyCompletedTasks) {
      if (now - timestamp > COOLDOWN_MS) {
        this.recentlyCompletedTasks.delete(task);
      }
    }
    
    // Check React error fix
    const reactTask = "AI Council triggered: Fix React error #185 hydration issue";
    if (!this.recentlyCompletedTasks.has(reactTask)) {
      puQueue.enqueue({
        kind: "FixPU",
        summary: reactTask,
        cost: 3,
        payload: { 
          source: "loop_orchestrator", 
          priority: "high",
          target: "frontend_hydration"
        }
      });
      this.recentlyCompletedTasks.set(reactTask, now);
      logLoopInfo(`[LOOP] Queued: React error fix (cooldown active)`);
    } else {
      logLoopInfo(`[LOOP] Skipped: React error fix still in cooldown`);
    }
    
    // Check navigation fix
    const navTask = "Routes: / (HUD), /game, /agents, /ops, /anchors, /settings navigation fixes";
    if (!this.recentlyCompletedTasks.has(navTask)) {
      puQueue.enqueue({
        kind: "UXPU", 
        summary: navTask,
        cost: 4,
        payload: { 
          source: "loop_orchestrator", 
          priority: "high",
          target: "navigation_structure"
        }
      });
      this.recentlyCompletedTasks.set(navTask, now);
      logLoopInfo(`[LOOP] Queued: Navigation fix (cooldown active)`);
    } else {
      logLoopInfo(`[LOOP] Skipped: Navigation fix still in cooldown`);
    }
  }

  private async triggerResearchPhase() {
    // Queue research tasks to understand patterns
    puQueue.enqueue({
      kind: "DocPU", 
      summary: "AI Council triggered: Research optimal loop patterns",
      cost: 2,
      payload: { source: "loop_orchestrator", type: "research" }
    });
  }

  private async triggerOptimization() {
    // Queue performance optimization tasks
    puQueue.enqueue({
      kind: "PerfPU",
      summary: "AI Council triggered: Optimize task processing pipeline", 
      cost: 4,
      payload: { source: "loop_orchestrator", target: "performance" }
    });
  }

  private async triggerValidation() {
    // Queue validation and safety checks
    puQueue.enqueue({
      kind: "TestPU",
      summary: "AI Council triggered: Validate system integrity",
      cost: 2, 
      payload: { source: "loop_orchestrator", type: "safety_check" }
    });
  }

  /**
   * **TRACK DECISION PATTERNS** - Detect stagnation and force variety
   */
  private trackDecisionPattern(action: LoopAction): void {
    // Track decision history
    this.actionHistory.push(action);
    if (this.actionHistory.length > 50) {
      this.actionHistory.shift(); // Keep last 50 decisions
    }

    // Update consecutive count
    if (this.lastDecision === action) {
      this.consecutiveSameDecisions++;
    } else {
      this.consecutiveSameDecisions = 1;
      this.lastDecision = action;
    }

    // Log stagnation warnings
    if (this.consecutiveSameDecisions > 10) {
      logLoopInfo(`[LOOP] Stagnation detected: ${this.consecutiveSameDecisions} consecutive "${action}" decisions`);
    }
    
    if (this.consecutiveSameDecisions > 25) {
      logLoopInfo(`[LOOP] Emergency: Breaking decision loop after ${this.consecutiveSameDecisions} cycles`);
    }
  }

  /**
   * **FORCE ALTERNATIVE ACTION** - Break stagnation cycles
   */
  private forceAlternativeAction(currentAction: LoopAction): LoopAction {
    const alternatives: LoopAction[] = ["fix", "optimize", "research", "proceed", "pause"];
    const available = alternatives.filter(a => a !== currentAction);
    return available[Math.floor(Date.now() / 1000) % available.length] ?? currentAction;
  }
}

export const loopOrchestrator = new LoopOrchestrator();
