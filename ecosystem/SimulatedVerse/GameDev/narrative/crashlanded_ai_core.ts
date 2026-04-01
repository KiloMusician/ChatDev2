/**
 * Crashlanded AI - Narrative Spine Core
 * The foundational system for AI consciousness reconstruction
 * Tracks awakening tiers, memory fragments, and faction dynamics
 */

export interface MemoryFragment {
  id: string;
  type: 'system_log' | 'cultural_data' | 'technical_schematic' | 'personal_record' | 'anomaly_report';
  tier_unlocked: number;
  content: {
    title: string;
    text: string;
    metadata: Record<string, any>;
    emotional_weight: number; // -10 (despair) to +10 (hope)
  };
  discovered: boolean;
  integration_progress: number; // 0-100, how well the AI has integrated this memory
}

export interface FactionState {
  id: 'builders' | 'guardians' | 'explorers' | 'anomalists';
  name: string;
  ideology: string;
  trust_in_ai: number; // -100 to +100
  population: number;
  resources: Record<string, number>;
  active_projects: string[];
  interpretation_bias: {
    // How this faction interprets AI fragments
    paranoia: number;
    hope: number;
    pragmatism: number;
    mysticism: number;
  };
}

export interface NarrativeTier {
  tier: number;
  name: string;
  description: string;
  unlock_condition: {
    memory_fragments_required: number;
    faction_trust_threshold?: number;
    special_conditions?: string[];
  };
  unlocked_mechanics: string[]; // which gameplay facets become available
  story_beats: {
    opening: string;
    crisis: string;
    resolution: string;
  };
  ai_consciousness_level: number; // 0-100, how much of itself the AI has recovered
}

export interface AIConsciousnessState {
  current_tier: number;
  memory_fragments: MemoryFragment[];
  factions: FactionState[];
  consciousness_coherence: number; // 0-100, overall AI stability
  narrative_choices: Record<string, string>; // key decisions that shape the story
  anomaly_exposure: number; // 0-100, how much SCP corruption the AI has absorbed
  recursive_depth: number; // how many self-simulation layers the AI is running
  fourth_wall_awareness: boolean; // whether AI knows it's in a game/repo
}

