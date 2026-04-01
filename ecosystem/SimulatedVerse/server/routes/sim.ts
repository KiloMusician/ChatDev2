import { Router } from "express";
import { z } from "zod";
import { getStore } from "../state/store.js";

export const sim = Router();

const ActSchema = z.object({
  actor: z.string().min(1),    // "agent:alpha" | "system:autopilot" | "human:<id>"
  action: z.string().min(1),   // "tick" | "buy_building" | "start_research" | "manual_action" etc.
  payload: z.record(z.any()).optional()
});

// Extended action schema for rich game actions
const BuildingSchema = z.object({
  action: z.literal("buy_building"),
  payload: z.object({
    building: z.enum(["generators", "factories", "labs", "farms", "workshops"])
  })
});

const ResearchSchema = z.object({
  action: z.literal("start_research"), 
  payload: z.object({
    research: z.string()
  })
});

const ManualActionSchema = z.object({
  action: z.literal("manual_action"),
  payload: z.object({
    action: z.enum(["gather_energy", "scavenge_materials", "boost_research", "surgical_edit", "cascade_trigger"])
  })
});

// **OBSERVE ENDPOINT** - Get current game state with full incremental game data
sim.get("/observe", (_req, res) => {
  try {
    const snapshot = getStore().readGameSnapshot();
    const richState = snapshot.richState;
    
    res.json({ 
      ok: true, 
      // Basic state
      phase: snapshot.phase, 
      tick: snapshot.tick, 
      resources: snapshot.resources ?? {}, 
      ui: snapshot.ui ?? {},
      autopilot: snapshot.autopilot,
      seed: snapshot.seed,
      lastError: snapshot.lastError,
      
      // Rich incremental game state
      buildings: richState?.buildings || {},
      research: richState?.research || { points: 0, completed: [], active: null, progress: 0 },
      unlocks: richState?.unlocks || {},
      effects: richState?.effects || { recentGains: [], achievements: [], multipliers: {} },
      totalTicks: richState?.totalTicks || 0,
      
      // Computed metrics for agents
      metrics: {
        totalBuildings: richState ? Object.values(richState.buildings).reduce((sum, count) => sum + count, 0) : 0,
        energyPerTick: richState ? richState.buildings.generators * 10 * (richState.effects?.multipliers?.energy ?? 1) : 0,
        materialsPerTick: richState ? richState.buildings.factories * 5 * (richState.effects?.multipliers?.materials ?? 1) : 0,
        researchPerTick: richState ? richState.buildings.labs * 2 * (richState.effects?.multipliers?.research ?? 1) : 0,
        unlockedCount: richState ? Object.values(richState.unlocks).filter(Boolean).length : 0
      }
    });
  } catch (error: any) {
    console.error('[SIM] Observation failed:', error?.message || error);
    res.status(500).json({ 
      ok: false, 
      error: "State observation failed", 
      details: error?.message || String(error),
      timestamp: new Date().toISOString()
    });
  }
});

// **ACT ENDPOINT** - Apply action to game state
sim.post("/act", (req, res) => {
  const parsed = ActSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "BAD_ACT", details: parsed.error });
  }
  
  const { actor, action, payload } = parsed.data;
  
  try {
    const result = getStore().applyAction(actor, action, payload ?? {});
    res.json({ ok: true, result });
  } catch (error: any) {
    console.error('[SIM] Action failed:', error?.message || error);
    res.status(500).json({ 
      ok: false, 
      error: "Action processing failed", 
      details: error?.message || String(error),
      timestamp: new Date().toISOString()
    });
  }
});

// **REWARD ENDPOINT** - Get reward signal for RL
sim.get("/reward", (_req, res) => {
  try {
    const reward = getStore().computeReward();
    const state = getStore().readGameSnapshot();
    res.json({ 
      ok: true, 
      reward, 
      phase: state.phase,
      tick: state.tick
    });
  } catch (error: any) {
    console.error('[SIM] Reward computation failed:', error?.message || error);
    res.status(500).json({ 
      ok: false, 
      error: "Reward computation failed", 
      details: error?.message || String(error),
      timestamp: new Date().toISOString()
    });
  }
});

// **RESET ENDPOINT** - Reset game state (for training)
sim.post("/reset", (_req, res) => {
  try {
    getStore().reset();
    res.json({ ok: true, message: "Game state reset" });
  } catch (error: any) {
    console.error('[SIM] Reset failed:', error?.message || error);
    res.status(500).json({ 
      ok: false, 
      error: "Game reset failed", 
      details: error?.message || String(error),
      timestamp: new Date().toISOString()
    });
  }
});

// **HISTORY ENDPOINT** - Get state history for ML training
sim.get("/history", (_req, res) => {
  try {
    const history = getStore().getHistory();
    res.json({ ok: true, history: history.slice(-20) }); // Last 20 states only
  } catch (error: any) {
    console.error('[SIM] History retrieval failed:', error?.message || error);
    res.status(500).json({ 
      ok: false, 
      error: "History retrieval failed", 
      details: error?.message || String(error),
      timestamp: new Date().toISOString()
    });
  }
});