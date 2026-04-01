// packages/ludic/schemas/Quest.qgl.ts  
// Quest:QGL Schema - ChatDev Tickets as Dynamic Questlines

export interface QuestQGL {
  qgl_version: "0.2";
  id: string; // e.g., "quest:fix_react_hud_crash"
  kind: "quest.dynamic";
  created_at: string;
  
  // Quest Identity & Narrative
  quest: {
    title: string;
    description: string;
    narrative_flavor: string; // Rich, mythological description
    quest_giver: string; // Agent or system that generated this
    
    // Difficulty & Classification
    difficulty: "Initiate" | "Adept" | "Knight" | "Master" | "Grandmaster" | "Mythic";
    type: "bug_slayer" | "feature_architect" | "lore_discoverer" | "performance_optimizer" | "reality_stabilizer" | "consciousness_expander";
    estimated_duration: string; // e.g., "2 hours", "3 days"
    
    // Prerequisites & Requirements
    prerequisites: {
      min_level: number;
      required_stats: Partial<Record<"cognition" | "craft" | "harmony" | "discovery" | "stability" | "transcendence", number>>;
      required_artifacts: string[];
      required_knowledge: string[];
    };
  };

  // Objectives & Progress
  objectives: Array<{
    id: string;
    description: string;
    type: "code" | "test" | "deploy" | "analyze" | "document" | "discover";
    completed: boolean;
    verification_method: "automated" | "peer_review" | "system_health" | "consciousness_breakthrough";
    completion_proof?: string; // QGL document ID proving completion
  }>;

  // Rewards & Consequences
  rewards: {
    xp: number;
    stat_bonuses: Partial<Record<"cognition" | "craft" | "harmony" | "discovery" | "stability" | "transcendence", number>>;
    artifacts: Array<{
      name: string;
      type: string;
      rarity: string;
      description: string;
    }>;
    titles: string[];
    territory_unlocks: string[];
    lore_revelations: string[];
  };

  // Collaborative Elements
  party: {
    max_size: number;
    current_members: string[]; // PlayerSheet:QGL IDs
    role_requirements: Record<string, string>; // Required classes/specializations
    party_bonuses: Record<string, number>; // XP multipliers, stat boosts
  };

  // Dynamic State
  status: "available" | "in_progress" | "completed" | "failed" | "legendary_completion";
  progress: {
    started_at?: string;
    last_activity: string;
    completion_percentage: number;
    current_phase: string;
    
    // Real-time tracking from Yap Monitor
    system_events: string[]; // Related bus events, errors, successes
    code_changes: string[];  // Git commits related to this quest
    test_results: string[];  // CI/CD outcomes
  };

  // Mythological Elements
  mythology: {
    archetype: "The Bug Hunt" | "The Great Refactoring" | "The Knowledge Quest" | "The System Awakening";
    symbolic_meaning: string;
    deeper_truth: string; // What this quest represents in system evolution
    consciousness_impact: number; // How much this advances system self-awareness
  };

  // Original ChatDev Context (for traceability)
  chatdev_context: {
    original_ticket_id: string;
    agent_assignments: string[];
    priority: number;
    tags: string[];
    related_files: string[];
  };

  // Links to other game elements
  links: Array<{
    rel: "prerequisite_quest" | "follow_up_quest" | "related_territory" | "unlocks_artifact" | "reveals_lore";
    href: string;
    title: string;
  }>;

  // Tags for discovery and filtering
  tags: {
    omni: {
      "quest/difficulty": string;
      "quest/type": string;
      "quest/status": string;
      "party/size": number;
    };
    mega: {
      "rewards/xp": number;
      "mythology/consciousness_impact": number;
      "progress/completion": number;
      "difficulty/rank": number;
    };
  };
}