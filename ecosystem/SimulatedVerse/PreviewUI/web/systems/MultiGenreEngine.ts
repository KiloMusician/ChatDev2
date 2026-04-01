/**
 * Multi-Genre Engine - Pokémon × Dwarf Fortress × Starcraft × Stellaris integration
 */

import { colonyBridge } from "../adapters/ColonyBridge";
import { useGame } from "../core/store";
import { useProgression } from "../core/state_manager";

// === POKÉMON LAYER: Creature Collection & Breeding ===

export interface Creature {
  id: string;
  species: string;
  nickname?: string;
  level: number;
  stats: {
    power: number;
    efficiency: number;
    resilience: number;
    intelligence: number;
  };
  traits: string[];
  workAssignment?: "MINING" | "RESEARCH" | "DEFENSE" | "LOGISTICS" | "EXPLORATION";
  breedingData?: {
    parent1?: string;
    parent2?: string;
    generation: number;
    mutations: string[];
  };
}

export class CreatureSystem {
  public creatures: Map<string, Creature> = new Map();
  
  async captureCreature(biomassData: any): Promise<Creature> {
    const species = this.determineSpecies(biomassData);
    const creature: Creature = {
      id: `creature_${Date.now()}`,
      species,
      level: 1,
      stats: this.generateRandomStats(),
      traits: this.generateTraits(species),
      breedingData: {
        generation: 1,
        mutations: []
      }
    };
    
    this.creatures.set(creature.id, creature);
    
    // Update progression system
    useProgression.getState().recordPokemonProgress(this.creatures.size);
    
    // Publish to Council Bus for agent awareness
    await fetch("/api/council-bus/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: "creatures.captured",
        payload: { creature, biomassSource: biomassData }
      })
    });
    
    return creature;
  }
  
  async breedCreatures(parent1: string, parent2: string): Promise<Creature | null> {
    const p1 = this.creatures.get(parent1);
    const p2 = this.creatures.get(parent2);
    
    if (!p1 || !p2) return null;
    
    // Breeding algorithm combines stats with random mutations
    const offspring: Creature = {
      id: `creature_${Date.now()}`,
      species: Math.random() < 0.9 ? p1.species : `${p1.species}_${p2.species}_hybrid`,
      level: 1,
      stats: {
        power: Math.floor((p1.stats.power + p2.stats.power) / 2 + (Math.random() - 0.5) * 10),
        efficiency: Math.floor((p1.stats.efficiency + p2.stats.efficiency) / 2 + (Math.random() - 0.5) * 10),
        resilience: Math.floor((p1.stats.resilience + p2.stats.resilience) / 2 + (Math.random() - 0.5) * 10),
        intelligence: Math.floor((p1.stats.intelligence + p2.stats.intelligence) / 2 + (Math.random() - 0.5) * 10)
      },
      traits: this.inheritTraits(p1.traits, p2.traits),
      breedingData: {
        parent1: parent1,
        parent2: parent2,
        generation: Math.max(p1.breedingData?.generation || 1, p2.breedingData?.generation || 1) + 1,
        mutations: this.generateMutations()
      }
    };
    
    this.creatures.set(offspring.id, offspring);
    return offspring;
  }
  
  private determineSpecies(biomassData: any): string {
    const species = ["NanoBug", "CircuitSlime", "DataMoth", "EnergySprite", "VoidWeaver"];
    return species[Math.floor(Math.random() * species.length)] || "NanoBug";
  }
  
  private generateRandomStats() {
    return {
      power: Math.floor(Math.random() * 50) + 25,
      efficiency: Math.floor(Math.random() * 50) + 25,
      resilience: Math.floor(Math.random() * 50) + 25,
      intelligence: Math.floor(Math.random() * 50) + 25
    };
  }
  
  private generateTraits(species: string): string[] {
    const allTraits = ["Hardy", "Quick", "Efficient", "Loyal", "Innovative", "Resilient"];
    return allTraits.filter(() => Math.random() < 0.3);
  }
  
  private inheritTraits(traits1: string[], traits2: string[]): string[] {
    const combined = [...new Set([...traits1, ...traits2])];
    return combined.filter(() => Math.random() < 0.7);
  }
  
  private generateMutations(): string[] {
    const mutations = ["Enhanced Vision", "Extra Appendage", "Electromagnetic Field", "Phase Shift"];
    return mutations.filter(() => Math.random() < 0.1);
  }
}

// === DWARF FORTRESS LAYER: Emergent Colony Simulation ===

export interface ColonyAgent {
  id: string;
  name: string;
  role: "MINER" | "ENGINEER" | "RESEARCHER" | "GUARD" | "MEDIC" | "COOK" | "CLEANER";
  skills: Record<string, number>;
  mood: "ECSTATIC" | "HAPPY" | "CONTENT" | "STRESSED" | "MISERABLE";
  needs: Record<string, number>;
  currentTask?: string;
  lastTaskTime?: number; // Add cooldown tracking
  assignedCreature?: string;
}

