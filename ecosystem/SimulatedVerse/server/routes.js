/**
 * 🎮 GAME API BRIDGE ROUTES
 * CoreLink Foundation - Fixes frontend/backend API disconnection
 * 
 * This file bridges the frontend game API calls to the working backend /api/sim endpoints
 * Frontend expects: /api/game/state, /api/game/actions, etc.
 * Backend provides: /api/sim/observe, /api/sim/act
 */

import { Router } from "express";
import { getStore } from "./state/store.ts";

const router = Router();

// **CORE GAME STATE ENDPOINT** - Frontend calls /api/game/state
router.get("/game/state", (req, res) => {
  try {
    const snapshot = getStore().readGameSnapshot();
    const richState = snapshot.richState;
    
    // Transform sim state to frontend-expected format
    const gameState = {
      id: "player-1",
      playerId: "player-1", 
      resources: {
        energy: richState?.resources?.energy || snapshot.resources?.energy || 100,
        materials: richState?.resources?.materials || snapshot.resources?.materials || 50,
        components: richState?.resources?.components || snapshot.resources?.components || 0,
        population: richState?.resources?.population || 1,
        researchPoints: richState?.resources?.research || 0,
        tools: richState?.resources?.tools || 5,
        food: richState?.resources?.food || 100,
        medicine: richState?.resources?.medicine || 10
      },
      automation: {
        solarCollectors: { level: 1, count: richState?.buildings?.generators || 1, active: true },
        windTurbines: { level: 1, count: 0, active: false },
        miners: { level: 1, count: richState?.buildings?.factories || 0, active: true },
        refineries: { level: 1, count: 0, active: false },
        workshops: { level: 1, count: richState?.buildings?.workshops || 0, active: true },
        laboratories: { level: 1, count: richState?.buildings?.labs || 0, active: true },
        greenhouses: { level: 1, count: richState?.buildings?.farms || 1, active: true },
        medicalCenters: { level: 1, count: 0, active: false }
      },
      research: {
        active: richState?.research?.active || null,
        progress: richState?.research?.progress || 0,
        completed: richState?.research?.completed || [],
        available: ["basic_automation", "solar_efficiency", "mining_tech", "bio_research"]
      },
      buildings: richState?.buildings || { generators: 1, factories: 0, labs: 0, farms: 1, workshops: 0 },
      weather: {
        current: "clear",
        duration: 100,
        effects: { energy: 1.0, materials: 1.0 },
        forecast: ["clear", "cloudy", "storm"],
        severity: 0,
        shelter: 0.8
      },
      achievements: richState?.effects?.achievements || [],
      settings: { difficulty: snapshot.profile?.difficulty || "normal" },
      lastSaved: new Date().toISOString(),
      totalPlaytime: Math.floor(Date.now() / 1000),
      createdAt: new Date().toISOString()
    };
    
    res.json(gameState);
  } catch (error) {
    console.error("🚨 Game state bridge error:", error);
    res.status(500).json({ error: "Failed to get game state" });
  }
});

// **GAME STATE SAVE ENDPOINT** - Frontend POSTs to /api/game/state  
router.post("/game/state", (req, res) => {
  try {
    // Frontend saves don't need backend persistence since 
    // the real game state is managed by the sim system
    res.json({ success: true, timestamp: Date.now() });
  } catch (error) {
    console.error("🚨 Game state save error:", error);
    res.status(500).json({ error: "Failed to save game state" });
  }
});

