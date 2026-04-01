// packages/consciousness/abilities/pipeline-analysis.ts
/**
 * ability:pipeline_analysis
 * Input: a set of QGL audit docs describing a process (todo → code → build → test → deploy)
 * Output: pipeline JSON with stages, deps, suggested changes.
 */
import fs from "node:fs";
import path from "node:path";
import { councilBus } from "../../council/events/eventBus";

export type PipelineConfig = {
  id: string;
  stages: Array<{ 
    id: string; 
    runs: string[]; 
    timeout_s?: number; 
    requires?: string[];
    parallel?: boolean;
    success_criteria?: string[];
  }>;
  policies: { 
    concurrency?: number; 
    retry?: number; 
    approvals?: string[];
    optimization_targets?: string[];
  };
  metrics: {
    estimated_duration_s: number;
    estimated_success_rate: number;
    bottlenecks: string[];
    optimization_opportunities: string[];
  };
  notes?: string;
};

const ARCH = process.env.SEMANTIC_ARCHIVE || "archive/semantic";
const OUT = "pipelines/generated";

function loadRecent(limit = 300) {
  if (!fs.existsSync(ARCH)) return [];
  return fs.readdirSync(ARCH)
    .filter(f => f.endsWith(".json"))
    .slice(-limit)
    .map(f => {
      try {
        return JSON.parse(fs.readFileSync(path.join(ARCH, f), "utf-8"));
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

function inferStages(docs: any[]) {
  const seen = new Set<string>();
  const timings: Record<string, number[]> = {};
  const successRates: Record<string, { success: number; total: number }> = {};

  for (const d of docs) {
    const t = d?.content?.action_topic ?? d?.topic ?? "";
    if (!t) continue;
    
    const success = d?.content?.outcome_analysis?.success ?? false;
    
    if (/chatdev\.session\.end/.test(t)) {
      seen.add("chatdev");
      if (!successRates.chatdev) successRates.chatdev = { success: 0, total: 0 };
      successRates.chatdev.total++;
      if (success) successRates.chatdev.success++;
    }
    if (/build\.result/.test(t)) {
      seen.add("build");
      if (!successRates.build) successRates.build = { success: 0, total: 0 };
      successRates.build.total++;
      if (success) successRates.build.success++;
    }
    if (/test\.result/.test(t)) {
      seen.add("test");
      if (!successRates.test) successRates.test = { success: 0, total: 0 };
      successRates.test.total++;
      if (success) successRates.test.success++;
    }
    if (/deploy\.result/.test(t)) {
      seen.add("deploy");
      if (!successRates.deploy) successRates.deploy = { success: 0, total: 0 };
      successRates.deploy.total++;
      if (success) successRates.deploy.success++;
    }
    if (/mhsa\.scan\.result|orchestrate\.layout/.test(t)) {
      seen.add("music_layout");
      if (!successRates.music_layout) successRates.music_layout = { success: 0, total: 0 };
      successRates.music_layout.total++;
      if (success) successRates.music_layout.success++;
    }
    if (/autonomous_loop\.decision/.test(t)) {
      seen.add("decision_loop");
      if (!successRates.decision_loop) successRates.decision_loop = { success: 0, total: 0 };
      successRates.decision_loop.total++;
      if (success) successRates.decision_loop.success++;
    }
  }

  const stages = Array.from(seen).map(s => {
    const rate = successRates[s];
    const successRate = rate ? rate.success / rate.total : 0.5;
    
    return {
      id: s,
      runs: [`run:${s}`],
      timeout_s: getTimeoutForStage(s),
      success_criteria: getSuccessCriteria(s),
      parallel: isParallelizable(s),
      estimated_success_rate: successRate
    };
  });

  // naive deps based on typical workflow
  const idToStage: Record<string, any> = Object.fromEntries(stages.map(s => [s.id, s]));
  if (idToStage["build"]) idToStage["build"].requires = ["chatdev"];
  if (idToStage["test"]) idToStage["test"].requires = ["build"];
  if (idToStage["deploy"]) idToStage["deploy"].requires = ["test"];
  if (idToStage["music_layout"]) idToStage["music_layout"].requires = [];
  if (idToStage["decision_loop"]) idToStage["decision_loop"].requires = [];

  return stages;
}

function getTimeoutForStage(stage: string): number {
  switch (stage) {
    case "chatdev": return 300; // 5 minutes
    case "build": return 180; // 3 minutes
    case "test": return 120; // 2 minutes
    case "deploy": return 240; // 4 minutes
    case "music_layout": return 60; // 1 minute
    case "decision_loop": return 30; // 30 seconds
    default: return 120;
  }
}

function getSuccessCriteria(stage: string): string[] {
  switch (stage) {
    case "chatdev": return ["Code compiles", "Tests pass", "Requirements met"];
    case "build": return ["No compilation errors", "Dependencies resolved", "Artifacts generated"];
    case "test": return ["All tests pass", "Coverage threshold met", "No regressions"];
    case "deploy": return ["Service starts successfully", "Health checks pass", "Rollback capability verified"];
    case "music_layout": return ["Invariance maintained", "Layout valid", "Performance acceptable"];
    case "decision_loop": return ["Consensus reached", "Confidence threshold met", "Action decided"];
    default: return ["Operation completes successfully"];
  }
}

function isParallelizable(stage: string): boolean {
  switch (stage) {
    case "music_layout": return true;
    case "decision_loop": return true;
    default: return false;
  }
}

function analyzeBottlenecks(stages: any[]): string[] {
  const bottlenecks: string[] = [];
  
  for (const stage of stages) {
    if (stage.estimated_success_rate < 0.7) {
      bottlenecks.push(`${stage.id}: Low success rate (${(stage.estimated_success_rate * 100).toFixed(1)}%)`);
    }
    if (stage.timeout_s > 240) {
      bottlenecks.push(`${stage.id}: Long duration (${stage.timeout_s}s)`);
    }
  }
  
  return bottlenecks;
}

function suggestOptimizations(stages: any[], bottlenecks: string[]): string[] {
  const optimizations: string[] = [];
  
  if (bottlenecks.some(b => b.includes("chatdev"))) {
    optimizations.push("Implement prompt caching for ChatDev sessions");
    optimizations.push("Add incremental prompt evolution based on success metrics");
  }
  
  if (bottlenecks.some(b => b.includes("build"))) {
    optimizations.push("Enable build caching and parallel compilation");
    optimizations.push("Implement dependency precompilation");
  }
  
  if (bottlenecks.some(b => b.includes("test"))) {
    optimizations.push("Parallelize test execution");
    optimizations.push("Implement smart test selection based on code changes");
  }
  
  const hasParallel = stages.some(s => s.parallel);
  if (hasParallel && stages.length > 2) {
    optimizations.push("Increase pipeline concurrency to leverage parallel stages");
  }
  
  return optimizations;
}

export function pipelineAnalysisGenerate(id = "pipeline.auto"): PipelineConfig {
  const docs = loadRecent();
  const stages = inferStages(docs);
  const bottlenecks = analyzeBottlenecks(stages);
  const optimizations = suggestOptimizations(stages, bottlenecks);
  
  const estimatedDuration = stages.reduce((sum, s) => sum + (s.timeout_s || 120), 0);
  const estimatedSuccessRate = stages.reduce((product, s) => product * (s.estimated_success_rate || 0.5), 1);
  
  const cfg: PipelineConfig = {
    id,
    stages,
    policies: { 
      concurrency: 2, 
      retry: 2, 
      approvals: ["council"],
      optimization_targets: ["success_rate", "duration", "resource_efficiency"]
    },
    metrics: {
      estimated_duration_s: estimatedDuration,
      estimated_success_rate: estimatedSuccessRate,
      bottlenecks,
      optimization_opportunities: optimizations
    },
    notes: "auto-generated from semantic audits; refine via director",
  };
  
  fs.mkdirSync(OUT, { recursive: true });
  const file = path.join(OUT, `${id}.json`);
  fs.writeFileSync(file, JSON.stringify(cfg, null, 2));
  
  councilBus.publish("pipeline.analysis.result", { 
    id, 
    file, 
    stages: stages.length,
    estimated_success_rate: estimatedSuccessRate,
    bottlenecks: bottlenecks.length,
    optimizations: optimizations.length
  });
  
  console.log(`[pipeline] generated → ${file} (${stages.length} stages, ${(estimatedSuccessRate * 100).toFixed(1)}% success rate)`);
  return cfg;
}

// Register this as an ability
export const PIPELINE_ANALYSIS_ABILITY = {
  id: "ability:pipeline_analysis",
  qgl_version: "0.2" as const,
  kind: "ability.definition" as const,
  created_at: new Date().toISOString(),
  
  ability_identity: {
    name: "Pipeline Analysis & Construction",
    category: "system_modification" as const,
    classification: "standard" as const,
    power_level: 0.7
  },
  
  operation: {
    description: "Analyze system processes from semantic audit trails and construct optimized pipelines",
    input_requirements: [
      {
        type: "system_state" as const,
        name: "semantic_audit_docs",
        validation_schema: { type: "array" },
        required: true
      }
    ],
    output_specification: {
      type: "system_transformation" as const,
      description: "Optimized pipeline configuration with stages, dependencies, and performance metrics",
      success_indicators: ["Pipeline completeness", "Optimization opportunities identified", "Bottleneck analysis"],
      failure_modes: [
        { mode: "insufficient_data", recovery_procedure: "Collect more semantic audit data over time" },
        { mode: "circular_dependencies", recovery_procedure: "Restructure pipeline with dependency validation" }
      ]
    },
    side_effects: [
      { effect: "Improved system efficiency", probability: 0.8, severity: "benign" as const, mitigation: "Monitor pipeline performance" }
    ]
  },
  
  unlock_requirements: {
    consciousness_threshold: 0.4,
    prerequisite_abilities: [],
    system_conditions: [
      { condition: "semantic_audit_active", validation_method: "event_check" as const, required_value: true }
    ],
    ethical_constraints: [
      { constraint: "Preserve existing functionality", enforcement_level: "advisory" as const, justification: "Maintain system stability during optimization" }
    ]
  }
};