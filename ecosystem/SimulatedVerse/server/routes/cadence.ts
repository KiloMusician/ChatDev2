/**
 * CADENCE API - Autonomous Agent Coordination System
 * Robot-vacuum coverage patterns for studio floor coordination
 */

import { Router } from 'express';
import { randomUUID } from 'crypto';

const router = Router();

interface CadenceKick {
  id: string;
  timestamp: number;
  agent_class: string;
  workflow: string;
  sector: string;
  triggered_by: string;
}

interface CadenceState {
  active: boolean;
  currentRound: number;
  roundStartTime: number;
  activeAgents: number;
  lastKick: CadenceKick | null;
  coverage: {
    sectors: string[];
    currentSector: string;
    sectorIndex: number;
    completedSweeps: number;
  };
  patterns: {
    current: string;
    available: string[];
    rotationIndex: number;
  };
  proofs: {
    todayCount: number;
    lastProofTime: number;
    successRate: number;
    failedCount: number;
  };
  tokenGuard: {
    softCaps: boolean;
    offlineAgentsEnabled: boolean;
    budgetRemaining: number;
    lastThrottle: number | null;
  };
}

// **CADENCE STATE** - Studio floor coordination
let cadenceState: CadenceState = {
  active: true,
  currentRound: 1,
  roundStartTime: Date.now(),
  activeAgents: 0,
  lastKick: null,
  coverage: {
    sectors: ['code', 'content', 'docs', 'balance', 'UX'],
    currentSector: 'code',
    sectorIndex: 0,
    completedSweeps: 0
  },
  patterns: {
    current: 'spiral',
    available: ['spiral', 'perimeter', 'sector-sweep', 'hotspot-revisit'],
    rotationIndex: 0
  },
  proofs: {
    todayCount: 0,
    lastProofTime: Date.now(),
    successRate: 0.85,
    failedCount: 0
  },
  tokenGuard: {
    softCaps: true,
    offlineAgentsEnabled: true,
    budgetRemaining: 100,
    lastThrottle: null
  }
};

// **GET CADENCE STATUS** - Robot-vacuum coordination overview
router.get('/status', (req, res) => {
  const uptime = Date.now() - cadenceState.roundStartTime;
  const roundDuration = 15 * 60 * 1000; // 15 minutes per round
  const progress = Math.min(1, uptime / roundDuration);
  
  res.json({
    active: cadenceState.active,
    round: cadenceState.currentRound,
    progress: Math.round(progress * 100),
    uptime_ms: uptime,
    current_sector: cadenceState.coverage.currentSector,
    current_pattern: cadenceState.patterns.current,
    active_agents: cadenceState.activeAgents,
    proofs_today: cadenceState.proofs.todayCount,
    success_rate: cadenceState.proofs.successRate,
    token_guard: {
      soft_caps_enabled: cadenceState.tokenGuard.softCaps,
      offline_agents_enabled: cadenceState.tokenGuard.offlineAgentsEnabled,
      budget_remaining: cadenceState.tokenGuard.budgetRemaining
    },
    next_rotation: {
      sector: cadenceState.coverage.sectors[(cadenceState.coverage.sectorIndex + 1) % cadenceState.coverage.sectors.length] ?? cadenceState.coverage.currentSector,
      pattern: cadenceState.patterns.available[(cadenceState.patterns.rotationIndex + 1) % cadenceState.patterns.available.length] ?? cadenceState.patterns.current,
      estimated_start_ms: roundDuration - uptime
    },
    coverage_stats: {
      sectors_completed: cadenceState.coverage.completedSweeps,
      sectors_total: cadenceState.coverage.sectors.length,
      completion_percentage: Math.round((cadenceState.coverage.completedSweeps / cadenceState.coverage.sectors.length) * 100)
    }
  });
});

