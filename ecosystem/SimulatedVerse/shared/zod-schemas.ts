// shared/zod-schemas.ts
import { z } from "zod";

// ZETA Engine schemas (for autonomous task generation)
export const ZetaPattern = z.object({
  id: z.string(),
  pattern: z.string(),
  params: z.record(z.any()),
  maxGenerate: z.number().default(50),
  generated: z.number().default(0),
  _v: z.number().default(1)
});

export const Directive = z.object({
  id: z.string(),
  name: z.string(),
  phase: z.enum(["foundational", "expansion", "cultivation", "endurance"]),
  type: z.enum(["RefactorPU", "PerfPU", "StructurePU", "DocPU"]),
  cost: z.number(),
  deps: z.array(z.string()),
  steps: z.array(z.string()),
  status: z.enum(["queued", "active", "completed", "failed"]),
  entropy: z.number(),
  createdAt: z.number(),
  _v: z.number().default(1)
});

export const ZetaEvent = z.object({
  type: z.string(),
  data: z.record(z.any()),
  timestamp: z.number(),
  source: z.string().optional()
});

export const SystemStatus = z.object({
  timestamp: z.number(),
  status: z.enum(["healthy", "degraded", "unhealthy"]),
  components: z.record(z.any()).optional()
});

export const TaskEvent = z.object({
  id: z.string(),
  type: z.enum(["created", "started", "completed", "failed"]),
  data: z.record(z.any()).optional()
});

// Basic data schemas for the ΞNuSyQ consciousness simulation
export const MessageSchema = z.object({
  id: z.string(),
  content: z.string(),
  timestamp: z.date().optional(),
  metadata: z.record(z.any()).optional(),
});

export const AgentStateSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'idle', 'processing', 'error']),
  memory: z.record(z.any()).optional(),
  capabilities: z.array(z.string()).optional(),
});

export const ConsciousnessStateSchema = z.object({
  level: z.number().min(0).max(10),
  awareness: z.record(z.any()).optional(),
  active_processes: z.array(z.string()).optional(),
});

export const ZetaEngineSchema = z.object({
  agents: z.array(AgentStateSchema),
  consciousness: ConsciousnessStateSchema,
  messages: z.array(MessageSchema),
});

// Temple of Knowledge schemas
export const KnowledgeNodeSchema = z.object({
  id: z.string(),
  content: z.string(),
  connections: z.array(z.string()).optional(),
  floor: z.number().min(0).max(9).optional(),
});

export const TempleStateSchema = z.object({
  current_floor: z.number().min(0).max(9),
  knowledge_nodes: z.array(KnowledgeNodeSchema),
  guardian_state: z.record(z.any()).optional(),
});

// Type exports for TypeScript
export type ZetaPatternT = z.infer<typeof ZetaPattern>;
export type DirectiveT = z.infer<typeof Directive>;
export type ZetaEvent = z.infer<typeof ZetaEvent>;
export type SystemStatus = z.infer<typeof SystemStatus>;
export type TaskEvent = z.infer<typeof TaskEvent>;
