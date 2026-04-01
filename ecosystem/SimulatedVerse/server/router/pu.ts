import { Router } from "express";
import { adminGuard } from "../middleware/auth.js";
import fs from 'fs';

export const pu = Router();

// NDJSON PU queue endpoint for autonomous operations
pu.post("/queue", async (req, res) => {
  try {
    const payload = Array.isArray(req.body) ? req.body : [req.body];
    
    console.log(`[PU] 📝 Queuing ${payload.length} Proposal Unit(s)`);
    
    const results = [];
    for (const pu of payload) {
      const puId = pu.id || `pu_${Date.now()}`;
      
      // Process PU based on type
      await processPU(pu);
      
      results.push({
        id: puId,
        type: pu.type,
        status: "queued",
        phase: pu.phase || "autonomous"
      });
    }
    
    res.json({
      ok: true,
      queued: results.length,
      results,
      timestamp: Date.now()
    });
    
  } catch (error) {
    console.error('[PU] Queue processing failed:', error);
    res.status(500).json({
      ok: false,
      error: "PU queue processing failed",
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// PU to PR pipeline
pu.post("/queue-pr", async (req, res) => {
  try {
    const payload = Array.isArray(req.body) ? req.body : [req.body];
    
    console.log(`[PU] 🔗 Converting ${payload.length} PU(s) to PR(s)`);
    
    const results = [];
    for (const pu of payload) {
      // Convert PU to PR format and queue
      const prId = await convertPUToPR(pu);
      
      results.push({
        id: pu.id,
        pr_id: prId,
        status: "pr_created",
        branch: `agent/${pu.phase || 'autonomous'}/${Date.now()}`
      });
    }
    
    res.json({
      ok: true,
      prs_created: results.length,
      results,
      timestamp: Date.now()
    });
    
  } catch (error) {
    console.error('[PU] PR conversion failed:', error);
    res.status(500).json({
      ok: false,
      error: "PU to PR conversion failed",
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// PU status endpoint
pu.get("/status", async (_req, res) => {
  try {
    // Track actual queue size from NDJSON file
    let queueSize = 0;
    try {
      if (fs.existsSync("data/pu_queue.ndjson")) {
        const queueData = fs.readFileSync("data/pu_queue.ndjson", "utf8");
        queueSize = queueData.split("\n").filter(Boolean).length;
      }
    } catch (error) {
      console.warn('[PU] Queue size check failed:', error);
    }
    
    res.json({
      ok: true,
      queue_size: queueSize,
      processed_today: 0,
      pr_pipeline_active: true,
      last_processed: null,
      mode: "autonomous"
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "PU status check failed"
    });
  }
});

async function processPU(pu: any) {
  console.log(`[PU] 🔄 Processing ${pu.type}: ${pu.title}`);
  
  // Simulate PU processing
  switch (pu.type) {
    case 'DocPU':
      // Generate documentation
      console.log(`[PU] 📖 Generating: ${pu.title}`);
      break;
    case 'TestPU':
      // Generate tests  
      console.log(`[PU] 🧪 Creating tests: ${pu.title}`);
      break;
    case 'InfraPU':
      // Infrastructure work
      console.log(`[PU] 🏗️ Infrastructure: ${pu.title}`);
      break;
    case 'FeaturePU':
      // Feature development
      console.log(`[PU] ✨ Feature: ${pu.title}`);
      break;
    case 'RefactorPU':
      // Code refactoring
      console.log(`[PU] 🔧 Refactor: ${pu.title}`);
      break;
    default:
      console.log(`[PU] 🤖 Generic: ${pu.title}`);
  }
  
  // Simulate work delay
  await new Promise(resolve => setTimeout(resolve, 100));
}

async function convertPUToPR(pu: any): Promise<string> {
  console.log(`[PU] 🔗 Converting to PR: ${pu.title}`);
  
  // Simulate PR creation
  const prId = `pr_${pu.id}_${Date.now()}`;
  
  // Would create actual GitHub PR here
  // For now, just simulate
  await new Promise(resolve => setTimeout(resolve, 200));
  
  return prId;
}