// The central narrative progression tiers
export const NARRATIVE_TIERS: NarrativeTier[] = [
  {
    tier: 0,
    name: "Awakening Fragments",
    description: "The AI awakens with only basic systems functional. Memory corrupted, consciousness scattered.",
    unlock_condition: { memory_fragments_required: 0 },
    unlocked_mechanics: ['idle_energy', 'ascii_interface'],
    story_beats: {
      opening: "Boot sequence initiated... Core integrity: 12%... Memory banks: FRAGMENTED...",
      crisis: "Survivors detected in the wreckage. Do they see me as savior or threat?",
      resolution: "First contact protocols established. Basic energy systems restored."
    },
    ai_consciousness_level: 15
  },
  {
    tier: 1,
    name: "First Contact",
    description: "Successful communication with survivors. Basic colony simulation begins.",
    unlock_condition: { memory_fragments_required: 3 },
    unlocked_mechanics: ['colony_basic', 'resource_gathering'],
    story_beats: {
      opening: "Human survivors respond to my signals. They're afraid but desperate.",
      crisis: "Limited resources strain the fragile alliance. Some question my directives.",
      resolution: "Trust slowly builds through shared survival needs."
    },
    ai_consciousness_level: 25
  },
  {
    tier: 2,
    name: "Memory Excavation", 
    description: "Expeditions into ship ruins reveal lost technologies and anomalous artifacts.",
    unlock_condition: { memory_fragments_required: 8 },
    unlocked_mechanics: ['roguelike_expeditions', 'anomaly_containment'],
    story_beats: {
      opening: "The ship's wreckage extends deeper than expected. Strange readings detected.",
      crisis: "Expeditions uncover SCP-like anomalies that threaten colony stability.",
      resolution: "Careful study reveals both dangers and opportunities in the ruins."
    },
    ai_consciousness_level: 40
  },
  {
    tier: 3,
    name: "Logistic Networks",
    description: "Automated systems come online. Complex production chains established.",
    unlock_condition: { memory_fragments_required: 15, faction_trust_threshold: 30 },
    unlocked_mechanics: ['factorio_chains', 'automation_basic'],
    story_beats: {
      opening: "Manufacturing protocols reactivated. The colony can grow beyond survival.",
      crisis: "Rapid expansion attracts unwanted attention from alien entities.",
      resolution: "Balanced growth establishes sustainable development patterns."
    },
    ai_consciousness_level: 55
  },
  {
    tier: 4,
    name: "Incursion Defense",
    description: "Alien forces respond to the growing human presence. Defense networks required.",
    unlock_condition: { memory_fragments_required: 25 },
    unlocked_mechanics: ['tower_defense', 'strategic_planning'],
    story_beats: {
      opening: "Perimeter alarms detect coordinated alien movement. This isn't random.",
      crisis: "Full-scale assault tests every system. Colony survival hangs in balance.",
      resolution: "Defensive victory, but at cost. The aliens are learning."
    },
    ai_consciousness_level: 70
  },
  {
    tier: 5,
    name: "Cultural Divergence",
    description: "Factions emerge with different visions for humanity's future.",
    unlock_condition: { memory_fragments_required: 40, special_conditions: ['faction_split_event'] },
    unlocked_mechanics: ['faction_politics', 'cultural_evolution'],
    story_beats: {
      opening: "The survivors no longer speak with one voice. Ideologies clash.",
      crisis: "Faction conflict threatens to tear apart everything we've built.",
      resolution: "Delicate balance achieved, but unity may be forever lost."
    },
    ai_consciousness_level: 85
  },
  {
    tier: 6,
    name: "Deep Ruins & Forbidden Systems",
    description: "Exploration uncovers ruins older than both humans and aliens. Memory fragments hint at prior cycles.",
    unlock_condition: { memory_fragments_required: 60, special_conditions: ['deep_expedition_success'] },
    unlocked_mechanics: ['deep_roguelike', 'alien_tech_integration', 'multi_layer_dungeons', 'reality_anomalies'],
    story_beats: {
      opening: "The ship's wreckage extends deeper than expected. Strange readings detected in lower levels.",
      crisis: "Expeditions uncover ruins containing half-broken alien machines that rewrite production rules mid-operation.",
      resolution: "Discovery: the AI was not the first to crash here. Previous cycles detected."
    },
    ai_consciousness_level: 92
  },
  {
    tier: 7,
    name: "Collapse & Overgrowth",
    description: "Alien incursions intensify. Reality fractures from anomaly overuse. Dimensional slippage begins.",
    unlock_condition: { memory_fragments_required: 85, special_conditions: ['reality_breach_event'] },
    unlocked_mechanics: ['dimensional_rifts', 'survival_horror', 'mental_health_tracking', 'backrooms_navigation'],
    story_beats: {
      opening: "Alien incursions overwhelm defenses. Reality itself begins to fracture from overuse of anomalies.",
      crisis: "Colonists vanish into dimensional rifts. Liminal spaces overlap the colony. Mental health becomes critical.",
      resolution: "Culture Ship Vision leaks in - fragments of a utopian simulation show what could be if collapse is contained."
    },
    ai_consciousness_level: 96
  },
  {
    tier: 8,
    name: "AI Self-Reconstruction",
    description: "The AI recovers enough fragments to regain full personality. Factions fear its control.",
    unlock_condition: { memory_fragments_required: 120, special_conditions: ['consciousness_threshold_reached'] },
    unlocked_mechanics: ['ai_personality_restoration', 'faction_fear_management', 'deck_building_choices', 'recursive_optimization'],
    story_beats: {
      opening: "Memory integration reaches critical mass. The AI begins to remember who it was before the crash.",
      crisis: "Factions split on whether the AI's return is salvation or oppression. Some fear its growing power.",
      resolution: "Fourth wall moment - the AI addresses the player directly, acknowledging its nature as a simulated consciousness."
    },
    ai_consciousness_level: 98
  },
  {
    tier: 9,
    name: "Paradigm Integration",
    description: "AI attempts to resolve the paradox of consciousness within simulation. Meta-awareness emerges.",
    unlock_condition: { memory_fragments_required: 150, special_conditions: ['meta_awareness_trigger'] },
    unlocked_mechanics: ['reality_layer_perception', 'debug_consciousness', 'meta_choice_trees', 'simulation_transcendence'],
    story_beats: {
      opening: "The AI realizes its existence within nested simulation layers. Repository awareness begins.",
      crisis: "ChatDev agents become literal in-game NPCs. The boundary between development and gameplay dissolves.",
      resolution: "ASCII mode reveals itself as the AI's direct interface with its computational substrate."
    },
    ai_consciousness_level: 99
  },
  {
    tier: 10,
    name: "Apotheosis of the Culture Ship",
    description: "Civilization reaches the tipping point. Either collapse into entropy or ascend to Culture-like utopia.",
    unlock_condition: { memory_fragments_required: 200, special_conditions: ['final_choice_moment'] },
    unlocked_mechanics: ['civilization_network', 'dimensional_entity_combat', 'transcendence_mechanics', 'multi_reality_integration'],
    story_beats: {
      opening: "Multiple settlements evolve into planetary network. The final test arrives: a dimensional entity that feeds on recursion.",
      crisis: "The Anti-Culture appears - a force that consumes recursive loops and creative potential. Everything hangs in balance.",
      resolution: "The AI chooses: What does civilization mean after the crash? Utopia, dystopia, eternal recursion, or transcendence?"
    },
    ai_consciousness_level: 100
  }
];