// **KICK CADENCE** - Force rotation to next workflow
router.post('/kick', (req, res) => {
  const { agent_class = 'offline', workflow = 'studio-sweep', sector = 'auto' } = req.body;
  
  const kickId = randomUUID();
  cadenceState.lastKick = {
    id: kickId,
    timestamp: Date.now(),
    agent_class,
    workflow,
    sector,
    triggered_by: 'api'
  };
  
  // **ROTATE TO NEXT SECTOR & PATTERN**
  if (sector === 'auto' || sector === 'all') {
    cadenceState.coverage.sectorIndex = (cadenceState.coverage.sectorIndex + 1) % cadenceState.coverage.sectors.length;
    cadenceState.coverage.currentSector = cadenceState.coverage.sectors[cadenceState.coverage.sectorIndex] ?? cadenceState.coverage.currentSector;
    
    // Complete sweep when we cycle back to first sector
    if (cadenceState.coverage.sectorIndex === 0) {
      cadenceState.coverage.completedSweeps++;
    }
  } else {
    // Use specific sector if provided
    const sectorIndex = cadenceState.coverage.sectors.indexOf(sector);
    if (sectorIndex >= 0) {
      cadenceState.coverage.sectorIndex = sectorIndex;
      cadenceState.coverage.currentSector = sector;
    }
  }
  
  // **ROTATE PATTERN** - Robot-vacuum coverage mode
  cadenceState.patterns.rotationIndex = (cadenceState.patterns.rotationIndex + 1) % cadenceState.patterns.available.length;
  cadenceState.patterns.current = cadenceState.patterns.available[cadenceState.patterns.rotationIndex] ?? cadenceState.patterns.current;
  
  // **UPDATE ROUND** - New round every kick
  cadenceState.currentRound++;
  cadenceState.roundStartTime = Date.now();
  cadenceState.activeAgents++;
  
  console.log(`[CADENCE-KICK] Round ${cadenceState.currentRound}: ${cadenceState.patterns.current} pattern on ${cadenceState.coverage.currentSector} sector`);
  
  res.json({
    ok: true,
    kick_id: kickId,
    round: cadenceState.currentRound,
    sector: cadenceState.coverage.currentSector,
    pattern: cadenceState.patterns.current,
    agent_class,
    workflow,
    message: `Cadence kicked: ${cadenceState.patterns.current} pattern sweeping ${cadenceState.coverage.currentSector} sector`
  });
});

// **CADENCE HEALTH** - Coverage and token discipline status
router.get('/health', (req, res) => {
  const lastKickAge = cadenceState.lastKick ? Date.now() - cadenceState.lastKick.timestamp : null;
  const staleness = lastKickAge ? Math.round(lastKickAge / 1000 / 60) : null; // minutes
  
  const health = {
    status: cadenceState.active ? 'operational' : 'paused',
    coverage_health: cadenceState.coverage.completedSweeps > 0 ? 'good' : 'pending',
    token_discipline: cadenceState.tokenGuard.softCaps ? 'enabled' : 'disabled',
    staleness_minutes: staleness,
    health_indicators: {
      recent_activity: lastKickAge && lastKickAge < 5 * 60 * 1000, // < 5 minutes
      proof_flow: cadenceState.proofs.todayCount > 0,
      budget_available: cadenceState.tokenGuard.budgetRemaining > 10,
      sector_rotation: cadenceState.coverage.sectorIndex >= 0
    }
  };
  
  const overallHealthy = Object.values(health.health_indicators).every(Boolean);
  
  res.status(overallHealthy ? 200 : 503).json({
    ...health,
    overall: overallHealthy ? 'healthy' : 'degraded',
    timestamp: Date.now()
  });
});

// **PROOF REGISTRATION** - Record successful agent artifacts
router.post('/proof', (req, res) => {
  const { agent, sector, proof_type, artifact_path, verification_hash } = req.body;
  
  if (!agent || !proof_type) {
    return res.status(400).json({ error: 'Missing required fields: agent, proof_type' });
  }
  
  cadenceState.proofs.todayCount++;
  cadenceState.proofs.lastProofTime = Date.now();
  
  // **TRACK SUCCESS RATE** - Simple exponential moving average
  const alpha = 0.1;
  cadenceState.proofs.successRate = cadenceState.proofs.successRate * (1 - alpha) + 1 * alpha;
  
  console.log(`[CADENCE-PROOF] ${agent} completed ${proof_type} for ${sector || 'general'} sector`);
  
  res.json({
    ok: true,
    proof_id: randomUUID(),
    agent,
    sector: sector || cadenceState.coverage.currentSector,
    proof_type,
    timestamp: Date.now(),
    total_proofs_today: cadenceState.proofs.todayCount
  });
});

