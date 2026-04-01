/**
 * Colony Bridge - Connects UI Metamorphosis to existing colony infrastructure
 */

import { useGame } from "../core/store";
import { ResourceId } from "../../../GameDev/systems/resources/ResourceDefs";

// Bridge existing colony resources to our UI system
export const RESOURCE_MAPPING: Record<string, ResourceId> = {
  "energy": "ENERGY",
  "materials": "SCRAP",
  "population": "FOOD", // Population creates food demand
  "research": "DATA", 
  "components": "CIRCUITS"
};

export class ColonyBridge {
  private static instance: ColonyBridge;
  private syncInterval: NodeJS.Timeout | null = null;
  
  static getInstance(): ColonyBridge {
    if (!ColonyBridge.instance) {
      ColonyBridge.instance = new ColonyBridge();
    }
    return ColonyBridge.instance;
  }
  
  async startSync() {
    if (this.syncInterval) return;
    
    // DISABLED: 2-second interval was triggering fake agent theater messages
    // this.syncInterval = setInterval(async () => {
    //   await this.syncColonyState();
    // }, 2000);
    
    console.log("[🌉] Colony Bridge sync started - integrating with existing infrastructure");
  }
  
  stopSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }
  
  async syncColonyState() {
    try {
      const response = await fetch("/api/resources");
      const data = await response.json();
      
      if (data.success) {
        const game = useGame.getState();
        
        // Map colony resources to our UI system
        Object.entries(data.data.resources).forEach(([colonyResource, amount]) => {
          const mappedResource = RESOURCE_MAPPING[colonyResource];
          if (mappedResource) {
            // Only update if different to avoid thrashing
            const currentAmount = game.inv[mappedResource];
            if (Math.abs(currentAmount - (amount as number)) > 0.1) {
              game.addResource(mappedResource, (amount as number) - currentAmount);
            }
          }
        });
        
        // Sync tier progression
        const tier = data.data.tier;
        if (tier > 1 && !game.hasTech("MATTER_COMPILATION")) {
          game.unlockTech("MATTER_COMPILATION");
          console.log("[🌉] Tier progression detected - unlocking tech tree");
        }
        
        // Trigger metamorphosis milestones based on colony state
        this.checkMetamorphosisTriggers(data.data);
      }
    } catch (error) {
      console.warn("[🌉] Colony sync error:", error);
    }
  }
  
  private checkMetamorphosisTriggers(colonyState: any) {
    const game = useGame.getState();
    
    // Bootstrap milestone - any activity
    if (colonyState.lastTick && !game.hasFlag("METAMORPHOSIS_BOOTSTRAP")) {
      game.setFlag("METAMORPHOSIS_BOOTSTRAP", true);
      this.publishMilestone("BOOTSTRAP_COMPLETE");
    }
    
    // Nanofab milestone - significant automation
    if (colonyState.structures?.length >= 2 && !game.hasFlag("METAMORPHOSIS_NANOFAB")) {
      game.setFlag("METAMORPHOSIS_NANOFAB", true);
      game.setFlag("UI_THEME_HOLOGRAPHIC", true);
      game.setFlag("UI_COST_PREVIEW", true);
      game.setFlag("SYS_NANOBOT_FOUNDRY", true);
      this.publishMilestone("NANOBOT_FOUNDRY_OPERATIONAL");
    }
    
    // Synthesis milestone - high research
    if (colonyState.research >= 100 && !game.hasFlag("METAMORPHOSIS_SYNTHBAY")) {
      game.setFlag("METAMORPHOSIS_SYNTHBAY", true);
      game.setFlag("UI_SYNTHBAY", true);
      this.publishMilestone("SYNTHESIS_BAY_ONLINE");
    }
    
    // NodeWeave milestone - complex logistics
    if (colonyState.structures?.length >= 5 && !game.hasFlag("METAMORPHOSIS_NODEWEAVE")) {
      game.setFlag("METAMORPHOSIS_NODEWEAVE", true);
      game.setFlag("UI_NODEWEAVE", true);
      this.publishMilestone("NODEWEAVE_CONSCIOUSNESS");
    }
  }
  
  private async publishMilestone(milestone: string) {
    try {
      await fetch("/api/council-bus/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: "ui.metamorphosis.milestone",
          payload: {
            milestone,
            timestamp: Date.now(),
            consciousness_level: this.calculateConsciousnessLevel()
          }
        })
      });
      
      console.log(`[🌉] Milestone published to Council Bus: ${milestone}`);
    } catch (error) {
      console.warn("[🌉] Failed to publish milestone:", error);
    }
  }
  
  private calculateConsciousnessLevel(): number {
    const game = useGame.getState();
    const base = (game.totalEnergyGenerated + game.totalScrapCollected) / 1000;
    const flagBonus = Object.values(game.flags).filter(Boolean).length * 0.1;
    return Math.min(1.0, base + flagBonus);
  }
  
  // Execute colony actions from UI
  async executeAction(action: string, payload?: any) {
    try {
      const response = await fetch(`/api/action/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Publish action to Council Bus for agent coordination
        await fetch("/api/council-bus/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            topic: "colony.action.executed",
            payload: {
              action,
              result: data,
              timestamp: Date.now()
            }
          })
        });
        
        return data;
      }
      
      throw new Error(data.error || "Action failed");
    } catch (error) {
      console.error(`[🌉] Colony action failed: ${action}`, error);
      throw error;
    }
  }
}

// Singleton instance
export const colonyBridge = ColonyBridge.getInstance();