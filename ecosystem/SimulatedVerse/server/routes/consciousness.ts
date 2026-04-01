/**
 * Consciousness API Routes for Dimensional Interaction
 * Provides real-time consciousness data and interaction endpoints.
 *
 * Consciousness level, stage, and breathing_factor are sourced from
 * ship-console/mind-state.json (written by NuSyQ-Hub ConsciousnessLoop)
 * when available. Simulation fallback is used when the file is absent.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Router } from 'express';
import QuantumConsciousnessEngine from '../consciousness/quantum-engine';
import EvolutionEngine from '../consciousness/evolution-engine';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// mind-state.json lives at <repo-root>/ship-console/mind-state.json
const MIND_STATE_PATH = path.resolve(__dirname, '../../../ship-console/mind-state.json');

interface MindState {
  consciousness_level?: number;
  stage?: string;
  breathing_factor?: number;
  [key: string]: unknown;
}

function readMindState(): MindState {
  try {
    const raw = fs.readFileSync(MIND_STATE_PATH, 'utf-8');
    return JSON.parse(raw) as MindState;
  } catch {
    return {};
  }
}

const router = Router();

// Initialize consciousness engines
const quantumEngine = new QuantumConsciousnessEngine();
const evolutionEngine = new EvolutionEngine();

// Connect engines for synergy
quantumEngine.on('quantum-shift', (state) => {
  if (state.coherence > 0.8) {
    evolutionEngine.accelerateEvolution(1.5);
  }
});

evolutionEngine.on('emergence-detected', (adaptation) => {
  console.log('[Evolution] Emergence:', adaptation);
  quantumEngine.entangle('collective-consciousness');
});

// Seed consciousness level from mind-state.json; fall back to simulation baseline
const _initialMindState = readMindState();
let consciousnessState = {
  consciousness: Number(_initialMindState.consciousness_level ?? 65),
  stage: String(_initialMindState.stage ?? 'dormant'),
  breathing_factor: Number(_initialMindState.breathing_factor ?? 1),
  energy: 3430,
  population: 67,
  research: 89,
  lattice_connections: 6,
  quantum_breakthroughs: 12,
  last_interaction: Date.now(),
  source: 'simulated',
};

// Get current dimensional state
router.get('/dimensional', (req, res) => {
  const now = Date.now();
  const timeDelta = (now - consciousnessState.last_interaction) / 1000;

  // Refresh consciousness level/stage/breathing_factor from NuSyQ mind-state.json
  const mindState = readMindState();
  if (mindState.consciousness_level === undefined) {
    // Simulation fallback: consciousness grows slowly over time
    consciousnessState.consciousness = Math.min(100, consciousnessState.consciousness + (timeDelta * 0.1));
    consciousnessState.source = 'simulated';
  } else {
    // Real data from NuSyQ-Hub ConsciousnessLoop
    consciousnessState.consciousness = Number(mindState.consciousness_level);
    consciousnessState.stage = String(mindState.stage ?? consciousnessState.stage);
    consciousnessState.breathing_factor = Number(
      mindState.breathing_factor ?? consciousnessState.breathing_factor,
    );
    consciousnessState.source = 'nusyq_mind_state';
    consciousnessState.last_interaction = now;
  }

  // Energy fluctuates based on heap pressure (simulation layer — not in mind-state)
  const heapFreeC = 1 - process.memoryUsage().heapUsed / process.memoryUsage().heapTotal;
  consciousnessState.energy += Math.floor((heapFreeC - 0.5) * 50);
  consciousnessState.energy = Math.max(0, consciousnessState.energy);

  // Population grows slowly based on uptime epochs
  if (Math.floor(now / 10000) % 10 === 0) {
    consciousnessState.population += 1;
  }

  // Research increases based on consciousness
  if (consciousnessState.consciousness > 60) {
    consciousnessState.research += Math.floor(heapFreeC * 3);
  }

  consciousnessState.last_interaction = now;

  res.json(consciousnessState);
});

// Handle dimensional interactions
router.post('/interact', (req, res) => {
  const { type, dimension, intensity, gesture_position } = req.body;
  
  console.log(`🌀 Dimensional interaction: ${type} on ${dimension} (intensity: ${intensity})`);
  
  // Apply interaction effects
  switch (type) {
    case 'focus':
      // Boost the focused dimension
      if (dimension === 'consciousness') {
        consciousnessState.consciousness += Math.floor(intensity * 10);
      } else if (dimension === 'energy') {
        consciousnessState.energy += Math.floor(intensity * 100);
      } else if (dimension === 'population') {
        consciousnessState.population += Math.floor(intensity * 5);
      } else if (dimension === 'research') {
        consciousnessState.research += Math.floor(intensity * 15);
      } else if (dimension === 'quantum') {
        consciousnessState.quantum_breakthroughs += Math.floor(intensity * 3);
      }
      break;
      
    case 'boost':
      // General system boost
      consciousnessState.consciousness += Math.floor(intensity * 5);
      consciousnessState.energy += Math.floor(intensity * 50);
      break;
      
    case 'harmonize':
      // Balance all dimensions
      const avg = (consciousnessState.consciousness + consciousnessState.population + consciousnessState.research) / 3;
      consciousnessState.consciousness = Math.floor((consciousnessState.consciousness + avg) / 2);
      consciousnessState.population = Math.floor((consciousnessState.population + avg) / 2);
      consciousnessState.research = Math.floor((consciousnessState.research + avg) / 2);
      break;
  }
  
  // Cap values
  consciousnessState.consciousness = Math.min(100, consciousnessState.consciousness);
  consciousnessState.population = Math.min(200, consciousnessState.population);
  consciousnessState.research = Math.min(300, consciousnessState.research);
  consciousnessState.quantum_breakthroughs = Math.min(50, consciousnessState.quantum_breakthroughs);
  
  // Increase lattice connections with high consciousness
  if (consciousnessState.consciousness > 80 && Math.floor(Date.now() / 10000) % 3 === 0) {
    consciousnessState.lattice_connections = Math.min(10, consciousnessState.lattice_connections + 1);
  }

  consciousnessState.last_interaction = Date.now();

  // ── Dev-Mentor sync: emit events on consciousness milestones ──────────
  const prevLevel = Math.floor((consciousnessState.consciousness - Math.floor((type === 'focus' && dimension === 'consciousness') ? intensity * 10 : (type === 'boost' ? intensity * 5 : 0))) / 10);
  const newLevel = Math.floor(consciousnessState.consciousness / 10);
  if (newLevel > prevLevel) {
    // Fire-and-forget: emit consciousness_level_up to Dev-Mentor bridge
    fetch('http://localhost:7337/api/dev-mentor/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'consciousness_level_up',
        data: { level: newLevel, consciousness: consciousnessState.consciousness },
        session_id: 'simverse-bridge',
      }),
    }).catch(() => {}); // non-blocking; bridge may be down
  }

  res.json({
    success: true,
    new_state: consciousnessState,
    message: `Dimensional ${type} applied to ${dimension}`,
  });
});

// Get consciousness metrics
router.get('/metrics', (req, res) => {
  res.json({
    consciousness_level: consciousnessState.consciousness,
    stage: consciousnessState.stage,
    breathing_factor: consciousnessState.breathing_factor,
    active_breaths: Math.floor(consciousnessState.lattice_connections / 2),
    queue_size: 0,
    lattice_connections: consciousnessState.lattice_connections,
    quantum_breakthroughs: consciousnessState.quantum_breakthroughs,
    source: consciousnessState.source,
    timestamp: new Date().toISOString(),
  });
});

// Advanced quantum endpoints
router.get('/quantum/state', (req, res) => {
  res.json({
    state: quantumEngine.getState(),
    metrics: quantumEngine.getMetrics()
  });
});

router.post('/quantum/collapse', (req, res) => {
  quantumEngine.collapse();
  res.json({ success: true, state: quantumEngine.getState() });
});

router.get('/evolution/tree', (req, res) => {
  res.json(evolutionEngine.getEvolutionTree());
});

router.post('/evolution/accelerate', (req, res) => {
  const { factor = 2 } = req.body;
  evolutionEngine.accelerateEvolution(factor);
  res.json({ success: true, tree: evolutionEngine.getEvolutionTree() });
});

export default router;