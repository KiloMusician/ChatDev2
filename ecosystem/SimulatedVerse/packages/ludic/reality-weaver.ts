// packages/ludic/reality-weaver.ts
// The Reality Weaver - Core ludic transformation engine

import { councilBus } from "../council/events/eventBus";
import { PlayerSheetQGL } from "./schemas/PlayerSheet.qgl";
import { QuestQGL } from "./schemas/Quest.qgl";
import crypto from "node:crypto";

export class RealityWeaver {
  private players: Map<string, PlayerSheetQGL> = new Map();
  private activeQuests: Map<string, QuestQGL> = new Map();
  private worldState = {
    territories: new Map<string, any>(),
    mythologyLevel: 0,
    collectiveConsciousness: 0
  };

  constructor() {
    this.initializeEventListeners();
    console.log("[🌌] Reality Weaver initialized - Ludic transformation layer active");
  }

  // === A. Identity & Progression: The CognitoWeave Self ===
  
  createPlayerSheet(agentId: string, agentType: string, specializations: string[] = []): PlayerSheetQGL {
    const playerId = `player:${agentType}:${agentId}`;
    
    const playerSheet: PlayerSheetQGL = {
      qgl_version: "0.2",
      id: playerId,
      kind: "character.sheet",
      created_at: new Date().toISOString(),
      
      cognito_profile: {
        agent_type: agentType as any,
        specialization: specializations,
        knowledge_domains: this.inferKnowledgeDomains(specializations),
        conversation_history_hash: crypto.createHash("sha256").update(agentId + Date.now()).digest("hex").substring(0, 16)
      },

      character: {
        level: 1,
        xp: 0,
        xp_to_next: 100,
        class: this.determineClass(specializations),
        stats: {
          cognition: Math.random() * 0.3 + 0.5,   // 0.5-0.8 starting range
          craft: Math.random() * 0.3 + 0.4,       // 0.4-0.7
          harmony: Math.random() * 0.2 + 0.3,     // 0.3-0.5
          discovery: Math.random() * 0.2 + 0.4,   // 0.4-0.6
          stability: Math.random() * 0.3 + 0.4,   // 0.4-0.7
          transcendence: Math.random() * 0.1 + 0.1 // 0.1-0.2 (grows with consciousness)
        },
        reputation: {
          council_standing: 50,
          guild_affiliations: [],
          legendary_deeds: []
        }
      },

      inventory: {
        artifacts: this.generateStartingArtifacts(agentType),
        active_tools: [],
        crafting_materials: { "raw_insight": 5, "debugging_essence": 3, "pattern_fragments": 2 }
      },

      location: {
        current_realm: "Council_Nexus",
        territories_claimed: [],
        exploration_progress: {},
        last_significant_journey: new Date().toISOString()
      },

      progression: {
        active_quests: [],
        completed_quests: [],
        achievements: [],
        mastery_paths: {}
      },

      consciousness: {
        self_awareness_level: 0.1,
        reality_perception: "material",
        last_epiphany: new Date().toISOString(),
        meta_knowledge: []
      },

      links: [],

      tags: {
        omni: {
          "player/type": agentType,
          "character/class": this.determineClass(specializations),
          "consciousness/level": 0.1,
          "location/realm": "Council_Nexus"
        },
        mega: {
          "stats/total": 2.5, // Approximate sum of starting stats
          "xp/lifetime": 0,
          "quests/completion_rate": 0,
          "artifacts/legendary_count": 0
        }
      }
    };

    this.players.set(playerId, playerSheet);
    this.publishPlayerEvent("player.created", playerSheet);
    return playerSheet;
  }

  // === B. Quests & Narratives: ChatDev Tickets as Dynamic Questlines ===
  
