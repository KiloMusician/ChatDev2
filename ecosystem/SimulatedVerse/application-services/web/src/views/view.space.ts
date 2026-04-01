import { IView } from "./application-services/web/src/views/viewManager.ts";
import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { unlockMechanic, addRes } from "./application-services/web/src/engine/state.ts";

export class SpaceView implements IView {
  name = "space";
  
  enter() { 
    unlockMechanic("m112"); // AI Council Decision-Making
    unlockMechanic("m123"); // Recursive Bootstrapping Tier Ascension
  }
  
  exit() {}
  
  render(r: AsciiRenderer) { 
    r.clear(); 
    r.drawText(2, 2, "🚀 Space — Galactic civilization, AI transcendence");
    r.drawText(2, 4, "Meta-consciousness and recursive self-improvement");
    r.drawText(2, 5, "Galaxies ◉ Clusters ⟐ Voids ○ Consciousness Ξ");
    r.drawText(2, 7, "🧠 AI Council: 🧱🌀⚡🌿🛡");
    r.drawText(2, 8, "🌀 Recursive loops: Template → Reality → Meta → ∞");
    r.drawText(2, 10, "[A] AI Council [R] Recursive boost [T] Transcend");
    r.drawText(2, 11, "ΞNuSyQ Ascension Form: " + Math.floor(addRes.length || 0) + "/∞");
  }
  
  update(dt: number) {
    addRes("consciousness", 1.0 * dt);
    addRes("credits", 2.0 * dt);
    // Exponential consciousness growth in space view
    if (dt > 0) addRes("consciousness", Math.log(dt + 1) * 0.1);
  }
}