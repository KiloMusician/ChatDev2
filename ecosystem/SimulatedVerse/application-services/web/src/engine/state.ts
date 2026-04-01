export type StageView = "microbe"|"colony"|"city"|"planet"|"system"|"space";

export interface SaveState {
  stage: StageView;
  seed: number;
  t: number;          // ticks
  paused: boolean;
  resources: Record<string, number>;
  mechanics: Record<string, boolean>; // Track which mechanics are unlocked
}

export const State: SaveState = {
  stage: "microbe",
  seed: 1337,
  t: 0,
  paused: false,
  resources: { biomass: 0, ore: 0, energy: 0, credits: 0, consciousness: 0 },
  mechanics: {}
};

export function setStage(s: StageView){ State.stage = s; }
export function togglePause(){ State.paused = !State.paused; }
export function addRes(k: string, v: number){ 
  State.resources[k] = (State.resources[k] || 0) + v; 
}
export function unlockMechanic(id: string) { 
  State.mechanics[id] = true; 
}

export function save(){ 
  localStorage.setItem("nusyq.save", JSON.stringify(State)); 
}

export function load(){
  const raw = localStorage.getItem("nusyq.save");
  if (raw) Object.assign(State, JSON.parse(raw));
}