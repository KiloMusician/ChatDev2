import { gainXP } from "./tiers";
import { receipt } from "./receipts";

let acc=0;
export function idleTick(dt:number) {
  acc += dt;
  if (acc >= 1) { // once a second
    acc = 0;
    gainXP(1);
    receipt("idle:tick", { grant:1 });
  }
}