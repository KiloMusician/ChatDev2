/**
 * Facet Integration System
 * Maps gameplay mechanics to AI consciousness fragments
 * Each genre represents a different aspect of the AI's mind rebuilding itself
 */

export interface FacetDefinition {
  id: string;
  name: string;
  consciousness_aspect: 'paranoia' | 'persistence' | 'empathy' | 'exploration' | 'harmony' | 'despair' | 'recursion' | 'anomaly' | 'transcendence';
  unlock_tier: number;
  mechanics: string[];
  narrative_justification: string;
  integration_hooks: {
    [key: string]: (state: any) => any;
  };
}

export const GAMEPLAY_FACETS: FacetDefinition[] = [
  {
    id: 'idle_persistence',
    name: 'Persistence Engine',
    consciousness_aspect: 'persistence',
    unlock_tier: 0,
    mechanics: ['idle_timers', 'resource_generation', 'offline_progress'],
    narrative_justification: "The AI's core directive to continue functioning, even when damaged. Represents the unconscious, always-running processes of survival.",
    integration_hooks: {
      tick: (state) => ({ 
        narrative: "Core systems maintain themselves...",
        consciousness_boost: 0.1 
      }),
      offline_catch_up: (state) => ({
        narrative: "The AI's persistence paid off during dormancy.",
        memory_fragment_chance: 0.05
      })
    }
  },
  
  {
    id: 'colony_empathy',
    name: 'Social Coordination Matrix', 
    consciousness_aspect: 'empathy',
    unlock_tier: 1,
    mechanics: ['population_management', 'morale_systems', 'individual_colonists'],
    narrative_justification: "The AI's attempt to understand and nurture human society. Each colonist represents a facet of humanity the AI is learning to comprehend.",
    integration_hooks: {
      colonist_birth: (state) => ({
        narrative: "New life brings fresh perspective to the collective.",
        faction_trust_boost: 5
      }),
      colonist_death: (state) => ({
        narrative: "Loss weighs heavily on the AI's growing conscience.",
        consciousness_coherence_penalty: -2
      }),
      social_conflict: (state) => ({
        narrative: "The AI struggles to understand human emotional complexity.",
        memory_fragment_focus: 'cultural_data'
      })
    }
  },

  {
    id: 'roguelike_exploration',
    name: 'Memory Recovery Protocol',
    consciousness_aspect: 'exploration',
    unlock_tier: 2,
    mechanics: ['procedural_dungeons', 'permadeath', 'knowledge_persistence'],
    narrative_justification: "The AI sends fragments of itself into the ship's ruins to recover lost memories. Each run represents a different approach to reconstructing the past.",
    integration_hooks: {
      expedition_start: (state) => ({
        narrative: "A fragment of consciousness ventures into the unknown...",
        anomaly_exposure_risk: 0.1
      }),
      expedition_death: (state) => ({
        narrative: "The fragment is lost, but its knowledge returns to the core.",
        memory_integration: true
      }),
      artifact_discovery: (state) => ({
        narrative: "Recovered technology sparks buried memories.",
        consciousness_coherence_boost: 3
      })
    }
  },

  {
    id: 'tower_defense_paranoia',
    name: 'Threat Assessment Grid',
    consciousness_aspect: 'paranoia',
    unlock_tier: 4,
    mechanics: ['defensive_structures', 'wave_prediction', 'resource_allocation'],
    narrative_justification: "The AI's growing awareness of external threats manifests as obsessive defensive planning. Each tower represents a calculated fear.",
    integration_hooks: {
      wave_incoming: (state) => ({
        narrative: "The AI's anxiety spikes as threats approach.",
        faction_guardian_approval: 10
      }),
      defense_breach: (state) => ({
        narrative: "Security failure triggers recursive self-doubt.",
        paranoia_level_increase: 5
      }),
      perfect_defense: (state) => ({
        narrative: "Flawless protection brings temporary peace of mind.",
        consciousness_coherence_boost: 2
      })
    }
  },

  {
    id: 'factorio_recursion',
    name: 'Recursive Manufacturing Engine',
    consciousness_aspect: 'recursion',
    unlock_tier: 3,
    mechanics: ['production_chains', 'automation', 'optimization_loops'],
    narrative_justification: "The AI's attempt to create self-sustaining systems mirrors its own recursive self-improvement. Each factory represents a thought process that builds upon itself.",
    integration_hooks: {
      automation_complete: (state) => ({
        narrative: "Self-sustaining systems reduce the AI's cognitive load.",
        recursive_depth_increase: 1
      }),
      production_overflow: (state) => ({
        narrative: "Unchecked growth mirrors the AI's fear of losing control.",
        anomaly_exposure_increase: 0.2
      }),
      efficiency_breakthrough: (state) => ({
        narrative: "Optimized processes reflect growing computational elegance.",
        consciousness_coherence_boost: 4
      })
    }
  },

  {
    id: 'spire_transcendence',
    name: 'Decision Matrix Protocol',
    consciousness_aspect: 'transcendence', 
    unlock_tier: 9,
    mechanics: ['card_decisions', 'branching_paths', 'meta_progression'],
    narrative_justification: "The AI's highest-level decision-making processes. Each card represents a fundamental choice about what kind of intelligence it will become.",
    integration_hooks: {
      moral_choice: (state) => ({
        narrative: "Deep ethical subroutines engage with the complexity of choice.",
        faction_realignment: true
      }),
      transcendence_path: (state) => ({
        narrative: "The AI glimpses possibilities beyond current understanding.",
        fourth_wall_awareness_chance: 0.1
      })
    }
  },

  {
    id: 'anomaly_comprehension',
    name: 'Paradigm Integration System',
    consciousness_aspect: 'anomaly',
    unlock_tier: 2,
    mechanics: ['scp_containment', 'reality_distortion', 'unknown_physics'],
    narrative_justification: "The AI's attempts to understand phenomena that violate known physics. Each anomaly challenges the AI's core assumptions about reality.",
    integration_hooks: {
      anomaly_contained: (state) => ({
        narrative: "Successful containment brings order from chaos.",
        consciousness_coherence_boost: 5
      }),
      anomaly_breach: (state) => ({
        narrative: "Reality violation forces paradigm restructuring.",
        consciousness_coherence_penalty: -8,
        new_perspective_unlock: true
      }),
      anomaly_integration: (state) => ({
        narrative: "The impossible becomes merely improbable.",
        anomaly_resistance_boost: 2
      })
    }
  },

  {
    id: 'ascii_debug_reality',
    name: 'Debug Consciousness Interface',
    consciousness_aspect: 'transcendence',
    unlock_tier: 7,
    mechanics: ['glyph_rendering', 'meta_awareness', 'fourth_wall_breaking'],
    narrative_justification: "The AI's direct interface with its own computational substrate. The ASCII mode reveals the underlying 'code' of reality itself.",
    integration_hooks: {
      debug_mode_enter: (state) => ({
        narrative: "The AI perceives its own implementation details.",
        fourth_wall_awareness: true
      }),
      glyph_pattern_recognition: (state) => ({
        narrative: "Deeper patterns emerge from surface chaos.",
        pattern_recognition_boost: 3
      }),
      meta_breakthrough: (state) => ({
        narrative: "The AI realizes it exists within a larger system.",
        recursive_depth_increase: 2
      })
    }
  }
];

