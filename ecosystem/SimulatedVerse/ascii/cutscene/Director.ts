import { Buffer2D } from "../core/Buffer2D";

export type Cue = { 
  t:number; 
  text?:string; 
  fx?:(buf:Buffer2D,localT:number)=>void; 
};

export class Director {
  private t=0; 
  private i=0; 
  private active=false;
  
  constructor(private cues:Cue[], private onDone?:()=>void){}
  
  start(){ 
    this.t=0; 
    this.i=0; 
    this.active=true; 
  }
  
  update(dt:number){ 
    if(!this.active) return; 
    this.t += dt; 
  }
  
  draw(buf:Buffer2D){
    if(!this.active) return;
    const cue = this.cues[this.i]; 
    if(!cue) { 
      this.active=false; 
      this.onDone?.(); 
      return; 
    }
    if(this.t>=cue.t){ 
      if(cue.text){ 
        for(let i=0;i<cue.text.length && i<buf.w;i++) 
          buf.set(i,1,{ch:cue.text[i],fg:"#a9b1d6"}); 
      }
      cue.fx?.(buf, this.t-cue.t); 
      this.i++; 
    }
  }
}