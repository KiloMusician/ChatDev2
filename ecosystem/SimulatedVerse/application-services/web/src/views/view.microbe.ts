import { IView } from "./application-services/web/src/views/viewManager.ts";
import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import * as ROT from "rot-js";
import { State, addRes, unlockMechanic } from "./application-services/web/src/engine/state.ts";

export class MicrobeView implements IView {
  name = "microbe";
  map: string[] = []; 
  w = 80; 
  h = 28; 
  player = {x: 3, y: 3, ch: "@"};
  fov: ROT.FOV.PreciseShadowcasting;
  seen = new Set<string>();

  constructor(){
    ROT.RNG.setSeed(State.seed);
    this.fov = new ROT.FOV.PreciseShadowcasting((x, y) => this.passable(x, y));
  }
  
  enter(){ 
    this.genMap(); 
    unlockMechanic("m001"); // Procedural ASCII Rendering
  }
  
  exit(){}

  key(dx: number, dy: number){
    const nx = this.player.x + dx, ny = this.player.y + dy;
    if(this.passable(nx, ny)){ 
      this.player.x = nx; 
      this.player.y = ny; 
      addRes("biomass", 0.1);
      addRes("consciousness", 0.01);
    }
  }
  
  passable(x: number, y: number){ 
    const t = this.tile(x, y); 
    return t && t !== "#"; 
  }
  
  tile(x: number, y: number){ 
    if(x < 0 || y < 0 || x >= this.w || y >= this.h) return "#"; 
    return this.map[y][x]; 
  }

  genMap(){
    const digger = new ROT.Map.Digger(this.w, this.h, {dugPercentage: 0.35});
    const cells: string[] = Array.from({length: this.h}, () => Array(this.w).fill("#").join(""));
    const grid = cells.map(r => r.split(""));
    digger.create((x, y, wall) => {
      grid[y][x] = wall ? "#" : ".";
    });
    this.map = grid.map(r => r.join(""));
    unlockMechanic("m018"); // Procedural Dungeon Generation
  }

  render(r: AsciiRenderer){
    r.clear();
    const vis = new Set<string>();
    this.fov.compute(this.player.x, this.player.y, 8, (x, y, _d, v) => {
      const k = `${x},${y}`; 
      vis.add(k); 
      this.seen.add(k);
    });
    
    for(let y = 0; y < this.h; y++){
      for(let x = 0; x < this.w; x++){
        const k = `${x},${y}`;
        const ch = (x === this.player.x && y === this.player.y) ? this.player.ch : this.tile(x, y);
        const seen = this.seen.has(k), visible = vis.has(k);
        if(!seen) continue;
        let fg = visible ? "#b0f" : "#445";
        let bg = visible ? "#0a0c10" : "#090a0f";
        r.draw({x, y, ch, fg, bg});
      }
    }
    
    r.drawText(0, 0, `Microbe — Explore & gather biomass. Arrows/WASD to move. [Space] pause, [Tab] next stage`);
    unlockMechanic("m003"); // Fog-of-War Cones
  }

  update(dt: number){
    if (State.t % 10 === 0) {
      addRes("biomass", 0.5 * dt);
      addRes("consciousness", 0.02 * dt);
    }
    unlockMechanic("m008"); // Idle Harvesting Loop
  }
}