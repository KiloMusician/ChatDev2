import { Buffer2D } from "./Buffer2D";

export class RendererDom {
  private pre: HTMLPreElement;
  
  constructor(root: HTMLElement){
    root.classList.add("ascii-root");
    const pre = document.createElement("pre");
    pre.className = "ascii-pre";
    root.appendChild(pre);
    this.pre = pre;
  }
  
  draw(buf: Buffer2D){ 
    this.pre.textContent = buf.toString(); 
  }
}