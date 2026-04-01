import { now } from "@shared/time";
import { bus } from "./events";
import { idleTick } from "./idle";

export function makeLoop(step:(dt:number,t:number)=>void) {
  let running=false, t0=now();
  const frame = ()=>{
    if (!running) return;
    const t = now(); const dt = Math.min(0.05, Math.max(0, t - t0));
    t0 = t;
    step(dt,t);
    bus.emit("breath:tick", {dt,t});
    requestAnimationFrame(frame);
  };
  return {
    start(){ if(!running){running=true; t0=now(); requestAnimationFrame(frame);} },
    stop(){ running=false; }
  };
}