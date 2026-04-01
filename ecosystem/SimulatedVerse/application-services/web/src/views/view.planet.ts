import { IView } from "./application-services/web/src/views/viewManager.ts";
import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { unlockMechanic, addRes } from "./application-services/web/src/engine/state.ts";

export class PlanetView implements IView {
  name = "planet";
  
  enter() { 
    unlockMechanic("m061"); // Worldgen (DF-style)
    unlockMechanic("m063"); // Overworld Travel
  }
  
  exit() {}
  
  render(r: AsciiRenderer) { 
    r.clear(); 
    r.drawText(2, 2, "🌍 Planet — World generation, biomes, exploration");
    r.drawText(2, 4, "Continental drift and climate simulation");
    r.drawText(2, 5, "Mountains ▲ Forests ♠ Oceans ≋ Deserts ░");
    r.drawText(2, 7, "[E] Expeditions [M] Mining [B] Biome analysis");
    r.drawText(2, 8, "[WIP] Dwarf Fortress-style worldgen coming...");
  }
  
  update(dt: number) {
    addRes("ore", 0.5 * dt);
    addRes("consciousness", 0.15 * dt);
  }
}