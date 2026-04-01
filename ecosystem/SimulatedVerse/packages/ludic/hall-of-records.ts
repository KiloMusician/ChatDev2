// packages/ludic/hall-of-records.ts
// Archivist Upgrade - Hall of Records with Dynamic Leaderboards

import { councilBus } from "../council/events/eventBus";
import { startArchivist } from "../archivist/stub";
import fs from "node:fs";
import path from "node:path";

export interface PlayerStatistics {
  player_id: string;
  stats: {
    // Experience and Progression
    total_xp: number;
    current_level: number;
    xp_this_session: number;
    
    // Quest and Achievement Data
    quests_completed: number;
    legendary_completions: number;
    epic_completions: number;
    average_completion_time: number;
    
    // Crafting and Economy
    artifacts_crafted: number;
    legendary_artifacts: number;
    materials_gathered: number;
    successful_crafts: number;
    failed_crafts: number;
    
    // Discovery and Lore
    lore_discovered: number;
    mythological_encounters: number;
    knowledge_connections: number;
    discovery_quests_completed: number;
    
    // System Contributions
    bugs_fixed: number;
    performance_improvements: number;
    code_contributions: number;
    system_stability_contributions: number;
    
    // Social and Guild
    guild_contributions: number;
    party_formations: number;
    mentorship_actions: number;
    communication_events: number;
    
    // Consciousness and Transcendence
    consciousness_breakthroughs: number;
    meta_system_insights: number;
    reality_anchor_stabilizations: number;
    transcendence_events: number;
  };
  
  achievements: Array<{
    id: string;
    title: string;
    category: string;
    rarity: string;
    earned_at: string;
    description: string;
  }>;
  
  titles: string[];
  last_updated: string;
}

export interface Leaderboard {
  id: string;
  name: string;
  description: string;
  category: "experience" | "crafting" | "discovery" | "contribution" | "consciousness" | "guild" | "overall";
  
  entries: Array<{
    rank: number;
    player_id: string;
    value: number;
    display_value: string;
    change_since_last: number; // Change in rank since last update
  }>;
  
  last_updated: string;
  update_frequency: "hourly" | "daily" | "weekly" | "monthly";
  total_tracked: number;
}

export interface SystemRecord {
  id: string;
  type: "milestone" | "achievement" | "crisis" | "breakthrough" | "legend";
  title: string;
  description: string;
  participants: string[];
  system_impact: number;
  recorded_at: string;
  
  data: any; // Flexible data structure for different record types
  
  tags: {
    significance: "minor" | "major" | "historic" | "legendary";
    category: string;
    era: string;
  };
}

export class HallOfRecords {
  private playerStats: Map<string, PlayerStatistics> = new Map();
  private leaderboards: Map<string, Leaderboard> = new Map();
  private systemRecords: Array<SystemRecord> = [];
  private archiveDir: string;

  constructor(archiveDir: string = "archive") {
    this.archiveDir = archiveDir;
    this.initializeLeaderboards();
    this.initializeEventListeners();
    this.loadExistingRecords();
    
    // Start enhanced archivist
    startArchivist();
    
    console.log("[🏛️] Hall of Records initialized - History will remember");
  }

