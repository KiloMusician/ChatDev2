import { z } from "zod";

// Basic schemas used across the codebase
export const ZetaEvent = z.object({
  type: z.string(),
  data: z.record(z.any()),
  timestamp: z.number(),
  source: z.string().optional()
});

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

export type ZetaEvent = z.infer<typeof ZetaEvent>;
export type ZetaPatternT = z.infer<typeof ZetaPattern>;
export type DirectiveT = z.infer<typeof Directive>;
export type SystemStatus = z.infer<typeof SystemStatus>;
export type TaskEvent = z.infer<typeof TaskEvent>;