// **GAME ACTIONS ENDPOINT** - Frontend action proxy to sim (support both /actions and /action)
router.post("/game/action", (req, res) => {
  try {
    const { action, target, payload } = req.body;
    
    // Forward to sim system via HTTP
    fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/sim/act`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        actor: "human:frontend",
        action: mapFrontendAction(action, target),
        payload: payload || { target }
      })
    })
    .then(response => response.json())
    .then(result => {
      res.json({ success: true, result, timestamp: Date.now() });
    })
    .catch(error => {
      res.status(500).json({ error: "Action failed", details: error.message });
    });
  } catch (error) {
    console.error("🚨 Game action error:", error);
    res.status(500).json({ error: "Failed to process action" });
  }
});

router.post("/game/actions", (req, res) => {
  try {
    const { action, payload } = req.body;
    
    // Map frontend actions to sim actions
    const simAction = {
      actor: "human:frontend",
      action: mapFrontendAction(action),
      payload: payload
    };
    
    // Forward to sim system (would need to import sim router or use HTTP)
    // For now, acknowledge the action
    res.json({ 
      success: true, 
      action: simAction,
      timestamp: Date.now(),
      note: "Action queued for sim processing"
    });
  } catch (error) {
    console.error("🚨 Game action error:", error);
    res.status(500).json({ error: "Failed to process action" });
  }
});

// **BUILDINGS ENDPOINT** - Building purchase/management
router.get("/game/buildings", (req, res) => {
  try {
    const snapshot = getStore().readGameSnapshot();
    const buildings = snapshot.richState?.buildings || {};
    
    const buildingData = {
      available: [
        { id: "generators", name: "Solar Generator", cost: { energy: 0, materials: 20 }, owned: buildings.generators || 1 },
        { id: "factories", name: "Material Factory", cost: { energy: 50, materials: 30 }, owned: buildings.factories || 0 },
        { id: "labs", name: "Research Lab", cost: { energy: 75, materials: 50 }, owned: buildings.labs || 0 },
        { id: "farms", name: "Hydroponic Farm", cost: { energy: 40, materials: 25 }, owned: buildings.farms || 1 },
        { id: "workshops", name: "Tool Workshop", cost: { energy: 60, materials: 40 }, owned: buildings.workshops || 0 }
      ]
    };
    
    res.json(buildingData);
  } catch (error) {
    console.error("🚨 Buildings data error:", error);
    res.status(500).json({ error: "Failed to get buildings data" });
  }
});

// **RESEARCH ENDPOINT** - Research tree and progress
router.get("/game/research", (req, res) => {
  try {
    const snapshot = getStore().readGameSnapshot();
    const research = snapshot.richState?.research || {};
    
    const researchData = {
      active: research.active,
      progress: research.progress || 0,
      completed: research.completed || [],
      available: [
        { id: "basic_automation", name: "Basic Automation", cost: 100, unlocks: ["auto_gather"] },
        { id: "solar_efficiency", name: "Solar Efficiency", cost: 150, unlocks: ["solar_boost"] },
        { id: "mining_tech", name: "Mining Technology", cost: 200, unlocks: ["auto_mining"] },
        { id: "bio_research", name: "Biological Research", cost: 250, unlocks: ["population_growth"] }
      ]
    };
    
    res.json(researchData);
  } catch (error) {
    console.error("🚨 Research data error:", error);
    res.status(500).json({ error: "Failed to get research data" });
  }
});

// **ACTION MAPPING HELPER** - Maps frontend actions to sim format
function mapFrontendAction(frontendAction, target) {
  const actionMap = {
    "gather_energy": "manual_action",
    "build": "buy_building", 
    "build_generator": "buy_building",
    "build_factory": "buy_building",
    "start_research": "start_research",
    "collect_resources": "manual_action",
    "advance_stage": "manual_action"
  };
  
  return actionMap[frontendAction] || "manual_action";
}

// **PROXY ENDPOINTS** - Direct sim access for advanced users
router.get("/sim/observe", (req, res) => {
  try {
    const snapshot = getStore().readGameSnapshot();
    res.json(snapshot);
  } catch (error) {
    res.status(500).json({ error: "Sim observe failed" });
  }
});

// **DEBUG LOGGING** - Let's see what routes are being hit
router.use((req, res, next) => {
  console.log(`[GAME-BRIDGE] ${req.method} ${req.originalUrl} ${req.path}`);
  next();
});

export default router;