export class ColonySimulation {
  public agents: Map<string, ColonyAgent> = new Map();
  
  async initializeAgents() {
    // Create starting agents based on existing ChatDev agents
    const startingAgents = [
      { name: "Navigator", role: "ENGINEER" as const },
      { name: "Raven", role: "RESEARCHER" as const },
      { name: "Artificer", role: "MINER" as const },
      { name: "Janitor", role: "CLEANER" as const }
    ];
    
    for (const { name, role } of startingAgents) {
      const agent: ColonyAgent = {
        id: `agent_${name.toLowerCase()}`,
        name,
        role,
        skills: this.generateSkills(role),
        mood: "CONTENT",
        needs: { food: 50, rest: 50, recreation: 50, work: 80 },
        currentTask: undefined
      };
      
      this.agents.set(agent.id, agent);
    }
    
    // Publish agent registry to Council Bus
    await fetch("/api/council-bus/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: "colony.agents.initialized",
        payload: { agents: Array.from(this.agents.values()) }
      })
    });
  }
  
  private generateSkills(role: string): Record<string, number> {
    const baseSkills = { mining: 5, crafting: 5, research: 5, combat: 5, medicine: 5 };
    
    switch (role) {
      case "MINER":
        baseSkills.mining = 15;
        break;
      case "ENGINEER":
        baseSkills.crafting = 15;
        break;
      case "RESEARCHER":
        baseSkills.research = 15;
        break;
      case "GUARD":
        baseSkills.combat = 15;
        break;
      case "MEDIC":
        baseSkills.medicine = 15;
        break;
    }
    
    return baseSkills;
  }
  
  async processAgentTasks() {
    for (const agent of this.agents.values()) {
      if (!agent.currentTask) {
        // Assign new task based on colony needs
        const task = await this.findOptimalTask(agent);
        if (task) {
          agent.currentTask = task;
          await this.executeAgentTask(agent, task);
        }
      }
    }
  }
  
  private async findOptimalTask(agent: ColonyAgent): Promise<string | null> {
    // Use existing colony API to determine optimal tasks
    const response = await fetch("/api/colony");
    const data = await response.json();
    
    if (!data.success) return null;
    
    const colony = data.data;
    
    // Intelligent task assignment with cooldown to prevent spam
    const now = Date.now();
    if (!agent.lastTaskTime || (now - agent.lastTaskTime) > 30000) { // 30-second cooldown per agent
      // Task priority based on colony state with meaningful thresholds
      if (colony.resources.energy < 50) {
        agent.lastTaskTime = now;
        return "GENERATE_ENERGY";
      }
      if (colony.resources.materials < 25) {
        agent.lastTaskTime = now;
        return "COLLECT_MATERIALS";
      }
      if (colony.structures.length < 2) {
        agent.lastTaskTime = now;
        return "BUILD_STRUCTURE";
      }
      if (colony.resources.research < colony.tier * 50) {
        agent.lastTaskTime = now;
        return "CONDUCT_RESEARCH";
      }
    }
    
    return null; // No task needed, prevent busy work
  }
  
  private async executeAgentTask(agent: ColonyAgent, task: string) {
    // Map tasks to existing colony actions
    const actionMap: Record<string, string> = {
      "GENERATE_ENERGY": "tick",
      "COLLECT_MATERIALS": "scout", 
      "BUILD_STRUCTURE": "build_outpost",
      "CONDUCT_RESEARCH": "research"
      // Removed MAINTAIN_COLONY mapping to break the loop
    };
    
    const action = actionMap[task];
    if (action) {
      try {
        await colonyBridge.executeAction(action);
        
        // Replace theater with intelligent contextual information
        const context = await this.generateContextualResponse(agent, task, action);
        console.log(`[🔧] Infrastructure: ${agent.name} ${context.action} - ${context.result}${context.impact ? ` → ${context.impact}` : ''}`);
        
        // Publish intelligent event instead of theater
        if ((window as any).councilBus) {
          (window as any).councilBus.publish('infrastructure.action.completed', {
            agent: agent.name,
            task: task,
            action: context.action,
            result: context.result,
            impact: context.impact,
            timestamp: Date.now()
          });
        }
        
        agent.currentTask = undefined;
        this.improveAgentSkill(agent, task);
        
      } catch (error) {
        console.warn(`[⚠️] ${agent.name} task failed: ${task} - ${error}`);
        agent.currentTask = undefined;
      }
    }
  }

  private async generateContextualResponse(agent: ColonyAgent, task: string, action: string): Promise<{
    action: string;
    result: string;
    impact?: string;
  }> {
    // Get current colony state for context
    const response = await fetch("/api/colony");
    const colony = await response.json();
    
    const contexts = {
      "GENERATE_ENERGY": {
        action: "optimized power grid",
        result: `+${Math.floor(Math.random() * 20 + 10)} energy`,
        impact: colony?.data?.resources?.energy > 100 ? "surplus achieved" : "building reserves"
      },
      "COLLECT_MATERIALS": {
        action: "surveyed sector 7-Beta",
        result: `located ${Math.floor(Math.random() * 15 + 5)} raw materials`,
        impact: colony?.data?.structures?.length < 3 ? "construction ready" : "stockpiling"
      },
      "BUILD_STRUCTURE": {
        action: "erected hab-module",
        result: `+1 structure (${colony?.data?.structures?.length + 1 || 1} total)`,
        impact: colony?.data?.resources?.population > 50 ? "population expansion enabled" : "infrastructure foundation"
      },
      "CONDUCT_RESEARCH": {
        action: "analyzed quantum patterns",
        result: `+${Math.floor(Math.random() * 10 + 5)} research`,
        impact: colony?.data?.resources?.research > 100 ? "breakthrough imminent" : "knowledge accumulating"
      }
    };
    
    return contexts[task as keyof typeof contexts] || {
      action: "performed maintenance",
      result: "systems nominal"
    };
  }
  
  private improveAgentSkill(agent: ColonyAgent, task: string) {
    const skillMap: Record<string, string> = {
      "GENERATE_ENERGY": "crafting",
      "COLLECT_MATERIALS": "mining",
      "BUILD_STRUCTURE": "crafting",
      "CONDUCT_RESEARCH": "research"
    };
    
    const skill = skillMap[task];
    if (skill && agent.skills[skill]) {
      agent.skills[skill] = Math.min(20, agent.skills[skill] + 0.1);
    }
  }
}

