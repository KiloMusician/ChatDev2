import express from "express";
import { loopOrchestrator } from "../services/loop_orchestrator.js";
import { autonomousLoopRunner } from "../services/autonomous_loop_runner.js";

export const loopRouter = express.Router();

/**
 * AI Council Loop Intelligence API
 * 
 * Provides contextual, intelligent loop decision-making endpoints
 * for autonomous operation without user confirmation.
 */

// Get current loop status and decision
loopRouter.get("/status", async (_req, res) => {
  try {
    const runnerStatus = autonomousLoopRunner.getStatus();
    const lastDecision = await loopOrchestrator.decideLoopAction();
    
    res.json({
      ok: true,
      autonomous_loop: runnerStatus,
      ai_council_decision: {
        action: lastDecision.action,
        confidence: lastDecision.confidence,
        reasoning: lastDecision.reasoning,
        next_evaluation_ms: lastDecision.next_evaluation_ms
      },
      features: [
        "contextual_decisions",
        "ai_council_voting", 
        "no_user_confirmation",
        "infrastructure_first",
        "cost_discipline",
        "neural_learning"
      ]
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Loop status check failed",
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// Start autonomous loop system
loopRouter.post("/start", async (_req, res) => {
  try {
    autonomousLoopRunner.start();
    
    res.json({
      ok: true,
      message: "AI Council autonomous loop system started",
      features: {
        intelligent_decisions: ["continue", "proceed", "pause", "fix", "research", "repeat", "optimize", "validate"],
        voting_agents: ["culture-ship", "council", "librarian", "redstone", "zod"],
        autonomous_operation: true,
        user_confirmation_required: false
      }
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Failed to start autonomous loop system",
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// Stop autonomous loop system
loopRouter.post("/stop", async (_req, res) => {
  try {
    autonomousLoopRunner.stop();
    
    res.json({
      ok: true,
      message: "Autonomous loop system stopped"
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Failed to stop autonomous loop system"
    });
  }
});

// Force immediate loop evaluation
loopRouter.post("/evaluate", async (_req, res) => {
  try {
    await autonomousLoopRunner.forceEvaluation();
    
    res.json({
      ok: true,
      message: "Forced loop evaluation completed"
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Loop evaluation failed",
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// Get AI Council decision without executing
loopRouter.get("/decision", async (_req, res) => {
  try {
    const decision = await loopOrchestrator.decideLoopAction();
    
    res.json({
      ok: true,
      decision,
      explanation: {
        action: decision.action,
        confidence_percent: Math.round(decision.confidence * 100),
        reasoning: decision.reasoning,
        next_check_seconds: Math.round(decision.next_evaluation_ms / 1000),
        conditions: decision.conditions || []
      }
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Failed to get AI Council decision",
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// Get loop performance metrics
loopRouter.get("/metrics", async (_req, res) => {
  try {
    res.json({
      ok: true,
      metrics: {
        decisions_made: "tracking_enabled",
        success_rate: "monitoring_active",
        cost_efficiency: "optimizing",
        loop_intelligence: "ai_council_active",
        contextual_adaptation: "learning_enabled"
      },
      capabilities: {
        boolean_logic: "redstone_agent",
        consensus_building: "council_agent", 
        pattern_recognition: "librarian_agent",
        strategic_oversight: "culture_ship_agent",
        safety_validation: "zod_agent"
      }
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Failed to get loop metrics"
    });
  }
});