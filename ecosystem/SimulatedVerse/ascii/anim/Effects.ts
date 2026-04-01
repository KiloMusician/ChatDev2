import { Buffer2D } from "../core/Buffer2D";

export const Effects = {
  typewriter(text:string, t:number){ 
    const n=Math.floor(t*30); 
    return text.slice(0,n); 
  },
  
  matrix(buf:Buffer2D, t:number){
    for(let x=0;x<buf.w;x++){
      const y = Math.floor((Math.sin(t*3 + x*0.5)+1)*0.5 * (buf.h-1));
      buf.set(x,y,{ch:"|",fg:"#7aa2f7"});
    }
  }
};