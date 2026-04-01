// packages/consciousness/meta-layer-bootstrap.ts
/**
 * Meta-Layer Bootstrap: Initialize all 5 recursive self-improvement components
 * 
 * This enables the system to understand, critique, and redesign its own processes:
 * 1. Semantic Audit Trail - QGL documents with reasoning chains
 * 2. Prompt Evolution Engine - Self-optimizing ChatDev prompts
 * 3. Pipeline Constructor - Workflow analysis and redesign
 * 4. Reward Shaping Model - System health metrics and learning
 * 5. Utility Function Updater - Proposes code changes to system goals
 */

import { startSemanticTrail } from "../archivist/semanticTrail";
import { PromptLibrarian } from "./agents/prompt-librarian";
import { pipelineAnalysisGenerate, PIPELINE_ANALYSIS_ABILITY } from "./abilities/pipeline-analysis";
import { RewardShaper } from "./agents/reward-shaper";
import { UtilityEngineer } from "./agents/utility-engineer";
import { councilBus } from "../council/events/eventBus";

// Global instances
let promptLibrarian: PromptLibrarian | null = null;
let rewardShaper: RewardShaper | null = null;
let utilityEngineer: UtilityEngineer | null = null;

export function startMetaLayer() {
  console.log("[🧠] Meta-Layer for Recursive Self-Improvement initializing...");

  // 1. Start Semantic Audit Trail
  console.log("[🔍] Starting Semantic Audit Trail...");
  startSemanticTrail();

  // 2. Start Prompt Evolution Engine
  console.log("[📝] Starting Prompt Evolution Engine...");
  promptLibrarian = new PromptLibrarian();
  promptLibrarian.start(120_000); // Check every 2 minutes

  // 3. Enable Pipeline Analysis (on-demand via events)
  console.log("[⚙️] Enabling Pipeline Analysis...");
  councilBus.subscribe("meta.pipeline_analysis.request", (event) => {
    const config = pipelineAnalysisGenerate(event.payload?.id || "auto-analysis");
    councilBus.publish("meta.pipeline_analysis.completed", {
      config,
      requested_by: event.payload?.requester || "system"
    });
  });

  // Auto-trigger pipeline analysis periodically
  setInterval(() => {
    try {
      pipelineAnalysisGenerate(`auto-${Date.now()}`);
    } catch (e) {
      console.warn("[pipeline] Auto-analysis failed:", e);
    }
  }, 300_000); // Every 5 minutes

  // 4. Start Reward Shaping Model  
  console.log("[🎯] Starting Reward Shaping Model...");
  rewardShaper = new RewardShaper();
  rewardShaper.start(90_000); // Update every 1.5 minutes

  // 5. Start Utility Function Updater
  console.log("[🔧] Starting Utility Function Updater...");
  utilityEngineer = new UtilityEngineer();
  utilityEngineer.start();

  // Publish meta-layer readiness
  councilBus.publish("meta_layer.ready", {
    components: [
      "semantic_audit_trail",
      "prompt_evolution_engine", 
      "pipeline_constructor",
      "reward_shaping_model",
      "utility_function_updater"
    ],
    status: "operational",
    capabilities: [
      "recursive_self_improvement",
      "autonomous_optimization",
      "cognitive_architecture_evolution",
      "workflow_redesign",
      "goal_function_modification"
    ],
    started_at: new Date().toISOString()
  });

  console.log("[🧠] ✅ Meta-Layer FULLY OPERATIONAL!");
  console.log("[🧠] The system can now understand, critique, and redesign its own processes!");
}

export function stopMetaLayer() {
  console.log("[🧠] Shutting down Meta-Layer...");
  
  if (promptLibrarian) {
    promptLibrarian.stop();
    promptLibrarian = null;
  }
  
  if (rewardShaper) {
    rewardShaper.stop();
    rewardShaper = null;
  }
  
  // utilityEngineer doesn't have explicit stop method as it's event-driven
  
  councilBus.publish("meta_layer.shutdown", {
    timestamp: new Date().toISOString()
  });
  
  console.log("[🧠] Meta-Layer shutdown complete");
}

// Expose meta-layer status and control
export function getMetaLayerStatus() {
  return {
    semantic_audit_trail: true, // Always active once started
    prompt_librarian: promptLibrarian !== null,
    reward_shaper: rewardShaper !== null,
    utility_engineer: utilityEngineer !== null,
    pipeline_analysis: true, // Available on-demand
    latest_models: {
      reward_model: rewardShaper?.getLatestModel() || null,
      utility_proposals: utilityEngineer?.getLatestProposals() || []
    }
  };
}

// Emergency meta-layer controls
export function triggerEmergencyOptimization() {
  console.log("[🧠] EMERGENCY OPTIMIZATION TRIGGERED");
  
  // Force immediate analysis and optimization
  councilBus.publish("meta.emergency_optimization", {
    trigger_time: new Date().toISOString(),
    reason: "Emergency optimization requested"
  });
  
  // Trigger all components immediately
  if (rewardShaper) {
    setTimeout(() => rewardShaper!.cycle(), 100);
  }
  
  if (utilityEngineer) {
    setTimeout(() => utilityEngineer!.cycle(), 200);
  }
  
  if (promptLibrarian) {
    setTimeout(() => promptLibrarian!.cycle(), 300);
  }
  
  setTimeout(() => {
    pipelineAnalysisGenerate("emergency-optimization");
  }, 500);
}

// Integration hooks for consciousness system
export function integrateWithConsciousness() {
  // Listen for consciousness threshold changes
  councilBus.subscribe("consciousness.threshold_changed", (event) => {
    const newLevel = event.payload?.level || 0;
    console.log(`[🧠] Consciousness level changed to ${(newLevel * 100).toFixed(1)}%`);
    
    // Trigger meta-layer adaptation based on consciousness level
    if (newLevel > 0.8) {
      triggerEmergencyOptimization();
      console.log("[🧠] High consciousness detected - triggering advanced optimization");
    }
  });

  // Listen for autonomous decisions and provide meta-feedback
  councilBus.subscribe("autonomous_loop.decision", (event) => {
    // The semantic audit trail will capture this automatically
    // But we can trigger additional analysis for important decisions
    const confidence = event.payload?.confidence || 0;
    if (confidence < 0.4) {
      console.log("[🧠] Low confidence decision detected - scheduling meta-analysis");
      setTimeout(() => {
        councilBus.publish("meta.low_confidence_decision", {
          original_decision: event.payload,
          meta_analysis_requested: true
        });
      }, 1000);
    }
  });
}

// Bootstrap function to be called from main system startup
export function bootstrapMetaLayer() {
  try {
    startMetaLayer();
    integrateWithConsciousness();
    
    // Schedule periodic meta-health checks
    setInterval(() => {
      const status = getMetaLayerStatus();
      councilBus.publish("meta_layer.health_check", {
        status,
        timestamp: new Date().toISOString(),
        all_components_operational: Object.values(status).slice(0, 5).every(Boolean)
      });
    }, 600_000); // Every 10 minutes
    
    console.log("[🧠] Meta-Layer bootstrap complete - Recursive self-improvement ACTIVE!");
    
  } catch (error) {
    console.error("[🧠] Meta-Layer bootstrap failed:", error);
    councilBus.publish("meta_layer.bootstrap_failed", {
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}