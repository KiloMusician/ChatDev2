import { Express } from "express";
import { nanoid } from "nanoid";

interface ColonyState {
  id: string;
  created: number;
  lastTick: number;
  resources: {
    energy: number;
    materials: number;
    population: number;
    research: number;
    components: number;
  };
  structures: Array<{
    id: string;
    type: string;
    level: number;
    position: { x: number; y: number };
    health: number;
    production?: Record<string, number>;
  }>;
  tier: number;
  achievements: string[];
  consciousness: number;
  settings: {
    autoTick: boolean;
    tickRate: number; // ms
  };
}

// Global colony state (in production, this would be database-backed)
let colonyState: ColonyState = {
  id: nanoid(),
  created: Date.now(),
  lastTick: Date.now(),
  resources: {
    energy: 100,
    materials: 50,
    population: 1,
    research: 0,
    components: 0,
  },
  structures: [],
  tier: 1,
  achievements: [],
  consciousness: 1.01, // Initial: (100/10000 + 1/100 + 0/10) = 0.01 + 0.01 + 0 = 0.02
  settings: {
    autoTick: true,
    tickRate: 1000, // 1 second
  }
};

// Tick processing
function processColonyTick() {
  const now = Date.now();
  const deltaMs = now - colonyState.lastTick;
  const deltaSeconds = deltaMs / 1000;
  
  // Base resource generation
  const baseRates = {
    energy: 1.0,
    materials: 0.5,
    research: 0.1,
    components: 0.0,
    population: 0.0,
  };
  
  // Apply structure bonuses
  let structureBonuses = { energy: 0, materials: 0, research: 0, components: 0, population: 0 };
  
  for (const structure of colonyState.structures) {
    if (structure.health > 0 && structure.production) {
      for (const [resource, rate] of Object.entries(structure.production)) {
        if (resource in structureBonuses) {
          structureBonuses[resource as keyof typeof structureBonuses] += rate * structure.level;
        }
      }
    }
  }
  
  // Apply tick
  for (const [resource, baseRate] of Object.entries(baseRates)) {
    if (resource in colonyState.resources) {
      const totalRate = baseRate + (structureBonuses[resource as keyof typeof structureBonuses] || 0);
      const gain = totalRate * deltaSeconds;
      colonyState.resources[resource as keyof typeof colonyState.resources] += gain;
    }
  }
  
  // Tier progression check
  if (colonyState.tier === 1 && colonyState.resources.research >= 100) {
    colonyState.tier = 2;
    colonyState.achievements.push("tier_2_unlocked");
  }
  
  // Calculate consciousness level: (energy/10000 + population/100 + research/10)
  colonyState.consciousness = Math.round((
    colonyState.resources.energy / 10000 + 
    colonyState.resources.population / 100 + 
    colonyState.resources.research / 10
  ) * 1000) / 1000;
  
  colonyState.lastTick = now;
  
  return {
    processed: true,
    deltaMs,
    gains: structureBonuses,
    newTier: colonyState.tier,
  };
}

// Auto-tick timer
let tickInterval: NodeJS.Timeout | null = null;

function startAutoTick() {
  if (tickInterval) return;
  
  tickInterval = setInterval(() => {
    if (colonyState.settings.autoTick) {
      processColonyTick();
    }
  }, colonyState.settings.tickRate);
}

function stopAutoTick() {
  if (tickInterval) {
    clearInterval(tickInterval);
    tickInterval = null;
  }
}

