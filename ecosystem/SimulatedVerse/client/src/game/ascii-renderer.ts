import * as ROT from "rot-js";
import { world } from "./ecs";

export class AsciiRenderer {
  private display: ROT.Display;
  constructor(private mount: HTMLElement, private w=60, private h=24) {
    this.display = new ROT.Display({ width: w, height: h, fontSize: 14 });
    mount.innerHTML = "";
    const container = this.display.getContainer();
    if (container) {
      mount.appendChild(container);
    }
  }
  draw() {
    this.display.clear();
    // draw resources
    for (const [e,res] of world.res) {
      const p = world.pos.get(e);
      if (!p) continue;
      const glyph = res.kind?.charAt(0).toUpperCase() ?? '?';
      this.display.draw(p.x, p.y, glyph, "#8ff", "#072");
    }
    // draw actors on top
    for (const [e,act] of world.act) {
      const p = world.pos.get(e);
      if (!p) continue;
      const glyph = act.glyph ?? '?';
      this.display.draw(p.x, p.y, glyph, "#fff", "#000");
    }
  }
}
