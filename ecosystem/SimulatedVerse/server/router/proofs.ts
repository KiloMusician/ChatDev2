// Proof Registry and Validation System
import { Router } from "express";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

export const proofsRouter = Router();

interface ProofStats {
  today: {
    total: number;
    pass: number;
    fail: number;
    pending: number;
  };
  recent: Array<{
    id: string;
    timestamp: number;
    verdict: string;
    type: string;
  }>;
}

// Get proof statistics
proofsRouter.get("/stats", (_req, res) => {
  const stats: ProofStats = {
    today: { total: 0, pass: 0, fail: 0, pending: 0 },
    recent: []
  };
  
  const proofDirs = ["ops/proofs", "ops/local-proofs"];
  const today = new Date().toDateString();
  
  for (const dir of proofDirs) {
    if (!existsSync(dir)) continue;
    
    try {
      const files = readdirSync(dir, { recursive: true });
      for (const file of files) {
        if (typeof file === "string" && file.endsWith('.json')) {
          const filePath = join(dir, file);
          const stat = statSync(filePath);
          
          if (stat.mtime.toDateString() === today) {
            stats.today.total++;
            
            try {
              const proof = JSON.parse(readFileSync(filePath, 'utf8'));
              const verdict = proof.verdict || "pending";
              
              if (verdict === "PASS") stats.today.pass++;
              else if (verdict === "FAIL") stats.today.fail++;
              else stats.today.pending++;
              
              stats.recent.push({
                id: proof.proofId || proof.job_id || file,
                timestamp: proof.timestamp || stat.mtime.getTime(),
                verdict,
                type: proof.type || "unknown"
              });
            } catch (e) {
              stats.today.pending++;
            }
          }
        }
      }
    } catch (e) {
      // Directory read error, continue
    }
  }
  
  // Sort recent by timestamp
  stats.recent = stats.recent
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, 20);
  
  res.json(stats);
});

// Register a proof artifact
proofsRouter.post("/register", (req, res) => {
  const { job_id, agent, proof_path, metadata } = req.body;
  
  if (!job_id || !proof_path) {
    return res.status(400).json({ error: "Missing required fields" });
  }
  
  // Verify proof file exists
  const exists = existsSync(proof_path);
  
  res.json({
    ok: true,
    registered: true,
    job_id,
    proof_exists: exists,
    timestamp: Date.now()
  });
});

// Get recent proofs
proofsRouter.get("/recent", (_req, res) => {
  const proofDirs = ["ops/proofs", "ops/local-proofs"];
  const recentProofs = [];
  
  for (const dir of proofDirs) {
    if (!existsSync(dir)) continue;
    
    try {
      const files = readdirSync(dir, { recursive: true });
      for (const file of files) {
        if (typeof file === "string" && file.endsWith('.json')) {
          const filePath = join(dir, file);
          const stat = statSync(filePath);
          
          try {
            const proof = JSON.parse(readFileSync(filePath, 'utf8'));
            recentProofs.push({
              ...proof,
              filePath,
              size: stat.size,
              modified: stat.mtime.getTime()
            });
          } catch (e) {
            // Invalid JSON, skip
          }
        }
      }
    } catch (e) {
      // Directory read error, continue
    }
  }
  
  res.json({
    count: recentProofs.length,
    proofs: recentProofs.sort((a, b) => b.modified - a.modified).slice(0, 50)
  });
});

export default proofsRouter;