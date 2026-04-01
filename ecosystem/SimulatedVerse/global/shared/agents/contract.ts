import { z } from "zod";

export const AgentId = z.string().regex(/^[a-z0-9\-]{2,64}$/i);
export const AgentRole = z.enum([
  "alchemist","artificer","librarian","intermediary",
  "council","party","culture-ship","redstone","zod"
]);

export const AgentCapability = z.enum([
  "plan","act","index","build","route","vote","inspect","patch","compose"
]);

export const AgentManifest = z.object({
  id: AgentId,
  role: AgentRole,
  name: z.string(),
  description: z.string(),
  capabilities: z.array(AgentCapability).nonempty(),
  version: z.string().default("0.1.0"),
  runner: z.enum(["in-process","replit-agent","external"]).default("in-process"),
  enabled: z.boolean().default(true)
});
export type AgentManifest = z.infer<typeof AgentManifest>;

export const AgentInput = z.object({
  t: z.number(), // monotonic tick
  utc: z.number(), // Date.now()
  budget: z.number().min(0).max(1), // normalized 0..1 remaining
  entropy: z.number().min(0).max(1),
  context: z.record(z.unknown()).default({}),
  ask: z.object({
    type: z.enum(["plan","act","index","build","route","vote","inspect","patch","compose"]),
    payload: z.any()
  })
});
export type AgentInput = z.infer<typeof AgentInput>;

export const SideEffect = z.object({
  // At least one must be present to be considered "real work"
  stateDelta: z.record(z.unknown()).optional(),
  artifactPath: z.string().optional(), // wrote a file
  busEvents: z.array(z.record(z.unknown())).optional(),
  notes: z.string().optional(),
});
export type SideEffect = z.infer<typeof SideEffect>;

export interface Agent {
  manifest(): AgentManifest;
  health(): Promise<{ ok: boolean; lastRunUTC?: number; notes?: string }>;
  run(input: AgentInput): Promise<{ ok: boolean; effects?: SideEffect; error?: string }>;
}