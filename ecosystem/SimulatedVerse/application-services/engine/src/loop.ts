import type { KPulseState } from '../../../shared/types/core';
import { hashState } from '../../../shared/utils/hash';
import { spawnIfEligible } from './spawn';

// Game state
let state: KPulseState = {
  tier: 1,
  timestamp: Date.now(),
  
  resources: {
    metal: 50,
    power: 100,
    food: 30,
    knowledge: 10,
    exotic: 0
  },
  
  buildings: {},
  colonists: {},
  
  research: {
    active: null,
    progress: 0,
    completed: new Set(),
    available: new Set(['basic_tools', 'power_grid']),
    tree: []
  },
  
  narrative: {
    activeArcs: [],
    recentEvents: [],
    storytellerMood: 'adaptive',
    intensity: 3,
    lastNarration: Date.now(),
    dialogueHistory: []
  },
  
  hash: '',
  checkpoints: []
};

// Production rates per second
const PRODUCTION_RATES = {
  metal: 0.5,
  power: 0.8,
  knowledge: 0.1,
  food: -0.2 // Food consumption
};

// Tier advancement thresholds
const TIER_THRESHOLDS = [
  { tier: 2, requirements: { metal: 500, power: 200 } },
  { tier: 3, requirements: { metal: 1500, power: 800, knowledge: 100 } },
  { tier: 4, requirements: { metal: 5000, power: 2000, knowledge: 500 } },
  { tier: 5, requirements: { metal: 15000, power: 8000, knowledge: 2000, food: 100 } },
  { tier: 6, requirements: { metal: 50000, power: 25000, knowledge: 10000, exotic: 10 } },
  { tier: 7, requirements: { metal: 150000, power: 100000, knowledge: 50000, exotic: 100 } },
  { tier: 8, requirements: { metal: 500000, power: 400000, knowledge: 200000, exotic: 1000 } }
];

export async function initializeEngine() {
  console.log('🔧 Initializing engine state...');
  
  // Initialize first colonists
  state.colonists = {
    'alex_chen': {
      id: 'alex_chen',
      name: 'Alex Chen',
      traits: ['engineer', 'optimist'],
      mood: 75,
      skills: { engineering: 8, science: 6 },
      task: 'maintain_power',
      relationships: { 'maya_torres': 60 },
      voiceProfile: {
        tone: 'technical',
        verbosity: 3,
        quirks: ['uses_engineering_metaphors']
      },
      memoryBank: []
    },
    'maya_torres': {
      id: 'maya_torres',
      name: 'Dr. Maya Torres',
      traits: ['philosopher', 'social'],
      mood: 55,
      skills: { science: 9, leadership: 7 },
      task: 'research',
      relationships: { 'alex_chen': 70 },
      voiceProfile: {
        tone: 'formal',
        verbosity: 4,
        quirks: ['quotes_philosophers']
      },
      memoryBank: []
    }
  };
  
  // Update hash
  state.hash = hashState(state);
  
  console.log(`✅ Engine initialized - Tier ${state.tier}, Hash: ${state.hash}`);
}

export function step(dt: number) {
  // Update timestamp
  state.timestamp = Date.now();
  
  // Resource production
  updateResources(dt);
  
  // Check tier advancement
  checkTierAdvancement();
  
  // Tier 8+ directive spawning
  if (state.tier >= 8) {
    spawnIfEligible(state);
  }
  
  // Update research
  updateResearch(dt);
  
  // Update colonist tasks
  updateColonists(dt);
  
  // Update hash
  state.hash = hashState(state);
}

function updateResources(dt: number) {
  // Base production
  for (const [resource, rate] of Object.entries(PRODUCTION_RATES)) {
    if (resource in state.resources) {
      (state.resources as any)[resource] += rate * dt;
    }
  }
  
  // Building modifiers
  Object.values(state.buildings).forEach(building => {
    if (!building.active) return;
    
    const efficiency = building.efficiency * building.level;
    
    switch (building.type) {
      case 'generator':
        state.resources.power += 2.0 * efficiency * dt;
        break;
      case 'mine':
        state.resources.metal += 1.5 * efficiency * dt;
        break;
      case 'lab':
        state.resources.knowledge += 0.8 * efficiency * dt;
        break;
      case 'farm':
        state.resources.food += 1.0 * efficiency * dt;
        break;
    }
  });
  
  // Ensure no negative resources (except food)
  state.resources.metal = Math.max(0, state.resources.metal);
  state.resources.power = Math.max(0, state.resources.power);
  state.resources.knowledge = Math.max(0, state.resources.knowledge);
  state.resources.exotic = Math.max(0, state.resources.exotic);
  
  // Food can go negative (starvation)
  if (state.resources.food < 0) {
    // Reduce colonist mood when starving
    Object.values(state.colonists).forEach(colonist => {
      colonist.mood = Math.max(0, colonist.mood - 0.1 * dt);
    });
  }
}

