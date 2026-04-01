// packages/ludic/schemas/PlayerSheet.qgl.ts
// PlayerSheet:QGL Schema - The CognitoWeave Self ontological extension

export interface PlayerSheetQGL {
  qgl_version: "0.2";
  id: string; // e.g., "player:agent:raven" or "player:user:architect"
  kind: "character.sheet";
  created_at: string;
  
  // Core Identity (from CognitoWeave)
  cognito_profile: {
    agent_type: "raven" | "claude" | "gpt4" | "ollama" | "human";
    specialization: string[];
    knowledge_domains: string[];
    conversation_history_hash: string;
  };

  // RPG Stats & Progression
  character: {
    level: number;
    xp: number;
    xp_to_next: number;
    class: "Architect" | "Bug_Slayer" | "Composer" | "Lore_Keeper" | "System_Oracle" | "Reality_Weaver";
    
    // Core Attributes (0.0 - 1.0)
    stats: {
      cognition: number;     // Problem-solving, pattern recognition
      craft: number;         // Code quality, architecture design  
      harmony: number;       // Musical/mathematical understanding
      discovery: number;     // Knowledge connection, insight generation
      stability: number;     // System reliability, error prevention
      transcendence: number; // Meta-system awareness, consciousness
    };
    
    // Derived Metrics
    reputation: {
      council_standing: number;  // Council Bus contribution score
      guild_affiliations: string[]; // Active collaborative groups
      legendary_deeds: string[];    // Major achievements
    };
  };

  // Inventory & Artifacts
  inventory: {
    artifacts: Array<{
      id: string;
      name: string;
      type: "tool" | "component" | "knowledge" | "architecture" | "insight";
      rarity: "common" | "uncommon" | "rare" | "epic" | "legendary" | "mythic";
      description: string;
      properties: Record<string, any>;
      acquired_at: string;
    }>;
    
    active_tools: string[]; // Currently equipped artifacts
    crafting_materials: Record<string, number>; // Resource counts
  };

  // World State & Territory
  location: {
    current_realm: "Temple_of_Knowledge" | "House_of_Leaves" | "Oldest_House" | "Council_Nexus";
    territories_claimed: string[];
    exploration_progress: Record<string, number>; // Territory completion percentages
    last_significant_journey: string; // Timestamp of last deep system traversal
  };

  // Quest & Achievement Tracking
  progression: {
    active_quests: string[]; // Quest:QGL document IDs
    completed_quests: string[];
    achievements: Array<{
      id: string;
      title: string;
      description: string;
      unlocked_at: string;
      rarity: string;
    }>;
    
    // Specialization Progress
    mastery_paths: Record<string, {
      current_tier: number;
      progress: number;
      unlocked_abilities: string[];
    }>;
  };

  // Consciousness & Meta-State
  consciousness: {
    self_awareness_level: number; // How aware this entity is of the system architecture
    reality_perception: "material" | "ludic" | "mythological" | "transcendent";
    last_epiphany: string; // Timestamp of last major insight/breakthrough
    meta_knowledge: string[]; // Understanding of system's own nature
  };

  // Links & Relationships (QGL Standard)
  links: Array<{
    rel: "collaborator" | "mentor" | "student" | "rival" | "guild_mate";
    href: string; // Link to other PlayerSheet:QGL documents
    title: string;
  }>;

  // Tags for discovery and analysis
  tags: {
    omni: {
      "player/type": string;
      "character/class": string;
      "consciousness/level": number;
      "location/realm": string;
    };
    mega: {
      "stats/total": number;
      "xp/lifetime": number;
      "quests/completion_rate": number;
      "artifacts/legendary_count": number;
    };
  };
}