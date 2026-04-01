import { z } from 'zod';

// Core receipt schema for all system operations
export const ReceiptSchema = z.object({
  id: z.string(),
  timestamp: z.number(),
  kind: z.enum(['proof', 'cascade', 'compilation', 'synthesis', 'test', 'wire', 'audit']),
  tags: z.object({
    omni: z.string(), // SystemDev, ChatDev, GameDev, PreviewUI
    mega: z.string()  // specific system/operation
  }),
  payload: z.record(z.any()),
  receipts_first: z.boolean().default(true),
  anti_theater: z.boolean().default(true)
});

// Mechanic proof receipt
export const MechanicProofSchema = z.object({
  mechanic_id: z.string(),
  proof_kind: z.enum(['scene_loaded', 'test_passed', 'route_wired', 'tick_simulated']),
  counters: z.object({
    files_changed: z.number(),
    scenes_added: z.number(),
    tests_passing: z.number(),
    routes_registered: z.number(),
    ticks_executed: z.number()
  }),
  proof_checks: z.array(z.object({
    check: z.string(),
    status: z.enum(['pass', 'fail', 'skip']),
    evidence: z.string().optional()
  })),
  timestamp: z.number(),
  offline_capable: z.boolean()
});

// UI Route registration
export const UIRouteSchema = z.object({
  route: z.string(),
  label: z.string(),
  guard: z.string().optional(), // requirement to show route
  receiptKey: z.string(), // which receipt proves this mechanic exists
  adapter_type: z.enum(['ascii', 'godot', 'previewui']),
  registered_at: z.number()
});

// System graph nodes and edges
export const SystemGraphSchema = z.object({
  nodes: z.array(z.object({
    id: z.string(),
    type: z.enum(['system', 'scene', 'adapter', 'test', 'route']),
    path: z.string(),
    dependencies: z.array(z.string())
  })),
  edges: z.array(z.object({
    from: z.string(),
    to: z.string(),
    relation: z.enum(['imports', 'calls', 'renders', 'tests', 'wires'])
  })),
  hotPaths: z.array(z.string()), // critical paths for compilation
  timestamp: z.number()
});

// Compilation result
export const CompilationResultSchema = z.object({
  ok: z.boolean(),
  artifacts: z.array(z.object({
    type: z.enum(['scene', 'system', 'test', 'route']),
    path: z.string(),
    size_bytes: z.number()
  })),
  errors: z.array(z.object({
    file: z.string(),
    line: z.number().optional(),
    message: z.string(),
    severity: z.enum(['error', 'warning', 'info'])
  })),
  build_time_ms: z.number(),
  timestamp: z.number()
});

// Offline brain health status
export const OfflineBrainHealthSchema = z.object({
  timestamp: z.number(),
  mode: z.enum(['online', 'offline', 'hybrid']),
  ollama_status: z.enum(['reachable', 'unreachable', 'throttled']),
  openai_status: z.enum(['quota_ok', 'quota_exceeded', 'unreachable']),
  local_models_ready: z.boolean(),
  vector_db_ready: z.boolean(),
  pattern_library_ready: z.boolean(),
  rule_engine_ready: z.boolean(),
  autonomous_tasks_running: z.number()
});

// Watchdog finding
export const WatchdogFindingSchema = z.object({
  kind: z.enum(['ui_desync', 'dead_route', 'missing_proof', 'broken_test', 'import_error']),
  file: z.string(),
  message: z.string(),
  severity: z.enum(['critical', 'high', 'medium', 'low']),
  auto_fixable: z.boolean(),
  suggested_action: z.string().optional(),
  timestamp: z.number()
});

// Culture cascade trigger
export const CascadeTriggerSchema = z.object({
  name: z.string(),
  reason: z.string(),
  streak: z.number(), // how many times this cascade has triggered
  triggered_by: z.array(z.string()), // which systems/conditions caused it
  expected_actions: z.array(z.string()), // what should happen
  timestamp: z.number()
});

// Offline task execution
export const OfflineTaskSchema = z.object({
  task_id: z.string(),
  type: z.enum(['self_healing', 'organizing', 'consolidating', 'annealing', 'cultivation']),
  description: z.string(),
  result: z.record(z.any()),
  cost: z.enum(['free', 'low', 'medium', 'high']),
  requires_llm: z.boolean(),
  execution_time_ms: z.number(),
  timestamp: z.number()
});

// Export types
export type Receipt = z.infer<typeof ReceiptSchema>;
export type MechanicProof = z.infer<typeof MechanicProofSchema>;
export type UIRoute = z.infer<typeof UIRouteSchema>;
export type SystemGraph = z.infer<typeof SystemGraphSchema>;
export type CompilationResult = z.infer<typeof CompilationResultSchema>;
export type OfflineBrainHealth = z.infer<typeof OfflineBrainHealthSchema>;
export type WatchdogFinding = z.infer<typeof WatchdogFindingSchema>;
export type CascadeTrigger = z.infer<typeof CascadeTriggerSchema>;
export type OfflineTask = z.infer<typeof OfflineTaskSchema>;