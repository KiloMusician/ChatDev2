import { EventEmitter } from "node:events";
export type Finding = { kind:string; path?:string; detail?:any; severity?:"info"|"warn"|"error" };
export type Action = { name:string; args?:any; proof?:string };
export const bus = new EventEmitter();

// CIE listens to "kick", "focus", "flush", "prove"
export const emitKick = (why:string)=> bus.emit("kick",{why});
export const onKick  = (fn:(p:any)=>void)=> bus.on("kick",fn);