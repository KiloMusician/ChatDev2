import { Router, Request, Response } from 'express';

const router = Router();

// In-memory game state (would be in DB in production)
let colonyState = {
  id: 'colony-1',
  resources: {
    energy: 1000,
    materials: 500,
    population: 10,
    research: 0,
    food: 100,
    components: 0,
    tools: 0,
    medicine: 0
  },
  structures: {
    energyCollectors: 2,
    materialGatherers: 1,
    researchLabs: 0,
    greenhouses: 1,
    workshops: 0,
    medicalCenters: 0
  },
  automation: {
    solarCollectors: { level: 1, count: 2, active: true },
    windTurbines: { level: 0, count: 0, active: false },
    miners: { level: 1, count: 1, active: true },
    refineries: { level: 0, count: 0, active: false },
    workshops: { level: 0, count: 0, active: false },
    laboratories: { level: 0, count: 0, active: false },
    greenhouses: { level: 1, count: 1, active: true },
    medicalCenters: { level: 0, count: 0, active: false }
  },
  research: {
    active: null as string | null,
    progress: 0,
    completed: [] as string[],
    available: [] as string[]
  },
  consciousness: 0,
  lastUpdate: Date.now()
};

// Calculate consciousness based on resources
function calculateConsciousness(state: typeof colonyState): number {
  const energy = state.resources.energy || 0;
  const population = state.resources.population || 0;
  const research = state.resources.research || 0;
  
  // Formula: (energy/10000 + population/100 + research/10)
  return Math.min(100, (energy / 10000 + population / 100 + research / 10) * 100);
}

// Process automation tick
function processAutomation(state: typeof colonyState): void {
  const now = Date.now();
  const deltaTime = (now - state.lastUpdate) / 1000; // seconds since last update
  
  // Energy production
  state.resources.energy += state.automation.solarCollectors.count * 2 * deltaTime;
  state.resources.energy += state.automation.windTurbines.count * 3 * deltaTime;
  
  // Material gathering
  state.resources.materials += state.automation.miners.count * 1 * deltaTime;
  
  // Research generation
  state.resources.research += state.automation.laboratories.count * 0.5 * deltaTime;
  
  // Food production
  state.resources.food += state.automation.greenhouses.count * 0.8 * deltaTime;
  
  // Component manufacturing
  state.resources.components += state.automation.workshops.count * 0.3 * deltaTime;
  
  // Medicine production
  state.resources.medicine += state.automation.medicalCenters.count * 0.2 * deltaTime;
  
  state.lastUpdate = now;
}

// Get colony state
router.get('/colony', (req: Request, res: Response) => {
  // Process automation before returning state
  processAutomation(colonyState);
  
  // Update consciousness
  colonyState.consciousness = calculateConsciousness(colonyState);
  
  res.json({
    success: true,
    data: colonyState
  });
});

// Update colony state
router.post('/colony', (req: Request, res: Response) => {
  const updates = req.body;
  
  // Process automation first
  processAutomation(colonyState);
  
  // Apply updates
  if (updates.resources) {
    colonyState.resources = { ...colonyState.resources, ...updates.resources };
  }
  
  if (updates.structures) {
    colonyState.structures = { ...colonyState.structures, ...updates.structures };
  }
  
  if (updates.automation) {
    colonyState.automation = { ...colonyState.automation, ...updates.automation };
  }

  if (updates.research) {
    colonyState.research = { ...colonyState.research, ...updates.research };
  }
  
  // Recalculate consciousness
  colonyState.consciousness = calculateConsciousness(colonyState);
  
  res.json({
    success: true,
    data: colonyState
  });
});

// Perform colony action
router.post('/colony/action', (req: Request, res: Response) => {
  const { action, params } = req.body;
  
  // Process automation first
  processAutomation(colonyState);
  
  let success = false;
  let message = '';
  
  switch (action) {
    case 'gather_energy':
      colonyState.resources.energy += 10;
      success = true;
      message = 'Gathered 10 energy';
      break;
      
    case 'gather_materials':
      colonyState.resources.materials += 5;
      success = true;
      message = 'Gathered 5 materials';
      break;
      
    case 'build_collector':
      if (colonyState.resources.materials >= 25) {
        colonyState.resources.materials -= 25;
        colonyState.automation.solarCollectors.count += 1;
        success = true;
        message = 'Built energy collector';
      } else {
        message = 'Not enough materials';
      }
      break;
      
    case 'build_gatherer':
      if (colonyState.resources.energy >= 50) {
        colonyState.resources.energy -= 50;
        colonyState.automation.miners.count += 1;
        success = true;
        message = 'Built material gatherer';
      } else {
        message = 'Not enough energy';
      }
      break;
      
    case 'build_lab':
      if (colonyState.resources.materials >= 100 && colonyState.resources.energy >= 100) {
        colonyState.resources.materials -= 100;
        colonyState.resources.energy -= 100;
        colonyState.automation.laboratories.count += 1;
        success = true;
        message = 'Built research lab';
      } else {
        message = 'Not enough resources';
      }
      break;
      
    case 'grow_population':
      if (colonyState.resources.energy >= 100 && colonyState.resources.food >= 50) {
        colonyState.resources.energy -= 100;
        colonyState.resources.food -= 50;
        colonyState.resources.population += 1;
        success = true;
        message = 'Population increased';
      } else {
        message = 'Not enough resources';
      }
      break;
      
    default:
      message = 'Unknown action';
  }
  
  // Recalculate consciousness
  colonyState.consciousness = calculateConsciousness(colonyState);
  
  res.json({
    success,
    message,
    data: colonyState
  });
});

// Reset colony (for testing)
router.post('/colony/reset', (req: Request, res: Response) => {
  colonyState = {
    id: 'colony-1',
    resources: {
      energy: 1000,
      materials: 500,
      population: 10,
      research: 0,
      food: 100,
      components: 0,
      tools: 0,
      medicine: 0
    },
    structures: {
      energyCollectors: 2,
      materialGatherers: 1,
      researchLabs: 0,
      greenhouses: 1,
      workshops: 0,
      medicalCenters: 0
    },
    automation: {
      solarCollectors: { level: 1, count: 2, active: true },
      windTurbines: { level: 0, count: 0, active: false },
      miners: { level: 1, count: 1, active: true },
      refineries: { level: 0, count: 0, active: false },
      workshops: { level: 0, count: 0, active: false },
      laboratories: { level: 0, count: 0, active: false },
      greenhouses: { level: 1, count: 1, active: true },
      medicalCenters: { level: 0, count: 0, active: false }
    },
    research: {
      active: null as string | null,
      progress: 0,
      completed: [] as string[],
      available: [] as string[]
    },
    consciousness: 0,
    lastUpdate: Date.now()
  };
  
  res.json({
    success: true,
    message: 'Colony reset',
    data: colonyState
  });
});

export default router;