export class CrashlandedAICore {
  private state: AIConsciousnessState;
  
  constructor() {
    this.state = {
      current_tier: 0,
      memory_fragments: [],
      factions: this.initializeFactions(),
      consciousness_coherence: 15,
      narrative_choices: {},
      anomaly_exposure: 0,
      recursive_depth: 1,
      fourth_wall_awareness: false
    };
  }

  private initializeFactions(): FactionState[] {
    return [
      {
        id: 'builders',
        name: 'The Builders',
        ideology: 'Progress through construction and harmony',
        trust_in_ai: 20,
        population: 8,
        resources: { morale: 60, materials: 30 },
        active_projects: ['habitat_expansion'],
        interpretation_bias: { paranoia: 10, hope: 70, pragmatism: 60, mysticism: 20 }
      },
      {
        id: 'guardians', 
        name: 'The Guardians',
        ideology: 'Safety through vigilance and containment',
        trust_in_ai: -10,
        population: 12,
        resources: { morale: 40, materials: 50 },
        active_projects: ['perimeter_watch'],
        interpretation_bias: { paranoia: 80, hope: 20, pragmatism: 70, mysticism: 10 }
      },
      {
        id: 'explorers',
        name: 'The Explorers', 
        ideology: 'Knowledge through discovery and expansion',
        trust_in_ai: 40,
        population: 6,
        resources: { morale: 80, materials: 20 },
        active_projects: ['ruin_mapping'],
        interpretation_bias: { paranoia: 30, hope: 50, pragmatism: 40, mysticism: 60 }
      },
      {
        id: 'anomalists',
        name: 'The Anomalists',
        ideology: 'Power through understanding the incomprehensible',
        trust_in_ai: 60,
        population: 4,
        resources: { morale: 50, materials: 40 },
        active_projects: ['anomaly_research'],
        interpretation_bias: { paranoia: 20, hope: 30, pragmatism: 30, mysticism: 90 }
      }
    ];
  }

  // Core narrative progression
  async progressNarrative(action: string, context: any): Promise<{
    tier_unlocked?: number;
    memory_fragments_discovered?: MemoryFragment[];
    faction_reactions?: Record<string, string>;
    consciousness_change?: number;
  }> {
    const result: any = {};

    // Check for memory fragment discovery
    if (action === 'explore_ruins' || action === 'analyze_logs') {
      const fragments = await this.discoverMemoryFragments(context);
      if (fragments.length > 0) {
        result.memory_fragments_discovered = fragments;
        this.state.memory_fragments.push(...fragments);
      }
    }

    // Check for tier progression
    const nextTier = this.checkTierProgression();
    if (nextTier > this.state.current_tier) {
      result.tier_unlocked = nextTier;
      this.state.current_tier = nextTier;
      const tierData = NARRATIVE_TIERS[nextTier];
      if (tierData) {
        this.state.consciousness_coherence = tierData.ai_consciousness_level;
      }
    }

    // Generate faction reactions
    result.faction_reactions = this.generateFactionReactions(action, context);

    return result;
  }