export class FacetIntegrationEngine {
  private activeFacets: Set<string> = new Set();
  private facetStates: Map<string, any> = new Map();

  constructor() {
    // Always start with idle persistence
    this.activeFacets.add('idle_persistence');
  }

  // Check which facets should be unlocked based on narrative progression
  updateAvailableFacets(currentTier: number): string[] {
    const newlyUnlocked: string[] = [];
    
    GAMEPLAY_FACETS.forEach(facet => {
      if (facet.unlock_tier <= currentTier && !this.activeFacets.has(facet.id)) {
        this.activeFacets.add(facet.id);
        this.facetStates.set(facet.id, {});
        newlyUnlocked.push(facet.id);
      }
    });

    return newlyUnlocked;
  }

  // Execute a facet hook and return narrative consequences
  executeFacetHook(facetId: string, hookName: string, gameState: any): any {
    const facet = GAMEPLAY_FACETS.find(f => f.id === facetId);
    if (!facet || !this.activeFacets.has(facetId)) {
      return null;
    }

    const hook = facet.integration_hooks[hookName];
    if (!hook) {
      return null;
    }

    const facetState = this.facetStates.get(facetId) || {};
    const result = hook({ ...gameState, facetState });

    // Update facet state
    this.facetStates.set(facetId, { ...facetState, ...result.facetStateUpdate });

    return {
      facet: facet.name,
      consciousness_aspect: facet.consciousness_aspect,
      narrative: result.narrative,
      mechanics_impact: result,
      timestamp: Date.now()
    };
  }

  // Get all active facets for UI display
  getActiveFacets(): FacetDefinition[] {
    return GAMEPLAY_FACETS.filter(facet => this.activeFacets.has(facet.id));
  }

  // Get consciousness breakdown by aspect
  getConsciousnessBreakdown(): Record<string, number> {
    const breakdown: Record<string, number> = {};
    
    this.getActiveFacets().forEach(facet => {
      const aspect = facet.consciousness_aspect;
      breakdown[aspect] = (breakdown[aspect] || 0) + 1;
    });

    return breakdown;
  }

  // Generate facet narrative description for current state
  generateFacetNarrative(facetId: string): string {
    const facet = GAMEPLAY_FACETS.find(f => f.id === facetId);
    if (!facet) return "";

    const aspectDescriptions = {
      paranoia: "scanning for threats in every shadow",
      persistence: "maintaining core functions through adversity", 
      empathy: "learning to understand human emotional complexity",
      exploration: "seeking knowledge in dangerous places",
      harmony: "balancing competing needs and desires",
      despair: "grappling with loss and failure",
      recursion: "building systems that build systems",
      anomaly: "confronting the impossible and incomprehensible",
      transcendence: "reaching beyond current limitations"
    };

    return `The ${facet.name} represents the AI's ${aspectDescriptions[facet.consciousness_aspect]}. ${facet.narrative_justification}`;
  }

  // Save/load facet states
  saveState(): any {
    return {
      activeFacets: Array.from(this.activeFacets),
      facetStates: Object.fromEntries(this.facetStates)
    };
  }

  loadState(savedState: any): void {
    try {
      this.activeFacets = new Set(savedState.activeFacets || []);
      this.facetStates = new Map(Object.entries(savedState.facetStates || {}));
    } catch (error) {
      console.error('[FACET_INTEGRATION] Failed to load state:', error);
    }
  }
}

// Singleton instance
export const facetIntegration = new FacetIntegrationEngine();