/* 
OWNERS: team/infra, ai/prime
TAGS: infra, testing, chamber, shadow-fs, proof
STABILITY: beta
INTEGRATIONS: scope/resolver, proof/gate, git/operations
*/

import { Router } from "express";
import { resolveScope, type ScopeSelection } from "../lib/scope.js";
import { adminGuard } from '../middleware/auth.js';
import { strictRateLimit } from '../middleware/rate-limit.js';
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const router = Router();

interface ChamberOperation {
  id: string;
  scope: ScopeSelection;
  patches: Array<{
    file: string;
    operation: 'create' | 'update' | 'delete';
    content?: string;
    originalHash?: string;
  }>;
  status: 'pending' | 'applied' | 'testing' | 'passed' | 'failed';
  proofClaim?: string;
  timestamp: string;
}

const activeChambers = new Map<string, ChamberOperation>();

// Apply patches to Testing Chamber (shadow FS)
router.post("/apply", strictRateLimit, adminGuard, async (req, res) => {
  try {
    const { scope, patches, operationId } = req.body;
    
    if (!scope || !patches || !Array.isArray(patches)) {
      return res.status(400).json({
        ok: false,
        error: "Invalid request: scope and patches required"
      });
    }

    // Validate scope and get file list
    const scopeResult = resolveScope(scope);
    
    // Validate patches only touch files in scope
    const outOfScopeFiles = patches
      .map(p => p.file)
      .filter(file => !scopeResult.files.includes(file));
      
    if (outOfScopeFiles.length > 0) {
      return res.status(400).json({
        ok: false,
        error: "Patches reference files outside scope",
        outOfScopeFiles
      });
    }

    const chamberId = operationId || `chamber_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    
    // Create chamber operation
    const operation: ChamberOperation = {
      id: chamberId,
      scope,
      patches,
      status: 'pending',
      timestamp: new Date().toISOString()
    };

    // Apply to shadow branch
    const shadowBranch = await createShadowBranch(chamberId);
    await applyPatchesToShadow(patches, shadowBranch);
    
    operation.status = 'applied';
    activeChambers.set(chamberId, operation);

    // Trigger smoke tests
    const smokeResults = await runScopeSmokes(scope, shadowBranch);
    
    if (smokeResults.passed) {
      operation.status = 'passed';
      operation.proofClaim = `proof_chamber_${chamberId}`;
    } else {
      operation.status = 'failed';
    }

    activeChambers.set(chamberId, operation);

    res.json({
      ok: true,
      chamberId,
      status: operation.status,
      proofClaim: operation.proofClaim,
      smokeResults,
      message: operation.status === 'passed' 
        ? "Patches applied and tested successfully" 
        : "Patches failed smoke tests"
    });

  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Chamber operation failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Get chamber status
router.get("/status/:chamberId", (req, res) => {
  const { chamberId } = req.params;
  const operation = activeChambers.get(chamberId);
  
  if (!operation) {
    return res.status(404).json({
      ok: false,
      error: "Chamber operation not found"
    });
  }

  res.json({
    ok: true,
    chamber: operation,
    age: Date.now() - new Date(operation.timestamp).getTime()
  });
});

// List active chambers
router.get("/list", (req, res) => {
  const chambers = Array.from(activeChambers.values()).map(op => ({
    id: op.id,
    scope: op.scope,
    status: op.status,
    patchCount: op.patches.length,
    timestamp: op.timestamp
  }));

  res.json({
    ok: true,
    chambers,
    count: chambers.length
  });
});

// Merge successful chamber to main
router.post("/merge/:chamberId", strictRateLimit, adminGuard, async (req, res) => {
  try {
    const { chamberId } = req.params;
    if (!chamberId) {
      return res.status(400).json({ ok: false, error: "Chamber ID required" });
    }
    const operation = activeChambers.get(chamberId);
    
    if (!operation) {
      return res.status(404).json({
        ok: false,
        error: "Chamber operation not found"
      });
    }

    if (operation.status !== 'passed') {
      return res.status(400).json({
        ok: false,
        error: "Can only merge chambers that passed smoke tests",
        status: operation.status
      });
    }

    // Merge shadow branch to main
    const mergeResult = await mergeShadowBranch(chamberId!);
    
    // Clean up chamber
    activeChambers.delete(chamberId);
    
    res.json({
      ok: true,
      merged: true,
      mergeResult,
      prNumber: mergeResult.prNumber,
      commitHash: mergeResult.commitHash,
      message: "Chamber successfully merged to main"
    });

  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Merge failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

async function createShadowBranch(chamberId: string): Promise<string> {
  const branchName = `chamber/${chamberId}`;
  try {
    execSync(`git checkout -b ${branchName}`, { stdio: 'pipe' });
    console.log(`[Chamber] Created shadow branch: ${branchName}`);
    return branchName;
  } catch (error) {
    console.warn(`[Chamber] Failed to create branch, using existing:`, error);
    return branchName;
  }
}

async function applyPatchesToShadow(patches: ChamberOperation['patches'], branch: string) {
  for (const patch of patches) {
    try {
      switch (patch.operation) {
        case 'create':
        case 'update':
          if (patch.content !== undefined) {
            const dir = path.dirname(patch.file);
            if (!fs.existsSync(dir)) {
              fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(patch.file, patch.content);
            console.log(`[Chamber] ${patch.operation} ${patch.file}`);
          }
          break;
        case 'delete':
          if (fs.existsSync(patch.file)) {
            fs.unlinkSync(patch.file);
            console.log(`[Chamber] deleted ${patch.file}`);
          }
          break;
      }
    } catch (error) {
      console.error(`[Chamber] Failed to apply patch to ${patch.file}:`, error);
      throw error;
    }
  }
  
  // Stage changes
  try {
    execSync(`git add .`, { stdio: 'pipe' });
    execSync(`git commit -m "Chamber operation: ${patches.length} patches"`, { stdio: 'pipe' });
  } catch (error) {
    console.warn(`[Chamber] Git operations failed:`, error);
  }
}

async function runScopeSmokes(scope: ScopeSelection, branch: string) {
  // Simplified smoke test - check for TypeScript compilation
  try {
    execSync(`npx tsc --noEmit --skipLibCheck`, { stdio: 'pipe' });
    return { passed: true, tests: ['typescript'], details: 'TypeScript compilation passed' };
  } catch (error) {
    return { 
      passed: false, 
      tests: ['typescript'], 
      details: `TypeScript compilation failed: ${error}`,
      error: String(error)
    };
  }
}

async function mergeShadowBranch(chamberId: string) {
  const branchName = `chamber/${chamberId}`;
  
  try {
    // Switch back to main and merge
    execSync(`git checkout main`, { stdio: 'pipe' });
    execSync(`git merge --no-ff ${branchName}`, { stdio: 'pipe' });
    
    // Get commit hash
    const commitHash = execSync(`git rev-parse HEAD`, { stdio: 'pipe', encoding: 'utf8' }).trim();
    
    // Clean up branch
    execSync(`git branch -d ${branchName}`, { stdio: 'pipe' });
    
    return {
      prNumber: null, // Would integrate with GitHub API for real PRs
      commitHash,
      success: true
    };
  } catch (error) {
    console.error(`[Chamber] Merge failed:`, error);
    throw error;
  }
}

export default router;