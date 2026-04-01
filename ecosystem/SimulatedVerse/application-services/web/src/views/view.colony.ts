import { IView } from "./application-services/web/src/views/viewManager.ts";
import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { State, addRes, unlockMechanic } from "./application-services/web/src/engine/state.ts";

export class ColonyView implements IView {
  name = "colony";
  gridW = 50; 
  gridH = 22;
  towers: {x: number; y: number; ch: string; range: number; dps: number}[] = [
    {x: 10, y: 10, ch: "♜", range: 6, dps: 0.3}
  ];
  creeps: {x: number; y: number; hp: number; ch: string}[] = [];

  enter() { 
    unlockMechanic("m021"); // Modular Base Construction
    unlockMechanic("m042"); // Tower Defense Lanes
  }
  
  exit(){}

  render(r: AsciiRenderer){
    r.clear();
    
    // Ground grid
    for(let y = 0; y < this.gridH; y++){
      for(let x = 0; x < this.gridW; x++){
        const edge = (x === 0 || y === 0 || x === this.gridW - 1 || y === this.gridH - 1);
        r.draw({x, y, ch: edge ? "▓" : "·", fg: edge ? "#364" : "#274"});
      }
    }
    
    // Towers
    for(const t of this.towers){ 
      r.draw({x: t.x, y: t.y, ch: t.ch, fg: "#ff9"}); 
    }
    
    // Spawn creeps occasionally
    if (Math.random() < 0.03) {
      this.creeps.push({
        x: this.gridW - 2, 
        y: 1 + Math.floor(Math.random() * (this.gridH - 2)), 
        hp: 3, 
        ch: "Ϟ"
      });
    }
    
    // Move creeps
    this.creeps.forEach(c => { 
      c.x -= 1; 
      if(c.x < 1) c.hp = 0; 
    });
    
    // Tower damage
    for(const t of this.towers){
      this.creeps.forEach(c => {
        const dx = c.x - t.x, dy = c.y - t.y;
        const dist = Math.hypot(dx, dy);
        if(dist <= t.range){ 
          c.hp -= t.dps; 
        }
      });
    }
    
    this.creeps = this.creeps.filter(c => c.hp > 0);
    this.creeps.forEach(c => r.draw({x: c.x, y: c.y, ch: c.ch, fg: "#f66"}));

    r.drawText(0, 0, `Colony — Build & defend. [B]uild tower, [Del] remove, arrows to pan.`);
    
    unlockMechanic("m041"); // Procedural Swarm AI
    unlockMechanic("m043"); // Modular Turret Upgrades
  }

  update(dt: number){
    addRes("ore", 0.2 * dt);
    addRes("energy", 0.15 * dt);
    addRes("consciousness", 0.05 * dt);
    
    unlockMechanic("m023"); // Idle Production Chains
    unlockMechanic("m027"); // Energy/Power Grid
  }
}