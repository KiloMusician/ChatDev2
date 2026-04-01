/**
 * 🔐 Proof Gate Service - Anti-Hallucination Architecture
 * Verifies agent artifacts with SHA-256 integrity checks and schema validation
 * No agent can claim success without passing through this gate
 */

import fs from "fs";
import path from "path";
import crypto from "crypto";

const CHAMBER = process.env.TESTING_CHAMBER_DIR || "testing_chamber";
const PROOFS = process.env.PROOF_DIR || "ops/proofs";
const MAX_SIZE = Number(process.env.PROOF_MAX_SIZE_BYTES || 1048576); // 1MB limit

export type ProofCheck = { 
  name: string; 
  ok: boolean; 
  detail?: string 
};

export type ProofVerdict = "pass" | "fail";

export type ProofArtifact = {
  id: string;
  job_id: string;
  actor: string;
  kind: "file" | "pr" | "endpoint" | "dataset";
  path: string;
  sha256: string;
  size: number;
  created_at: string;
  checks: ProofCheck[];
  verdict: ProofVerdict;
};

export function sha256(buf: Buffer): string {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function readJSON(filePath: string): any {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

export function ensureDirs(): void {
  fs.mkdirSync(PROOFS, { recursive: true });
  fs.mkdirSync(CHAMBER, { recursive: true });
}

/**
 * Core verification function - computes real checks and verdict
 * Agents never declare success themselves - only this gate decides
 */
export function verifyJob(jobId: string): ProofArtifact {
  ensureDirs();
  const jobRoot = path.join(CHAMBER, "jobs", jobId);
  const proofPath = path.join(jobRoot, "proof.json");
  const filesDir = path.join(jobRoot, "files");

  const checks: ProofCheck[] = [];

  // Check 1: Files exist
  const exists = fs.existsSync(proofPath) && fs.existsSync(filesDir);
  checks.push({ name: "exists", ok: exists });
  if (!exists) {
    return writeVerdict(jobId, checks, "fail", { error: "Missing proof.json or files directory" });
  }

  // Check 2: Schema validation
  let proof;
  try {
    proof = readJSON(proofPath);
    if (!proof || !Array.isArray(proof.files)) {
      throw new Error("files[] array missing in proof.json");
    }
    checks.push({ name: "schema", ok: true });
  } catch (e: any) {
    checks.push({ name: "schema", ok: false, detail: String(e.message || e) });
    return writeVerdict(jobId, checks, "fail", { error: "Invalid proof.json schema" });
  }

  // Check 3: File integrity (SHA-256 + size validation)
  let integrityPass = true;
  for (const fileSpec of proof.files) {
    const filePath = path.join(filesDir, fileSpec.path);
    
    if (!fs.existsSync(filePath)) {
      checks.push({ name: "file_exists", ok: false, detail: fileSpec.path });
      integrityPass = false;
      continue;
    }

    const stat = fs.statSync(filePath);
    if (stat.size <= 0 || stat.size > MAX_SIZE) {
      checks.push({ name: "file_size", ok: false, detail: `${fileSpec.path}:${stat.size}` });
      integrityPass = false;
      continue;
    }

    const content = fs.readFileSync(filePath);
    const computedHash = sha256(content);
    const hashMatch = (fileSpec.sha256 === computedHash);
    checks.push({ 
      name: "sha256", 
      ok: hashMatch, 
      detail: `${fileSpec.path}:${computedHash}` 
    });
    
    if (!hashMatch) integrityPass = false;
  }

  // Check 4: Non-empty files
  const nonEmpty = proof.files.length > 0;
  checks.push({ name: "nonempty", ok: nonEmpty });

  // Final verdict computation
  const verdict: ProofVerdict = integrityPass && nonEmpty ? "pass" : "fail";
  
  return writeVerdict(jobId, checks, verdict, { 
    proof,
    file_count: proof.files.length,
    total_bytes: proof.files.reduce((sum: number, f: any) => sum + (f.size || 0), 0)
  });
}

function writeVerdict(
  jobId: string, 
  checks: ProofCheck[], 
  verdict: ProofVerdict, 
  extra?: any
): ProofArtifact {
  const artifact: ProofArtifact = {
    id: `proof_${jobId}`,
    job_id: jobId,
    actor: extra?.proof?.agent || "unknown",
    kind: "file", // Default, can be overridden
    path: `${PROOFS}/proof_${jobId}.json`,
    sha256: "", // Will be computed after writing
    size: 0, // Will be computed after writing
    created_at: new Date().toISOString(),
    checks,
    verdict,
    ...extra
  };

  const artifactPath = path.join(PROOFS, `proof_${jobId}.json`);
  const content = JSON.stringify(artifact, null, 2);
  fs.writeFileSync(artifactPath, content);
  
  // Compute final hash and size
  const finalContent = fs.readFileSync(artifactPath);
  artifact.sha256 = sha256(finalContent);
  artifact.size = finalContent.length;
  
  // Write final version with computed hash
  fs.writeFileSync(artifactPath, JSON.stringify(artifact, null, 2));
  
  return artifact;
}

/**
 * Get recent proof statistics for monitoring
 */
export function getProofStats(): {
  total: number;
  pass: number;
  fail: number;
  last24h: { pass: number; fail: number };
  recent: ProofArtifact[];
} {
  ensureDirs();
  
  if (!fs.existsSync(PROOFS)) {
    return { total: 0, pass: 0, fail: 0, last24h: { pass: 0, fail: 0 }, recent: [] };
  }

  const proofFiles = fs.readdirSync(PROOFS)
    .filter(f => f.startsWith("proof_") && f.endsWith(".json"))
    .map(f => path.join(PROOFS, f));

  const proofs = proofFiles.map(f => {
    try {
      return readJSON(f) as ProofArtifact;
    } catch {
      return null;
    }
  }).filter(Boolean) as ProofArtifact[];

  const now = Date.now();
  const day = 24 * 60 * 60 * 1000;
  const recent24h = proofs.filter(p => 
    (now - new Date(p.created_at).getTime()) < day
  );

  return {
    total: proofs.length,
    pass: proofs.filter(p => p.verdict === "pass").length,
    fail: proofs.filter(p => p.verdict === "fail").length,
    last24h: {
      pass: recent24h.filter(p => p.verdict === "pass").length,
      fail: recent24h.filter(p => p.verdict === "fail").length
    },
    recent: proofs.slice(-10).reverse() // Last 10, newest first
  };
}