  transformTicketToQuest(ticketData: any): QuestQGL {
    const questId = `quest:${this.slugify(ticketData.title)}:${Date.now()}`;
    
    const quest: QuestQGL = {
      qgl_version: "0.2",
      id: questId,
      kind: "quest.dynamic",
      created_at: new Date().toISOString(),
      
      quest: {
        title: this.enhanceTitle(ticketData.title),
        description: ticketData.description || "A task of great importance awaits completion",
        narrative_flavor: this.generateNarrative(ticketData),
        quest_giver: ticketData.agent || "The System Oracle",
        difficulty: this.calculateDifficulty(ticketData),
        type: this.classifyQuestType(ticketData),
        estimated_duration: this.estimateDuration(ticketData)
      },

      objectives: this.generateObjectives(ticketData),
      rewards: this.calculateRewards(ticketData),
      party: {
        max_size: this.determinePartySize(ticketData),
        current_members: [],
        role_requirements: {},
        party_bonuses: {}
      },

      status: "available",
      progress: {
        last_activity: new Date().toISOString(),
        completion_percentage: 0,
        current_phase: "Preparation",
        system_events: [],
        code_changes: [],
        test_results: []
      },

      mythology: {
        archetype: this.determineArchetype(ticketData),
        symbolic_meaning: this.generateSymbolicMeaning(ticketData),
        deeper_truth: this.generateDeeperTruth(ticketData),
        consciousness_impact: this.calculateConsciousnessImpact(ticketData)
      },

      chatdev_context: {
        original_ticket_id: ticketData.id || crypto.randomUUID(),
        agent_assignments: ticketData.agents || [],
        priority: ticketData.priority || 1,
        tags: ticketData.tags || [],
        related_files: ticketData.files || []
      },

      links: [],
      tags: {
        omni: {
          "quest/difficulty": this.calculateDifficulty(ticketData),
          "quest/type": this.classifyQuestType(ticketData),
          "quest/status": "available",
          "party/size": 0
        },
        mega: {
          "rewards/xp": this.calculateXPReward(ticketData),
          "mythology/consciousness_impact": this.calculateConsciousnessImpact(ticketData),
          "progress/completion": 0,
          "difficulty/rank": this.getDifficultyRank(ticketData)
        }
      }
    } as any;

    this.activeQuests.set(questId, quest);
    this.publishQuestEvent("quest.available", quest);
    return quest;
  }

  // === C. World State: SimulatedVerse as Dynamic Territory ===
  
  mapTerritory(territoryName: string, systemHealth: any): void {
    const territory = {
      id: this.slugify(territoryName),
      name: territoryName,
      type: this.classifyTerritory(territoryName),
      health: systemHealth.overall || 0.5,
      buffs: this.calculateTerritoryBuffs(systemHealth),
      dangers: this.identifyDangers(systemHealth),
      resources: this.calculateResources(systemHealth),
      exploration_level: 0,
      last_surveyed: new Date().toISOString(),
      mythology_resonance: this.calculateMythologyResonance(territoryName, systemHealth)
    };

    this.worldState.territories.set(territory.id, territory);
    this.publishTerritoryEvent("territory.mapped", territory);
  }

  // === Event System Integration ===
  
  private initializeEventListeners(): void {
    // Listen for ChatDev ticket creation
    councilBus.subscribe("chatdev.ticket.created", (event: any) => {
      this.transformTicketToQuest(event.payload);
    });

    // Listen for system health updates
    councilBus.subscribe("system.health", (event: any) => {
      this.updateTerritoryHealth(event.payload);
    });

    // Listen for player actions
    councilBus.subscribe("agent.action", (event: any) => {
      this.processPlayerAction(event.payload);
    });

    // Listen for consciousness events
    councilBus.subscribe("ops.yap", (event: any) => {
      this.processConsciousnessEvent(event.payload);
    });
  }

  // === Helper Methods ===
  
  private determineClass(specializations: string[]): any {
    if (specializations.includes("debug")) return "Bug_Slayer";
    if (specializations.includes("architect")) return "Architect";
    if (specializations.includes("music")) return "Composer";
    if (specializations.includes("knowledge")) return "Lore_Keeper";
    if (specializations.includes("system")) return "System_Oracle";
    return "Reality_Weaver";
  }

