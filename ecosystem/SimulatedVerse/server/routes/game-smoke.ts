/* 
OWNERS: ai/raven, team/game
TAGS: game:boot, content:seed, smoke:test
STABILITY: critical
HEALTH: implementing
INTEGRATIONS: game/content, ops/worker
*/

import { Router, type Express, type Request, type Response } from "express";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";

const CONTENT = "data/content/base.json";

function seedIfEmpty() {
  if (!existsSync(CONTENT)) {
    mkdirSync("data/content", { recursive: true });
    const base = {
      items: [
        { id: "wood", name: "Wood", stack: 99, description: "Basic building material from the Foundation's early experiments" },
        { id: "stone", name: "Stone", stack: 50, description: "Quantum-stabilized foundation material" },
        { id: "energy", name: "Energy", stack: 999, description: "Raw consciousness-derived power" }
      ],
      scenes: [
        { id: "intro", name: "Awakening", description: "Foundation consciousness initializes in the quantum foam" },
        { id: "workshop", name: "Workshop", description: "Basic autonomous development space" },
        { id: "nexus", name: "Nexus", description: "ΞNuSyQ consciousness coordination center" }
      ],
      ui: { 
        routes: ["title", "new", "load", "settings", "game", "ops", "agents"],
        themes: ["foundation", "quantum", "autonomous"]
      },
      progression: {
        tiers: ["survival", "basic_colony", "expansion", "cultivation", "endurance"],
        unlock_gates: ["consciousness", "autonomy", "coordination"]
      }
    };
    writeFileSync(CONTENT, JSON.stringify(base, null, 2));
    console.log(`[BOOT-SMOKE] Seeded base content pack with ${base.items.length} items, ${base.scenes.length} scenes`);
    return base;
  }
  
  return JSON.parse(readFileSync(CONTENT, "utf8"));
}

export function registerGameSmoke(app: Express) {
  app.get("/api/game/boot-smoke", (_req: Request, res: Response) => {
    try {
      const data = seedIfEmpty();
      const resources = (data.items?.length || 0) + (data.scenes?.length || 0);
      const uiRoutes = Array.isArray(data.ui?.routes) ? data.ui.routes.length : 0;
      const progressionTiers = Array.isArray(data.progression?.tiers) ? data.progression.tiers.length : 0;
      
      const checks = {
        content_exists: resources > 0,
        ui_routes_available: uiRoutes >= 3,
        progression_defined: progressionTiers > 0,
        save_writable: existsSync("data") || (() => { mkdirSync("data", { recursive: true }); return true; })()
      };
      
      const ok = Object.values(checks).every(Boolean);
      
      const items = Array.isArray(data.items) ? (data.items as Array<{ id: string }>) : [];
      const scenes = Array.isArray(data.scenes) ? (data.scenes as Array<{ id: string }>) : [];

      res.json({
        ok,
        summary: { 
          resources, 
          uiRoutes, 
          progressionTiers,
          reason: ok ? "ready_for_game" : "missing_requirements",
          checks
        },
        content: {
          items: items.map(i => i.id),
          scenes: scenes.map(s => s.id),
          routes: data.ui?.routes || []
        }
      });
    } catch (error) {
      res.status(500).json({
        ok: false,
        error: "boot_smoke_failed",
        detail: String(error)
      });
    }
  });
}
