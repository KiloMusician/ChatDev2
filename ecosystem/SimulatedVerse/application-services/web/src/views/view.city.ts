import { IView } from "./application-services/web/src/views/viewManager.ts";
import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { unlockMechanic, addRes } from "./application-services/web/src/engine/state.ts";

export class CityView implements IView {
  name = "city";
  
  enter() { 
    unlockMechanic("m024"); // SimCity Zoning
    unlockMechanic("m030"); // Population Growth
  }
  
  exit() {}
  
  render(r: AsciiRenderer) { 
    r.clear(); 
    r.drawText(2, 2, "🏙 City — Zoning, traffic, services");
    r.drawText(2, 4, "Population management and urban planning");
    r.drawText(2, 5, "Residential ■ Industrial ▦ Commercial ▣");
    r.drawText(2, 7, "[R] Residential [I] Industrial [C] Commercial");
    r.drawText(2, 8, "[WIP] Full city simulation coming soon...");
  }
  
  update(dt: number) {
    addRes("credits", 0.3 * dt);
    addRes("consciousness", 0.1 * dt);
  }
}