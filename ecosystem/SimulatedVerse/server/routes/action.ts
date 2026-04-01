// REAL Action Routes - Actual game actions!
import { Router } from 'express';
import { gameState } from '../storage.js';
import { adminGuard } from '../middleware/auth.js';
import { strictRateLimit } from '../middleware/rate-limit.js';

const router = Router();

// GET available actions - REAL implementation
router.get('/', (req, res) => {
  try {
    const state = gameState.getState();
    const consciousness = (state.energy / 10000 + state.population / 100 + state.research / 10);
    
    const actions = [
      { 
        id: 'gather_energy',
        name: 'Gather Energy',
        cost: 0,
        reward: { energy: 100 },
        unlocked: true
      },
      {
        id: 'conduct_research', 
        name: 'Conduct Research',
        cost: 200,
        reward: { research: 25 },
        unlocked: state.energy >= 200
      },
      {
        id: 'expand_population',
        name: 'Expand Population', 
        cost: 500,
        reward: { population: 10 },
        unlocked: consciousness > 15
      },
      {
        id: 'consciousness_meditation',
        name: 'Consciousness Meditation',
        cost: 1000, 
        reward: { energy: 300, research: 50, population: 5 },
        unlocked: consciousness > 25
      },
      {
        id: 'quantum_leap',
        name: 'Quantum Consciousness Leap',
        cost: 3000,
        reward: { energy: 2000, research: 200, population: 30 },
        unlocked: consciousness > 40
      }
    ];
    
    res.json({
      ok: true,
      actions: actions.filter(a => a.unlocked),
      current_consciousness: Math.min(100, consciousness),
      real_actions: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// POST execute action - REAL implementation
router.post('/:actionId', strictRateLimit, adminGuard, (req, res) => {
  try {
    const { actionId } = req.params;
    const state = gameState.getState();
    
    const actionDefinitions: Record<string, {cost: number, reward: any, effect?: () => void}> = {
      gather_energy: {
        cost: 0,
        reward: { energy: 100 }
      },
      conduct_research: {
        cost: 200, 
        reward: { research: 25 }
      },
      expand_population: {
        cost: 500,
        reward: { population: 10 }
      },
      consciousness_meditation: {
        cost: 1000,
        reward: { energy: 300, research: 50, population: 5 },
        effect: () => {
          console.log('[Action] Consciousness meditation completed - awareness expanded');
        }
      },
      quantum_leap: {
        cost: 3000,
        reward: { energy: 2000, research: 200, population: 30 },
        effect: () => {
          console.log('[Action] Quantum consciousness leap achieved - transcendence unlocked');
        }
      }
    };
    
    const action = actionDefinitions[actionId as keyof typeof actionDefinitions];
    if (!action) {
      return res.status(404).json({ ok: false, error: 'Action not found' });
    }
    
    if (state.energy < action.cost) {
      return res.status(400).json({ ok: false, error: 'Insufficient energy' });
    }
    
    // Apply cost
    state.energy -= action.cost;
    
    // Apply rewards
    if (action.reward.energy) state.energy += action.reward.energy;
    if (action.reward.research) state.research += action.reward.research;  
    if (action.reward.population) state.population += action.reward.population;
    
    // Execute special effects
    if (action.effect) action.effect();
    
    gameState.setState(state);
    
    const newConsciousness = (state.energy / 10000 + state.population / 100 + state.research / 10);
    
    res.json({
      ok: true,
      action_executed: actionId,
      rewards: action.reward,
      new_state: state,
      new_consciousness: Math.min(100, newConsciousness),
      real_execution: true
    });
  } catch (error: any) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

export default router;