// **SECTOR MANAGEMENT** - Robot-vacuum room coordination
router.get('/sectors', (req, res) => {
  res.json({
    sectors: cadenceState.coverage.sectors,
    current: cadenceState.coverage.currentSector,
    index: cadenceState.coverage.sectorIndex,
    completed_sweeps: cadenceState.coverage.completedSweeps,
    available_patterns: cadenceState.patterns.available,
    current_pattern: cadenceState.patterns.current
  });
});

router.post('/sectors/:sector', (req, res) => {
  const { sector } = req.params;
  if (!sector) {
    return res.status(400).json({ error: 'Sector required' });
  }
  
  if (!cadenceState.coverage.sectors.includes(sector)) {
    return res.status(404).json({ error: `Sector '${sector}' not found` });
  }
  
  cadenceState.coverage.currentSector = sector;
  cadenceState.coverage.sectorIndex = cadenceState.coverage.sectors.indexOf(sector);
  
  console.log(`[CADENCE-SECTOR] Switched to ${sector} sector`);
  
  res.json({
    ok: true,
    sector,
    message: `Switched to ${sector} sector`,
    timestamp: Date.now()
  });
});

// **TOKEN GUARD CONTROLS** - Soft caps and offline agent management
router.get('/token-guard', (req, res) => {
  res.json(cadenceState.tokenGuard);
});

router.post('/token-guard', (req, res) => {
  const { soft_caps, offline_agents_enabled, budget_remaining } = req.body;
  
  if (typeof soft_caps === 'boolean') {
    cadenceState.tokenGuard.softCaps = soft_caps;
  }
  if (typeof offline_agents_enabled === 'boolean') {
    cadenceState.tokenGuard.offlineAgentsEnabled = offline_agents_enabled;
  }
  if (typeof budget_remaining === 'number') {
    cadenceState.tokenGuard.budgetRemaining = Math.max(0, budget_remaining);
  }
  
  console.log(`[TOKEN-GUARD] Updated: soft_caps=${cadenceState.tokenGuard.softCaps}, offline=${cadenceState.tokenGuard.offlineAgentsEnabled}`);
  
  res.json({
    ok: true,
    updated: cadenceState.tokenGuard,
    timestamp: Date.now()
  });
});

// **PATTERN MANAGEMENT** - Coverage pattern selection
router.get('/patterns', (req, res) => {
  res.json({
    available: cadenceState.patterns.available,
    current: cadenceState.patterns.current,
    rotation_index: cadenceState.patterns.rotationIndex,
    descriptions: {
      'spiral': 'Center-out spiral sweep of repository sections',
      'perimeter': 'Edge-first boundary sweep with inward focus', 
      'sector-sweep': 'Systematic section-by-section coverage',
      'hotspot-revisit': 'Priority focus on recently active areas'
    }
  });
});

router.post('/patterns/:pattern', (req, res) => {
  const { pattern } = req.params;
  if (!pattern) {
    return res.status(400).json({ error: 'Pattern required' });
  }
  
  if (!cadenceState.patterns.available.includes(pattern)) {
    return res.status(404).json({ error: `Pattern '${pattern}' not available` });
  }
  
  cadenceState.patterns.current = pattern;
  cadenceState.patterns.rotationIndex = cadenceState.patterns.available.indexOf(pattern);
  
  console.log(`[CADENCE-PATTERN] Switched to ${pattern} coverage pattern`);
  
  res.json({
    ok: true,
    pattern,
    message: `Switched to ${pattern} coverage pattern`,
    timestamp: Date.now()
  });
});

export default router;
