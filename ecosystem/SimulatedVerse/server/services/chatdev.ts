import { z } from "zod";
import { randomUUID } from "node:crypto";
import { BUDGET_CONFIG } from "../config/constants.js";
import { log } from "./log.js";

// ---- Schemas
export const AgentSpec = z.object({
  id: z.string(),
  role: z.enum(["Architect","Prototyper","Refactorer","Tester","Docsmith","LoreWeaver","Balancer","UX","Perf","Economist","ASCIIArt","GodotIntegrator","Archivist","Analyst","Budgeteer"]),
  traits: z.array(z.string()).default([]),
  maxTokens: z.number().int().nonnegative().default(500),
});

export const TaskSpec = z.object({
  id: z.string(),
  type: z.enum(["RefactorPU","TestPU","DocPU","PerfPU","UXPU","LorePU","BalancePU","GodotPU","DataPU"]),
  title: z.string(),
  payload: z.record(z.any()).default({}),
  estTokens: z.number().int().default(BUDGET_CONFIG.DEFAULT_EST_TOKENS),
  priority: z.enum(["low","med","high","critical"]).default("med"),
});

export const PipelineSpec = z.object({
  id: z.string(),
  name: z.string(),
  stages: z.array(z.object({
    agentId: z.string(),
    promptId: z.string(),
    output: z.enum(["code","plan","notes","tests","metrics","artifact"]),
  })),
});

type TAgent = z.infer<typeof AgentSpec>;
type TTask  = z.infer<typeof TaskSpec>;
type TPipe  = z.infer<typeof PipelineSpec>;

// ---- In-memory registry backed by Store (KV/SQLite)
const registry = {
  agents: new Map<string,TAgent>(),
  prompts: new Map<string,string>(),
  pipelines: new Map<string,TPipe>(),
};

let BUDGET_USED = 0;
const MAX_BUDGET = BUDGET_CONFIG.MAX_BUDGET;

const Budget = {
  reserve(tokens: number): boolean {
    return (BUDGET_USED + tokens) <= MAX_BUDGET;
  },
  consume(tokens: number): void {
    BUDGET_USED += tokens;
  }
};

// ---- Events store (simplified)
const Store = {
  events: {
    async write(event: any): Promise<void> {
      log.info(event, `[ChatDev.Event] ${event.type}`);
    }
  }
};

export const ChatDev = {
  registerAgent(a: TAgent) {
    const v = AgentSpec.parse(a);
    registry.agents.set(v.id, v);
  },
  registerPrompt(id: string, text: string) {
    registry.prompts.set(id, text);
  },
  registerPipeline(p: TPipe) {
    const v = PipelineSpec.parse(p);
    registry.pipelines.set(v.id, v);
  },
  async runPipeline(pipelineId: string, task: TTask) {
    const pl = registry.pipelines.get(pipelineId);
    if (!pl) throw new Error(`Pipeline ${pipelineId} not found`);
    const t = TaskSpec.parse(task);
    
    // Budget gate
    if (!Budget.reserve(t.estTokens)) {
      log.warn({ taskId: t.id, estTokens: t.estTokens }, `[ChatDev] budget denied`);
      return { ok:false, reason:"budget" };
    }
    
    const outputs: Record<string,unknown>[] = [];
    for (const stage of pl.stages) {
      const agent = registry.agents.get(stage.agentId);
      const prompt = registry.prompts.get(stage.promptId) || "";
      if (!agent) throw new Error(`Agent ${stage.agentId} missing`);
      
      // Local deterministic "agent" pass (rule-based / template-based),
      // later can proxy to real LLM if OLLAMA_BRIDGE_URL present.
      const result = await simulateAgent(agent, stage.output, prompt, t);
      outputs.push({ stage, result });
      Budget.consume(Math.min(agent.maxTokens, t.estTokens));
    }
    
    // Persist artifact & event
    await Store.events.write({ 
      type:"chatdev.pipeline.done", 
      taskId:t.id, 
      pipelineId, 
      at:Date.now(), 
      outputs 
    });
    
    return { ok:true, outputs };
  },
  getRegistry() {
    return {
      agents: Array.from(registry.agents.values()),
      prompts: Object.fromEntries(registry.prompts),
      pipelines: Array.from(registry.pipelines.values()),
    };
  }
};

async function simulateAgent(agent: TAgent, output: string, prompt: string, task: TTask) {
  // Deterministic scaffolder: converts task.payload + prompt into a structured artifact.
  // (Keeps us working even if LLM offline; replace with proxy when available.)
  return {
    agent: agent.role,
    notes: `[SIM] ${agent.role} processed ${task.type} — ${task.title}`,
    promptExcerpt: prompt.slice(0,160),
    artifactType: output,
    payloadEcho: task.payload,
    timestamp: Date.now(),
    taskId: task.id,
  };
}
