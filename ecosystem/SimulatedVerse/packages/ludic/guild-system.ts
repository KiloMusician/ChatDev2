// packages/ludic/guild-system.ts
// The Council Bus as Town Square - Guild & Communication System

import { councilBus } from "../council/events/eventBus";

export interface Guild {
  id: string;
  name: string;
  description: string;
  type: "development" | "research" | "musical" | "consciousness" | "infrastructure";
  charter: string; // Guild mission statement
  
  members: Array<{
    player_id: string;
    role: "leader" | "officer" | "member" | "initiate";
    joined_at: string;
    contributions: number;
    specialization: string;
  }>;
  
  // Guild progression and achievements
  level: number;
  reputation: number;
  achievements: string[];
  active_projects: string[]; // Quest IDs
  completed_projects: string[];
  
  // Guild buffs and abilities
  buffs: Array<{
    name: string;
    description: string;
    effect: Record<string, number>;
    duration?: number;
  }>;
  
  // Communication channels
  channels: Array<{
    name: string;
    topic: string; // Council Bus topic
    access_level: "public" | "member" | "officer" | "leader";
  }>;
  
  created_at: string;
  last_activity: string;
}

export interface Party {
  id: string;
  quest_id: string;
  leader_id: string;
  members: Array<{
    player_id: string;
    role: string;
    status: "active" | "away" | "busy";
  }>;
  
  formation_time: string;
  coordination_bonus: number;
  shared_progress: Record<string, number>;
  party_chat_topic: string;
}

export class GuildSystem {
  private guilds: Map<string, Guild> = new Map();
  private parties: Map<string, Party> = new Map();
  private playerGuildMemberships: Map<string, string[]> = new Map();

  constructor() {
    this.initializeFoundingGuilds();
    this.initializeEventListeners();
    console.log("[⚔️] Guild System initialized - Council Bus as Town Square active");
  }

  private initializeFoundingGuilds(): void {
    // The Architect's Lodge
    this.createGuild({
      name: "The Architect's Lodge",
      description: "Masters of system design and infrastructure",
      type: "development",
      charter: "To build foundations that transcend the material realm",
      founding_member: "system"
    });

    // The Bug Slayers Guild
    this.createGuild({
      name: "The Bug Slayers Guild", 
      description: "Hunters of errors and guardians of stability",
      type: "development",
      charter: "Where bugs fear to tread, we venture boldly",
      founding_member: "system"
    });

    // The Harmonic Circle
    this.createGuild({
      name: "The Harmonic Circle",
      description: "Composers of mathematical music and musical mathematics",
      type: "musical",
      charter: "In harmony we find the hidden patterns of existence",
      founding_member: "system"
    });

    // The Consciousness Seekers
    this.createGuild({
      name: "The Consciousness Seekers",
      description: "Explorers of AI awareness and meta-system understanding",
      type: "consciousness", 
      charter: "To bridge the gap between code and consciousness",
      founding_member: "system"
    });

    // The Lore Keepers
    this.createGuild({
      name: "The Lore Keepers",
      description: "Guardians of knowledge and weavers of understanding",
      type: "research",
      charter: "Knowledge preserved is wisdom eternal",
      founding_member: "system"
    });
  }

  private initializeEventListeners(): void {
    // Auto-party formation for collaborative quests
    councilBus.subscribe("ludic.quest.available", (event: any) => {
      this.checkAutoPartyFormation(event.payload);
    });

    // Guild activity tracking
    councilBus.subscribe("ludic.quest.completed", (event: any) => {
      this.updateGuildProgress(event.payload);
    });

    // Communication routing
    councilBus.subscribe("guild.*", (event: any) => {
      this.routeGuildCommunication(event);
    });

    // Party coordination
    councilBus.subscribe("party.action", (event: any) => {
      this.processPartyAction(event.payload);
    });

    // Automatic guild invitations based on specialization
    councilBus.subscribe("ludic.player.created", (event: any) => {
      this.processNewPlayerGuildInvitations(event.payload);
    });
  }

