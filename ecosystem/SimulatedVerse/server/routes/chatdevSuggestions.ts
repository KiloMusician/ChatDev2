/**
 * 💡 ChatDev Suggestions - Auto-filled tasks based on game state
 * Converts "what should I run?" into context-aware, ready-to-execute tasks
 * Sources suggestions from current gameplay progression and system needs
 */

import { Router } from "express";
import fetch from "node-fetch";

const router = Router();

/**
 * GET /suggestions - Auto-generate contextual task suggestions
 * Reads live game state to propose relevant development tasks
 */
router.get("/suggestions", async (req, res) => {
  try {
    // Pull current game state to shape suggestions
    let gameState: any = {};
    const simHost = process.env.SIMULATEDVERSE_HOST || "127.0.0.1";
    const simPort = process.env.PORT || process.env.SIMULATEDVERSE_PORT || "5000";
    const baseUrl = process.env.BASE_URL || `http://${simHost}:${simPort}`;
    try {
      const response = await fetch(`${baseUrl}/api/sim/observe`);
      gameState = await response.json();
    } catch (fetchError) {
      console.warn("[SUGGESTIONS] Could not fetch game state, using defaults");
    }

    const energy = gameState?.resources?.energy ?? 0;
    const buildings = gameState?.buildings || {};
    const unlocks = gameState?.unlocks || {};
    const metrics = gameState?.metrics || {};

    const suggestions = [];

    // **CONTENT SEEDING** - Essential for early game
    if (metrics.totalBuildings < 3) {
      suggestions.push({
        pipeline: "idler_feature",
        task: {
          id: "seed-core-content",
          type: "RefactorPU", 
          title: "Seed missing tiers/generators/upgrades",
          description: "Use content-seeder agent to ensure Tier -1/0/1, starter generators, and basic upgrades exist.",
          context: { 
            energy, 
            reason: "Boot → Survival ramp",
            missing_content: true
          },
          agent: "content-seeder"
        }
      });
    }

    // **HUD ENHANCEMENT** - Show progression visually  
    if (buildings.generators >= 1) {
      suggestions.push({
        pipeline: "ascii_hud_enhance",
        task: {
          id: "hud-panels",
          type: "UXPU",
          title: "Add HUD panels (Tiers, Gens, Upgrades)",
          description: "Render tabs + panels bound to content files; show ROI/next-cost; mobile-friendly.",
          context: { 
            panels: ["Tiers", "Generators", "Upgrades"],
            generators_unlocked: true
          }
        }
      });
    }

    // **RESEARCH OPTIMIZATION** - When enough energy for research
    if (energy >= 100 && !gameState?.research?.active) {
      suggestions.push({
        pipeline: "research_enhance", 
        task: {
          id: "auto-research",
          type: "GamePU",
          title: "Auto-start efficiency research",
          description: "Begin solar efficiency research to boost energy generation.",
          context: {
            energy_threshold_met: true,
            suggested_research: "solar_efficiency"
          }
        }
      });
    }

    // **AUTOMATION UNLOCK** - When ready for next tier
    if (energy >= 200 && !unlocks.automation) {
      suggestions.push({
        pipeline: "progression_unlock",
        task: {
          id: "unlock-automation",
          type: "GamePU", 
          title: "Unlock automation tier",
          description: "Enable automated building construction and resource management.",
          context: {
            unlock_ready: "automation",
            energy_surplus: energy - 200
          }
        }
      });
    }

    // **LORE EXPANSION** - Add narrative depth
    if (metrics.totalBuildings >= 2) {
      suggestions.push({
        pipeline: "lore_pack",
        task: {
          id: "tier1-lore",
          type: "LorePU",
          title: "Survival Protocols: Lore Beacons", 
          description: "Inject 3 lore beacons unlocked by Tier 1 milestones.",
          context: { 
            unlock: "tier_1",
            buildings_established: true
          }
        }
      });
    }

    // **PERFORMANCE OPTIMIZATION** - When system is stable
    if (energy >= 150 && metrics.totalBuildings >= 3) {
      suggestions.push({
        pipeline: "performance_tune",
        task: {
          id: "optimize-tick-performance", 
          type: "PerfPU",
          title: "Optimize game tick performance",
          description: "Profile and enhance tick loop efficiency for smoother gameplay.",
          context: {
            stable_system: true,
            tick_optimization_ready: true
          }
        }
      });
    }

    res.json({ 
      ok: true, 
      suggestions,
      count: suggestions.length,
      context: {
        energy,
        buildings: Object.keys(buildings).length,
        unlocks_available: Object.values(unlocks).filter(Boolean).length,
        game_phase: energy < 50 ? "survival" : energy < 200 ? "growth" : "expansion"
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    res.status(500).json({
      ok: false,
      error: error instanceof Error ? error.message : "Suggestions generation failed",
      timestamp: new Date().toISOString()
    });
  }
});

export default router;
