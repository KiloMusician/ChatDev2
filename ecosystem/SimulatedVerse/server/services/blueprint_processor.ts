import { z } from "zod";

// 123-step blueprint schema
const BlueprintStepSchema = z.object({
  id: z.string(),
  phase: z.string(),
  type: z.string(),
  priority: z.enum(["critical", "high", "medium", "low"]),
  title: z.string(),
  dependencies: z.array(z.string()).optional(),
  budget_estimate: z.number().optional(),
  files: z.array(z.object({
    path: z.string(),
    content: z.string()
  })).optional(),
  labels: z.array(z.string()).optional()
});

const BlueprintSchema = z.array(BlueprintStepSchema);

type BlueprintStep = z.infer<typeof BlueprintStepSchema>;
type Blueprint = z.infer<typeof BlueprintSchema>;

// Dependency resolver for 123-step execution
export class BlueprintProcessor {
  private steps: Map<string, BlueprintStep> = new Map();
  private dependencyGraph: Map<string, string[]> = new Map();
  private completed: Set<string> = new Set();
  private inProgress: Set<string> = new Set();
  
  constructor(blueprint: Blueprint) {
    // Build dependency graph
    for (const step of blueprint) {
      this.steps.set(step.id, step);
      this.dependencyGraph.set(step.id, step.dependencies || []);
    }
  }
  
