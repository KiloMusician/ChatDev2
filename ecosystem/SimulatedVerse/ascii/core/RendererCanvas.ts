import { Buffer2D } from "./Buffer2D";

export class RendererCanvas {
  private canvas: HTMLCanvasElement; 
  private ctx: CanvasRenderingContext2D;
  private chW=8; 
  private chH=12;
  
  constructor(root: HTMLElement){
    root.classList.add("ascii-root");
    this.canvas = document.createElement("canvas");
    this.canvas.style.imageRendering = "pixelated";
    root.appendChild(this.canvas);
    const ctx = this.canvas.getContext("2d");
    if(!ctx) throw new Error("Canvas 2D unavailable");
    this.ctx = ctx;
    this.ctx.font = "12px var(--ascii-font)";
  }
  
  draw(buf: Buffer2D){
    this.canvas.width = buf.w * this.chW; 
    this.canvas.height = buf.h * this.chH;
    this.ctx.fillStyle = getComputedStyle(this.canvas).getPropertyValue("--ascii-bg") || "#000";
    this.ctx.fillRect(0,0,this.canvas.width,this.canvas.height);
    const fg = getComputedStyle(this.canvas).getPropertyValue("--ascii-fg") || "#fff";
    this.ctx.fillStyle = fg;
    this.ctx.font = "12px var(--ascii-font)";
    for(let y=0;y<buf.h;y++){
      for(let x=0;x<buf.w;x++){
        const { ch } = (buf as any).get(x,y);
        this.ctx.fillText(ch, x*this.chW, (y+1)*this.chH-2);
      }
    }
  }
}