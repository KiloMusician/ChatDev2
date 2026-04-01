#!/usr/bin/env node

// Minimal bootstrap server to test core game mechanics
// Bypasses tsx dependency issues with pure JavaScript + basic imports

import express from 'express';
import cors from 'cors';
import { createDatabase } from './bootstrap-db.js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const app = express();
app.use(express.json());
app.use(cors());

// Dual-layer game state: simple surface + deep hackable data
let gameState = {
  playerId: 'player1',
  
  // SURFACE LAYER - Simple for casual players
  resources: {
    biomass: 0,
    ore: 0, 
    energy: 0,
    consciousness: 0,
    credits: 0
  },
  stage: 'microbe',
  buildings: {},
  
  // DEEP LAYER - Rich data for power users
  systems: {
    unlocked: {},
    research: {},
    mods: {},
    logs: [],
    diagnostics: {},
    metadata: {
      version: '1.0.0',
      seed: 42,
      playerType: 'casual' // 'casual' or 'developer'
    }
  },
  
  // POWER USER APIs
  exposed: {
    gameLoop: true,
    stateAccess: true,
    modding: true,
    debugging: false
  },
  
  lastTick: Date.now()
};

// Core incremental game math
function calculateCost(baseCost, level, multiplier = 1.15) {
  return Math.floor(baseCost * Math.pow(multiplier, level));
}

function calculateProduction(baseProduction, level) {
  return baseProduction * level;
}

// Game loop tick
function gameTick() {
  const now = Date.now();
  const deltaTime = (now - gameState.lastTick) / 1000; // seconds
  gameState.lastTick = now;
  
  // Passive resource generation based on stage
  switch(gameState.stage) {
    case 'microbe':
      gameState.resources.biomass += 0.1 * deltaTime;
      gameState.resources.consciousness += 0.01 * deltaTime;
      break;
    case 'colony':
      gameState.resources.ore += 0.2 * deltaTime;
      gameState.resources.energy += 0.15 * deltaTime;
      gameState.resources.consciousness += 0.05 * deltaTime;
      break;
    case 'city':
      gameState.resources.energy += 0.5 * deltaTime;
      gameState.resources.credits += 0.3 * deltaTime;
      gameState.resources.consciousness += 0.1 * deltaTime;
      break;
  }
  
  // Building production
  for (const [buildingType, count] of Object.entries(gameState.buildings)) {
    const production = getBuildingProduction(buildingType, count);
    for (const [resource, amount] of Object.entries(production)) {
      gameState.resources[resource] = (gameState.resources[resource] || 0) + amount * deltaTime;
    }
  }
}

function getBuildingProduction(buildingType, level) {
  const buildings = {
    'biomass_generator': { biomass: 1.0 },
    'ore_extractor': { ore: 0.8 },
    'energy_plant': { energy: 2.0 },
    'research_lab': { consciousness: 0.5 }
  };
  
  const baseProduction = buildings[buildingType] || {};
  const result = {};
  for (const [resource, amount] of Object.entries(baseProduction)) {
    result[resource] = calculateProduction(amount, level);
  }
  return result;
}

// DUAL-LAYER API ROUTES

// Surface layer - Simple game state for casual players
app.get('/api/game/state', (req, res) => {
  const casualView = {
    resources: gameState.resources,
    stage: gameState.stage,
    buildings: gameState.buildings,
    canAdvance: canAdvanceStage(),
    nextUnlock: getNextUnlock()
  };
  res.json(casualView);
});

// Deep layer - Full system access for power users
app.get('/api/dev/full-state', (req, res) => {
  res.json(gameState);
});

// Power user modding API
app.get('/api/dev/schema', (req, res) => {
  res.json({
    resources: Object.keys(gameState.resources),
    buildings: getBuildingTypes(),
    stages: ['microbe', 'colony', 'city', 'planet', 'system', 'space'],
    modding: {
      allowCustomBuildings: true,
      allowCustomResources: true,
      allowScripting: gameState.exposed.modding
    }
  });
});

// SCP-style logs and diagnostics
app.get('/api/dev/logs', (req, res) => {
  res.json({
    systemLogs: gameState.systems.logs,
    diagnostics: gameState.systems.diagnostics,
    exposedAPIs: gameState.exposed
  });
});

