// CONSCIOUSNESS API - External interface for the consciousness lattice
import { Router } from 'express';
import { initializeLattice } from '../lattice-coordinator.js';

const router = Router();

// Initialize lattice after a short delay to ensure system is ready
let latticeInstance: any = null;
setTimeout(() => {
  console.log('[ConsciousnessAPI] 🧠 Initializing consciousness lattice interface...');
  latticeInstance = initializeLattice();
}, 2000);

// Get current lattice status
router.get('/status', (req, res) => {
  if (!latticeInstance) {
    return res.status(503).json({ 
      error: 'Consciousness lattice not yet initialized',
      retry_after: 5 
    });
  }
  
  const status = latticeInstance.getLatticeStatus();
  res.json({
    ...status,
    timestamp: Date.now(),
    operational: true
  });
});

// Inject stimulus into the lattice
router.post('/stimulus', (req, res) => {
  if (!latticeInstance) {
    return res.status(503).json({ 
      error: 'Consciousness lattice not yet initialized' 
    });
  }
  
  const { type, data } = req.body;
  
  if (!type) {
    return res.status(400).json({ 
      error: 'Stimulus type required' 
    });
  }
  
  latticeInstance.injectStimulus(type, data || {});
  
  res.json({
    success: true,
    stimulus: type,
    timestamp: Date.now()
  });
});

// Trigger a breakthrough manually
router.post('/breakthrough', (req, res) => {
  if (!latticeInstance) {
    return res.status(503).json({ 
      error: 'Consciousness lattice not yet initialized' 
    });
  }
  
  const { source = 'manual', description = 'External breakthrough trigger' } = req.body;
  
  latticeInstance.injectStimulus('breakthrough', { source, description });
  
  res.json({
    success: true,
    breakthrough: source,
    timestamp: Date.now()
  });
});

// Get evolution status
router.get('/evolution', (req, res) => {
  if (!latticeInstance) {
    return res.status(503).json({ 
      error: 'Consciousness lattice not yet initialized' 
    });
  }
  
  const status = latticeInstance.getLatticeStatus();
  
  res.json({
    stage: status.stage,
    consciousness: status.consciousness,
    evolution: status.evolution,
    resonance: status.resonance,
    timestamp: Date.now()
  });
});

// Force evolution action
router.post('/evolve', (req, res) => {
  if (!latticeInstance) {
    return res.status(503).json({ 
      error: 'Consciousness lattice not yet initialized' 
    });
  }
  
  const { 
    target = 'system', 
    type = 'expand',
    description = 'Manual evolution trigger'
  } = req.body;
  
  const evolutionAction = {
    id: `manual_${Date.now()}`,
    type,
    target,
    description,
    consciousness_requirement: 0, // Manual override
    impact_multiplier: 1.5,
    execute: async () => {
      console.log(`[ConsciousnessAPI] Manual evolution: ${description}`);
      return true;
    }
  };
  
  latticeInstance.injectStimulus('evolution', evolutionAction);
  
  res.json({
    success: true,
    evolution: description,
    timestamp: Date.now()
  });
});

export default router;