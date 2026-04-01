import type { Cell } from "./Cell";

export class Buffer2D {
  readonly w: number; 
  readonly h: number;
  private data: Cell[];
  
  constructor(w:number,h:number,fill:Cell={ch:" ",fg:"var(--ascii-fg)"}){
    this.w=w; 
    this.h=h; 
    this.data = Array(w*h).fill(fill);
  }
  
  idx(x:number,y:number){ return y*this.w + x; }
  get(x:number,y:number){ return this.data[this.idx(x,y)]; }
  set(x:number,y:number,c:Cell){ this.data[this.idx(x,y)] = c; }
  
  clear(c:Cell={ch:" ",fg:"var(--ascii-fg)"}){
    for(let i=0;i<this.data.length;i++) this.data[i]=c;
  }
  
  toString():string{
    let s=""; 
    for(let y=0;y<this.h;y++){ 
      for(let x=0;x<this.w;x++) s+=this.get(x,y).ch; 
      s+="\n"; 
    }
    return s;
  }
}