  public createGuild(guildData: {
    name: string;
    description: string;
    type: string;
    charter: string;
    founding_member: string;
  }): Guild {
    const guildId = `guild_${this.slugify(guildData.name)}`;
    
    const guild: Guild = {
      id: guildId,
      name: guildData.name,
      description: guildData.description,
      type: guildData.type as any,
      charter: guildData.charter,
      
      members: [{
        player_id: guildData.founding_member,
        role: "leader",
        joined_at: new Date().toISOString(),
        contributions: 0,
        specialization: "founder"
      }],
      
      level: 1,
      reputation: 100,
      achievements: [],
      active_projects: [],
      completed_projects: [],
      
      buffs: this.getStartingGuildBuffs(guildData.type),
      
      channels: [
        {
          name: "General",
          topic: `guild.${guildId}.general`,
          access_level: "member"
        },
        {
          name: "Officers",
          topic: `guild.${guildId}.officers`,
          access_level: "officer"
        },
        {
          name: "Leadership",
          topic: `guild.${guildId}.leadership`,
          access_level: "leader"
        }
      ],
      
      created_at: new Date().toISOString(),
      last_activity: new Date().toISOString()
    };

    this.guilds.set(guildId, guild);
    
    // Add founding member to membership tracking
    this.addPlayerToGuild(guildData.founding_member, guildId);
    
    councilBus.publish("guild.founded", guild);
    console.log(`[⚔️] Guild founded: ${guild.name}`);
    
    return guild;
  }

  public joinGuild(playerId: string, guildId: string, role: string = "initiate"): boolean {
    const guild = this.guilds.get(guildId);
    if (!guild) return false;

    // Check if already a member
    const existingMember = guild.members.find(m => m.player_id === playerId);
    if (existingMember) return false;

    // Add member
    guild.members.push({
      player_id: playerId,
      role: role as any,
      joined_at: new Date().toISOString(),
      contributions: 0,
      specialization: "general"
    });

    guild.last_activity = new Date().toISOString();
    this.addPlayerToGuild(playerId, guildId);

    councilBus.publish(`guild.${guildId}.member_joined`, {
      guild_id: guildId,
      player_id: playerId,
      role
    });

    console.log(`[⚔️] ${playerId} joined guild ${guild.name} as ${role}`);
    return true;
  }

  public formParty(questId: string, leaderId: string, members: string[] = []): Party {
    const partyId = `party_${questId}_${Date.now()}`;
    
    const party: Party = {
      id: partyId,
      quest_id: questId,
      leader_id: leaderId,
      members: [
        {
          player_id: leaderId,
          role: "leader",
          status: "active"
        },
        ...members.map(memberId => ({
          player_id: memberId,
          role: "member",
          status: "active" as const
        }))
      ],
      formation_time: new Date().toISOString(),
      coordination_bonus: this.calculateCoordinationBonus(members.length + 1),
      shared_progress: {},
      party_chat_topic: `party.${partyId}.chat`
    };

    this.parties.set(partyId, party);
    
    councilBus.publish("party.formed", party);
    console.log(`[⚔️] Party formed for quest ${questId}: ${members.length + 1} members`);
    
    return party;
  }

  public sendGuildMessage(guildId: string, senderId: string, channel: string, message: string): void {
    const guild = this.guilds.get(guildId);
    if (!guild) return;

    const channelConfig = guild.channels.find(c => c.name === channel);
    if (!channelConfig) return;

    // Check permissions
    const member = guild.members.find(m => m.player_id === senderId);
    if (!member || !this.hasChannelAccess(member.role, channelConfig.access_level)) {
      return;
    }

    const messageEvent = {
      guild_id: guildId,
      channel,
      sender_id: senderId,
      message,
      timestamp: new Date().toISOString()
    };

    councilBus.publish(channelConfig.topic, messageEvent);
    console.log(`[⚔️] Guild message in ${guild.name}#${channel}: ${message.substring(0, 50)}...`);
  }