export function bootstrapGameAPI(app: Express) {
  console.log("[GAME_API_BOOTSTRAP] Initializing colony interface...");
  
  // Start auto-tick
  startAutoTick();
  
  // Get current colony state
  app.get("/api/colony", (req, res) => {
    res.json({
      success: true,
      data: colonyState,
      timestamp: Date.now(),
    });
  });
  
  // Get resources only (lightweight)
  app.get("/api/resources", (req, res) => {
    res.json({
      success: true,
      data: {
        resources: colonyState.resources,
        tier: colonyState.tier,
        structures: colonyState.structures.length,
        lastTick: colonyState.lastTick,
      },
      timestamp: Date.now(),
    });
  });
  
  // Perform colony actions
  app.post("/api/action/:action", (req, res) => {
    const action = req.params.action;
    const { payload } = req.body || {};
    
    let result: any = { success: false, error: "Unknown action" };
    
    switch (action) {
      case "scout":
        if (colonyState.resources.energy >= 10) {
          colonyState.resources.energy -= 10;
          const materialsGain = 10 + Math.floor(Math.random() * 10);
          colonyState.resources.materials += materialsGain;
          result = {
            success: true,
            action: "scout",
            cost: { energy: 10 },
            gains: { materials: materialsGain },
            message: `Scouting complete. Found ${materialsGain} materials.`,
          };
        } else {
          result = { success: false, error: "Insufficient energy" };
        }
        break;
        
      case "build_outpost":
        if (colonyState.resources.energy >= 50 && colonyState.resources.materials >= 25) {
          colonyState.resources.energy -= 50;
          colonyState.resources.materials -= 25;
          colonyState.resources.population += 1;
          
          const outpost = {
            id: nanoid(),
            type: "outpost",
            level: 1,
            position: { x: 0, y: 0 },
            health: 100,
            production: { population: 0.1 },
          };
          colonyState.structures.push(outpost);
          
          result = {
            success: true,
            action: "build_outpost",
            cost: { energy: 50, materials: 25 },
            gains: { population: 1 },
            structure: outpost,
            message: "Outpost constructed. Population capacity increased.",
          };
        } else {
          result = { success: false, error: "Insufficient resources" };
        }
        break;
        
      case "research":
        if (colonyState.resources.energy >= 20) {
          colonyState.resources.energy -= 20;
          const researchGain = 10 + Math.floor(Math.random() * 5);
          colonyState.resources.research += researchGain;
          result = {
            success: true,
            action: "research",
            cost: { energy: 20 },
            gains: { research: researchGain },
            message: `Research conducted. Gained ${researchGain} research points.`,
          };
        } else {
          result = { success: false, error: "Insufficient energy" };
        }
        break;
        
      case "automate":
        if (colonyState.resources.energy >= 100 && colonyState.resources.research >= 25) {
          colonyState.resources.energy -= 100;
          colonyState.resources.research -= 25;
          
          const automator = {
            id: nanoid(),
            type: "automator",
            level: 1,
            position: { x: 1, y: 0 },
            health: 75,
            production: { energy: 0.5, materials: 0.2 },
          };
          colonyState.structures.push(automator);
          
          result = {
            success: true,
            action: "automate",
            cost: { energy: 100, research: 25 },
            structure: automator,
            message: "Automation system installed. Resource generation improved.",
          };
        } else {
          result = { success: false, error: "Insufficient resources" };
        }
        break;
        
      case "tick":
        result = {
          success: true,
          action: "manual_tick",
          ...processColonyTick(),
          message: "Manual tick processed.",
        };
        break;
        
      default:
        result = { success: false, error: `Unknown action: ${action}` };
    }
    
    res.json({
      ...result,
      colony: {
        resources: colonyState.resources,
        tier: colonyState.tier,
        structures: colonyState.structures.length,
      },
      timestamp: Date.now(),
    });
  });
  
  // Update colony settings
  app.put("/api/colony/settings", (req, res) => {
    const { autoTick, tickRate } = req.body;
    
    if (typeof autoTick === "boolean") {
      colonyState.settings.autoTick = autoTick;
    }
    
    if (typeof tickRate === "number" && tickRate >= 100 && tickRate <= 10000) {
      colonyState.settings.tickRate = tickRate;
      if (tickInterval) {
        stopAutoTick();
        startAutoTick();
      }
    }
    
    res.json({
      success: true,
      settings: colonyState.settings,
      message: "Settings updated",
      timestamp: Date.now(),
    });
  });
  
  // Reset colony (for testing)
  app.post("/api/colony/reset", (req, res) => {
    colonyState = {
      id: nanoid(),
      created: Date.now(),
      lastTick: Date.now(),
      resources: { energy: 100, materials: 50, population: 1, research: 0, components: 0 },
      structures: [],
      tier: 1,
      achievements: [],
      consciousness: 0.02, // Initial: (100/10000 + 1/100 + 0/10)
      settings: { autoTick: true, tickRate: 1000 },
    };
    
    res.json({
      success: true,
      message: "Colony reset to initial state",
      colony: colonyState,
      timestamp: Date.now(),
    });
  });
  
  console.log(`[GAME_API_BOOTSTRAP] Colony interface ready:
    GET  /api/colony - Full colony state
    GET  /api/resources - Resources and basic info  
    POST /api/action/:action - Perform actions (scout, build_outpost, research, automate, tick)
    PUT  /api/colony/settings - Update settings
    POST /api/colony/reset - Reset colony
    Auto-tick: ${colonyState.settings.autoTick ? 'enabled' : 'disabled'}
    Tick rate: ${colonyState.settings.tickRate}ms`);
}

export function generateGameAPIReceipt() {
  return {
    timestamp: Date.now(),
    operation: "game_api_bootstrap",
    colony_id: colonyState.id,
    api_endpoints: [
      "/api/colony",
      "/api/resources", 
      "/api/action/:action",
      "/api/colony/settings",
      "/api/colony/reset"
    ],
    auto_tick: colonyState.settings.autoTick,
    tick_rate: colonyState.settings.tickRate,
    initial_resources: colonyState.resources,
    status: "operational"
  };
}