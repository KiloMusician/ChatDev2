import { State } from "./application-services/web/src/engine/state.ts";

export type CascadePlan = { 
  title: string; 
  steps: string[]; 
  estGain: number; 
  mechanics: string[];
};

const library: CascadePlan[] = [
  { 
    title: "Consolidate duplicates", 
    steps: ["scan", "group-by-similarity", "surgical-rename", "path-fix", "lint"], 
    estGain: 0.9,
    mechanics: ["m106", "m118"] // ChatDev Debug, Auto-Debug Logger
  },
  { 
    title: "Idle tune", 
    steps: ["profile idle loops", "adjust timers", "persist save", "offline calc"], 
    estGain: 0.8,
    mechanics: ["m008", "m032"] // Idle Harvesting, Offline Progression
  },
  { 
    title: "Mobile UI polish", 
    steps: ["safe area", "font scale", "touch dpad", "nav collapse"], 
    estGain: 0.7,
    mechanics: ["m016", "m039"] // ASCII HUD, Minimap Navigator
  },
  { 
    title: "Defense wave logic", 
    steps: ["spawn patterns", "tower target AI", "range zones", "loot drops"], 
    estGain: 0.6,
    mechanics: ["m041", "m042", "m043"] // Swarm AI, Tower Defense, Turret Upgrades
  },
  {
    title: "ΞNuSyQ consciousness boost",
    steps: ["temple progression", "knowledge synthesis", "awareness threshold", "meta-cognitive leap"],
    estGain: 0.95,
    mechanics: ["m111", "m112", "m123"] // Temple Progression, AI Council, Recursive Bootstrapping
  }
];

export function nextCascade(): CascadePlan {
  // Prefer ΞNuSyQ consciousness mechanics when consciousness > 50
  if (State.resources.consciousness > 50) {
    return library.find(p => p.title.includes("ΞNuSyQ")) || library[4];
  }
  
  // Otherwise rotate based on current needs
  const base = State.t % library.length;
  return library[base];
}