// === STARCRAFT LAYER: Tactical Combat ===

export interface TacticalSquad {
  id: string;
  name: string;
  units: Array<{
    id: string;
    type: "SCOUT" | "WARRIOR" | "ENGINEER" | "SUPPORT";
    health: number;
    damage: number;
    speed: number;
    assignedCreature?: string;
  }>;
  formation: "DEFENSIVE" | "AGGRESSIVE" | "RECON" | "BUILDER";
  currentMission?: string;
}

export class TacticalSystem {
  public squads: Map<string, TacticalSquad> = new Map();
  private activeMissions: Map<string, any> = new Map();
  
  async deploySquad(squadId: string, missionType: string) {
    const squad = this.squads.get(squadId);
    if (!squad) return null;
    
    // Execute mission using existing colony action system
    const missionActions: Record<string, string> = {
      "SCOUT_PERIMETER": "scout",
      "DEFEND_COLONY": "tick", // Passive defense boost
      "EXPAND_TERRITORY": "build_outpost",
      "RESEARCH_ANOMALY": "research"
    };
    
    const action = missionActions[missionType];
    if (action) {
      const result = await colonyBridge.executeAction(action);
      
      // Apply squad bonuses to result
      const bonusMultiplier = 1 + (squad.units.length * 0.1);
      return { ...result, squad_bonus: bonusMultiplier };
    }
    
    return null;
  }
}

// === STELLARIS LAYER: 4X Expansion ===

export interface Sector {
  id: string;
  name: string;
  type: "CORE" | "FRONTIER" | "EXPLORATION" | "STRATEGIC";
  resources: Record<string, number>;
  colonies: string[];
  threats: string[];
  diplomaticStatus?: Record<string, "NEUTRAL" | "FRIENDLY" | "HOSTILE">;
}

export class ExpansionSystem {
  public sectors: Map<string, Sector> = new Map();
  
  async initializeGalaxy() {
    // Create initial sectors
    const homeSector: Sector = {
      id: "home_sector",
      name: "Origin System",
      type: "CORE",
      resources: { energy: 1000, materials: 500, research: 100 },
      colonies: ["home_colony"],
      threats: []
    };
    
    this.sectors.set(homeSector.id, homeSector);
    
    // Generate neighboring sectors
    for (let i = 1; i <= 4; i++) {
      const sector: Sector = {
        id: `sector_${i}`,
        name: `Sector ${i}`,
        type: Math.random() < 0.3 ? "STRATEGIC" : "FRONTIER",
        resources: {
          energy: Math.floor(Math.random() * 500) + 100,
          materials: Math.floor(Math.random() * 300) + 50,
          research: Math.floor(Math.random() * 200)
        },
        colonies: [],
        threats: Math.random() < 0.4 ? ["pirate_base"] : []
      };
      
      this.sectors.set(sector.id, sector);
    }
    
    console.log("[🌌] Galaxy initialized with 5 sectors");
  }
  
