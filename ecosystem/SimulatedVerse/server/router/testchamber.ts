// Testing Chamber - Safe Edit Pipeline
import { Router } from "express";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { randomUUID } from "node:crypto";

export const testChamberRouter = Router();

interface EditContract {
  file: string;
  selectors?: string[];
  intent: string;
  edits: Array<{
    find?: string;
    replace?: string;
    insertAfter?: string;
    text?: string;
  }>;
  validators: Array<{
    type: "tsc" | "lint" | "renderProbe";
    path?: string;
    nonBlank?: boolean;
  }>;
  rollback: boolean;
  expect_proof: {
    kind: "pr" | "file" | "diff";
    checks: string[];
  };
}

// Health check endpoint
testChamberRouter.get("/health", (_req, res) => {
  res.json({
    status: "operational",
    version: "1.0.0",
    capabilities: ["plan", "sandbox", "diff", "lint", "proof", "pr"],
    timestamp: Date.now()
  });
});

// Plan endpoint - analyze edit request
testChamberRouter.post("/plan", (req, res) => {
  const contract: EditContract = req.body;
  
  if (!contract.file || !existsSync(contract.file)) {
    return res.status(400).json({
      error: "File not found",
      file: contract.file
    });
  }
  
  const planId = randomUUID();
  const planPath = `ops/testchamber/plans/${planId}.json`;
  
  // Ensure directory exists
  if (!existsSync("ops/testchamber/plans")) {
    mkdirSync("ops/testchamber/plans", { recursive: true });
  }
  
  // Store plan
  writeFileSync(planPath, JSON.stringify(contract, null, 2));
  
  res.json({
    ok: true,
    planId,
    planPath,
    fileExists: true,
    readyForSandbox: true
  });
});

// Diff endpoint - show what would change
testChamberRouter.post("/diff", (req, res) => {
  const { file, edits } = req.body;
  
  if (!existsSync(file)) {
    return res.status(404).json({ error: "File not found" });
  }
  
  const original = readFileSync(file, 'utf8');
  let modified = original;
  
  // Apply edits to create diff
  for (const edit of edits) {
    if (edit.find && edit.replace) {
      modified = modified.replace(edit.find, edit.replace);
    } else if (edit.insertAfter && edit.text) {
      const lines = modified.split('\n');
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line && line.includes(edit.insertAfter)) {
          lines.splice(i + 1, 0, edit.text);
          break;
        }
      }
      modified = lines.join('\n');
    }
  }
  
  const diffLines = modified.split('\n').length - original.split('\n').length;
  
  res.json({
    ok: true,
    originalLines: original.split('\n').length,
    modifiedLines: modified.split('\n').length,
    diffLines: Math.abs(diffLines),
    preview: modified.slice(0, 500) + (modified.length > 500 ? "..." : "")
  });
});

// Proof endpoint - generate verification artifact
testChamberRouter.post("/proof", (req, res) => {
  const { planId, diffResult, lintResult } = req.body;
  
  const proofId = `testchamber_${planId}_${Date.now()}`;
  const proofPath = `ops/proofs/testchamber/${proofId}.json`;
  
  // Ensure directory exists
  if (!existsSync("ops/proofs/testchamber")) {
    mkdirSync("ops/proofs/testchamber", { recursive: true });
  }
  
  const proof = {
    proofId,
    planId,
    timestamp: Date.now(),
    type: "testchamber_execution",
    checks: {
      diffLines: diffResult?.diffLines || 0,
      lintPassed: lintResult?.success || false,
      fileExists: true
    },
    verdict: diffResult?.diffLines > 0 && (lintResult?.success !== false) ? "PASS" : "FAIL"
  };
  
  writeFileSync(proofPath, JSON.stringify(proof, null, 2));
  
  res.json({
    ok: true,
    proofPath,
    verdict: proof.verdict,
    checks: proof.checks
  });
});

export default testChamberRouter;
