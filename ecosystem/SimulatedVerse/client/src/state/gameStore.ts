import { create } from "zustand";

export type Phase = "BOOT" | "TITLE" | "GAME";
type View = "HUD" | "ASCII" | "MAP" | "LAB" | "SYSTEM" | "CHATDEV" | "VANTAGES" | "ADMIN" | "DEFENSE" | "EXPLORE" | "DASHBOARD" | "GAMEPLAY" | "INTERFACE" | "TEMPLE" | "CONSCIOUSNESS" | "GAME";

export interface GameState {
  phase: Phase;
  view: View;
  mobile: boolean;
  soundOn: boolean;
  fps: number;
  tick: number;
  consciousness: number; // 0..100
  quantum: number; // 0..100
  agentsActive: number;

  setPhase: (p: Phase) => void;
  setView: (v: View) => void;
  setMobile: (m: boolean) => void;
  toggleSound: () => void;
  setFps: (f: number) => void;
  bumpTick: () => void;
  nudgeStats: () => void;
}

export const useGame = create<GameState>((set, get) => ({
  phase: "BOOT",
  view: "ASCII",
  mobile: /Mobi|Android/i.test(navigator.userAgent),
  soundOn: false,
  fps: 0,
  tick: 0,
  consciousness: 0,
  quantum: 0,
  agentsActive: 0,

  setPhase: (p) => set({ phase: p }),
  setView: (v) => set({ view: v }),
  setMobile: (m) => set({ mobile: m }),
  toggleSound: () => set({ soundOn: !get().soundOn }),
  setFps: (f) => set({ fps: f }),
  bumpTick: () => set({ tick: get().tick + 1 }),
  nudgeStats: () => {
    const clamp = (x:number)=>Math.max(0, Math.min(100, x));
    const rnd = (d=2)=> (Math.random()*d - d/2);
    set({
      consciousness: clamp(get().consciousness + rnd(1.0)),
      quantum: clamp(get().quantum + rnd(1.2)),
      agentsActive: Math.max(0, Math.round(get().agentsActive + rnd(0.8))),
    });
  },
}));