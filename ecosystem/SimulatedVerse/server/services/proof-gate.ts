/* 
OWNERS: ai/raven, team/verification
TAGS: ops:proof, verification:gate, connectome
STABILITY: critical
HEALTH: implementing
INTEGRATIONS: ops/worker, agents/*, connectome
*/

import { statSync, readFileSync, existsSync, mkdirSync, writeFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";

export type ProofArtifact = {
  id: string;
  kind: "file" | "pr" | "endpoint" | "dataset";
  path: string; // file path or url
  creator: string; // agent/...
  job_id: string;
  sha256: string;
  size: number;
  created_at: string;
  checks: { name: string; ok: boolean; detail?: string }[];
  verdict: "pass" | "fail";
};

const REG_DIR = "connectome/proof_artifacts";

function sha256File(path: string): string {
  try {
    const buf = readFileSync(path);
    const h = createHash("sha256"); 
    h.update(buf);
    return h.digest("hex");
  } catch {
    return "";
  }
}

export function verifyFileArtifact(jobId: string, agent: string, path: string): ProofArtifact {
  const checks: ProofArtifact["checks"] = [];
  let verdict: "pass" | "fail" = "fail";
  let size = 0, sum = "";

  // Check if file exists
  if (!existsSync(path)) {
    checks.push({ name: "exists", ok: false, detail: "file_not_found" });
    return {
      id: `proof_${jobId}`,
      kind: "file",
      path, creator: `agent/${agent}`, job_id: jobId,
      sha256: "", size: 0, created_at: new Date().toISOString(),
      checks, verdict
    };
  }

  try {
    const st = statSync(path); 
    size = st.size;
    checks.push({ name: "exists", ok: true });
    checks.push({ name: "nonempty", ok: size > 0, detail: `${size} bytes` });

    // Content validation for different types
    if (path.endsWith('.ndjson')) {
      const content = readFileSync(path, "utf8");
      const lines = content.trim().split("\n").filter(Boolean);
      let validLines = 0;
      
      for (const line of lines) {
        try {
          JSON.parse(line);
          validLines++;
        } catch {
          // Invalid JSON line
        }
      }
      
      const isValid = lines.length > 0 && validLines === lines.length;
      checks.push({ 
        name: "schema", 
        ok: isValid, 
        detail: `ndjson:${validLines}/${lines.length} valid lines` 
      });
    } else if (path.endsWith('.json')) {
      try {
        const content = readFileSync(path, "utf8");
        JSON.parse(content);
        checks.push({ name: "schema", ok: true, detail: "valid json" });
      } catch (e) {
        checks.push({ name: "schema", ok: false, detail: `invalid json: ${e}` });
      }
    } else {
      // Generic file validation
      checks.push({ name: "schema", ok: true, detail: "file format accepted" });
    }

    sum = sha256File(path);
    checks.push({ name: "integrity", ok: sum.length === 64, detail: `sha256:${sum.slice(0,8)}...` });

  } catch (e) {
    checks.push({ name: "access", ok: false, detail: `error: ${e}` });
  }

  verdict = checks.every(c => c.ok) ? "pass" : "fail";

  mkdirSync(REG_DIR, { recursive: true });
  const record: ProofArtifact = {
    id: `proof_${jobId}`,
    kind: "file",
    path, creator: `agent/${agent}`, job_id: jobId,
    sha256: sum, size, created_at: new Date().toISOString(),
    checks, verdict
  };
  
  const out = join(REG_DIR, `${record.id}.json`);
  writeFileSync(out, JSON.stringify(record, null, 2));
  return record;
}

export function getProofStats() {
  if (!existsSync(REG_DIR)) return { total: 0, today: 0, passed: 0, failed: 0 };
  
  const files = readdirSync(REG_DIR).filter(f => f.endsWith(".json"));
  const records = files.map(f => {
    try {
      return JSON.parse(readFileSync(join(REG_DIR, f), "utf8"));
    } catch {
      return null;
    }
  }).filter(Boolean);
  
  const todayIso = new Date().toISOString().slice(0, 10);
  const today = records.filter((r: any) => (r.created_at || "").startsWith(todayIso)).length;
  const passed = records.filter((r: any) => r.verdict === "pass").length;
  const failed = records.filter((r: any) => r.verdict === "fail").length;
  
  return { total: records.length, today, passed, failed };
}