// shared/agents/contract.ts
import { z } from "zod";

// Legacy schemas (kept for backward compatibility)
export const AgentInput = z.object({
  content: z.string(),
  metadata: z.record(z.any()).optional(),
});

export const AgentOutput = z.object({
  content: z.string(),
  metadata: z.record(z.any()).optional(),
});

export const AgentManifest = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  version: z.string().optional(),
  author: z.string().optional(),
  tags: z.array(z.string()).optional(),
  capabilities: z.array(z.string()).optional(),
  dependencies: z.array(z.string()).optional(),
  role: z.string().optional(),
  runner: z.string().optional(),
  enabled: z.boolean().optional(),
});

// Modern agent types (used by actual agents)
export type TAgentManifest = {
  id: string;
  role: string;
  name: string;
  description: string;
  capabilities: string[];
  version: string;
  runner: string;
  enabled: boolean;
};

export type TAgentInput = {
  t: number;
  utc: number;
  ask?: {
    payload?: {
      action?: string;
      [key: string]: any;
    };
    [key: string]: any;
  };
  [key: string]: any;
};

export type TAgentOutput = {
  ok: boolean;
  effects?: {
    artifactPath?: string;
    stateDelta?: Record<string, any>;
    busEvents?: any[];
  };
  error?: string;
  [key: string]: any;
};

export type TAgentHealth = {
  ok: boolean;
  notes?: string;
  [key: string]: any;
};

export interface Agent {
  manifest: () => TAgentManifest;
  health: () => Promise<TAgentHealth>;
  run: (input: TAgentInput) => Promise<TAgentOutput>;
}

// Legacy interface (kept for backward compatibility)
export interface LegacyAgent {
  process(input: z.infer<typeof AgentInput>): Promise<z.infer<typeof AgentOutput>>;
}

export type { AgentInput as AgentInputType, AgentOutput as AgentOutputType };
