/**
 * Upgrade definitions and UI evolution flags for Culture-Ship metamorphosis
 */

import { z } from "zod";
import { ResourceId, Pricer } from "../../systems/resources/ResourceDefs";

export type UnlockFlag =
  | "UI_TIPS" | "UI_COST_PREVIEW" | "UI_HOTKEYS" | "UI_BATCH_BUY"
  | "UI_THEME_HOLOGRAPHIC" | "UI_TERMINAL_INTERACTIVE"
  | "UI_NODEWEAVE" | "UI_SYNTHBAY" | "UI_GHOST_PREVIEWS"
  | "SYS_NANOBOT_FOUNDRY" | "SYS_AUTOTICKS" | "SYS_BLUEPRINTS"
  | "SYS_FACTORIES" | "SYS_LIFECYCLE" | "SYS_TRADE_BEACONS"
  | "LORE_CHANNEL_2" | "LORE_CHANNEL_3" | "LORE_FIRST_CONTACT"
  | "METAMORPHOSIS_BOOTSTRAP" | "METAMORPHOSIS_NANOFAB"
  | "METAMORPHOSIS_SYNTHBAY" | "METAMORPHOSIS_NODEWEAVE";

export interface UpgradeDef {
  id: string;
  title: string;
  desc: string;
  pricer: Pricer;
  grants?: Partial<Record<ResourceId, number>>; // capacity/production deltas
  flags?: UnlockFlag[];                        // UI/Feature flags
  requires?: string[];                         // tech prereqs
  tierHint?: number;                           // for Metamorphosis
  category?: "CORE" | "NANO" | "SYNTH" | "QOL" | "LORE";
}

export interface TechDef {
  id: string; 
  title: string; 
  nodes: string[];        // tree coordinates
  requires?: string[];    // dependency IDs
  unlocks: string[];      // upgrade IDs this unlocks
  loreKey?: string;       // text pack binding
}

// Core upgrade catalog - the Ship-AI repairing itself
export const UPGRADES: UpgradeDef[] = [
  // === BOOTSTRAP PHASE ===
  {
    id: "CRASH_RECOVERY",
    title: "Crash Recovery Protocol",
    desc: "Stabilize core systems and begin diagnostics",
    category: "CORE",
    pricer: {
      base: [{ r: "SCRAP", amount: 5 }],
      curve: { kind: "linear", k: 1.2 }
    },
    grants: { ENERGY: 2 },
    flags: ["UI_TIPS"]
  },
  
  {
    id: "BOOTSTRAP_FABRICATOR", 
    title: "Bootstrap Fabricator",
    desc: "Jury-rig a basic matter compiler from salvage",
    category: "CORE",
    pricer: {
      base: [{ r: "SCRAP", amount: 10 }, { r: "ENERGY", amount: 5 }],
      curve: { kind: "exp", k: 1.5 },
      previewDepth: 3
    },
    grants: { CIRCUITS: 1 },
    flags: ["UI_COST_PREVIEW"],
    requires: ["CRASH_RECOVERY"]
  },

  // === NANOBOT FOUNDRY MILESTONE ===
  {
    id: "NANO_THREAD",
    title: "Nanobot Threading",
    desc: "Each thread grants +1 automation capacity",
    category: "NANO",
    pricer: {
      base: [{ r: "CIRCUITS", amount: 3 }, { r: "SILICON", amount: 2 }],
      curve: { kind: "exp_softcap", k: 1.8, cap: 1000 },
      previewDepth: 5
    },
    grants: { NANOBOTS: 1 },
    flags: ["SYS_NANOBOT_FOUNDRY", "UI_THEME_HOLOGRAPHIC", "UI_BATCH_BUY"],
    requires: ["BOOTSTRAP_FABRICATOR"],
    tierHint: 1
  },

  {
    id: "SIGNAL_UPLINK",
    title: "Signal Uplink Array", 
    desc: "Gain cosmic awareness and anomaly detection",
    category: "CORE",
    pricer: {
      base: [{ r: "CIRCUITS", amount: 8 }, { r: "DATA", amount: 3 }],
      curve: { kind: "exp", k: 2.0 }
    },
    grants: { DATA: 5 },
    flags: ["LORE_CHANNEL_2", "UI_GHOST_PREVIEWS"],
    requires: ["NANO_THREAD"]
  },

  // === QOL UPGRADES ===
  {
    id: "BATCH_PLANNER",
    title: "Batch Action Planner",
    desc: "Queue multiple actions for execution",
    category: "QOL", 
    pricer: {
      base: [{ r: "DATA", amount: 5 }, { r: "NANOBOTS", amount: 2 }],
      curve: { kind: "linear", k: 1.3 }
    },
    flags: ["UI_HOTKEYS"],
    requires: ["NANO_THREAD"]
  },

  {
    id: "TERMINAL_UPLINK",
    title: "Terminal Command Interface",
    desc: "Enable direct command input to ship systems",
    category: "QOL",
    pricer: {
      base: [{ r: "DATA", amount: 10 }, { r: "CIRCUITS", amount: 5 }],
      curve: { kind: "exp", k: 1.4 }
    },
    flags: ["UI_TERMINAL_INTERACTIVE"],
    requires: ["SIGNAL_UPLINK"]
  }
];

// Tech tree definitions
export const TECH_TREE: TechDef[] = [
  {
    id: "MATTER_COMPILATION",
    title: "Matter Compilation",
    nodes: ["0,0"],
    unlocks: ["CRASH_RECOVERY", "BOOTSTRAP_FABRICATOR"],
    loreKey: "tech.matter_compilation"
  },
  {
    id: "NANOBOT_SWARM", 
    title: "Nanobot Swarm Control",
    nodes: ["1,0"],
    requires: ["MATTER_COMPILATION"],
    unlocks: ["NANO_THREAD"],
    loreKey: "tech.nanobot_swarm"
  },
  {
    id: "SIGNAL_PROCESSING",
    title: "Deep Signal Processing", 
    nodes: ["1,1"],
    requires: ["NANOBOT_SWARM"],
    unlocks: ["SIGNAL_UPLINK", "TERMINAL_UPLINK"],
    loreKey: "tech.signal_processing"
  }
];