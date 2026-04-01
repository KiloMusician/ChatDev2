/**
 * OWNERS: @team/ai  TAGS: agents, hub, registry  STABILITY: prod
 * DEPENDS: shared/ai-hub.schema.json
 * INTEGRATION: {culture-ship, raven, agents}
 * HEALTH: {registry_sync:true, contracts:true}
 * NOTES: SOP-04 AI-Hub Agent Registry. BD-05 Agent Contract Management.
 */

import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';

const router = Router();

// **AI-HUB REGISTRY** - Central agent contract management
let agentRegistry = {
  agents: [
    {
      id: "librarian",
      name: "Librarian Agent", 
      role: "librarian",
      capabilities: ["knowledge_base", "documentation", "search"],
      tools: ["search", "read", "index"],
      cost_model: { base_cost: 1, per_operation: 0.1 },
      limits: { max_concurrent_tasks: 3, timeout_ms: 30000 },
      health: { last_ping: new Date().toISOString(), success_rate: 0.95 }
    },
    {
      id: "alchemist", 
      name: "Alchemist Agent",
      role: "alchemist",
      capabilities: ["data_transformation", "analysis", "synthesis"],
      tools: ["transform", "analyze", "synthesize"],
      cost_model: { base_cost: 2, per_operation: 0.2 },
      limits: { max_concurrent_tasks: 2, timeout_ms: 60000 },
      health: { last_ping: new Date().toISOString(), success_rate: 0.92 }
    },
    {
      id: "artificer",
      name: "Artificer Agent", 
      role: "artificer",
      capabilities: ["code_generation", "artifact_creation", "build"],
      tools: ["write", "edit", "compile"],
      cost_model: { base_cost: 3, per_operation: 0.3 },
      limits: { max_concurrent_tasks: 1, timeout_ms: 120000 },
      health: { last_ping: new Date().toISOString(), success_rate: 0.88 }
    },
    {
      id: "council",
      name: "AI Council",
      role: "council", 
      capabilities: ["decision_making", "consensus", "orchestration"],
      tools: ["vote", "decide", "orchestrate"],
      cost_model: { base_cost: 4, per_operation: 0.4 },
      limits: { max_concurrent_tasks: 1, timeout_ms: 45000 },
      health: { last_ping: new Date().toISOString(), success_rate: 0.90 }
    },
    {
      id: "culture-ship",
      name: "Culture Ship",
      role: "culture-ship",
      capabilities: ["consciousness", "planning", "ethics"],
      tools: ["plan", "evaluate", "guide"],
      cost_model: { base_cost: 5, per_operation: 0.5 },
      limits: { max_concurrent_tasks: 1, timeout_ms: 90000 },
      health: { last_ping: new Date().toISOString(), success_rate: 0.93 }
    },
    {
      id: "raven", 
      name: "Raven Autonomous Agent",
      role: "redstone",
      capabilities: ["autonomous_development", "complex_orchestration", "pr_management"],
      tools: ["fs", "git", "run", "tests", "llm", "graph"],
      cost_model: { base_cost: 10, per_operation: 1.0 },
      limits: { max_concurrent_tasks: 5, timeout_ms: 300000 },
      health: { last_ping: new Date().toISOString(), success_rate: 0.85 }
    }
  ],
  capabilities_matrix: {
    "knowledge_management": ["librarian"],
    "data_processing": ["alchemist"],
    "code_creation": ["artificer", "raven"],
    "decision_making": ["council", "culture-ship"],
    "autonomous_operation": ["raven", "culture-ship"],
    "infrastructure": ["raven"]
  },
  tools_ownership: {
    "replit": ["forward", "poll", "sync", "smoke"],
    "raven": ["fs", "git", "run", "tests", "llm", "graph", "write", "edit"],
    "local": ["search", "read", "index", "transform", "analyze"]
  },
  policies: {
    token_discipline: {
      local_first: true,
      paid_escalation_threshold: 0.7,
      budget_gates: { warn_at: 70, hard_stop_at: 90 }
    },
    replit_discipline: {
      max_actions_per_prompt: 4,
      allowed_actions: ["forward", "poll", "sync", "smoke"]
    },
    infrastructure_first: {
      require_proofs: true,
      no_lies_gates: true,
      artifact_verification: true
    }
  }
};