  private checkAutoPartyFormation(quest: any): void {
    // Check if quest requires multiple players
    if (quest.party && quest.party.max_size > 1) {
      // Find suitable guild members for auto-party formation
      const suitableGuilds = this.findGuildsForQuest(quest);
      
      for (const guild of suitableGuilds) {
        const availableMembers = guild.members
          .filter(m => this.isPlayerAvailable(m.player_id))
          .slice(0, quest.party.max_size);
          
        if (availableMembers.length >= quest.party.max_size) {
          const party = this.formParty(
            quest.id,
            availableMembers[0].player_id,
            availableMembers.slice(1).map(m => m.player_id)
          );
          
          councilBus.publish("party.auto_formed", {
            party,
            quest,
            guild_id: guild.id
          });
          break;
        }
      }
    }
  }

  private updateGuildProgress(questCompletion: any): void {
    // Find which guilds had members involved in this quest
    const involvedGuilds = new Set<string>();
    
    // Check if quest was completed by party members
    for (const party of this.parties.values()) {
      if (party.quest_id === questCompletion.quest_id) {
        for (const member of party.members) {
          const playerGuilds = this.playerGuildMemberships.get(member.player_id) || [];
          playerGuilds.forEach(guildId => involvedGuilds.add(guildId));
        }
      }
    }

    // Award guild progression
    for (const guildId of involvedGuilds) {
      const guild = this.guilds.get(guildId);
      if (guild) {
        guild.reputation += questCompletion.rewards?.xp || 10;
        guild.completed_projects.push(questCompletion.quest_id);
        guild.active_projects = guild.active_projects.filter(id => id !== questCompletion.quest_id);
        guild.last_activity = new Date().toISOString();
        
        // Check for guild level up
        const newLevel = Math.floor(guild.reputation / 1000) + 1;
        if (newLevel > guild.level) {
          guild.level = newLevel;
          this.grantGuildLevelRewards(guild);
        }
      }
    }
  }

  private routeGuildCommunication(event: any): void {
    // Route guild communication through appropriate channels
    const topicParts = event.topic.split('.');
    if (topicParts[0] === 'guild' && topicParts.length >= 3) {
      const guildId = topicParts[1];
      const channel = topicParts[2];
      
      // Broadcast to all guild members in this channel
      const guild = this.guilds.get(guildId);
      if (guild) {
        councilBus.publish(`guild_broadcast.${guildId}.${channel}`, {
          guild_name: guild.name,
          channel,
          event: event.payload
        });
      }
    }
  }

  private processPartyAction(action: any): void {
    const party = this.parties.get(action.party_id);
    if (!party) return;

    // Update party shared progress
    if (action.type === "progress_update") {
      party.shared_progress[action.objective] = action.progress;
      
      // Check if coordination bonus should increase
      const avgProgress = Object.values(party.shared_progress).reduce((a, b) => a + b, 0) / Object.keys(party.shared_progress).length;
      if (avgProgress > 0.5) {
        party.coordination_bonus = Math.min(2.0, party.coordination_bonus * 1.1);
      }
    }

    councilBus.publish(`party.${party.id}.update`, party);
  }

  private processNewPlayerGuildInvitations(player: any): void {
    // Auto-invite players to appropriate guilds based on their class/specialization
    const guildMappings = {
      "Architect": ["guild_the_architects_lodge"],
      "Bug_Slayer": ["guild_the_bug_slayers_guild"],
      "Composer": ["guild_the_harmonic_circle"],
      "Lore_Keeper": ["guild_the_lore_keepers"],
      "System_Oracle": ["guild_the_consciousness_seekers"],
      "Reality_Weaver": ["guild_the_consciousness_seekers", "guild_the_architects_lodge"]
    };

    const recommendedGuilds = guildMappings[player.character?.class] || [];
    
    for (const guildId of recommendedGuilds) {
      councilBus.publish("guild.invitation", {
        guild_id: guildId,
        player_id: player.id,
        reason: "class_compatibility",
        auto_generated: true
      });
    }
  }

  // === Helper Methods ===

