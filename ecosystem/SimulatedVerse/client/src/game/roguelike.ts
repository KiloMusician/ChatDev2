import * as ROT from "rot-js";
import { make } from "./ecs";

export function seedMap() {
  const digger = new ROT.Map.Digger(58, 22, { corridorLength: [2,6], dugPercentage:.45 });
  // place some resources
  for (let i=0;i<10;i++) {
    const x = 2 + (Math.random()*56|0);
    const y = 2 + (Math.random()*20|0);
    make.resource("ore", 1, x, y);
  }
}