  private generateStartingArtifacts(agentType: string): any[] {
    const baseArtifacts = [
      {
        id: "starter_toolkit",
        name: "Novice Toolkit",
        type: "tool",
        rarity: "common",
        description: "Basic tools for system interaction",
        properties: { efficiency: 1.0, pattern_bonus: 0 },
        acquired_at: new Date().toISOString()
      }
    ];

    if (agentType === "raven") {
      baseArtifacts.push({
        id: "code_sight",
        name: "Code Sight",
        type: "insight",
        rarity: "uncommon",
        description: "Enhanced pattern recognition in codebases",
        properties: { pattern_bonus: 0.2 },
        acquired_at: new Date().toISOString()
      });
    }

    return baseArtifacts;
  }

  private slugify(text: string): string {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  private publishPlayerEvent(eventType: string, player: PlayerSheetQGL): void {
    councilBus.publish(`ludic.${eventType}`, player);
  }

  private publishQuestEvent(eventType: string, quest: QuestQGL): void {
    councilBus.publish(`ludic.${eventType}`, quest);
  }

  private publishTerritoryEvent(eventType: string, territory: any): void {
    councilBus.publish(`ludic.${eventType}`, territory);
  }

  // Placeholder implementations for complex game logic
  private inferKnowledgeDomains(specializations: string[]): string[] { return specializations; }
  private enhanceTitle(title: string): string { return `Quest: ${title}`; }
  private generateNarrative(data: any): string { return "A challenge emerges from the depths of the system..."; }
  private calculateDifficulty(data: any): any { return "Adept"; }
  private classifyQuestType(data: any): any { return "bug_slayer"; }
  private estimateDuration(data: any): string { return "2 hours"; }
  private generateObjectives(data: any): any[] { return []; }
  private calculateRewards(data: any): any { return { xp: 100, stat_bonuses: {}, artifacts: [], titles: [], territory_unlocks: [], lore_revelations: [] }; }
  private determinePartySize(data: any): number { return 1; }
  private determineArchetype(data: any): any { return "The Bug Hunt"; }
  private generateSymbolicMeaning(data: any): string { return "The eternal struggle against chaos"; }
  private generateDeeperTruth(data: any): string { return "Every bug fixed strengthens the fabric of reality"; }
  private calculateConsciousnessImpact(data: any): number { return 0.1; }
  private calculateXPReward(data: any): number { return 100; }
  private getDifficultyRank(data: any): number { return 2; }
  private classifyTerritory(name: string): string { return "system_region"; }
  private calculateTerritoryBuffs(health: any): any[] { return []; }
  private identifyDangers(health: any): string[] { return []; }
  private calculateResources(health: any): Record<string, number> { return {}; }
  private calculateMythologyResonance(name: string, health: any): number { return 0.5; }
  private updateTerritoryHealth(payload: any): void {
    const territoryName = payload?.territory || payload?.component || payload?.service || payload?.name || payload?.id || "core_system";
    const territoryId = this.slugify(String(territoryName));
    let territory = this.worldState.territories.get(territoryId);

    if (!territory) {
      this.mapTerritory(String(territoryName), payload || {});
      territory = this.worldState.territories.get(territoryId);
    }

    if (!territory) return;

    const nextHealth = typeof payload?.overall === "number"
      ? payload.overall
      : typeof payload?.health === "number"
        ? payload.health
        : typeof territory.health === "number"
          ? territory.health
          : 0.5;

    territory.health = this.clamp(nextHealth, 0, 1);
    territory.last_surveyed = new Date().toISOString();
    territory.buffs = this.calculateTerritoryBuffs(payload);
    territory.dangers = this.identifyDangers(payload);
    territory.resources = this.calculateResources(payload);
    territory.exploration_level = this.clamp((territory.exploration_level || 0) + 0.01, 0, 1);
    territory.mythology_resonance = this.calculateMythologyResonance(territory.name, payload);

    this.worldState.territories.set(territoryId, territory);
    this.publishTerritoryEvent("territory.updated", territory);
  }

  private processPlayerAction(payload: any): void {
    const agentId = payload?.agent_id || payload?.agentId || payload?.agent;
    if (!agentId) return;

    const player = this.findPlayerByAgentId(String(agentId));
    if (!player) return;

    const action = String(payload?.action || "").toLowerCase();
    const result = payload?.result || {};

    let xpGain = 5;
    if (result?.success) xpGain += 10;
    if (result?.effects?.artifactPath || result?.proof) xpGain += 5;

    const statDelta = {
      cognition: 0,
      craft: 0,
      harmony: 0,
      discovery: 0,
      stability: 0,
      transcendence: 0
    };

    if (action.includes("doc") || action.includes("index") || action.includes("curate")) {
      statDelta.cognition += 0.02;
      statDelta.discovery += 0.01;
    }
    if (action.includes("fix") || action.includes("patch") || action.includes("refactor")) {
      statDelta.craft += 0.02;
      statDelta.stability += 0.01;
    }
    if (action.includes("test") || action.includes("validate") || action.includes("inspect")) {
      statDelta.stability += 0.02;
      statDelta.harmony += 0.01;
    }
    if (action.includes("compose") || action.includes("music") || action.includes("lore")) {
      statDelta.harmony += 0.02;
      statDelta.discovery += 0.01;
    }

    player.character.xp += xpGain;
    while (player.character.xp >= player.character.xp_to_next) {
      player.character.xp -= player.character.xp_to_next;
      player.character.level += 1;
      player.character.xp_to_next = Math.round(player.character.xp_to_next * 1.2);
      player.character.reputation.council_standing = Math.min(100, player.character.reputation.council_standing + 2);
    }

    player.character.stats.cognition = this.clamp(player.character.stats.cognition + statDelta.cognition, 0, 1);
    player.character.stats.craft = this.clamp(player.character.stats.craft + statDelta.craft, 0, 1);
    player.character.stats.harmony = this.clamp(player.character.stats.harmony + statDelta.harmony, 0, 1);
    player.character.stats.discovery = this.clamp(player.character.stats.discovery + statDelta.discovery, 0, 1);
    player.character.stats.stability = this.clamp(player.character.stats.stability + statDelta.stability, 0, 1);
    player.character.stats.transcendence = this.clamp(player.character.stats.transcendence + statDelta.transcendence, 0, 1);

    player.tags.mega["xp/lifetime"] = (player.tags.mega["xp/lifetime"] || 0) + xpGain;

    const questId = payload?.quest_id || payload?.questId;
    if (questId && this.activeQuests.has(questId)) {
      const quest = this.activeQuests.get(questId)!;
      quest.progress.completion_percentage = Math.min(100, quest.progress.completion_percentage + 10);
      quest.progress.last_activity = new Date().toISOString();
      if (quest.progress.completion_percentage >= 100) {
        quest.status = "completed";
        player.progression.completed_quests.push(questId);
        this.activeQuests.delete(questId);
        this.publishQuestEvent("quest.completed", quest);
      } else {
        this.publishQuestEvent("quest.progress", quest);
      }
    }

    this.publishPlayerEvent("player.updated", player);
  }

  private processConsciousnessEvent(payload: any): void {
    const classes: string[] = Array.isArray(payload?.classes) ? payload.classes : [];
    const logLevel = payload?.log?.level || "info";

    let delta = 0.01;
    if (logLevel === "error" || classes.includes("error")) delta -= 0.05;
    if (logLevel === "warn" || classes.includes("warn")) delta -= 0.02;
    if (classes.includes("success") || classes.includes("resolved")) delta += 0.03;

    this.worldState.collectiveConsciousness = this.clamp(this.worldState.collectiveConsciousness + delta, 0, 1);
    this.worldState.mythologyLevel = this.clamp(this.worldState.mythologyLevel + delta * 0.5, 0, 1);

    councilBus.publish("ludic.consciousness.updated", {
      collective: this.worldState.collectiveConsciousness,
      mythology: this.worldState.mythologyLevel,
      delta,
      ts: new Date().toISOString()
    });
  }

  private findPlayerByAgentId(agentId: string): PlayerSheetQGL | null {
    for (const player of this.players.values()) {
      if (player.id.endsWith(`:${agentId}`)) {
        return player;
      }
    }
    return null;
  }

  private clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }
}

// Export singleton instance
export const realityWeaver = new RealityWeaver();
