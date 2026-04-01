/**
 * 🤖 Agent Gateway - All agent executions route through Testing Chamber
 * Eliminates direct repo modifications and fake success claims
 * Agents must stage files + manifest to pass Proof Gate verification
 */

import { Router } from "express";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { sha256, verifyJob, ensureDirs } from "../services/proofGate.js";

const CHAMBER = process.env.TESTING_CHAMBER_DIR || "testing_chamber";
const router = Router();

function createJobStaging(jobId: string): { base: string; files: string } {
  ensureDirs();
  const base = path.join(CHAMBER, "jobs", jobId);
  const files = path.join(base, "files");
  fs.mkdirSync(files, { recursive: true });
  return { base, files };
}

function listStagedFiles(rootDir: string): string[] {
  const files: string[] = [];
  
  const walk = (dir: string, prefix = "") => {
    for (const item of fs.readdirSync(dir)) {
      const fullPath = path.join(dir, item);
      const relativePath = path.join(prefix, item);
      const stats = fs.statSync(fullPath);
      
      if (stats.isDirectory()) {
        walk(fullPath, relativePath);
      } else {
        files.push(relativePath);
      }
    }
  };
  
  if (fs.existsSync(rootDir)) {
    walk(rootDir);
  }
  
  return files;
}

function resolveAgentRunner(agentName: string): string | null {
  const candidates = [
    path.join(process.cwd(), "agents", agentName, "runner.js"), // Prefer JS for execution
    path.join(process.cwd(), "agents", agentName, "index.js"),
    path.join(process.cwd(), "agents", agentName, "runner.ts"),
    path.join(process.cwd(), "agents", agentName, "index.ts")
  ];
  
  return candidates.find(fs.existsSync) || null;
}

/**
 * POST /api/agent/:agent/execute - Execute agent through Testing Chamber
 * Agent writes to AGENT_OUT_DIR, this creates proof manifest and runs verification
 */
router.post("/agent/:agent/execute", async (req, res) => {
  const { agent } = req.params;
  const jobId = req.body?.job_id || `${agent}-${Date.now()}`;
  const payload = req.body || {};

  const runnerPath = resolveAgentRunner(agent);
  if (!runnerPath) {
    return res.status(404).json({ 
      ok: false, 
      error: `Agent runner not found: ${agent}`,
      job_id: jobId 
    });
  }

  const { base, files } = createJobStaging(jobId);

  try {
    // Spawn agent runner with staging directory
    const proc = spawn(process.execPath, [runnerPath], {
      stdio: ["pipe", "pipe", "pipe"],
      env: { 
        ...process.env, 
        AGENT_OUT_DIR: files,
        JOB_ID: jobId
      }
    });

    // Send payload to agent
    const input = JSON.stringify({
      job_id: jobId,
      input: payload.input || {},
      context: payload.context || {}
    });
    
    proc.stdin.write(input);
    proc.stdin.end();

    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", chunk => stdout += chunk.toString());
    proc.stderr.on("data", chunk => stderr += chunk.toString());

    proc.on("close", (exitCode) => {
      try {
        // Create proof manifest from staged files
        const stagedFiles = listStagedFiles(files).map(relativePath => {
          const fullPath = path.join(files, relativePath);
          const content = fs.readFileSync(fullPath);
          return {
            path: relativePath,
            sha256: sha256(content),
            size: content.length
          };
        });

        const proof = {
          job_id: jobId,
          agent,
          files: stagedFiles,
          created_at: new Date().toISOString(),
          runner_exit_code: exitCode,
          runner_stdout: stdout.slice(0, 2000), // Truncate for storage
          runner_stderr: stderr.slice(0, 1000)
        };

        fs.writeFileSync(path.join(base, "proof.json"), JSON.stringify(proof, null, 2));

        // Run Proof Gate verification
        const verification = verifyJob(jobId);

        res.json({
          ok: exitCode === 0 && verification.verdict === "pass",
          job_id: jobId,
          agent,
          exit_code: exitCode,
          verdict: verification.verdict,
          checks: verification.checks,
          staged_files: stagedFiles.length,
          proof_path: verification.path,
          stderr: stderr.slice(0, 1000) // Include errors for debugging
        });

      } catch (manifestError) {
        res.status(500).json({
          ok: false,
          error: "Failed to create proof manifest",
          job_id: jobId,
          detail: manifestError instanceof Error ? manifestError.message : "Unknown error"
        });
      }
    });

    // Handle spawn errors
    proc.on("error", (spawnError) => {
      res.status(500).json({
        ok: false,
        error: "Agent execution failed",
        job_id: jobId,
        detail: spawnError.message
      });
    });

  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Gateway execution failed",
      job_id: jobId,
      detail: error instanceof Error ? error.message : "Unknown error"
    });
  }
});

/**
 * GET /api/agent/discovery - List available agents
 */
router.get("/agent/discovery", (req, res) => {
  const agentsDir = path.join(process.cwd(), "agents");
  
  if (!fs.existsSync(agentsDir)) {
    return res.json({ ok: true, agents: [] });
  }

  const agents = fs.readdirSync(agentsDir)
    .filter(item => {
      const agentDir = path.join(agentsDir, item);
      return fs.statSync(agentDir).isDirectory() && resolveAgentRunner(item);
    })
    .map(agentName => ({
      name: agentName,
      runner: resolveAgentRunner(agentName),
      status: "available"
    }));

  res.json({ ok: true, agents, count: agents.length });
});

export default router;