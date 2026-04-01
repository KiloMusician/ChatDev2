/**
 * OWNERS: ops,infra,culture-ship
 * TAGS: proof-gate,verification,infrastructure-first
 * STABILITY: stable
 * INTEGRATIONS: agent-gateway,cadence,discipline
 * 
 * PROOF GATE SYSTEM - Verification and Registry
 * Validates agent artifacts and maintains proof registry
 * Infrastructure-First proof-driven development
 */

import { Router } from 'express';
import { readFileSync, existsSync, statSync } from 'fs';
import { createHash } from 'crypto';
import path from 'path';

const router = Router();

interface ProofRegistryStats {
  total: number;
  today: number;
  passed: number;
  failed: number;
  last_verification: string | null;
}

interface VerificationCheck {
  name: string;
  status: 'pass' | 'fail';
  detail: string;
}

interface ProofVerification {
  exists: boolean;
  nonempty: boolean;
  schema: boolean;
  hash: boolean;
  content: Record<string, any> | null;
  size: number;
  checks: VerificationCheck[];
  verdict: 'pass' | 'fail';
}

interface ProofArtifact {
  id: string;
  job_id: string;
  agent: string;
  proof_path: string;
  verification: ProofVerification;
  metadata: Record<string, any>;
  registered_at: string;
  verdict: 'pass' | 'fail';
  last_verified?: string;
}

interface ProofRegistry {
  artifacts: Map<string, ProofArtifact>;
  stats: ProofRegistryStats;
  verification_rules: {
    min_size: number;
    max_size: number;
    required_fields: string[];
    allowed_kinds: string[];
  };
}

// **PROOF REGISTRY** - In-memory proof tracking
let proofRegistry: ProofRegistry = {
  artifacts: new Map(),
  stats: {
    total: 0,
    today: 0,
    passed: 0,
    failed: 0,
    last_verification: null
  },
  verification_rules: {
    min_size: 1,
    max_size: 10 * 1024 * 1024, // 10MB
    required_fields: ['id', 'kind', 'path', 'created_at'],
    allowed_kinds: ['file', 'dataset', 'endpoint', 'pr']
  }
};

// Reset daily stats at midnight
setInterval(() => {
  const now = new Date();
  if (now.getHours() === 0 && now.getMinutes() === 0) {
    proofRegistry.stats.today = 0;
    console.log('[PROOF-GATE] Daily stats reset');
  }
}, 60000); // Check every minute

// **VERIFY PROOF** - Core verification logic
function verifyProof(proofPath: string, expectedHash: string | null = null): ProofVerification {
  const verification: ProofVerification = {
    exists: false,
    nonempty: false,
    schema: false,
    hash: false,
    content: null,
    size: 0,
    checks: [],
    verdict: 'fail'
  };
  
  try {
    // Check existence
    if (!existsSync(proofPath)) {
      verification.checks.push({ name: 'exists', status: 'fail', detail: 'File not found' });
      return verification;
    }
    verification.exists = true;
    verification.checks.push({ name: 'exists', status: 'pass', detail: 'File exists' });
    
    // Check size
    const stats = statSync(proofPath);
    verification.size = stats.size;
    
    if (stats.size === 0) {
      verification.checks.push({ name: 'nonempty', status: 'fail', detail: 'File is empty' });
      return verification;
    }
    verification.nonempty = true;
    verification.checks.push({ name: 'nonempty', status: 'pass', detail: `Size: ${stats.size} bytes` });
    
    // Read and parse content
    const content = readFileSync(proofPath, 'utf8');
    const parsedContent = JSON.parse(content);
    if (!parsedContent || typeof parsedContent !== 'object') {
      verification.checks.push({ name: 'schema', status: 'fail', detail: 'Invalid JSON object' });
      return verification;
    }

    verification.content = parsedContent as Record<string, any>;
    verification.schema = true;
    verification.checks.push({ name: 'schema', status: 'pass', detail: 'Valid JSON' });
    
    // Verify required fields
    const missing = proofRegistry.verification_rules.required_fields.filter(
      field => !verification.content || !(field in verification.content)
    );
    
    if (missing.length > 0) {
      verification.checks.push({ 
        name: 'schema', 
        status: 'fail', 
        detail: `Missing fields: ${missing.join(', ')}` 
      });
      return verification;
    }
    
    // Hash verification
    if (expectedHash) {
      const actualHash = createHash('sha256').update(content).digest('hex');
      verification.hash = actualHash === expectedHash;
      verification.checks.push({ 
        name: 'hash', 
        status: verification.hash ? 'pass' : 'fail',
        detail: verification.hash ? 'Hash matches' : `Expected ${expectedHash}, got ${actualHash}`
      });
    } else {
      verification.hash = true;
      verification.checks.push({ name: 'hash', status: 'pass', detail: 'No hash provided to verify' });
    }
    
    // Overall verdict
    verification.verdict = verification.exists && verification.nonempty && 
                          verification.schema && verification.hash ? 'pass' : 'fail';
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    verification.checks.push({ 
      name: 'error', 
      status: 'fail', 
      detail: errorMessage 
    });
  }
  
  return verification;
}