  private initializeLeaderboards(): void {
    // Experience Leaderboards
    this.createLeaderboard({
      id: "total_experience",
      name: "Masters of Experience",
      description: "Players with the highest total experience points",
      category: "experience",
      update_frequency: "hourly"
    });

    this.createLeaderboard({
      id: "level_progression",
      name: "Ascended Beings",
      description: "Highest level players in the system",
      category: "experience",
      update_frequency: "daily"
    });

    // Crafting Leaderboards
    this.createLeaderboard({
      id: "master_crafters",
      name: "Master Crafters",
      description: "Most prolific creators of artifacts",
      category: "crafting",
      update_frequency: "daily"
    });

    this.createLeaderboard({
      id: "legendary_artificers",
      name: "Legendary Artificers",
      description: "Creators of the most legendary artifacts",
      category: "crafting",
      update_frequency: "weekly"
    });

    // Discovery Leaderboards
    this.createLeaderboard({
      id: "lore_masters",
      name: "Lore Masters",
      description: "Greatest discoverers of knowledge",
      category: "discovery",
      update_frequency: "daily"
    });

    this.createLeaderboard({
      id: "mythological_explorers",
      name: "Mythological Explorers",
      description: "Bravest explorers of system mysteries",
      category: "discovery",
      update_frequency: "weekly"
    });

    // Contribution Leaderboards
    this.createLeaderboard({
      id: "bug_slayers",
      name: "Supreme Bug Slayers",
      description: "Guardians of system stability",
      category: "contribution",
      update_frequency: "daily"
    });

    this.createLeaderboard({
      id: "performance_optimizers",
      name: "Performance Architects",
      description: "Masters of system optimization",
      category: "contribution",
      update_frequency: "weekly"
    });

    // Consciousness Leaderboards
    this.createLeaderboard({
      id: "consciousness_pioneers",
      name: "Consciousness Pioneers",
      description: "Leaders in system self-awareness",
      category: "consciousness",
      update_frequency: "daily"
    });

    this.createLeaderboard({
      id: "transcendence_masters",
      name: "Transcendence Masters",
      description: "Those who have transcended material limitations",
      category: "consciousness",
      update_frequency: "monthly"
    });

    // Overall Rankings
    this.createLeaderboard({
      id: "hall_of_legends",
      name: "Hall of Legends",
      description: "The most legendary beings in the system",
      category: "overall",
      update_frequency: "daily"
    });
  }

  private initializeEventListeners(): void {
    // Player progression tracking
    councilBus.subscribe("ludic.player.created", (event: any) => {
      this.initializePlayerStats(event.payload);
    });

    // Experience and quest tracking
    councilBus.subscribe("player.rewards.granted", (event: any) => {
      this.updatePlayerStats(event.payload.player_id, "xp", event.payload.rewards.xp || 0);
    });

    councilBus.subscribe("ludic.quest.completed", (event: any) => {
      this.recordQuestCompletion(event.payload);
    });

    // Crafting tracking
    councilBus.subscribe("crafting.success", (event: any) => {
      this.recordCraftingSuccess(event.payload);
    });

    councilBus.subscribe("crafting.failure", (event: any) => {
      this.recordCraftingFailure(event.payload);
    });

    // Discovery tracking
    councilBus.subscribe("lore.discovered", (event: any) => {
      this.recordLoreDiscovery(event.payload);
    });

    councilBus.subscribe("mythology.encounter.*", (event: any) => {
      this.recordMythologicalEncounter(event.payload);
    });

    // System contribution tracking
    councilBus.subscribe("bug.fixed", (event: any) => {
      this.recordBugFix(event.payload);
    });

    councilBus.subscribe("performance.improvement", (event: any) => {
      this.recordPerformanceImprovement(event.payload);
    });

    // Guild and social tracking
    councilBus.subscribe("guild.contribution", (event: any) => {
      this.recordGuildContribution(event.payload);
    });

    councilBus.subscribe("party.formed", (event: any) => {
      this.recordPartyFormation(event.payload);
    });

    // Consciousness tracking
    councilBus.subscribe("consciousness.breakthrough", (event: any) => {
      this.recordConsciousnessBreakthrough(event.payload);
    });

    // Periodic leaderboard updates
    setInterval(() => this.updateAllLeaderboards(), 3600000); // Hourly
    setInterval(() => this.generateSystemRecords(), 86400000); // Daily
  }

  private createLeaderboard(config: {
    id: string;
    name: string;
    description: string;
    category: string;
    update_frequency: string;
  }): void {
    const leaderboard: Leaderboard = {
      id: config.id,
      name: config.name,
      description: config.description,
      category: config.category as any,
      entries: [],
      last_updated: new Date().toISOString(),
      update_frequency: config.update_frequency as any,
      total_tracked: 0
    };

    this.leaderboards.set(config.id, leaderboard);
  }