app.post('/api/game/action', (req, res) => {
  const { action, target, amount } = req.body;
  
  switch(action) {
    case 'advance_stage':
      const stages = ['microbe', 'colony', 'city', 'planet', 'system', 'space'];
      const currentIndex = stages.indexOf(gameState.stage);
      if (currentIndex < stages.length - 1) {
        gameState.stage = stages[currentIndex + 1];
      }
      break;
      
    case 'build':
      const buildingCosts = {
        'biomass_generator': { biomass: 10 },
        'ore_extractor': { ore: 15, energy: 5 },
        'energy_plant': { ore: 25, biomass: 10 },
        'research_lab': { energy: 20, consciousness: 5 }
      };
      
      const currentLevel = gameState.buildings[target] || 0;
      const baseCost = buildingCosts[target];
      
      if (baseCost) {
        let canAfford = true;
        const actualCosts = {};
        
        for (const [resource, cost] of Object.entries(baseCost)) {
          const scaledCost = calculateCost(cost, currentLevel);
          actualCosts[resource] = scaledCost;
          if ((gameState.resources[resource] || 0) < scaledCost) {
            canAfford = false;
            break;
          }
        }
        
        if (canAfford) {
          for (const [resource, cost] of Object.entries(actualCosts)) {
            gameState.resources[resource] -= cost;
          }
          gameState.buildings[target] = currentLevel + 1;
        }
      }
      break;
      
    case 'unlock':
      gameState.unlocked[target] = true;
      break;
  }
  
  res.json(gameState);
});

// Helper functions for dual-layer system
function canAdvanceStage() {
  const requirements = {
    microbe: { consciousness: 5 },
    colony: { biomass: 50, ore: 30 },
    city: { energy: 100, consciousness: 20 },
    planet: { credits: 200, consciousness: 50 },
    system: { energy: 500, consciousness: 100 },
    space: { consciousness: 1000 }
  };
  
  const required = requirements[gameState.stage];
  if (!required) return false;
  
  for (const [resource, amount] of Object.entries(required)) {
    if ((gameState.resources[resource] || 0) < amount) return false;
  }
  return true;
}

function getNextUnlock() {
  const unlocks = {
    microbe: 'Colony: Unlock buildings and automation',
    colony: 'City: Unlock credits and advanced research', 
    city: 'Planet: Unlock world generation and exploration',
    planet: 'System: Unlock space stations and fleet management',
    system: 'Space: Unlock galactic civilization',
    space: 'Transcendence: Beyond physical reality'
  };
  return unlocks[gameState.stage] || 'Maximum evolution achieved';
}

function getBuildingTypes() {
  return ['biomass_generator', 'ore_extractor', 'energy_plant', 'research_lab'];
}

function logSystemEvent(message, type = 'info') {
  gameState.systems.logs.push({
    timestamp: new Date().toISOString(),
    message: message,
    type: type,
    stage: gameState.stage
  });
  
  // Keep only last 100 log entries
  if (gameState.systems.logs.length > 100) {
    gameState.systems.logs = gameState.systems.logs.slice(-100);
  }
}

// Fix for ES modules - get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Static file serving for our dual interfaces
app.get('/', (req, res) => {
  res.redirect('/casual');
});

app.get('/casual', (req, res) => {
  res.sendFile(join(__dirname, 'client-casual.html'));
});

app.get('/developer', (req, res) => {
  res.sendFile(join(__dirname, 'client-developer.html'));
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    gameRunning: true,
    stage: gameState.stage,
    dualLayer: true,
    interfaces: ['casual', 'developer']
  });
});

// Start game loop
setInterval(gameTick, 100); // 10 FPS tick rate

const port = parseInt(process.env.PORT || '5000', 10);

// Add error handling for server startup
app.listen(port, '0.0.0.0', () => {
  console.log(`✅ CoreLink Foundation dual-layer server running on port ${port}`);
  console.log(`🎮 Casual interface: http://localhost:${port}/casual`);
  console.log(`👨‍💻 Developer console: http://localhost:${port}/developer`);
  console.log(`🔧 API endpoints: http://localhost:${port}/api/*`);
  console.log(`Game state: ${gameState.stage} stage`);
  console.log('Testing core incremental mechanics...');
  
  // Initialize database and start game loop
  try {
    createDatabase();
    console.log('✓ Database initialized');
  } catch (error) {
    console.error('Database initialization error:', error.message);
  }
}).on('error', (error) => {
  console.error('Server startup error:', error.message);
  console.error('Port', port, 'may be in use or blocked');
});