  // Get next executable steps (dependencies satisfied)
  getReadySteps(): BlueprintStep[] {
    const ready: BlueprintStep[] = [];
    
    for (const [stepId, dependencies] of this.dependencyGraph) {
      if (this.completed.has(stepId) || this.inProgress.has(stepId)) {
        continue; // Skip completed or in-progress
      }
      
      // Check if all dependencies are completed
      const canExecute = dependencies.every(dep => this.completed.has(dep));
      
      if (canExecute) {
        const step = this.steps.get(stepId);
        if (step) ready.push(step);
      }
    }
    
    // Sort by priority (critical first)
    return ready.sort((a, b) => {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
  }
  
  // Mark step as started
  startStep(stepId: string) {
    this.inProgress.add(stepId);
    console.log(`[BLUEPRINT] 🔄 Starting ${stepId}`);
  }
  
  // Mark step as completed
  completeStep(stepId: string) {
    this.inProgress.delete(stepId);
    this.completed.add(stepId);
    console.log(`[BLUEPRINT] ✅ Completed ${stepId}`);
  }
  
  // Get progress stats
  getProgress() {
    const total = this.steps.size;
    const completed = this.completed.size;
    const inProgress = this.inProgress.size;
    const remaining = total - completed - inProgress;
    
    return {
      total,
      completed,
      inProgress, 
      remaining,
      percentComplete: Math.round((completed / total) * 100)
    };
  }
  
  // Get current phase focus
  getCurrentPhases(): string[] {
    const readySteps = this.getReadySteps();
    const phases = [...new Set(readySteps.map(s => s.phase))];
    return phases;
  }
}

// The 123-step Culture Ship blueprint
export const CULTURE_SHIP_BLUEPRINT: Blueprint = [
  {"id":"M001","phase":"marble_foundation","type":"InfraPU","priority":"critical","title":"Pin toolchain (single-port, Node20+TS) and stabilize boot"},
  {"id":"M002","phase":"marble_foundation","type":"RoutingPU","priority":"critical","title":"Mount /api/marble (ingest/status) and wire to cascade planner","dependencies":["M001"]},
  {"id":"M003","phase":"marble_foundation","type":"SafetyPU","priority":"critical","title":"Crash boundaries + entropy index; never die on bad cascades","dependencies":["M001"]},
  {"id":"M004","phase":"marble_foundation","type":"SafetyPU","priority":"critical","title":"/readyz gates on seeds+scheduler; degraded HUD if not ready","dependencies":["M003"]},
  {"id":"M005","phase":"marble_foundation","type":"PersistPU","priority":"high","title":"KV/SQLite hybrid for cascades, runs, artifacts, snapshots","dependencies":["M001"]},
  {"id":"M006","phase":"marble_foundation","type":"BudgetPU","priority":"critical","title":"TokenBudget: local-first, warn@70%, hard@90%, backoff","dependencies":["M001"]},
  {"id":"M007","phase":"marble_foundation","type":"EventsPU","priority":"high","title":"SSE /events + WS /ws compact HUD frames (keepalive 15s)","dependencies":["M001"]},
  {"id":"M008","phase":"marble_foundation","type":"UtilsPU","priority":"critical","title":"Null-safe formatters (safeNumber/safeJSON/percent) everywhere","dependencies":["M001"]},
  {"id":"M009","phase":"marble_foundation","type":"AuthPU","priority":"critical","title":"ADMIN_TOKEN on all mutating routes","dependencies":["M001"]},
  {"id":"M010","phase":"marble_foundation","type":"LogsPU","priority":"high","title":"Pino ring buffer (<=2MB) + compaction job","dependencies":["M008"]},
  {"id":"M011","phase":"marble_foundation","type":"DocPU","priority":"high","title":"README: Infrastructure-First Principles & marble overview","dependencies":["M002"]},
  {"id":"M012","phase":"marble_foundation","type":"DocPU","priority":"high","title":"ARCH.md: single-port, cascades, persistence, budget","dependencies":["M002","M005","M006"]},
  {"id":"M013","phase":"marble_foundation","type":"OpsPU","priority":"high","title":"/api/ops/queue (NDJSON) + dry-run executor","dependencies":["M009"]},
  {"id":"M014","phase":"marble_foundation","type":"OpsPU","priority":"high","title":"Snapshots (manual+daily) + retention (last 7)","dependencies":["M005"]},
  {"id":"M015","phase":"marble_foundation","type":"UI-PU","priority":"high","title":"HUD v1: Stability, Entropy, Budget, Last Msg⛛","dependencies":["M007","M006"]},
  {"id":"M016","phase":"marble_foundation","type":"PolicyPU","priority":"medium","title":"Rate limits on write routes (token bucket)","dependencies":["M009"]},
  {"id":"M017","phase":"marble_foundation","type":"BuildPU","priority":"high","title":"Postinstall client; degrade to server-only if build fails","dependencies":["M001"]},
  {"id":"M018","phase":"marble_foundation","type":"A11yPU","priority":"high","title":"AA contrast, focus rings, reduced motion toggle","dependencies":["M015"]},
  {"id":"M019","phase":"marble_foundation","type":"TestsPU","priority":"high","title":"server.spec (health/ready/ops) + format/validator specs","dependencies":["M008","M013"]},
  {"id":"M020","phase":"marble_foundation","type":"SealPU","priority":"critical","title":"Marble Seal I: Base infra affirmed","dependencies":["M001","M002","M003","M004","M006","M009"]},

  {"id":"M021","phase":"marble_bridges","type":"IntegrationPU","priority":"critical","title":"Git PR bridge: /api/pu/queue-pr (branch, files → PR)","dependencies":["M020"]},
  {"id":"M022","phase":"marble_bridges","type":"CI-PU","priority":"critical","title":"CI: lint/type/test + automerge label hook","dependencies":["M021"]},
  {"id":"M023","phase":"marble_bridges","type":"OpsPU","priority":"high","title":"/replit/sync webhook: pull main, rebuild, gentle restart","dependencies":["M021"]},
  {"id":"M024","phase":"marble_bridges","type":"IntegrationPU","priority":"high","title":"Replit agent runner: /api/agent/lease + /ack (optional)","dependencies":["M021"]},
  {"id":"M025","phase":"marble_bridges","type":"DocPU","priority":"high","title":"PIPELINE.md: System→PR→CI→merge→Replit pull","dependencies":["M022","M023"]},
  {"id":"M026","phase":"marble_bridges","type":"TestsPU","priority":"high","title":"PR smoke: build+test must fail truthfully (no lies)","dependencies":["M022"]},
  {"id":"M027","phase":"marble_bridges","type":"PolicyPU","priority":"medium","title":"CODEOWNERS + branch protection for sensitive paths","dependencies":["M022"]},
  {"id":"M028","phase":"marble_bridges","type":"PersistPU","priority":"medium","title":"Century-capsule snapshot on seals","dependencies":["M014"]},
  {"id":"M029","phase":"marble_bridges","type":"DocPU","priority":"medium","title":"CONTRIBUTING.md (feat/fix/refactor/agent/docs lanes)","dependencies":["M025"]},
  {"id":"M030","phase":"marble_bridges","type":"SealPU","priority":"critical","title":"Marble Seal II: PR/CI/Sync loop proven","dependencies":["M021","M022","M023","M026"]},

  {"id":"M031","phase":"cascade_core","type":"FeaturePU","priority":"critical","title":"Cascade planner: prompt → 6 phases → 500 ops plan","dependencies":["M030"]},
  {"id":"M032","phase":"cascade_core","type":"FeaturePU","priority":"critical","title":"Autonomous executor: budget-aware tick, retry/backoff","dependencies":["M031"]},
  {"id":"M033","phase":"cascade_core","type":"DataPU","priority":"high","title":"Artifact store: plans, diffs, metrics, transcripts","dependencies":["M031"]},
  {"id":"M034","phase":"cascade_core","type":"TestsPU","priority":"high","title":"Deterministic cascade test (same prompt → same phases)","dependencies":["M032"]},
  {"id":"M035","phase":"cascade_core","type":"UXPU","priority":"high","title":"HUD: phase meter, wave counters, ETA","dependencies":["M032"]},
  {"id":"M036","phase":"cascade_core","type":"BudgetPU","priority":"high","title":"Phase quotas; stall detectors; quiet mode on spikes","dependencies":["M032"]},
  {"id":"M037","phase":"cascade_core","type":"RefactorPU","priority":"high","title":"Codemods for templated file scaffolds (low-diff)","dependencies":["M031"]},
  {"id":"M038","phase":"cascade_core","type":"QualityPU","priority":"high","title":"Truthy smoke: forbid 'print: MODULE ACTIVE' fakery","dependencies":["M034"]},
  {"id":"M039","phase":"cascade_core","type":"DocPU","priority":"medium","title":"CASCADE.md: phases, plans, guardrails, budgets","dependencies":["M031","M032"]},
  {"id":"M040","phase":"cascade_core","type":"SealPU","priority":"critical","title":"Marble Seal III: Cascade engine affirmed","dependencies":["M031","M032","M034","M036"]},

  // Continue with remaining phases...
  {"id":"M041","phase":"neural_graph","type":"FeaturePU","priority":"critical","title":"Neural graph index: files/dirs as nodes, edges by import/usage","dependencies":["M040"]},
  {"id":"M050","phase":"neural_graph","type":"SealPU","priority":"critical","title":"Marble Seal IV: Neural planning live","dependencies":["M041"]},
  
  {"id":"M051","phase":"ai_stack","type":"IntegrationPU","priority":"critical","title":"Ollama endpoints (/api/ml/ollama/status|generate)","dependencies":["M050"]},
  {"id":"M060","phase":"ai_stack","type":"SealPU","priority":"critical","title":"Marble Seal V: Local-first AI active","dependencies":["M051"]},
  
  {"id":"M061","phase":"agents_mesh","type":"FeaturePU","priority":"critical","title":"Agent bus: proposals, votes, rate limits","dependencies":["M060"]},
  {"id":"M070","phase":"agents_mesh","type":"SealPU","priority":"critical","title":"Marble Seal VI: Agents mesh online","dependencies":["M061"]},
  
  {"id":"M071","phase":"game_core","type":"FeaturePU","priority":"critical","title":"Deterministic tick loop + speed multipliers","dependencies":["M070"]},
  {"id":"M080","phase":"game_core","type":"SealPU","priority":"critical","title":"Marble Seal VII: Idle backbone verified","dependencies":["M071"]},
  
  {"id":"M081","phase":"cost_truth","type":"TestsPU","priority":"critical","title":"No-lies smoke suite (AI/game/agents/HUD)","dependencies":["M080"]},
  {"id":"M090","phase":"cost_truth","type":"SealPU","priority":"critical","title":"Marble Seal VIII: Cost discipline active","dependencies":["M081"]},
  
  {"id":"M091","phase":"knowledge","type":"IntegrationPU","priority":"high","title":"Obsidian vault sync for docs/lore","dependencies":["M090"]},
  {"id":"M100","phase":"knowledge","type":"SealPU","priority":"critical","title":"Marble Seal IX: Knowledge base live","dependencies":["M091"]},
  
  {"id":"M101","phase":"bloat_guard","type":"FeaturePU","priority":"critical","title":"Curator agent: dupe/orphan detector + purge PRs","dependencies":["M100"]},
  {"id":"M110","phase":"bloat_guard","type":"SealPU","priority":"critical","title":"Marble Seal X: Bloat kept in check","dependencies":["M101"]},
  
  {"id":"M111","phase":"wave_opt","type":"PerfPU","priority":"critical","title":"Wave scheduler: parallel where safe, serialize hotspots","dependencies":["M110"]},
  {"id":"M120","phase":"wave_opt","type":"SealPU","priority":"critical","title":"Marble Seal XI: Waves optimized","dependencies":["M111"]},
  
  {"id":"M121","phase":"endgame","type":"DocPU","priority":"high","title":"Bloomwave Codex: culture, glyphs, rituals","dependencies":["M120"]},
  {"id":"M122","phase":"endgame","type":"SealPU","priority":"critical","title":"Marble Seal XII: Recursive Seal declared","dependencies":["M121"]},
  {"id":"M123","phase":"endgame","type":"SealPU","priority":"critical","title":"Marble Final Seal: Culture Ship ∞ operational","dependencies":["M122"]}
];

export function validateBlueprint(data: unknown): Blueprint {
  return BlueprintSchema.parse(data);
}

export function createBlueprintProcessor(blueprint?: Blueprint): BlueprintProcessor {
  return new BlueprintProcessor(blueprint || CULTURE_SHIP_BLUEPRINT);
}