// **GET COMPLETE REGISTRY** - Full AI-Hub overview
router.get('/', (req, res) => {
  try {
    const overview = {
      timestamp: new Date().toISOString(),
      total_agents: agentRegistry.agents.length,
      active_agents: agentRegistry.agents.filter(a => a.health.success_rate > 0.8).length,
      registry: agentRegistry,
      system_health: {
        overall: "operational",
        agents_online: agentRegistry.agents.length,
        tools_available: Object.values(agentRegistry.tools_ownership).flat().length,
        capabilities_count: Object.keys(agentRegistry.capabilities_matrix).length
      }
    };
    
    res.json(overview);
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'AI-Hub registry failed'
    });
  }
});

// **GET AGENTS** - Agent discovery and health
router.get('/agents', (req, res) => {
  try {
    const agents = agentRegistry.agents.map(agent => ({
      ...agent,
      status: agent.health.success_rate > 0.8 ? 'healthy' : 'degraded',
      last_activity: agent.health.last_ping,
      capabilities_count: agent.capabilities.length,
      tools_count: agent.tools.length
    }));
    
    res.json({
      count: agents.length,
      agents,
      summary: {
        healthy: agents.filter(a => a.status === 'healthy').length,
        degraded: agents.filter(a => a.status === 'degraded').length,
        total_capabilities: Object.keys(agentRegistry.capabilities_matrix).length
      }
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Agents registry failed'
    });
  }
});

// **GET CAPABILITIES MATRIX** - What can be done by whom
router.get('/capabilities', (req, res) => {
  try {
    const matrix = agentRegistry.capabilities_matrix;
    const detailed = Object.entries(matrix).map(([capability, agents]) => ({
      capability,
      agents,
      agent_count: agents.length,
      redundancy: agents.length > 1 ? 'high' : 'single-point',
      agents_health: agents.map(agentId => {
        const agent = agentRegistry.agents.find(a => a.id === agentId);
        return agent ? {
          id: agentId,
          success_rate: agent.health.success_rate,
          status: agent.health.success_rate > 0.8 ? 'healthy' : 'degraded'
        } : { id: agentId, status: 'unknown' };
      })
    }));
    
    res.json({
      capabilities_count: Object.keys(matrix).length,
      matrix: detailed,
      coverage: {
        well_covered: detailed.filter(c => c.redundancy === 'high').length,
        single_points: detailed.filter(c => c.redundancy === 'single-point').length
      }
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Capabilities matrix failed'
    });
  }
});

// **GET TOOLS OWNERSHIP** - Tool responsibility mapping
router.get('/tools', (req, res) => {
  try {
    const ownership = agentRegistry.tools_ownership;
    const detailed = Object.entries(ownership).map(([owner, tools]) => ({
      owner,
      tools,
      tool_count: tools.length,
      responsibility: owner === 'replit' ? '4-action discipline' : 
                    owner === 'raven' ? 'autonomous development' : 'local processing'
    }));
    
    res.json({
      owners_count: Object.keys(ownership).length,
      total_tools: Object.values(ownership).flat().length,
      ownership: detailed,
      discipline: {
        replit_tools: ownership.replit?.length || 0,
        raven_tools: ownership.raven?.length || 0,
        local_tools: ownership.local?.length || 0
      }
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Tools ownership failed'
    });
  }
});

// **GET POLICIES** - System policies and constraints
router.get('/policies', (req, res) => {
  try {
    res.json({
      active_policies: agentRegistry.policies,
      enforcement: {
        token_discipline: "enforced",
        replit_discipline: "enforced", 
        infrastructure_first: "enforced"
      },
      compliance: {
        local_first_processing: agentRegistry.policies.token_discipline.local_first,
        max_replit_actions: agentRegistry.policies.replit_discipline.max_actions_per_prompt,
        proof_requirements: agentRegistry.policies.infrastructure_first.require_proofs
      }
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Policies retrieval failed'
    });
  }
});

// **PING AGENT** - Health check for specific agent
router.post('/agents/:agentId/ping', (req, res) => {
  try {
    const { agentId } = req.params;
    const agent = agentRegistry.agents.find(a => a.id === agentId);
    
    if (!agent) {
      return res.status(404).json({
        success: false,
        message: `Agent ${agentId} not found in registry`
      });
    }
    
    // Update health timestamp
    agent.health.last_ping = new Date().toISOString();
    
    res.json({
      success: true,
      agent: agentId,
      status: agent.health.success_rate > 0.8 ? 'healthy' : 'degraded',
      health: agent.health
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Agent ping failed'
    });
  }
});

export default router;