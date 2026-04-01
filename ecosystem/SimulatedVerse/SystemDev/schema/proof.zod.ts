import { z } from 'zod';

// Proof check individual result
export const ProofCheckSchema = z.object({
  check_id: z.string(),
  name: z.string(),
  status: z.enum(['pass', 'fail', 'skip', 'pending']),
  evidence: z.string().optional(), // file path, test output, etc.
  expected: z.string().optional(),
  actual: z.string().optional(),
  execution_time_ms: z.number().optional(),
  automated: z.boolean().default(true) // false if manual verification needed
});

// Complete proof result for a mechanic
export const ProofResultSchema = z.object({
  mechanic_id: z.string(),
  spec_path: z.string(), // GameDev/gameplay/specs/mechanic.yml
  proof_kind: z.enum(['full', 'smoke', 'regression', 'integration']),
  overall_status: z.enum(['pass', 'fail', 'partial']),
  checks: z.array(ProofCheckSchema),
  artifacts: z.array(z.object({
    type: z.enum(['scene', 'system', 'test', 'route', 'balance']),
    path: z.string(),
    verified: z.boolean()
  })),
  counters: z.object({
    scenes_loaded: z.number().default(0),
    tests_passed: z.number().default(0),
    routes_accessible: z.number().default(0),
    ticks_simulated: z.number().default(0),
    ui_elements_rendered: z.number().default(0)
  }),
  performance: z.object({
    total_time_ms: z.number(),
    compile_time_ms: z.number(),
    test_time_ms: z.number(),
    scene_load_time_ms: z.number()
  }),
  timestamp: z.number(),
  valid_until: z.number(), // when proof expires
  offline_capable: z.boolean() // can this mechanic work without LLM/internet
});

// Proof freshness check
export const ProofFreshnessSchema = z.object({
  mechanic_id: z.string(),
  last_proof_time: z.number(),
  age_ms: z.number(),
  freshness: z.enum(['fresh', 'stale', 'expired', 'missing']),
  grace_period_remaining_ms: z.number(),
  should_hide_ui: z.boolean() // true if UI should be hidden due to stale proof
});

// Proof pipeline stage
export const ProofPipelineStageSchema = z.object({
  stage: z.enum(['spec', 'synthesize', 'compile', 'test', 'wire', 'proof', 'menu']),
  status: z.enum(['pending', 'running', 'pass', 'fail', 'skip']),
  started_at: z.number().optional(),
  completed_at: z.number().optional(),
  output: z.string().optional(),
  error: z.string().optional()
});

// Complete pipeline execution
export const ProofPipelineSchema = z.object({
  mechanic_id: z.string(),
  pipeline_id: z.string(),
  stages: z.array(ProofPipelineStageSchema),
  overall_status: z.enum(['running', 'success', 'failed', 'cancelled']),
  started_at: z.number(),
  completed_at: z.number().optional(),
  triggered_by: z.string(), // agent/user/cascade that started it
  anti_theater_checks: z.array(z.object({
    check: z.string(),
    passed: z.boolean(),
    evidence: z.string()
  }))
});

// Batch proof validation for multiple mechanics
export const BatchProofSchema = z.object({
  batch_id: z.string(),
  mechanic_ids: z.array(z.string()),
  results: z.array(ProofResultSchema),
  summary: z.object({
    total: z.number(),
    passed: z.number(),
    failed: z.number(),
    skipped: z.number()
  }),
  timestamp: z.number(),
  execution_time_ms: z.number()
});

// Export types
export type ProofCheck = z.infer<typeof ProofCheckSchema>;
export type ProofResult = z.infer<typeof ProofResultSchema>;
export type ProofFreshness = z.infer<typeof ProofFreshnessSchema>;
export type ProofPipelineStage = z.infer<typeof ProofPipelineStageSchema>;
export type ProofPipeline = z.infer<typeof ProofPipelineSchema>;
export type BatchProof = z.infer<typeof BatchProofSchema>;