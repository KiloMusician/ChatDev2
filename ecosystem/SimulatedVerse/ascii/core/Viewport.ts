import { Buffer2D } from "./Buffer2D";

export class Viewport {
  buffer: Buffer2D; 
  backend:"dom"|"canvas"="dom";
  
  constructor(public w:number, public h:number){ 
    this.buffer = new Buffer2D(w,h); 
  }
}