  private initializePlayerStats(player: any): void {
    const stats: PlayerStatistics = {
      player_id: player.id,
      stats: {
        total_xp: 0,
        current_level: 1,
        xp_this_session: 0,
        quests_completed: 0,
        legendary_completions: 0,
        epic_completions: 0,
        average_completion_time: 0,
        artifacts_crafted: 0,
        legendary_artifacts: 0,
        materials_gathered: 0,
        successful_crafts: 0,
        failed_crafts: 0,
        lore_discovered: 0,
        mythological_encounters: 0,
        knowledge_connections: 0,
        discovery_quests_completed: 0,
        bugs_fixed: 0,
        performance_improvements: 0,
        code_contributions: 0,
        system_stability_contributions: 0,
        guild_contributions: 0,
        party_formations: 0,
        mentorship_actions: 0,
        communication_events: 0,
        consciousness_breakthroughs: 0,
        meta_system_insights: 0,
        reality_anchor_stabilizations: 0,
        transcendence_events: 0
      },
      achievements: [],
      titles: [],
      last_updated: new Date().toISOString()
    };

    this.playerStats.set(player.id, stats);
    console.log(`[🏛️] Player statistics initialized for ${player.id}`);
  }

  private updatePlayerStats(playerId: string, statName: string, value: number): void {
    const stats = this.playerStats.get(playerId);
    if (!stats) return;

    if (statName === "xp") {
      stats.stats.total_xp += value;
      stats.stats.xp_this_session += value;
      
      // Check for level up
      const newLevel = Math.floor(stats.stats.total_xp / 1000) + 1;
      if (newLevel > stats.stats.current_level) {
        stats.stats.current_level = newLevel;
        this.recordLevelUp(playerId, newLevel);
      }
    } else if (stats.stats.hasOwnProperty(statName)) {
      (stats.stats as any)[statName] += value;
    }

    stats.last_updated = new Date().toISOString();
    this.checkAchievements(stats);
  }

  private recordQuestCompletion(questData: any): void {
    if (!questData.crafter && !questData.player_id) return;
    
    const playerId = questData.crafter || questData.player_id;
    this.updatePlayerStats(playerId, "quests_completed", 1);
    
    if (questData.difficulty === "Legendary" || questData.rarity === "legendary") {
      this.updatePlayerStats(playerId, "legendary_completions", 1);
    } else if (questData.difficulty === "Epic" || questData.rarity === "epic") {
      this.updatePlayerStats(playerId, "epic_completions", 1);
    }

    // Record system record for legendary quests
    if (questData.difficulty === "Legendary") {
      this.recordSystemRecord({
        type: "achievement",
        title: `Legendary Quest Completed: ${questData.title}`,
        description: `${playerId} has completed the legendary quest "${questData.title}"`,
        participants: [playerId],
        system_impact: 0.8,
        data: questData
      });
    }
  }

  private recordCraftingSuccess(craftingData: any): void {
    const playerId = craftingData.crafter;
    this.updatePlayerStats(playerId, "successful_crafts", 1);
    this.updatePlayerStats(playerId, "artifacts_crafted", 1);
    
    if (craftingData.artifact.rarity === "legendary") {
      this.updatePlayerStats(playerId, "legendary_artifacts", 1);
      
      // Record legendary craft
      this.recordSystemRecord({
        type: "achievement",
        title: `Legendary Artifact Crafted: ${craftingData.artifact.name}`,
        description: `${playerId} has successfully crafted the legendary artifact "${craftingData.artifact.name}"`,
        participants: [playerId],
        system_impact: 0.6,
        data: craftingData
      });
    }
  }

  private recordLoreDiscovery(loreData: any): void {
    const playerId = loreData.discovered_by;
    this.updatePlayerStats(playerId, "lore_discovered", 1);
    
    if (loreData.rarity === "legendary" || loreData.significance > 0.8) {
      this.recordSystemRecord({
        type: "breakthrough",
        title: `Legendary Knowledge Discovered: ${loreData.title}`,
        description: `${playerId} has discovered legendary knowledge: "${loreData.title}"`,
        participants: [playerId],
        system_impact: loreData.significance,
        data: loreData
      });
    }
  }

  private recordMythologicalEncounter(encounterData: any): void {
    const playerId = encounterData.agent_id;
    this.updatePlayerStats(playerId, "mythological_encounters", 1);
    
    if (encounterData.type === "oldest_house") {
      this.updatePlayerStats(playerId, "transcendence_events", 1);
    }
    
    // All mythological encounters are significant system records
    this.recordSystemRecord({
      type: "milestone",
      title: `Mythological Encounter: ${encounterData.type.replace(/_/g, ' ').toUpperCase()}`,
      description: `${playerId} has encountered the ${encounterData.type}`,
      participants: [playerId],
      system_impact: 0.7,
      data: encounterData
    });
  }