function checkTierAdvancement() {
  const nextTier = TIER_THRESHOLDS.find(t => t.tier > state.tier);
  if (!nextTier) return;
  
  const meetsRequirements = Object.entries(nextTier.requirements).every(
    ([resource, amount]) => (state.resources as any)[resource] >= amount
  );
  
  if (meetsRequirements) {
    const oldTier = state.tier;
    state.tier = nextTier.tier;
    
    console.log(`🎉 Tier advancement: ${oldTier} -> ${state.tier}`);
    
    // Unlock new research
    unlockTierResearch(state.tier);
  }
}

function updateResearch(dt: number) {
  if (!state.research.active) return;
  
  const researchRate = 1.0; // Base research rate
  let modifiedRate = researchRate;
  
  // Lab bonuses
  Object.values(state.buildings).forEach(building => {
    if (building.type === 'lab' && building.active) {
      modifiedRate += 0.5 * building.level * building.efficiency;
    }
  });
  
  // Scientist bonuses
  Object.values(state.colonists).forEach(colonist => {
    if (colonist.task === 'research') {
      modifiedRate += (colonist.skills.science || 0) * 0.1;
    }
  });
  
  state.research.progress += modifiedRate * dt;
  
  // Check completion (research duration is dynamic based on complexity)
  const targetProgress = 100; // Base research time
  if (state.research.progress >= targetProgress) {
    completeResearch(state.research.active);
  }
}

function completeResearch(researchId: string) {
  state.research.completed.add(researchId);
  state.research.available.delete(researchId);
  state.research.active = null;
  state.research.progress = 0;
  
  console.log(`🔬 Research completed: ${researchId}`);
  
  // Unlock new research based on what was completed
  unlockResearchDependencies(researchId);
}

function unlockTierResearch(tier: number) {
  const tierResearch = {
    2: ['advanced_materials', 'energy_efficiency'],
    3: ['automation_basics', 'hydroponics'],
    4: ['quantum_computing', 'exotic_matter'],
    5: ['dimensional_engineering', 'consciousness_transfer'],
    6: ['reality_manipulation', 'temporal_mechanics'],
    7: ['universe_simulation', 'godlike_intelligence'],
    8: ['transcendence_protocols', 'omnipotence_research']
  };
  
  const research = tierResearch[tier as keyof typeof tierResearch] || [];
  research.forEach(id => state.research.available.add(id));
}

function unlockResearchDependencies(researchId: string) {
  const dependencies = {
    'basic_tools': ['advanced_tools', 'metallurgy'],
    'power_grid': ['fusion_power', 'solar_arrays'],
    'automation_basics': ['ai_systems', 'robotic_workforce'],
    'quantum_computing': ['quantum_entanglement', 'parallel_processing']
  };
  
  const unlocks = dependencies[researchId as keyof typeof dependencies] || [];
  unlocks.forEach(id => state.research.available.add(id));
}

function updateColonists(dt: number) {
  Object.values(state.colonists).forEach(colonist => {
    // Mood decay over time
    colonist.mood = Math.max(0, colonist.mood - 0.01 * dt);
    
    // Task-based mood changes
    if (colonist.task === 'research' && colonist.skills.science > 7) {
      colonist.mood += 0.05 * dt; // Enjoys research
    }
    
    // Memory consolidation (simplified)
    if (Math.random() < 0.001 * dt) {
      colonist.memoryBank.push({
        event: `Performed ${colonist.task} task`,
        timestamp: Date.now(),
        emotionalWeight: colonist.mood / 100,
        tags: [colonist.task || 'idle']
      });
      
      // Limit memory bank size
      if (colonist.memoryBank.length > 50) {
        colonist.memoryBank = colonist.memoryBank.slice(-25);
      }
    }
  });
}

export function getState(): KPulseState {
  return state;
}

export function setState(newState: KPulseState) {
  state = newState;
}