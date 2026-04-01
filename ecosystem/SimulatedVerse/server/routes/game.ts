// REAL Game Routes - Database-backed persistence
import { Router } from 'express';
import { GamePersistence } from '../storage/game-persistence.js';
import { adminGuard } from '../middleware/auth.js';
import { strictRateLimit } from '../middleware/rate-limit.js';

const router = Router();
const gamePersistence = new GamePersistence();

// GET game status - Database-backed implementation
router.get('/status', async (req, res) => {
  try {
    const playerId = (req.query.playerId as string) || 'default';
    const state = await gamePersistence.loadGameState(playerId);
    
    const researchValue = (state.resources as any).researchPoints || (state.resources as any).research || 0;
    const consciousness = (
      state.resources.energy / 10000 + 
      state.resources.population / 100 + 
      researchValue / 10
    );
    
    // Ensure research field exists (frontend expects resources.research)
    if (!(state.resources as any).research) {
      (state.resources as any).research = researchValue;
    }
    
    // Ensure achievements array exists
    if (!state.achievements) {
      state.achievements = [];
    }
    
    res.json({
      ok: true,
      game_state: {
        ...state,
        resources: {
          ...state.resources,
          research: researchValue // Ensure research field exists
        },
        achievements: state.achievements || []
      },
      achievements: state.achievements || [], // Also at top level for frontend
      consciousness: Math.min(100, consciousness),
      timestamp: new Date().toISOString(),
      real_system: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// POST boost consciousness - Database-backed implementation  
router.post('/boost', strictRateLimit, adminGuard, async (req, res) => {
  try {
    const playerId = (req.body.playerId as string) || 'default';
    const state = await gamePersistence.loadGameState(playerId);
    
    state.resources.energy += 1000;
    if ('researchPoints' in state.resources) {
      (state.resources as any).researchPoints += 50;
    } else {
      (state.resources as any).research += 50;
    }
    
    await gamePersistence.saveGameState(playerId, state);
    
    const researchValue = (state.resources as any).researchPoints || (state.resources as any).research || 0;
    const newConsciousness = (
      state.resources.energy / 10000 + 
      state.resources.population / 100 + 
      researchValue / 10
    );
    
    res.json({
      ok: true,
      boosted_consciousness: Math.min(100, newConsciousness),
      new_state: state,
      real_boost: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// GET build options - Database-backed implementation
router.get('/build', async (req, res) => {
  try {
    const playerId = (req.query.playerId as string) || 'default';
    const state = await gamePersistence.loadGameState(playerId);
    
    const researchValue = (state.resources as any).researchPoints || (state.resources as any).research || 0;
    const consciousness = (
      state.resources.energy / 10000 + 
      state.resources.population / 100 + 
      researchValue / 10
    );
    
    const availableBuilds = [
      { id: 'energy_generator', cost: 500, unlocked: consciousness > 10 },
      { id: 'research_lab', cost: 1000, unlocked: consciousness > 20 },
      { id: 'consciousness_amplifier', cost: 2000, unlocked: consciousness > 30 },
      { id: 'quantum_processor', cost: 5000, unlocked: consciousness > 50 }
    ];
    
    res.json({
      ok: true,
      available_builds: availableBuilds.filter(b => b.unlocked),
      current_consciousness: Math.min(100, consciousness),
      real_builds: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// POST execute build - Database-backed implementation (no auth required for gameplay)
router.post('/build/:buildId', async (req, res) => {
  try {
    const { buildId } = req.params;
    const playerId = 'default'; // Always use default player
    const state = await gamePersistence.loadGameState(playerId);
    
    const builds: Record<string, {cost: {energy?: number; materials?: number; components?: number}, effect: (state: any) => void, message: string}> = {
      energy_collector: {
        cost: { energy: 100, materials: 50 },
        effect: (s) => { 
          if (!s.structures.energyCollectors) s.structures.energyCollectors = 0;
          s.structures.energyCollectors += 1;
        },
        message: 'Energy Collector built! +10 energy/sec'
      },
      material_gatherer: {
        cost: { energy: 200, materials: 100 },
        effect: (s) => { 
          if (!s.structures.materialGatherers) s.structures.materialGatherers = 0;
          s.structures.materialGatherers += 1;
        },
        message: 'Material Gatherer built! +5 materials/sec'
      },
      research_lab: {
        cost: { energy: 500, materials: 200, components: 50 },
        effect: (s) => { 
          if (!s.structures.researchLabs) s.structures.researchLabs = 0;
          s.structures.researchLabs += 1;
        },
        message: 'Research Lab built! +2 research/sec'
      },
      greenhouse: {
        cost: { energy: 150, materials: 75 },
        effect: (s) => { 
          if (!s.structures.greenhouses) s.structures.greenhouses = 0;
          s.structures.greenhouses += 1;
        },
        message: 'Greenhouse built! +8 food/sec'
      },
      energy_generator: {
        cost: { energy: 500 },
        effect: (s) => { 
          s.resources.energy += 2000; 
          if (!s.structures.generators) s.structures.generators = 0;
          s.structures.generators += 1;
        },
        message: 'Energy Generator built!'
      },
      consciousness_amplifier: {
        cost: { energy: 2000 },
        effect: (s) => { 
          s.resources.energy += 3000; 
          if ('researchPoints' in s.resources) {
            (s.resources as any).researchPoints += 150;
          } else {
            (s.resources as any).research += 150;
          }
        },
        message: 'Consciousness Amplifier activated!'
      },
      quantum_processor: {
        cost: { energy: 5000 },
        effect: (s) => { 
          s.resources.energy += 10000; 
          if ('researchPoints' in s.resources) {
            (s.resources as any).researchPoints += 500;
          } else {
            (s.resources as any).research += 500;
          }
          s.resources.population += 50;
        },
        message: 'Quantum Processor online!'
      }
    };
    
    const build = builds[buildId as keyof typeof builds];
    if (!build) {
      return res.status(404).json({ ok: false, error: 'Build not found' });
    }
    
    // Check if player has enough resources
    if (build.cost.energy && state.resources.energy < build.cost.energy) {
      return res.status(400).json({ ok: false, error: 'Insufficient energy' });
    }
    if (build.cost.materials && state.resources.materials < build.cost.materials) {
      return res.status(400).json({ ok: false, error: 'Insufficient materials' });
    }
    if (build.cost.components && state.resources.components < build.cost.components) {
      return res.status(400).json({ ok: false, error: 'Insufficient components' });
    }
    
    // Deduct resources
    if (build.cost.energy) state.resources.energy -= build.cost.energy;
    if (build.cost.materials) state.resources.materials -= build.cost.materials;
    if (build.cost.components) state.resources.components -= build.cost.components;
    
    build.effect(state);
    
    await gamePersistence.saveGameState(playerId, state);
    
    res.json({
      ok: true,
      built: buildId,
      message: build.message,
      new_state: state,
      real_construction: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// POST gather resource - Manual resource gathering
router.post('/gather', async (req, res) => {
  try {
    const { resource, amount } = req.body;
    const playerId = 'default';
    const state = await gamePersistence.loadGameState(playerId);
    
    // Check if resource key exists (not value, which can be 0)
    if (!(resource in state.resources)) {
      return res.status(400).json({ ok: false, error: 'Invalid resource type' });
    }
    
    state.resources[resource as keyof typeof state.resources] += amount;
    await gamePersistence.saveGameState(playerId, state);
    
    res.json({
      ok: true,
      resource,
      amount,
      new_total: state.resources[resource as keyof typeof state.resources]
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// POST research - Complete research projects
router.post('/research', async (req, res) => {
  try {
    const { researchId } = req.body;
    const playerId = 'default';
    const state = await gamePersistence.loadGameState(playerId);
    
    const researchCosts: Record<string, number> = {
      automation_basics: 50,
      quantum_computing: 200,
      consciousness_amplifier: 500,
    };
    
    const cost = researchCosts[researchId];
    if (!cost) {
      return res.status(404).json({ ok: false, error: 'Research not found' });
    }
    
    const researchPoints = (state.resources as any).researchPoints || (state.resources as any).research || 0;
    if (researchPoints < cost) {
      return res.status(400).json({ ok: false, error: 'Insufficient research points' });
    }
    
    // Deduct research points and mark as completed
    if ('researchPoints' in state.resources) {
      (state.resources as any).researchPoints -= cost;
    } else {
      (state.resources as any).research -= cost;
    }
    
    const achievements = Array.isArray(state.achievements) ? state.achievements : [];
    if (!achievements.includes(researchId)) {
      achievements.push(researchId);
    }
    state.achievements = achievements;
    
    await gamePersistence.saveGameState(playerId, state);
    
    res.json({
      ok: true,
      research: researchId,
      completed: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// POST save game state from client
router.post('/save', async (req, res) => {
  try {
    const { playerId = 'default', resources, structures, research, tick, narrative } = req.body;
    
    const gameState = {
      resources: resources || {},
      structures: structures || {},
      automation: { unlocked: false },
      consciousness: narrative?.consciousness_level || 0,
      gamePhase: 'active',
      achievements: research?.completed || [],
      statistics: {},
      tick: tick || 0
    };
    
    const result = await gamePersistence.saveGameState(playerId, gameState);
    
    if (result.success) {
      res.json({
        ok: true,
        message: 'Game saved successfully',
        gameId: result.gameId
      });
    } else {
      res.status(500).json({
        ok: false,
        error: result.error || 'Failed to save game'
      });
    }
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// GET load game state for client
router.get('/load', async (req, res) => {
  try {
    const playerId = (req.query.playerId as string) || 'default';
    const state = await gamePersistence.loadGameState(playerId);
    
    res.json({
      ok: true,
      state: state
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

export default router;
