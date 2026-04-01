import * as ROT from "rot-js";

export type DrawCell = { x:number; y:number; ch:string; fg?:string; bg?:string };

export class AsciiRenderer {
  display: ROT.Display;
  w: number; 
  h: number;
  
  constructor(w: number, h: number){
    this.w = w; 
    this.h = h;
    this.display = new ROT.Display({
      width: w, 
      height: h,
      forceSquareRatio: false,
      spacing: 1.1,
      fontSize: parseInt(getComputedStyle(document.documentElement).getPropertyValue("--tileH")) || 18,
      bg: "#0a0c10",
      fg: "#e6edf3"
    });
  }
  
  mount(el: HTMLElement){
    el.innerHTML = "";
    el.appendChild(this.display.getContainer()!);
  }
  
  clear(){ this.display.clear(); }
  
  draw(c: DrawCell){ 
    this.display.draw(c.x, c.y, c.ch, c.fg, c.bg); 
  }
  
  drawText(x: number, y: number, text: string, fg?: string, bg?: string){
    this.display.drawText(x, y, "%c{" + (fg || "#e6edf3") + "}" + text, bg);
  }
}