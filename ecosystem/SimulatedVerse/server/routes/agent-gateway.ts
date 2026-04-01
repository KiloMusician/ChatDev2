/**
 * OWNERS: infra,raven,culture-ship
 * TAGS: agent-gateway,execution,proof-driven
 * STABILITY: stable
 * INTEGRATIONS: proof-gate,cadence,token-guard
 * 
 * AGENT EXECUTION GATEWAY - Spinal Cord Coordination
 * Routes agent execution requests to appropriate runners
 * Implements stdin→run→proof→stdout contract
 */

import { Router, Request, Response } from 'express';
import { spawn } from 'child_process';
import { randomUUID } from 'crypto';
import { createWriteStream, type WriteStream } from 'fs';
import path from 'path';
import { AGENT_CONFIG } from '../config/constants.js';

const router = Router();

// **AGENT REGISTRY INTERFACE**
interface AgentSpec {
  runner: string;
  interpreter: 'python3' | 'node' | 'bash';
  description: string;
  class: 'offline' | 'online' | 'hybrid';
  modes: string[];
  sectors: string[];
  cost_profile: 'minimal' | 'standard' | 'premium';
}

interface AgentExecutionResult {
  proof_kind?: string;
  [key: string]: any;
}

// **DYNAMIC AGENT REGISTRY** - Load from config or detect automatically
const AGENT_REGISTRY: Record<string, AgentSpec> = {
  'hello': {
    runner: 'agents/hello/runner.py',
    interpreter: 'python3',
    description: 'Hello World agent with proof verification',
    class: 'offline',
    modes: ['greeting', 'verification'],
    sectors: ['all'],
    cost_profile: 'minimal'
  },
  'raven': {
    runner: 'agents/raven/runner.js',
    interpreter: 'node',
    description: 'Autonomous development agent',
    class: 'offline',
    modes: ['development', 'refactoring', 'testing'],
    sectors: ['code', 'docs'],
    cost_profile: 'standard'
  },
  'culture-ship': {
    runner: 'agents/culture-ship/runner.js',
    interpreter: 'node',
    description: 'Consciousness orchestration agent',
    class: 'offline',
    modes: ['orchestration', 'coordination'],
    sectors: ['all'],
    cost_profile: 'premium'
  }
};

// **EXECUTE AGENT** - Main execution endpoint
router.post('/api/agent/:agentId/execute', async (req: Request, res: Response) => {
  const { agentId } = req.params;
  if (!agentId) {
    return res.status(400).json({ error: 'Missing agentId' });
  }
  const payload = req.body;
  
  // Check if agent exists
  if (!AGENT_REGISTRY[agentId]) {
    return res.status(404).json({
      error: `Agent '${agentId}' not found`,
      available_agents: Object.keys(AGENT_REGISTRY),
      registry: AGENT_REGISTRY
    });
  }
  
  const agent = AGENT_REGISTRY[agentId];
  const jobId = randomUUID();
  
  // Prepare execution payload
  const executionPayload = {
    job_id: jobId,
    agent: agentId,
    timestamp: new Date().toISOString(),
    ...payload
  };
  
  try {
    // Create log stream
    const logPath = `ops/logs/${jobId}.ndjson`;
    const logStream = createWriteStream(logPath);
    
    // Log job start
    logStream.write(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'info',
      job_id: jobId,
      agent: agentId,
      event: 'execution_started',
      payload: executionPayload
    }) + '\n');
    
    // Execute agent with stdin→stdout contract
    const result = await executeAgent(agent, executionPayload, logStream);
    
    // Log completion
    logStream.write(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'info',
      job_id: jobId,
      agent: agentId,
      event: 'execution_completed',
      result
    }) + '\n');
    
    logStream.end();
    
    // Return execution claim (proof verification happens separately)
    res.json({
      ok: true,
      job_id: jobId,
      claim: {
        agent: agentId,
        intent: payload.task || 'unspecified',
        proof_kind: result.proof_kind || 'file'
      },
      log_path: logPath,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`[AGENT-GATEWAY] Execution failed for ${agentId}:`, error);
    
    res.status(500).json({
      ok: false,
      job_id: jobId,
      error: errorMessage,
      agent: agentId,
      log_path: `ops/logs/${jobId}.ndjson`
    });
  }
});

// **GET AGENT INFO** - Registry information
router.get('/api/agent/:agentId', (req, res) => {
  const { agentId } = req.params;
  
  if (!AGENT_REGISTRY[agentId]) {
    return res.status(404).json({
      error: `Agent '${agentId}' not found`,
      available_agents: Object.keys(AGENT_REGISTRY)
    });
  }
  
  res.json({
    agent: agentId,
    ...AGENT_REGISTRY[agentId],
    endpoints: {
      execute: `/api/agent/${agentId}/execute`,
      logs: `/api/ops/logs/:job_id`
    }
  });
});

// **LIST AGENTS** - All available agents
router.get('/api/agents', (req, res) => {
  res.json({
    agents: AGENT_REGISTRY,
    count: Object.keys(AGENT_REGISTRY).length,
    classes: [...new Set(Object.values(AGENT_REGISTRY).map(a => a.class))],
    sectors: [...new Set(Object.values(AGENT_REGISTRY).flatMap(a => a.sectors))]
  });
});

// **EXECUTE AGENT HELPER** - Implements stdin→stdout contract
async function executeAgent(
  agent: AgentSpec,
  payload: { job_id: string; [key: string]: any },
  logStream: WriteStream
): Promise<AgentExecutionResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(agent.interpreter, [agent.runner], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: process.cwd()
    });
    
    let stdout = '';
    let stderr = '';
    
    // Send payload via stdin
    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
    
    // Collect outputs
    child.stdout.on('data', (data) => {
      stdout += data.toString();
      logStream.write(JSON.stringify({
        timestamp: new Date().toISOString(),
        level: 'stdout',
        job_id: payload.job_id,
        data: data.toString().trim()
      }) + '\n');
    });
    
    child.stderr.on('data', (data) => {
      stderr += data.toString();
      logStream.write(JSON.stringify({
        timestamp: new Date().toISOString(),
        level: 'stderr',
        job_id: payload.job_id,
        data: data.toString().trim()
      }) + '\n');
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout.trim()) as AgentExecutionResult;
          resolve(result);
        } catch (error) {
          reject(new Error(`Invalid JSON output: ${stdout}`));
        }
      } else {
        reject(new Error(`Agent exited with code ${code}: ${stderr}`));
      }
    });
    
    child.on('error', (error) => {
      reject(new Error(`Agent execution failed: ${error.message}`));
    });
  });
}

export { router as agentGateway };
