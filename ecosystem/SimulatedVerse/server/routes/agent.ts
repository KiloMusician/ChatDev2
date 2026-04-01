// Real Agent API Implementation
// Created to fix broken agent endpoints exposed in audit

import { Router } from 'express';
import path from 'path';
import fs from 'fs';
import { ROUTE_CONFIG } from '../config/constants.js';

const router = Router();

// Load all agents dynamically
const agentsDir = path.resolve('agents');
const agents = new Map();

async function loadAgents() {
  if (!fs.existsSync(agentsDir)) {
    console.log('[AGENT-API] No agents directory found');
    return;
  }

  const agentDirs = fs.readdirSync(agentsDir, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  for (const agentName of agentDirs) {
    try {
      let agentPath: string | null = null;
      
      // Try multiple extensions in order of preference
      for (const ext of ROUTE_CONFIG.SUPPORTED_AGENT_EXTENSIONS) {
        const candidatePath = path.join(agentsDir, agentName, `index${ext}`);
        if (fs.existsSync(candidatePath)) {
          agentPath = candidatePath;
          break;
        }
      }
      
      if (agentPath) {
        const agentModule = await import(agentPath);
        const agentKey = Object.keys(agentModule).find(key => key.includes('Agent'));
        if (agentKey && agentModule[agentKey]) {
          agents.set(agentName, agentModule[agentKey]);
          console.log(`[AGENT-API] Loaded agent: ${agentName} from ${agentPath}`);
        }
      } else {
        console.log(`[AGENT-API] No index file found for agent: ${agentName}`);
      }
    } catch (error) {
      console.log(`[AGENT-API] Failed to load agent ${agentName}:`, (error as Error).message);
    }
  }
}

// Initialize agents on startup
loadAgents();

// GET /api/agents - List all available agents
router.get('/', (req, res) => {
  const agentList = Array.from(agents.entries()).map(([name, agent]) => ({
    name,
    manifest: agent.manifest ? agent.manifest() : { id: name, name }
  }));
  
  res.json({
    ok: true,
    agents: agentList,
    count: agentList.length
  });
});

// GET /api/agents/:name - Get agent info
router.get('/:name', (req, res) => {
  const { name } = req.params;
  const agent = agents.get(name);
  
  if (!agent) {
    return res.status(404).json({
      ok: false,
      error: `Agent '${name}' not found`
    });
  }

  res.json({
    ok: true,
    agent: {
      name,
      manifest: agent.manifest ? agent.manifest() : { id: name, name }
    }
  });
});

// POST /api/agents/:name/run - Execute agent
router.post('/:name/run', async (req, res) => {
  const { name } = req.params;
  const agent = agents.get(name);
  
  if (!agent) {
    return res.status(404).json({
      ok: false,
      error: `Agent '${name}' not found`
    });
  }

  if (!agent.run) {
    return res.status(400).json({
      ok: false,
      error: `Agent '${name}' has no run method`
    });
  }

  try {
    const input = {
      ...req.body,
      utc: new Date().toISOString(),
      t: Date.now()
    };

    const result = await agent.run(input);
    
    res.json({
      ok: true,
      agent: name,
      result,
      timestamp: Date.now()
    });
  } catch (error) {
    console.log(`[AGENT-API] Error running agent ${name}:`, error);
    res.status(500).json({
      ok: false,
      error: (error as Error).message,
      agent: name
    });
  }
});

// GET /api/agents/:name/health - Check agent health
router.get('/:name/health', async (req, res) => {
  const { name } = req.params;
  const agent = agents.get(name);
  
  if (!agent) {
    return res.status(404).json({
      ok: false,
      error: `Agent '${name}' not found`
    });
  }

  try {
    const health = agent.health ? await agent.health() : { ok: true, notes: "no health check" };
    res.json({
      ok: true,
      agent: name,
      health
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      agent: name,
      error: (error as Error).message
    });
  }
});

export default router;