import { IView } from "./application-services/web/src/views/viewManager.ts";
import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { unlockMechanic, addRes } from "./application-services/web/src/engine/state.ts";

export class SystemView implements IView {
  name = "system";
  
  enter() { 
    unlockMechanic("m077"); // ASCII Starfield/Universe Zoom
    unlockMechanic("m075"); // Vehicles/Transport Overlay
  }
  
  exit() {}
  
  render(r: AsciiRenderer) { 
    r.clear(); 
    r.drawText(2, 2, "⭐ System — Solar system management, space stations");
    r.drawText(2, 4, "Orbital mechanics and interplanetary logistics");
    r.drawText(2, 5, "Sun ☉ Planets ● Moons ◐ Asteroids ∘ Stations ⬟");
    r.drawText(2, 7, "[S] Stations [T] Trade routes [O] Orbital view");
    r.drawText(2, 8, "🚀 Space logistics: Fleet operations and supply chains");
    r.drawText(2, 9, "⚡ Energy distribution across orbital stations");
    r.drawText(2, 10, "🛸 Active ships: 12 | ⚓ Docked: 8 | 🔧 Under repair: 2");
  }
  
  update(dt: number) {
    addRes("energy", 1.0 * dt);
    addRes("consciousness", 0.2 * dt);
  }
}