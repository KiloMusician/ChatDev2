// server/router/agents.ts
import { Router } from "express";
import { loadAgents } from "../../agents/registry.js";
import { AgentInput, type TAgentInput } from "../../shared/agents/contract.js";

export const agentsRouter = Router();

agentsRouter.get("/", async (_req, res) => {
  const loaded = await loadAgents();
  
  // Get live health status for each agent
  const agentsWithHealth = await Promise.all(
    loaded.map(async (agent) => {
      try {
        const health = await agent.impl.health();
        return {
          ...agent.manifest,
          health: health?.ok ? "operational" : "degraded",
          mounted: health?.ok ? "mounted" : "unmounted",
          lastCheck: Date.now(),
          notes: health?.notes
        };
      } catch (error) {
        return {
          ...agent.manifest,
          health: "offline",
          mounted: "unmounted", 
          lastCheck: Date.now(),
          error: error instanceof Error ? error.message : "Unknown error"
        };
      }
    })
  );
  
  res.json({ 
    count: loaded.length, 
    agents: agentsWithHealth,
    timestamp: Date.now(),
    all_mounted: agentsWithHealth.every(a => a.mounted === "mounted")
  });
});

agentsRouter.get("/:id/health", async (req, res) => {
  const loaded = await loadAgents();
  const agent = loaded.find(a => a.id === req.params.id);
  if (!agent) return res.status(404).json({ error: "not found" });
  const h = await agent.impl.health();
  res.json(h);
});

agentsRouter.post("/:id/run", async (req, res) => {
  const loaded = await loadAgents();
  const agent = loaded.find(a => a.id === req.params.id);
  if (!agent) return res.status(404).json({ error: "not found" });

  const input = AgentInput.safeParse(req.body);
  if (!input.success) return res.status(400).json({ error: input.error.flatten() });

  const now = Date.now();
  const data = input.data as Record<string, any>;
  const t = typeof data.t === "number" ? data.t : now;
  const utc = typeof data.utc === "number" ? data.utc : now;
  const normalizedInput: TAgentInput = {
    ...data,
    t,
    utc,
    ask: data.ask ?? { payload: data }
  };
  const out = await agent.impl.run(normalizedInput);
  // minimal "fake print" defense: require at least one side-effect
  if (out.ok && (!out.effects || (!out.effects.stateDelta && !out.effects.artifactPath && !out.effects.busEvents))) {
    return res.status(500).json({ ok:false, error:"no side-effects detected" });
  }
  res.json(out);
});
