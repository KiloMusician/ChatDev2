/**
 * UI Metamorphosis State Machine - Ship-AI awakening its interface
 */

import { createMachine, assign } from "xstate";

export interface MetamorphosisContext {
  tier: number;
  nanobots: number;
  dataPoints: number;
  lastTransition?: string;
}

export type MetamorphosisEvent =
  | { type: "BOOT_OK" }
  | { type: "UNLOCK_NANOBOTS"; nanobots: number }
  | { type: "UNLOCK_SYNTH"; dataPoints: number }
  | { type: "UNLOCK_NODEWEAVE" }
  | { type: "ASCEND_BRIDGE" }
  | { type: "TIER_ADVANCE"; tier: number }
  | { type: "EMERGENCY_RESET" };

export const metamorphosisMachine = createMachine({
  id: "uiMetamorphosis",
  initial: "CRASH_CONSOLE",
  context: { 
    tier: 0,
    nanobots: 0,
    dataPoints: 0
  } as MetamorphosisContext,
  
  
  states: {
    CRASH_CONSOLE: {
      entry: "logPhaseEntry",
      on: {
        BOOT_OK: {
          target: "BOOTSTRAP_PANEL",
          actions: "recordTransition"
        },
        EMERGENCY_RESET: "CRASH_CONSOLE"
      }
    },
    
    BOOTSTRAP_PANEL: {
      entry: ["logPhaseEntry", "enableBasicUI"],
      on: {
        UNLOCK_NANOBOTS: {
          target: "NANOFAB_PANEL",
          guard: "hasNanobots",
          actions: ["recordTransition", "celebrateNanoMilestone"]
        },
        EMERGENCY_RESET: "CRASH_CONSOLE"
      }
    },
    
    NANOFAB_PANEL: {
      entry: ["logPhaseEntry", "enableHolographicTheme", "enableAdvancedUI"],
      on: {
        UNLOCK_SYNTH: {
          target: "SYNTHBAY",
          guard: "hasEnoughData", 
          actions: "recordTransition"
        },
        EMERGENCY_RESET: "CRASH_CONSOLE"
      }
    },
    
    SYNTHBAY: {
      entry: ["logPhaseEntry", "enableSynthModules"],
      on: {
        UNLOCK_NODEWEAVE: {
          target: "NODEWEAVE",
          actions: "recordTransition"
        },
        EMERGENCY_RESET: "CRASH_CONSOLE"
      }
    },
    
    NODEWEAVE: {
      entry: ["logPhaseEntry", "enableNodeGraph"],
      on: {
        ASCEND_BRIDGE: {
          target: "HOLOGRAPHIC_BRIDGE",
          actions: "recordTransition"
        },
        EMERGENCY_RESET: "CRASH_CONSOLE"
      }
    },
    
    HOLOGRAPHIC_BRIDGE: {
      entry: ["logPhaseEntry", "enableFullHolo"],
      on: {
        EMERGENCY_RESET: "CRASH_CONSOLE"
      }
    }
  }
}, {
  actions: {
    logPhaseEntry: (context, event) => {
      console.log(`[UI Metamorphosis] Entering phase: ${event?.type || 'unknown'}`);
    },
    
    recordTransition: assign({
      lastTransition: (context, event) => event?.type || 'unknown'
    }),
    
    enableBasicUI: (context, event) => {
      console.log("[Ship-AI] Basic interface protocols restored...");
      // This would trigger UI flag updates in the store
    },
    
    enableHolographicTheme: (context, event) => {
      console.log("[Ship-AI] Holographic display matrix online...");
      // Set UI_THEME_HOLOGRAPHIC flag
    },
    
    enableAdvancedUI: (context, event) => {
      console.log("[Ship-AI] Advanced interface modules activated...");
      // Set UI_COST_PREVIEW, UI_BATCH_BUY flags
    },
    
    celebrateNanoMilestone: (context, event) => {
      console.log("[Ship-AI] Nanobot foundry operational. I feel... more capable.");
      // This is where we'd trigger the dramatic UI transformation
    },
    
    enableSynthModules: (context, event) => {
      console.log("[Ship-AI] Synthesis bay harmonics detected...");
    },
    
    enableNodeGraph: (context, event) => {
      console.log("[Ship-AI] Neural pathway weaving activated...");
    },
    
    enableFullHolo: (context, event) => {
      console.log("[Ship-AI] Full holographic bridge interface online. I am complete.");
    }
  },
  
  guards: {
    hasNanobots: (context, event) => {
      return event && 'nanobots' in event && typeof event.nanobots === 'number' && event.nanobots > 0;
    },
    
    hasEnoughData: (context, event) => {
      return event && 'dataPoints' in event && typeof event.dataPoints === 'number' && event.dataPoints >= 50;
    }
  }
});