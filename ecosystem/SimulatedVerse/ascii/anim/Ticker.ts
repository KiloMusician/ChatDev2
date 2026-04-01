export class Ticker {
  private last=0; 
  private raf=0; 
  private running=false;
  
  constructor(private cb:(dt:number)=>void){}
  
  start(){ 
    if(this.running) return; 
    this.running=true; 
    this.last=performance.now(); 
    this.loop(); 
  }
  
  stop(){ 
    this.running=false; 
    cancelAnimationFrame(this.raf); 
  }
  
  private loop=()=>{ 
    this.raf=requestAnimationFrame(now=>{ 
      const dt=(now-this.last)/1000; 
      this.last=now; 
      this.cb(dt); 
      if(this.running) this.loop(); 
    }); 
  }
}