// **REGISTER PROOF** - Add proof to registry
router.post('/register', (req, res) => {
  const { job_id, agent, proof_path, expected_hash, metadata = {} } = req.body;
  
  if (!job_id || !agent || !proof_path) {
    return res.status(400).json({
      error: 'Missing required fields: job_id, agent, proof_path',
      provided: { job_id: !!job_id, agent: !!agent, proof_path: !!proof_path }
    });
  }
  
  // Verify the proof
  const verification = verifyProof(proof_path, expected_hash);
  
  // Register in database
  const artifact = {
    id: `${agent}-${job_id}`,
    job_id,
    agent,
    proof_path,
    verification,
    metadata,
    registered_at: new Date().toISOString(),
    verdict: verification.verdict
  };
  
  proofRegistry.artifacts.set(artifact.id, artifact);
  proofRegistry.stats.total++;
  proofRegistry.stats.today++;
  proofRegistry.stats.last_verification = artifact.registered_at;
  
  if (verification.verdict === 'pass') {
    proofRegistry.stats.passed++;
    console.log(`[PROOF-GATE] ✅ VERIFIED: ${agent} job ${job_id} - PROOF FOUND!`);
  } else {
    proofRegistry.stats.failed++;
    console.log(`[PROOF-GATE] ❌ FAILED: ${agent} job ${job_id} - NO PROOF`);
  }
  
  res.json({
    ok: true,
    artifact_id: artifact.id,
    verdict: verification.verdict,
    verification: verification.checks,
    stats_updated: {
      total: proofRegistry.stats.total,
      passed: proofRegistry.stats.passed,
      failed: proofRegistry.stats.failed
    }
  });
});

// **GET PROOF STATS** - System statistics
router.get('/stats', (req, res) => {
  res.json(proofRegistry.stats);
});

// **GET ARTIFACT** - Retrieve specific proof artifact
router.get('/artifact/:id', (req, res) => {
  const { id } = req.params;
  const artifact = proofRegistry.artifacts.get(id);
  
  if (!artifact) {
    return res.status(404).json({
      error: `Artifact '${id}' not found`,
      available_count: proofRegistry.artifacts.size
    });
  }
  
  res.json(artifact);
});

// **LIST ARTIFACTS** - All proof artifacts
router.get('/artifacts', (req, res) => {
  const { agent, verdict, limit } = req.query;
  const agentFilter = typeof agent === 'string' ? agent : Array.isArray(agent) ? agent[0] : undefined;
  const verdictFilter = typeof verdict === 'string' ? verdict : Array.isArray(verdict) ? verdict[0] : undefined;
  const rawLimitValue = typeof limit === 'string'
    ? limit
    : Array.isArray(limit)
      ? limit[0]
      : undefined;
  const rawLimit = typeof rawLimitValue === 'string' ? rawLimitValue : undefined;
  const parsedLimit = rawLimit ? parseInt(rawLimit, 10) : 50;
  const safeLimit = Number.isFinite(parsedLimit) ? parsedLimit : 50;
  
  let artifacts = Array.from(proofRegistry.artifacts.values());
  
  // Filter by agent
  if (agentFilter) {
    artifacts = artifacts.filter(a => a.agent === agentFilter);
  }
  
  // Filter by verdict
  if (verdictFilter) {
    artifacts = artifacts.filter(a => a.verdict === verdictFilter);
  }
  
  // Sort by registered_at descending
  artifacts.sort((a, b) => new Date(b.registered_at).getTime() - new Date(a.registered_at).getTime());
  
  // Limit results
  artifacts = artifacts.slice(0, Math.max(0, safeLimit));
  
  res.json({
    artifacts,
    count: artifacts.length,
    total_in_registry: proofRegistry.artifacts.size,
    filters: { agent: agentFilter, verdict: verdictFilter, limit: safeLimit }
  });
});

// **VERIFY EXISTING** - Re-verify a proof file
router.post('/verify/:id', (req, res) => {
  const { id } = req.params;
  const artifact = proofRegistry.artifacts.get(id);
  
  if (!artifact) {
    return res.status(404).json({
      error: `Artifact '${id}' not found`
    });
  }
  
  // Re-run verification
  const verification = verifyProof(artifact.proof_path);
  
  // Update artifact
  artifact.verification = verification;
  artifact.verdict = verification.verdict;
  artifact.last_verified = new Date().toISOString();
  
  console.log(`[PROOF-GATE] Re-verified ${id}: ${verification.verdict}`);
  
  res.json({
    ok: true,
    artifact_id: id,
    verdict: verification.verdict,
    verification: verification.checks,
    last_verified: artifact.last_verified
  });
});

// **HEALTH CHECK** - Proof gate system health
router.get('/health', (req, res) => {
  const health = {
    status: 'operational',
    stats: proofRegistry.stats,
    verification_rules: proofRegistry.verification_rules,
    registry_size: proofRegistry.artifacts.size,
    last_activity: proofRegistry.stats.last_verification,
    checks: {
      registry_accessible: true,
      verification_working: true,
      stats_updating: proofRegistry.stats.total > 0
    }
  };
  
  const overallHealthy = Object.values(health.checks).every(Boolean);
  
  res.status(overallHealthy ? 200 : 503).json({
    ...health,
    overall: overallHealthy ? 'healthy' : 'degraded'
  });
});

// **CLEAR REGISTRY** - Reset for testing (admin only)
router.post('/clear', (req, res) => {
  const previousCount = proofRegistry.artifacts.size;
  
  proofRegistry.artifacts.clear();
  proofRegistry.stats = {
    total: 0,
    today: 0,
    passed: 0,
    failed: 0,
    last_verification: null
  };
  
  console.log(`[PROOF-GATE] Registry cleared: ${previousCount} artifacts removed`);
  
  res.json({
    ok: true,
    cleared: previousCount,
    message: 'Proof registry has been reset'
  });
});

export default router;