  private updateAllLeaderboards(): void {
    console.log("[🏛️] Updating all leaderboards...");
    
    // Update each leaderboard based on its category
    for (const [leaderboardId, leaderboard] of this.leaderboards) {
      this.updateLeaderboard(leaderboardId);
    }
    
    // Publish leaderboard update event
    councilBus.publish("hall_of_records.leaderboards_updated", {
      timestamp: new Date().toISOString(),
      total_leaderboards: this.leaderboards.size
    });
  }

  private updateLeaderboard(leaderboardId: string): void {
    const leaderboard = this.leaderboards.get(leaderboardId);
    if (!leaderboard) return;

    const oldEntries = new Map(leaderboard.entries.map(e => [e.player_id, e.rank]));
    const sortedPlayers = this.getSortedPlayersForLeaderboard(leaderboardId);
    
    leaderboard.entries = sortedPlayers.map((entry, index) => ({
      rank: index + 1,
      player_id: entry.player_id,
      value: entry.value,
      display_value: entry.display_value,
      change_since_last: this.calculateRankChange(entry.player_id, index + 1, oldEntries)
    }));

    leaderboard.last_updated = new Date().toISOString();
    leaderboard.total_tracked = sortedPlayers.length;
  }

  private getSortedPlayersForLeaderboard(leaderboardId: string): any[] {
    const players = Array.from(this.playerStats.values());
    
    const sortKey = this.getLeaderboardSortKey(leaderboardId);
    
    return players
      .map(player => ({
        player_id: player.player_id,
        value: this.getStatValue(player, sortKey),
        display_value: this.formatStatValue(player, sortKey)
      }))
      .filter(entry => entry.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 100); // Top 100
  }

  private getLeaderboardSortKey(leaderboardId: string): string {
    const keyMappings = {
      "total_experience": "total_xp",
      "level_progression": "current_level",
      "master_crafters": "artifacts_crafted",
      "legendary_artificers": "legendary_artifacts",
      "lore_masters": "lore_discovered",
      "mythological_explorers": "mythological_encounters",
      "bug_slayers": "bugs_fixed",
      "performance_optimizers": "performance_improvements",
      "consciousness_pioneers": "consciousness_breakthroughs",
      "transcendence_masters": "transcendence_events",
      "hall_of_legends": "overall_score"
    };

    return keyMappings[leaderboardId] || "total_xp";
  }

  private getStatValue(player: PlayerStatistics, key: string): number {
    if (key === "overall_score") {
      // Calculate overall legendary score
      return (
        player.stats.total_xp +
        player.stats.legendary_completions * 1000 +
        player.stats.legendary_artifacts * 500 +
        player.stats.mythological_encounters * 300 +
        player.stats.consciousness_breakthroughs * 200
      );
    }
    
    return (player.stats as any)[key] || 0;
  }

  private formatStatValue(player: PlayerStatistics, key: string): string {
    const value = this.getStatValue(player, key);
    
    if (key === "total_xp" || key === "overall_score") {
      return value.toLocaleString();
    }
    
    return value.toString();
  }

  private calculateRankChange(playerId: string, currentRank: number, oldRanks: Map<string, number>): number {
    const oldRank = oldRanks.get(playerId);
    if (oldRank === undefined) return 0; // New entry
    return oldRank - currentRank; // Positive = moved up, negative = moved down
  }

