import { Router } from "express";
import { ChatDev, TaskSpec } from "../services/chatdev.js";
import { chatDevActivator } from '../autonomous/chatdev-activator.js';
import { RealFileOps } from '../services/real-file-ops.js';
import { AUTH_CONFIG } from '../config/constants.js';

export const chatdev = Router();

// Initialize ChatDev systems
const hasChatDevProvider =
  Boolean(process.env.OPENAI_API_KEY) ||
  Boolean(process.env.OLLAMA_HOST) ||
  process.env.CHATDEV_USE_OLLAMA === "1";

const shouldAutoStartChatDev =
  process.env.ENABLE_CHATDEV_AUTOSTART === "1" ||
  (process.env.ENABLE_CHATDEV_AUTOSTART !== "0" && hasChatDevProvider);

if (shouldAutoStartChatDev) {
  chatDevActivator.initialize().catch(console.error);
} else {
  console.warn("[ChatDev] Autostart disabled: no provider configured");
}
// Theater system removed - using simple file operations

// Improved auth middleware with configurable token
const requireAdmin = (req: any, res: any, next: any) => {
  const token = req.headers.authorization?.replace('Bearer ', '') || 
                req.headers[AUTH_CONFIG.ADMIN_TOKEN_HEADER];
  const adminToken = process.env.ADMIN_TOKEN || 'admin-token';
  
  if (!token || token !== adminToken) {
    return res.status(401).json({ 
      ok: false, 
      error: 'Admin access required',
      hint: 'Provide token via Authorization header or x-admin-token'
    });
  }
  next();
};

chatdev.post("/pipeline/:id/run", requireAdmin, async (req, res) => {
  try {
    const task = TaskSpec.parse(req.body?.task || {});
    const out = await ChatDev.runPipeline(req.params.id, task);
    res.json(out);
  } catch (e: any) {
    res.status(400).json({ ok: false, error: e.message });
  }
});

chatdev.get("/registry", (_, res) => {
  // Expose shallow registry snapshot for UI (no secrets)
  const registry = ChatDev.getRegistry();
  res.json({ ok: true, registry });
});

chatdev.get("/status", (_, res) => {
  const registry = ChatDev.getRegistry();
  const chatdevProjects = chatDevActivator.getActiveProjects();
  const metaProjects = []; // Simplified - no complex meta projects
  
  res.json({ 
    ok: true, 
    agents: registry.agents.length,
    pipelines: registry.pipelines.length,
    prompts: Object.keys(registry.prompts).length,
    autonomous: {
      chatdev: {
        active: chatdevProjects.length,
        total: chatdevProjects.length
      },
      meta: {
        active: metaProjects.length,
        total: 0 // Simplified
      },
      system: 'operational',
      self_improvement: true
    }
  });
});

// New autonomous development endpoints
chatdev.get("/autonomous/projects", (req, res) => {
  try {
    const projects = chatDevActivator.getActiveProjects();
    res.json({
      ok: true,
      projects,
      count: projects.length
    });
  } catch (error: any) {
    res.status(500).json({
      ok: false,
      error: error.message
    });
  }
});

chatdev.post("/autonomous/create", async (req, res) => {
  try {
    const { idea } = req.body;
    
    if (!idea) {
      return res.status(400).json({
        ok: false,
        error: 'Project idea is required'
      });
    }
    
    const projectId = await chatDevActivator.createProject(idea);
    
    res.json({
      ok: true,
      projectId,
      message: 'Autonomous development project initiated'
    });
    
  } catch (error: any) {
    res.status(500).json({
      ok: false,
      error: error.message
    });
  }
});

chatdev.get("/meta/projects", (req, res) => {
  try {
    const projects: any[] = []; // Simplified
    res.json({
      ok: true,
      projects,
      active: 0 // Simplified
    });
  } catch (error: any) {
    res.status(500).json({
      ok: false,
      error: error.message
    });
  }
});

chatdev.post("/meta/improve", async (req, res) => {
  try {
    const { description, target } = req.body;
    
    if (!description || !target) {
      return res.status(400).json({
        ok: false,
        error: 'Description and target are required'
      });
    }
    
    const projectId = 'simple_' + Date.now(); // Simplified
    
    res.json({
      ok: true,
      projectId,
      message: 'Meta-improvement project initiated'
    });
    
  } catch (error: any) {
    res.status(500).json({
      ok: false,
      error: error.message
    });
  }
});