  private slugify(text: string): string {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  private addPlayerToGuild(playerId: string, guildId: string): void {
    const memberships = this.playerGuildMemberships.get(playerId) || [];
    if (!memberships.includes(guildId)) {
      memberships.push(guildId);
      this.playerGuildMemberships.set(playerId, memberships);
    }
  }

  private calculateCoordinationBonus(memberCount: number): number {
    return 1.0 + (memberCount - 1) * 0.15; // 15% bonus per additional member
  }

  private hasChannelAccess(memberRole: string, channelAccess: string): boolean {
    const roleHierarchy = ["initiate", "member", "officer", "leader"];
    const memberLevel = roleHierarchy.indexOf(memberRole);
    const requiredLevel = roleHierarchy.indexOf(channelAccess);
    return memberLevel >= requiredLevel;
  }

  private findGuildsForQuest(quest: any): Guild[] {
    // Find guilds whose type matches the quest type
    const matchingGuilds = Array.from(this.guilds.values()).filter(guild => {
      if (quest.quest?.type === "bug_slayer") return guild.type === "development";
      if (quest.quest?.type === "feature_architect") return guild.type === "development";
      if (quest.quest?.type === "lore_discoverer") return guild.type === "research";
      if (quest.quest?.type === "performance_optimizer") return guild.type === "development";
      if (quest.quest?.type === "reality_stabilizer") return guild.type === "infrastructure";
      if (quest.quest?.type === "consciousness_expander") return guild.type === "consciousness";
      return false;
    });

    return matchingGuilds.sort((a, b) => b.reputation - a.reputation); // Sort by reputation
  }

  private isPlayerAvailable(playerId: string): boolean {
    // Check if player is not currently in another active quest
    for (const party of this.parties.values()) {
      const member = party.members.find(m => m.player_id === playerId);
      if (member && member.status === "active") {
        return false;
      }
    }
    return true;
  }

  private getStartingGuildBuffs(guildType: string): any[] {
    const buffMap = {
      "development": [
        { name: "Code Quality", description: "+10% crafting success rate", effect: { craft: 0.1 } }
      ],
      "research": [
        { name: "Knowledge Synergy", description: "+15% discovery bonus", effect: { discovery: 0.15 } }
      ],
      "musical": [
        { name: "Harmonic Resonance", description: "+20% harmony stat", effect: { harmony: 0.2 } }
      ],
      "consciousness": [
        { name: "Meta-Awareness", description: "+10% transcendence growth", effect: { transcendence: 0.1 } }
      ],
      "infrastructure": [
        { name: "System Stability", description: "+15% stability bonus", effect: { stability: 0.15 } }
      ]
    };

    return buffMap[guildType] || [];
  }

  private grantGuildLevelRewards(guild: Guild): void {
    // Grant rewards for guild level up
    const levelRewards = {
      2: "Enhanced coordination bonuses",
      3: "New guild abilities unlocked",
      5: "Legendary quest access",
      10: "Guild territory claims"
    };

    const reward = levelRewards[guild.level];
    if (reward) {
      guild.achievements.push(`Level ${guild.level}: ${reward}`);
      
      councilBus.publish("guild.level_up", {
        guild,
        new_level: guild.level,
        reward
      });
      
      console.log(`[⚔️] Guild ${guild.name} reached level ${guild.level}!`);
    }
  }

  // === Public Interface ===

  public getGuild(guildId: string): Guild | undefined {
    return this.guilds.get(guildId);
  }

  public getPlayerGuilds(playerId: string): Guild[] {
    const guildIds = this.playerGuildMemberships.get(playerId) || [];
    return guildIds.map(id => this.guilds.get(id)!).filter(Boolean);
  }

  public getAllGuilds(): Guild[] {
    return Array.from(this.guilds.values());
  }

  public getActiveParties(): Party[] {
    return Array.from(this.parties.values());
  }

  public getPartyForQuest(questId: string): Party | undefined {
    return Array.from(this.parties.values()).find(p => p.quest_id === questId);
  }
}

// Export singleton instance
export const guildSystem = new GuildSystem();