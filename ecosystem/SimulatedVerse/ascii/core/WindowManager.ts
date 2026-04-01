export type AsciiWindow = { 
  id:string; 
  title:string; 
  x:number; 
  y:number; 
  w:number; 
  h:number; 
  visible:boolean; 
  z:number 
};

export class WindowManager {
  windows: AsciiWindow[] = [];
  
  create(win: Omit<AsciiWindow,"z">){ 
    const z = this.windows.length+1; 
    const w = {...win, z}; 
    this.windows.push(w); 
    return w; 
  }
  
  bringToFront(id:string){ 
    const w = this.windows.find(x=>x.id===id); 
    if(!w) return; 
    w.z = Math.max(...this.windows.map(x=>x.z))+1; 
  }
  
  toggle(id:string, vis?:boolean){ 
    const w=this.windows.find(x=>x.id===id); 
    if(w) w.visible = vis??!w.visible; 
  }
}