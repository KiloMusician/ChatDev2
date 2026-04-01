/**
 * 🧪 Testing Chamber API - Safe Agent Execution with Proof Verification
 * All agent work goes through staging → verification → merge pipeline
 * Eliminates direct repo modifications and "success" hallucinations
 */

import { Router } from "express";
import fs from "fs";
import path from "path";
import { verifyJob, getProofStats, ensureDirs } from "../services/proofGate.js";

const CHAMBER = process.env.TESTING_CHAMBER_DIR || "testing_chamber";
const router = Router();

/**
 * GET /api/testing-chamber/job/:jobId - Check job staging status
 */
router.get("/job/:jobId", (req, res) => {
  const { jobId } = req.params;
  const jobBase = path.join(CHAMBER, "jobs", jobId);
  const proofPath = path.join(jobBase, "proof.json");
  const filesDir = path.join(jobBase, "files");
  
  const status = {
    exists: fs.existsSync(jobBase),
    proof: fs.existsSync(proofPath),
    files: fs.existsSync(filesDir) ? fs.readdirSync(filesDir) : [],
    staged_count: fs.existsSync(filesDir) ? fs.readdirSync(filesDir).length : 0
  };
  
  res.json({ ok: true, job_id: jobId, status });
});

/**
 * POST /api/testing-chamber/verify/:jobId - Run Proof Gate verification
 * Computes real SHA-256 hashes and integrity checks
 */
router.post("/verify/:jobId", (req, res) => {
  try {
    const { jobId } = req.params;
    const artifact = verifyJob(jobId);
    
    res.json({
      ok: true,
      job_id: jobId,
      verdict: artifact.verdict,
      checks: artifact.checks,
      proof_path: artifact.path,
      file_count: artifact.checks.filter(c => c.name === "sha256").length
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: error instanceof Error ? error.message : "Verification failed",
      job_id: req.params.jobId
    });
  }
});

/**
 * POST /api/testing-chamber/merge/:jobId - Merge verified files to repo
 * Only proceeds if Proof Gate verdict === "pass"
 */
router.post("/merge/:jobId", (req, res) => {
  try {
    const { jobId } = req.params;
    const proofPath = path.join(process.env.PROOF_DIR || "ops/proofs", `proof_${jobId}.json`);
    
    if (!fs.existsSync(proofPath)) {
      return res.status(400).json({ 
        ok: false, 
        error: "Proof artifact missing - run verification first",
        job_id: jobId 
      });
    }

    const proof = JSON.parse(fs.readFileSync(proofPath, "utf8"));
    if (proof.verdict !== "pass") {
      return res.status(400).json({ 
        ok: false, 
        error: `Proof Gate verdict: ${proof.verdict} - cannot merge`,
        job_id: jobId,
        failing_checks: proof.checks.filter((c: any) => !c.ok)
      });
    }

    // Safe merge: copy staged files to repo (update-over-create)
    const jobFilesDir = path.join(CHAMBER, "jobs", jobId, "files");
    const mergedFiles: string[] = [];
    
    for (const fileSpec of proof.proof.files) {
      const srcPath = path.join(jobFilesDir, fileSpec.path);
      const dstPath = path.join(process.cwd(), fileSpec.path);
      
      // Ensure destination directory exists
      fs.mkdirSync(path.dirname(dstPath), { recursive: true });
      
      // Copy verified file to repo
      fs.copyFileSync(srcPath, dstPath);
      mergedFiles.push(fileSpec.path);
    }

    res.json({ 
      ok: true, 
      job_id: jobId,
      verdict: "pass",
      merged: mergedFiles,
      merge_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: error instanceof Error ? error.message : "Merge failed",
      job_id: req.params.jobId
    });
  }
});

/**
 * GET /api/testing-chamber/stats - Proof Gate statistics
 */
router.get("/stats", (req, res) => {
  try {
    const stats = getProofStats();
    res.json({ ok: true, ...stats });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: error instanceof Error ? error.message : "Stats failed"
    });
  }
});

/**
 * GET /api/testing-chamber/status - Overall chamber health
 */
router.get("/status", (req, res) => {
  try {
    ensureDirs();
    const stats = getProofStats();
    const chambersActive = fs.existsSync(path.join(CHAMBER, "jobs")) ? 
      fs.readdirSync(path.join(CHAMBER, "jobs")).length : 0;
    
    res.json({
      ok: true,
      status: "operational",
      chambers_active: chambersActive,
      proofs_total: stats.total,
      success_rate_24h: stats.last24h.pass + stats.last24h.fail > 0 ? 
        (stats.last24h.pass / (stats.last24h.pass + stats.last24h.fail)) : 0,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: error instanceof Error ? error.message : "Status check failed"
    });
  }
});

export default router;