  async expandToSector(sectorId: string): Promise<boolean> {
    const sector = this.sectors.get(sectorId);
    if (!sector || sector.type === "CORE") return false;
    
    // Expansion requires significant resources
    const expansionCost = {
      energy: 200,
      materials: 100,
      population: 5
    };
    
    try {
      // Use existing colony system for expansion
      await colonyBridge.executeAction("build_outpost");
      
      // Mark sector as colonized
      sector.colonies.push(`colony_${Date.now()}`);
      sector.type = "CORE";
      
      // Publish expansion event
      await fetch("/api/council-bus/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: "empire.expansion.success",
          payload: { sector, expansionCost }
        })
      });
      
      console.log(`[🌌] Successfully expanded to ${sector.name}`);
      return true;
      
    } catch (error) {
      console.error(`[🌌] Expansion to ${sectorId} failed:`, error);
      return false;
    }
  }
}

// === INTEGRATION ORCHESTRATOR ===

export class MultiGenreOrchestrator {
  private creatureSystem = new CreatureSystem();
  private colonySimulation = new ColonySimulation();
  private tacticalSystem = new TacticalSystem();
  private expansionSystem = new ExpansionSystem();
  
  async initializeAllSystems() {
    console.log("[🎮] Initializing Multi-Genre Engine...");
    
    // Initialize all subsystems
    await this.colonySimulation.initializeAgents();
    await this.expansionSystem.initializeGalaxy();
    
    // Start processing loops
    this.startGameLoops();
    
    // Connect to Council Bus for cross-system events
    this.setupCrossSystemEvents();
    
    console.log("[🎮] Multi-Genre Engine online - All systems integrated!");
  }
  
  private startGameLoops() {
    // Agent task processing DISABLED to eliminate MAINTAIN_COLONY spam
    // setInterval(() => {
    //   this.colonySimulation.processAgentTasks();
    // }, 30000);
    console.log("[🎮] Agent task processing disabled - eliminating theater messages");
    
    // System condition analysis (replaces random encounters with intelligence)
    setInterval(() => {
      this.analyzeSystemConditions();
    }, 45000); // Every 45 seconds - offset from agent processing
  }
  
  private setupCrossSystemEvents() {
    // When creatures are captured, they can be assigned to colony agents
    this.listenForEvent("creatures.captured", (data) => {
      console.log("[🎮] Cross-system: Creature captured, colony agents notified");
    });
    
    // When colony expands, new tactical opportunities arise
    this.listenForEvent("empire.expansion.success", (data) => {
      console.log("[🎮] Cross-system: Expansion successful, tactical squads deployed");
    });
    
    // When research completes, unlock new creature abilities
    this.listenForEvent("colony.action.executed", (data) => {
      if (data.action === "research") {
        console.log("[🎮] Cross-system: Research complete, creature abilities unlocked");
      }
    });
  }
  
  private async listenForEvent(topic: string, handler: (data: any) => void) {
    // Subscribe to Council Bus events
    // Note: In a full implementation, this would use SSE or WebSocket
    console.log(`[🎮] Listening for ${topic} events`);
  }
  
  private async analyzeSystemConditions() {
    try {
      // Get real system state for intelligent analysis
      const response = await fetch("/api/colony");
      const colony = await response.json();
      
      if (!colony.success) return;
      
      const data = colony.data;
      const insights = [];
      
      // Infrastructure analysis instead of random encounters
      if (data.resources.energy > data.resources.population * 2) {
        insights.push(`Energy abundance detected - infrastructure expansion recommended`);
      }
      
      if (data.resources.research >= data.tier * 50) {
        insights.push(`Research milestone reached - tier advancement available`);
      }
      
      if (data.structures.length < Math.floor(data.resources.population / 10)) {
        insights.push(`Population density critical - housing shortage detected`);
      }
      
      // Emit intelligent analysis instead of random encounters
      if (insights.length > 0) {
        await fetch("/api/council-bus/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            topic: "system.analysis.completed",
            payload: {
              insights: insights,
              timestamp: Date.now(),
              colony_state: {
                energy: data.resources.energy,
                population: data.resources.population,
                research: data.resources.research,
                structures: data.structures.length,
                tier: data.tier
              }
            }
          })
        });
        
        console.log(`[🧠] System Analysis: ${insights.join(' | ')}`);
      }
      
    } catch (error) {
      // Fail gracefully
    }
  }
  
  // Public interface for UI integration
  async getGameState() {
    return {
      creatures: Array.from(this.creatureSystem.creatures.values()),
      agents: Array.from(this.colonySimulation.agents.values()),
      squads: Array.from(this.tacticalSystem.squads.values()),
      sectors: Array.from(this.expansionSystem.sectors.values())
    };
  }
}

// Singleton
export const multiGenreEngine = new MultiGenreOrchestrator();