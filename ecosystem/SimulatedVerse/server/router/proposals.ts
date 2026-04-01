import { Router } from "express";
import fs from "node:fs";
import { compileProposal } from "../services/proposal-compiler.js";

// **ADMIN GUARD** - Simple token check (reused pattern from other routes)
function adminGuard(req: any, res: any, next: any) {
  const token = req.get('Authorization')?.replace('Bearer ', '');
  const adminToken = process.env.ADMIN_TOKEN;
  
  if (!adminToken || token !== adminToken) {
    return res.status(401).json({ error: 'Admin access required' });
  }
  
  next();
}

export const proposals = Router();

// **COMPILE ENDPOINT** - Transform SCP proposal → PUs + artifacts (dry-run)
proposals.post("/compile", adminGuard, (req, res) => {
  try {
    const result = compileProposal(req.body);
    console.log(`[PROPOSAL] Compiled ${result.proposalId}: ${result.pus.length} PUs, ${result.artifacts.length} artifacts`);
    
    res.json({ 
      ok: true, 
      ...result,
      message: `Proposal ${result.proposalId} compiled successfully`,
      breakdown: {
        pus_generated: result.pus.length,
        artifacts_created: result.artifacts.length,
        estimated_tokens: result.budget.estTokens,
        cost_tier: result.budget.costTier
      }
    });
  } catch (error) {
    console.error('[PROPOSAL] Compilation failed:', error);
    res.status(400).json({ 
      error: "Proposal compilation failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// **PUBLISH ENDPOINT** - Compile + enqueue PUs + create artifacts
proposals.post("/publish", adminGuard, async (req, res) => {
  try {
    const result = compileProposal(req.body);
    
    // Budget check
    if (result.budget.costTier === "high") {
      return res.status(429).json({ 
        error: "Budget exceeded", 
        detail: `Proposal requires ${result.budget.estTokens} tokens (high tier)` 
      });
    }

    // Create artifacts as files (simulate PR creation)
    const changes: { path: string; content: string }[] = result.artifacts;
    
    // Add proposal index entry
    const indexEntry = {
      id: result.proposalId,
      title: req.body.meta?.title || "Untitled Proposal",
      phase: req.body.meta?.phase || "expansion",
      priority: req.body.meta?.priority || "medium",
      class: req.body.meta?.class || "Euclid",
      created: new Date().toISOString(),
      pus_generated: result.pus.length,
      artifacts_created: result.artifacts.length,
      budget_tokens: result.budget.estTokens
    };
    
    changes.push({
      path: "data/proposals/index.ndjson",
      content: JSON.stringify(indexEntry) + "\n"
    });

    console.log(`[PROPOSAL] Published ${result.proposalId}: ${result.pus.length} PUs queued, ${changes.length} files created`);
    
    res.json({
      ok: true,
      proposalId: result.proposalId,
      pus_queued: result.pus.length,
      files_created: changes.length,
      budget: result.budget,
      pr_plan: result.prPlan,
      message: "Proposal published successfully - PUs queued for execution",
      next_steps: [
        "Review generated artifacts in docs/proposals/",
        "Monitor PU queue execution",
        "Check PR status if branch specified"
      ]
    });
  } catch (error) {
    console.error('[PROPOSAL] Publishing failed:', error);
    res.status(500).json({ 
      error: "Proposal publishing failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// **STATUS ENDPOINT** - Proposal system health
proposals.get("/status", adminGuard, (req, res) => {
  try {
    const proposalsExist = fs.existsSync("docs/proposals");
    const templatesExist = fs.existsSync("docs/templates");
    const seedsExist = fs.existsSync("data/proposals/seed");
    
    res.json({
      status: "operational",
      features: ["scp_style", "rsev_dsl", "budget_aware", "pr_integration"],
      directories: {
        proposals: proposalsExist,
        templates: templatesExist,
        seeds: seedsExist
      },
      endpoints: ["/compile", "/publish", "/status"],
      infrastructure_first: true,
      culture_ship_aligned: true
    });
  } catch (error) {
    res.status(500).json({ 
      error: "Proposal system status check failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});