import { Viewport } from "../core/Viewport";
import { RendererDom } from "../core/RendererDom";
import { RendererCanvas } from "../core/RendererCanvas";
import { Buffer2D } from "../core/Buffer2D";
import { Ticker } from "../anim/Ticker";
import { bus } from "../core/Bus";

export class AsciiView extends HTMLElement{
  static get observedAttributes(){ return ["width","height","backend","scale"]; }
  
  root: ShadowRoot; 
  viewport!: Viewport; 
  backend:"dom"|"canvas"="dom";
  dom!: RendererDom; 
  canvas!: RendererCanvas; 
  ticker!: Ticker;
  
  constructor(){
    super();
    this.root = this.attachShadow({mode:"open"});
    const style = document.createElement("link"); 
    style.rel="stylesheet"; 
    style.href="/styles/ascii.css";
    this.root.appendChild(style);
    const host = document.createElement("div"); 
    host.className="ascii-root"; 
    this.root.appendChild(host);
    this.dom = new RendererDom(host);
    this.canvas = new RendererCanvas(host);
    this.backend = (this.getAttribute("backend") as any) || "dom";
    this.ticker = new Ticker(dt=>this.onFrame(dt));
  }
  
  connectedCallback(){
    const w = parseInt(this.getAttribute("width")||"80",10);
    const h = parseInt(this.getAttribute("height")||"25",10);
    this.viewport = new Viewport(w,h);
    this.ticker.start();
    bus.on("ascii/toggleBackend", ()=>{ 
      this.backend = this.backend==="dom"?"canvas":"dom"; 
    });
  }
  
  disconnectedCallback(){ 
    this.ticker.stop(); 
  }
  
  attributeChangedCallback(){ 
    /* could resize here */ 
  }
  
  onFrame(dt:number){
    const buf = this.viewport.buffer; 
    buf.clear();
    // demo splash
    const msg = "ΞNuSyQ — ASCII SYSTEM ONLINE";
    for(let i=0;i<msg.length && i<buf.w;i++) 
      buf.set(i,0,{ch:msg[i],fg:"#7aa2f7"});
    // simple heartbeat dot
    const x = Math.floor((performance.now()/100)% (buf.w-2))+1;
    buf.set(x,2,{ch:"●",fg:"#e0af68"});
    // draw with selected backend
    (this.backend==="dom" ? this.dom : this.canvas).draw(buf);
  }
}

customElements.define("ascii-view", AsciiView);