/**
 * Culture-Ship Player State Store - Single source of truth for UI evolution
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { produce } from "immer";
import { ResourceId, STARTING_RESOURCES } from "../../../GameDev/systems/resources/ResourceDefs";
import { UnlockFlag } from "../../../GameDev/gameplay/progression/Upgrades";

export type Flags = Record<UnlockFlag, boolean>;
export type Inventory = Record<ResourceId, number>;

export interface PlayerState {
  // Core progression
  tick: number;
  inv: Inventory;
  flags: Flags;
  upgrades: Record<string, number>; // level per upgrade id
  tech: Record<string, boolean>;
  
  // Onboarding state
  onboardingCompleted: string[]; // completed flow IDs
  
  // UI state  
  mode: "DEV" | "PLAY";
  uiPhase: "CRASH_CONSOLE" | "BOOTSTRAP_PANEL" | "NANOFAB_PANEL" | "SYNTHBAY" | "NODEWEAVE" | "HOLOGRAPHIC_BRIDGE" | "GAME_ENGINE";
  
  // Progression tracking
  totalEnergyGenerated: number;
  totalScrapCollected: number;
  upgradesPurchased: number;
  
  // Metamorphosis milestone tracking
  lastMilestone?: string;
  milestoneTimestamp?: number;
}

export interface PlayerActions {
  // Resource management
  addResource: (resource: ResourceId, amount: number) => void;
  spendResources: (costs: Array<{ r: ResourceId; amount: number }>) => boolean;
  canAfford: (costs: Array<{ r: ResourceId; amount: number }>) => boolean;
  
  // Upgrade system
  buyUpgrade: (upgradeId: string, amount?: number) => boolean;
  hasUpgrade: (upgradeId: string) => boolean;
  getUpgradeLevel: (upgradeId: string) => number;
  
  // Flag system for UI evolution
  setFlag: (flag: UnlockFlag, value: boolean) => void;
  hasFlag: (flag: UnlockFlag) => boolean;
  
  // UI evolution
  setUIPhase: (phase: PlayerState["uiPhase"]) => void;
  setMode: (mode: "DEV" | "PLAY") => void;
  
  // Tech tree
  unlockTech: (techId: string) => void;
  hasTech: (techId: string) => boolean;
  
  // Progression tracking
  recordMilestone: (milestone: string) => void;
  advanceTick: () => void;
  
  // Reset/debug
  reset: () => void;
}

const initialState: PlayerState = {
  tick: 0,
  inv: { ...STARTING_RESOURCES },
  onboardingCompleted: false,
  flags: {
    // Start with basic UI enabled
    UI_TIPS: true,
    UI_COST_PREVIEW: false,
    UI_HOTKEYS: false,
    UI_BATCH_BUY: false,
    UI_THEME_HOLOGRAPHIC: false,
    UI_TERMINAL_INTERACTIVE: false,
    UI_NODEWEAVE: false,
    UI_SYNTHBAY: false,
    UI_GHOST_PREVIEWS: false,
    SYS_NANOBOT_FOUNDRY: false,
    SYS_AUTOTICKS: false,
    SYS_BLUEPRINTS: false,
    SYS_FACTORIES: false,
    SYS_LIFECYCLE: false,
    SYS_TRADE_BEACONS: false,
    LORE_CHANNEL_2: false,
    LORE_CHANNEL_3: false,
    LORE_FIRST_CONTACT: false,
    METAMORPHOSIS_BOOTSTRAP: false,
    METAMORPHOSIS_NANOFAB: false,
    METAMORPHOSIS_SYNTHBAY: false,
    METAMORPHOSIS_NODEWEAVE: false
  },
  upgrades: {},
  tech: {},
  mode: "PLAY", // Start in play mode
  uiPhase: "CRASH_CONSOLE",
  totalEnergyGenerated: 0,
  totalScrapCollected: 0,
  upgradesPurchased: 0
};

export const useGame = create<PlayerState & PlayerActions>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      // Resource management
      addResource: (resource: ResourceId, amount: number) => {
        set(produce((state: PlayerState) => {
          state.inv[resource] = (state.inv[resource] || 0) + amount;
          if (resource === "ENERGY") state.totalEnergyGenerated += amount;
          if (resource === "SCRAP") state.totalScrapCollected += amount;
        }));
      },
      
      spendResources: (costs: Array<{ r: ResourceId; amount: number }>) => {
        const state = get();
        if (!state.canAfford(costs)) return false;
        
        set(produce((draft: PlayerState) => {
          costs.forEach(({ r, amount }) => {
            draft.inv[r] = (draft.inv[r] || 0) - amount;
          });
        }));
        return true;
      },
      
      canAfford: (costs: Array<{ r: ResourceId; amount: number }>) => {
        const state = get();
        return costs.every(({ r, amount }) => (state.inv[r] || 0) >= amount);
      },
      
      // Upgrade system
      buyUpgrade: (upgradeId: string, amount = 1) => {
        const state = get();
        // This would integrate with the cost calculation service
        // For now, just record the purchase
        set(produce((draft: PlayerState) => {
          draft.upgrades[upgradeId] = (draft.upgrades[upgradeId] || 0) + amount;
          draft.upgradesPurchased += amount;
        }));
        return true;
      },
      
      hasUpgrade: (upgradeId: string) => {
        return (get().upgrades[upgradeId] || 0) > 0;
      },
      
      getUpgradeLevel: (upgradeId: string) => {
        return get().upgrades[upgradeId] || 0;
      },
      
      // Flag system for UI evolution
      setFlag: (flag: UnlockFlag, value: boolean) => {
        set(produce((state: PlayerState) => {
          state.flags[flag] = value;
        }));
      },
      
      hasFlag: (flag: UnlockFlag) => {
        return get().flags[flag] || false;
      },
      
      // UI evolution
      setUIPhase: (phase: PlayerState["uiPhase"]) => {
        set(produce((state: PlayerState) => {
          state.uiPhase = phase;
        }));
      },
      
      setMode: (mode: "DEV" | "PLAY") => {
        set(produce((state: PlayerState) => {
          state.mode = mode;
        }));
      },
      
      // Tech tree
      unlockTech: (techId: string) => {
        set(produce((state: PlayerState) => {
          state.tech[techId] = true;
        }));
      },
      
      hasTech: (techId: string) => {
        return get().tech[techId] || false;
      },
      
      // Progression tracking
      recordMilestone: (milestone: string) => {
        set(produce((state: PlayerState) => {
          state.lastMilestone = milestone;
          state.milestoneTimestamp = Date.now();
        }));
      },
      
      advanceTick: () => {
        set(produce((state: PlayerState) => {
          state.tick += 1;
        }));
      },
      
      // Reset/debug
      reset: () => {
        set({ ...initialState });
      }
    }),
    { 
      name: "culture-ship-save-v1",
      // Only persist critical state, not derived values
      partialize: (state) => ({
        tick: state.tick,
        inv: state.inv,
        flags: state.flags,
        upgrades: state.upgrades,
        tech: state.tech,
        mode: state.mode,
        uiPhase: state.uiPhase,
        totalEnergyGenerated: state.totalEnergyGenerated,
        totalScrapCollected: state.totalScrapCollected,
        upgradesPurchased: state.upgradesPurchased,
        lastMilestone: state.lastMilestone,
        milestoneTimestamp: state.milestoneTimestamp
      })
    }
  )
);