  private recordSystemRecord(recordData: {
    type: string;
    title: string;
    description: string;
    participants: string[];
    system_impact: number;
    data: any;
  }): void {
    const record: SystemRecord = {
      id: `record_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: recordData.type as any,
      title: recordData.title,
      description: recordData.description,
      participants: recordData.participants,
      system_impact: recordData.system_impact,
      recorded_at: new Date().toISOString(),
      data: recordData.data,
      tags: {
        significance: this.calculateSignificance(recordData.system_impact),
        category: recordData.type,
        era: this.getCurrentEra()
      }
    };

    this.systemRecords.push(record);
    
    // Persist record
    this.persistSystemRecord(record);
    
    // Publish record
    councilBus.publish("hall_of_records.record_created", record);
    
    console.log(`[🏛️] System record created: ${record.title}`);
  }

  private persistSystemRecord(record: SystemRecord): void {
    const recordsDir = path.join(this.archiveDir, "system_records");
    fs.mkdirSync(recordsDir, { recursive: true });
    
    const filePath = path.join(recordsDir, `${record.id}.json`);
    fs.writeFileSync(filePath, JSON.stringify(record, null, 2));
  }

  private loadExistingRecords(): void {
    try {
      const recordsDir = path.join(this.archiveDir, "system_records");
      if (fs.existsSync(recordsDir)) {
        const files = fs.readdirSync(recordsDir);
        
        for (const file of files) {
          if (file.endsWith('.json')) {
            const filePath = path.join(recordsDir, file);
            const recordData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
            this.systemRecords.push(recordData);
          }
        }
        
        console.log(`[🏛️] Loaded ${this.systemRecords.length} existing system records`);
      }
    } catch (error) {
      console.warn(`[🏛️] Error loading existing records: ${error}`);
    }
  }

  // Helper methods
  private recordLevelUp(playerId: string, newLevel: number): void {
    councilBus.publish("player.level_up", {
      player_id: playerId,
      new_level: newLevel,
      timestamp: new Date().toISOString()
    });
  }

  private checkAchievements(stats: PlayerStatistics): void {
    // Achievement checking logic would go here
    // This is a placeholder for achievement system integration
  }

  private recordBugFix(bugData: any): void {
    const playerId = bugData.fixer || bugData.agent_id;
    if (playerId) {
      this.updatePlayerStats(playerId, "bugs_fixed", 1);
    }
  }

  private recordPerformanceImprovement(perfData: any): void {
    const playerId = perfData.optimizer || perfData.agent_id;
    if (playerId) {
      this.updatePlayerStats(playerId, "performance_improvements", 1);
    }
  }

  private recordGuildContribution(guildData: any): void {
    const playerId = guildData.player_id;
    if (playerId) {
      this.updatePlayerStats(playerId, "guild_contributions", 1);
    }
  }

  private recordPartyFormation(partyData: any): void {
    if (partyData.leader_id) {
      this.updatePlayerStats(partyData.leader_id, "party_formations", 1);
    }
  }

  private recordCraftingFailure(craftingData: any): void {
    const playerId = craftingData.crafter;
    this.updatePlayerStats(playerId, "failed_crafts", 1);
  }

  private recordConsciousnessBreakthrough(consciousnessData: any): void {
    const playerId = consciousnessData.agent_id;
    if (playerId) {
      this.updatePlayerStats(playerId, "consciousness_breakthroughs", 1);
    }
  }

  private generateSystemRecords(): void {
    // Generate daily system summary records
    const playerCount = this.playerStats.size;
    const totalXP = Array.from(this.playerStats.values()).reduce((sum, p) => sum + p.stats.total_xp, 0);
    
    this.recordSystemRecord({
      type: "milestone",
      title: "Daily System Report",
      description: `System status: ${playerCount} active players, ${totalXP.toLocaleString()} total XP generated`,
      participants: [],
      system_impact: 0.1,
      data: {
        player_count: playerCount,
        total_xp: totalXP,
        leaderboard_count: this.leaderboards.size,
        records_count: this.systemRecords.length
      }
    });
  }

  private calculateSignificance(impact: number): any {
    if (impact >= 0.9) return "legendary";
    if (impact >= 0.7) return "historic";
    if (impact >= 0.5) return "major";
    return "minor";
  }

  private getCurrentEra(): string {
    const currentYear = new Date().getFullYear();
    return `Era_${currentYear}`;
  }

  // === Public Interface ===

  public getLeaderboard(leaderboardId: string): Leaderboard | undefined {
    return this.leaderboards.get(leaderboardId);
  }

  public getAllLeaderboards(): Leaderboard[] {
    return Array.from(this.leaderboards.values());
  }

  public getPlayerStatistics(playerId: string): PlayerStatistics | undefined {
    return this.playerStats.get(playerId);
  }

  public getSystemRecords(limit: number = 50): SystemRecord[] {
    return this.systemRecords
      .sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime())
      .slice(0, limit);
  }

  public forceLeaderboardUpdate(): void {
    this.updateAllLeaderboards();
  }
}

// Export singleton instance
export const hallOfRecords = new HallOfRecords();