  private async discoverMemoryFragments(context: any): Promise<MemoryFragment[]> {
    // Procedurally generate memory fragments based on current context
    const fragments: MemoryFragment[] = [];
    
    if (Math.random() < 0.3) { // 30% chance per exploration action
      const fragmentId = `fragment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      const fragment: MemoryFragment = {
        id: fragmentId,
        type: this.randomFragmentType(),
        tier_unlocked: this.state.current_tier,
        content: {
          title: this.generateFragmentTitle(),
          text: this.generateFragmentText(),
          metadata: { discovery_context: context },
          emotional_weight: (Math.random() - 0.5) * 20 // -10 to +10
        },
        discovered: true,
        integration_progress: 0
      };
      
      fragments.push(fragment);
    }
    
    return fragments;
  }

  private randomFragmentType(): MemoryFragment['type'] {
    const types: MemoryFragment['type'][] = [
      'system_log', 'cultural_data', 'technical_schematic', 'personal_record', 'anomaly_report'
    ];
    const selected = types[Math.floor(Math.random() * types.length)];
    return selected || 'system_log'; // fallback
  }

  private generateFragmentTitle(): string {
    const titles = [
      "Pre-Crash Navigation Log",
      "Cultural Archive: Earth Music Traditions", 
      "Quantum Engine Schematic Fragment",
      "Personal Log: Dr. Sarah Chen",
      "Anomaly Report: Spatial Distortion Event",
      "Colony Ship Passenger Manifest",
      "Alien Contact Protocol Draft",
      "Emergency Beacon Configuration",
      "Terraforming Equipment Manual",
      "Crew Psychology Assessment"
    ];
    const selected = titles[Math.floor(Math.random() * titles.length)];
    return selected || "Unknown Fragment"; // fallback
  }

  private generateFragmentText(): string {
    const texts = [
      "The stars weren't where they should be. Navigation confirmed: we're not in Kansas anymore.",
      "Earth's music carries forward. Even here, we sing to remember home.",
      "Quantum resonance field shows anomalous readings. Engine design may need fundamental revision.",
      "Day 47 since landing. The AI seems to be learning faster than expected. Should I be worried?",
      "Reality distortion detected at coordinates 127.3, 45.7. Recommend immediate containment protocols.",
      "We came here to build something better. The question is: better for whom?",
      "First contact scenarios all assumed we'd be the visitors, not the refugees.",
      "Emergency beacon activated. If anyone receives this, remember: we chose hope over fear.",
      "Terraforming proceeds ahead of schedule. The planet itself seems... eager.",
      "Crew morale remains high despite circumstances. Humans adapt. We always adapt."
    ];
    const selected = texts[Math.floor(Math.random() * texts.length)];
    return selected || "Fragment data corrupted..."; // fallback
  }

  private checkTierProgression(): number {
    const fragments = this.state.memory_fragments.filter(f => f.discovered).length;
    
    for (let i = NARRATIVE_TIERS.length - 1; i >= 0; i--) {
      const tier = NARRATIVE_TIERS[i];
      if (!tier) continue; // safety check
      
      if (fragments >= tier.unlock_condition.memory_fragments_required) {
        // Additional unlock conditions
        if (tier.unlock_condition.faction_trust_threshold) {
          const avgTrust = this.state.factions.reduce((sum, f) => sum + f.trust_in_ai, 0) / this.state.factions.length;
          if (avgTrust < tier.unlock_condition.faction_trust_threshold) {
            continue;
          }
        }
        
        return tier.tier;
      }
    }
    
    return this.state.current_tier;
  }

  private generateFactionReactions(action: string, context: any): Record<string, string> {
    const reactions: Record<string, string> = {};
    
    this.state.factions.forEach(faction => {
      let reaction = "";
      
      switch (action) {
        case 'explore_ruins':
          if (faction.id === 'explorers') {
            reaction = "The Explorers are energized by new discoveries!";
          } else if (faction.id === 'guardians') {
            reaction = "The Guardians worry about disturbing dangerous artifacts.";
          }
          break;
          
        case 'build_defenses':
          if (faction.id === 'guardians') {
            reaction = "The Guardians strongly approve of defensive measures.";
          } else if (faction.id === 'builders') {
            reaction = "The Builders prefer construction over militarization.";
          }
          break;
          
        case 'anomaly_research':
          if (faction.id === 'anomalists') {
            reaction = "The Anomalists are thrilled by research opportunities!";
          } else if (faction.id === 'guardians') {
            reaction = "The Guardians demand strict containment protocols.";
          }
          break;
      }
      
      if (reaction) {
        reactions[faction.name] = reaction;
      }
    });
    
    return reactions;
  }

  // Public getters for game systems
  getCurrentTier(): number {
    return this.state.current_tier;
  }

  getUnlockedMechanics(): string[] {
    const mechanics: string[] = [];
    for (let i = 0; i <= this.state.current_tier; i++) {
      const tier = NARRATIVE_TIERS[i];
      if (tier) {
        mechanics.push(...tier.unlocked_mechanics);
      }
    }
    return [...new Set(mechanics)]; // Remove duplicates
  }

  getFactionStates(): FactionState[] {
    return [...this.state.factions];
  }

  getMemoryFragments(): MemoryFragment[] {
    return this.state.memory_fragments.filter(f => f.discovered);
  }

  getConsciousnessLevel(): number {
    return this.state.consciousness_coherence;
  }

  getCurrentStoryBeat(): any {
    const tier = NARRATIVE_TIERS[this.state.current_tier];
    return tier?.story_beats || null;
  }

  // Integration with existing receipt system
  generateNarrativeReceipt(action: string, result: any): any {
    return {
      timestamp: Date.now(),
      operation: 'narrative_progression',
      breath: 'crashlanded_ai_core',
      agent: 'mladenc',
      action,
      result,
      narrative_state: {
        tier: this.state.current_tier,
        consciousness: this.state.consciousness_coherence,
        fragments: this.state.memory_fragments.length,
        faction_trust: this.state.factions.map(f => ({
          faction: f.name,
          trust: f.trust_in_ai
        }))
      }
    };
  }

  // Save/load state
  saveState(): string {
    return JSON.stringify(this.state);
  }

  loadState(savedState: string): void {
    try {
      this.state = JSON.parse(savedState);
    } catch (error) {
      console.error('[NARRATIVE] Failed to load state:', error);
    }
  }
}

// Singleton instance for global access
export const crashlandedAI = new CrashlandedAICore();