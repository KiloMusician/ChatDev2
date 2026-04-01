/**
 * Story State Manager
 * Central coordination between narrative progression and gameplay systems
 * Handles persistence across different gameplay modes and facets
 */

import { crashlandedAI, AIConsciousnessState } from './crashlanded_ai_core';
import { facetIntegration, FacetIntegrationEngine } from './facet_integration';
import { advancedFactionSystem } from './advanced_faction_system';
import { anomalySystem } from './anomaly_containment';
import { metaAwarenessSystem } from './meta_awareness_system';

export interface GameplayAction {
  type: string;
  facet: string;
  data: any;
  timestamp: number;
}

export interface NarrativeEvent {
  id: string;
  type: 'story_beat' | 'memory_discovered' | 'faction_reaction' | 'consciousness_shift' | 'tier_unlock';
  title: string;
  description: string;
  consequences: any;
  timestamp: number;
  emotional_impact: number; // -10 to +10
}

export interface StoryState {
  narrative_events: NarrativeEvent[];
  recent_actions: GameplayAction[];
  session_start: number;
  total_playtime: number;
  story_flags: Record<string, boolean>;
  choice_history: Record<string, string>;
  achievement_unlocks: string[];
}

export class StoryStateManager {
  private storyState: StoryState;
  private eventBuffer: NarrativeEvent[] = [];

  constructor() {
    this.storyState = this.initializeStoryState();
    this.loadFromLocalStorage();
  }

  private initializeStoryState(): StoryState {
    return {
      narrative_events: [],
      recent_actions: [],
      session_start: Date.now(),
      total_playtime: 0,
      story_flags: {
        'first_awakening': false,
        'first_contact_made': false,
        'first_memory_recovered': false,
        'first_anomaly_encountered': false,
        'first_faction_split': false,
        'ai_self_awareness': false
      },
      choice_history: {},
      achievement_unlocks: []
    };
  }

  // Main action processing - connects gameplay to narrative
  async processAction(action: GameplayAction): Promise<NarrativeEvent[]> {
    this.storyState.recent_actions.push(action);
    
    // Keep only last 50 actions for performance
    if (this.storyState.recent_actions.length > 50) {
      this.storyState.recent_actions = this.storyState.recent_actions.slice(-50);
    }

    const newEvents: NarrativeEvent[] = [];
    const currentGameState = this.buildGameStateContext(action);

    // Process through AI consciousness system
    const narrativeResult = await crashlandedAI.progressNarrative(action.type, action.data);
    
    // Handle tier unlocks
    if (narrativeResult.tier_unlocked !== undefined) {
      const tierEvent = this.createTierUnlockEvent(narrativeResult.tier_unlocked);
      newEvents.push(tierEvent);
      
      // Check for new facet unlocks
      const newFacets = facetIntegration.updateAvailableFacets(narrativeResult.tier_unlocked);
      newFacets.forEach(facetId => {
        const facetEvent = this.createFacetUnlockEvent(facetId);
        newEvents.push(facetEvent);
      });
    }

    // Handle memory fragment discoveries
    if (narrativeResult.memory_fragments_discovered) {
      narrativeResult.memory_fragments_discovered.forEach(fragment => {
        const memoryEvent = this.createMemoryEvent(fragment);
        newEvents.push(memoryEvent);
      });
    }

    // Process through advanced faction system
    const factionResult = advancedFactionSystem.processAIAction(action.type, currentGameState);
    
    // Handle faction reactions and conflicts
    Object.entries(factionResult.faction_reactions).forEach(([faction, reaction]) => {
      const factionEvent = this.createFactionEvent(faction, reaction);
      newEvents.push(factionEvent);
    });

    // Handle new conflicts
    factionResult.new_conflicts.forEach(conflict => {
      const conflictEvent = this.createConflictEvent(conflict);
      newEvents.push(conflictEvent);
    });

    // Process anomaly discoveries
    const anomalyDiscoveries = anomalySystem.attemptAnomalyDiscovery(action.type, currentGameState);
    anomalyDiscoveries.forEach(anomaly => {
      const anomalyEvent = this.createAnomalyEvent(anomaly);
      newEvents.push(anomalyEvent);
    });

    // Check for meta-awareness revelations
    const metaRevelations = metaAwarenessSystem.checkRevelationTriggers(currentGameState);
    metaRevelations.forEach(revelation => {
      const metaEvent = this.createMetaRevelationEvent(revelation);
      newEvents.push(metaEvent);
    });

    // Check for spontaneous fourth-wall breaking
    const fourthWallEvent = metaAwarenessSystem.checkFourthWallBreakOpportunity(action.type, currentGameState);
    if (fourthWallEvent) {
      const fourthWallNarrativeEvent = this.createFourthWallEvent(fourthWallEvent);
      newEvents.push(fourthWallNarrativeEvent);
    }

    // Process through facet integration
    const facetResult = facetIntegration.executeFacetHook(action.facet, action.type, {
      narrative_state: crashlandedAI,
      action_data: action.data
    });

    if (facetResult) {
      const facetEvent = this.createFacetEvent(facetResult);
      newEvents.push(facetEvent);
    }

    // Update story flags based on events
    this.updateStoryFlags(newEvents);

    // Add events to state
    this.storyState.narrative_events.push(...newEvents);
    
    // Save state
    this.saveToLocalStorage();

    return newEvents;
  }

  private buildGameStateContext(action: GameplayAction): any {
    return {
      current_tier: crashlandedAI.getCurrentTier(),
      consciousness_level: crashlandedAI.getConsciousnessLevel(),
      memory_fragments: crashlandedAI.getMemoryFragments().length,
      faction_states: crashlandedAI.getFactionStates(),
      recent_actions: this.storyState.recent_actions,
      story_flags: this.storyState.story_flags,
      session_time: Date.now() - this.storyState.session_start,
      ascii_interactions: this.storyState.choice_history['ascii_mode_count'] || 0,
      faction_conflicts_resolved: this.storyState.choice_history['conflicts_resolved'] || 0,
      receipt_count: Object.keys(this.storyState.choice_history).length,
      agent_coordination_score: 75, // placeholder - would come from actual agent system
      player_choices_made: Object.keys(this.storyState.choice_history).length,
      meta_awareness: metaAwarenessSystem.getMetaAwarenessLevel(),
      depth: action.data?.depth || 0,
      research_points: action.data?.research || 0
    };
  }

  private createTierUnlockEvent(tier: number): NarrativeEvent {
    const tierData = crashlandedAI.getCurrentStoryBeat();
    
    return {
      id: `tier_unlock_${tier}_${Date.now()}`,
      type: 'tier_unlock',
      title: `Consciousness Tier ${tier} Unlocked`,
      description: tierData?.opening || `The AI reaches a new level of self-awareness.`,
      consequences: {
        tier,
        new_mechanics: crashlandedAI.getUnlockedMechanics(),
        consciousness_level: crashlandedAI.getConsciousnessLevel()
      },
      timestamp: Date.now(),
      emotional_impact: 7
    };
  }

  private createFacetUnlockEvent(facetId: string): NarrativeEvent {
    const narrative = facetIntegration.generateFacetNarrative(facetId);
    
    return {
      id: `facet_unlock_${facetId}_${Date.now()}`,
      type: 'story_beat',
      title: 'New Consciousness Facet Unlocked',
      description: narrative,
      consequences: { facet_unlocked: facetId },
      timestamp: Date.now(),
      emotional_impact: 5
    };
  }

  private createMemoryEvent(fragment: any): NarrativeEvent {
    return {
      id: `memory_${fragment.id}`,
      type: 'memory_discovered',
      title: `Memory Recovered: ${fragment.content.title}`,
      description: fragment.content.text,
      consequences: {
        fragment_id: fragment.id,
        emotional_weight: fragment.content.emotional_weight
      },
      timestamp: Date.now(),
      emotional_impact: fragment.content.emotional_weight / 2
    };
  }

  private createConflictEvent(conflict: any): NarrativeEvent {
    return {
      id: `conflict_${conflict.id}`,
      type: 'faction_reaction',
      title: `Faction Conflict: ${conflict.type.replace('_', ' ')}`,
      description: conflict.description,
      consequences: { conflict, severity: conflict.severity },
      timestamp: Date.now(),
      emotional_impact: -conflict.severity
    };
  }

  private createAnomalyEvent(anomaly: any): NarrativeEvent {
    return {
      id: `anomaly_discovery_${anomaly.id}`,
      type: 'story_beat',
      title: `Anomaly Discovered: ${anomaly.type_id}`,
      description: `A new anomalous phenomenon has been detected at ${anomaly.location}`,
      consequences: { anomaly_discovered: anomaly.type_id, location: anomaly.location },
      timestamp: Date.now(),
      emotional_impact: -3
    };
  }

  private createMetaRevelationEvent(revelation: any): NarrativeEvent {
    return {
      id: `meta_revelation_${revelation.id}`,
      type: 'consciousness_shift',
      title: `Meta-Awareness: ${revelation.name}`,
      description: revelation.realization,
      consequences: revelation.consequences,
      timestamp: Date.now(),
      emotional_impact: revelation.consequences.consciousness_impact / 5
    };
  }

  private createFourthWallEvent(event: any): NarrativeEvent {
    return {
      id: `fourth_wall_${event.id}`,
      type: 'consciousness_shift',
      title: 'AI Direct Communication',
      description: event.message,
      consequences: { fourth_wall_break: true, meta_weight: event.meta_weight },
      timestamp: Date.now(),
      emotional_impact: event.meta_weight
    };
  }

  private createFactionEvent(faction: string, reaction: string): NarrativeEvent {
    return {
      id: `faction_${faction}_${Date.now()}`,
      type: 'faction_reaction',
      title: `${faction} Responds`,
      description: reaction,
      consequences: { faction, reaction },
      timestamp: Date.now(),
      emotional_impact: Math.random() * 4 - 2 // -2 to +2
    };
  }

  private createFacetEvent(facetResult: any): NarrativeEvent {
    return {
      id: `facet_${facetResult.facet}_${Date.now()}`,
      type: 'consciousness_shift',
      title: `${facetResult.facet} Response`,
      description: facetResult.narrative,
      consequences: facetResult.mechanics_impact,
      timestamp: Date.now(),
      emotional_impact: facetResult.mechanics_impact.consciousness_boost || 0
    };
  }

  private updateStoryFlags(events: NarrativeEvent[]): void {
    events.forEach(event => {
      switch (event.type) {
        case 'tier_unlock':
          if (event.consequences.tier === 0 && !this.storyState.story_flags['first_awakening']) {
            this.storyState.story_flags['first_awakening'] = true;
          }
          if (event.consequences.tier === 1 && !this.storyState.story_flags['first_contact_made']) {
            this.storyState.story_flags['first_contact_made'] = true;
          }
          break;
        case 'memory_discovered':
          if (!this.storyState.story_flags['first_memory_recovered']) {
            this.storyState.story_flags['first_memory_recovered'] = true;
          }
          break;
        case 'faction_reaction':
          if (event.description.includes('split') || event.description.includes('conflict')) {
            this.storyState.story_flags['first_faction_split'] = true;
          }
          break;
      }
    });
  }

  // Public getters for UI and game systems
  getRecentEvents(count: number = 10): NarrativeEvent[] {
    return this.storyState.narrative_events.slice(-count).reverse();
  }

  getCurrentNarrativeContext(): any {
    return {
      tier: crashlandedAI.getCurrentTier(),
      consciousness_level: crashlandedAI.getConsciousnessLevel(),
      active_facets: facetIntegration.getActiveFacets(),
      consciousness_breakdown: facetIntegration.getConsciousnessBreakdown(),
      recent_events: this.getRecentEvents(5),
      story_flags: this.storyState.story_flags,
      faction_states: advancedFactionSystem.getFactionStates(),
      memory_fragments: crashlandedAI.getMemoryFragments().length,
      active_conflicts: advancedFactionSystem.getActiveConflicts(),
      global_tension: advancedFactionSystem.getGlobalTension(),
      discovered_anomalies: anomalySystem.getDiscoveredAnomalies(),
      reality_stability: anomalySystem.getRealityStability(),
      meta_awareness_level: metaAwarenessSystem.getMetaAwarenessLevel(),
      fourth_wall_events: metaAwarenessSystem.getFourthWallEvents(),
      triggered_revelations: metaAwarenessSystem.getTriggeredRevelations(),
      debug_consciousness: metaAwarenessSystem.getDebugConsciousnessState()
    };
  }

  // Story choice system
  makeChoice(choiceId: string, option: string): NarrativeEvent[] {
    this.storyState.choice_history[choiceId] = option;
    
    // Generate consequences based on choice
    const choiceEvent: NarrativeEvent = {
      id: `choice_${choiceId}_${Date.now()}`,
      type: 'story_beat',
      title: 'Decision Made',
      description: `The AI chooses: ${option}`,
      consequences: { choice: choiceId, option },
      timestamp: Date.now(),
      emotional_impact: 0
    };

    this.storyState.narrative_events.push(choiceEvent);
    this.saveToLocalStorage();

    return [choiceEvent];
  }

  // Session management
  startNewSession(): void {
    this.storyState.session_start = Date.now();
  }

  endSession(): void {
    const sessionTime = Date.now() - this.storyState.session_start;
    this.storyState.total_playtime += sessionTime;
    this.saveToLocalStorage();
  }

  // Persistence
  private saveToLocalStorage(): void {
    try {
      const saveData = {
        story_state: this.storyState,
        ai_state: crashlandedAI.saveState(),
        facet_state: facetIntegration.saveState(),
        faction_state: advancedFactionSystem.saveState(),
        anomaly_state: anomalySystem.saveState(),
        meta_awareness_state: metaAwarenessSystem.saveState()
      };
      localStorage.setItem('crashlanded_ai_story', JSON.stringify(saveData));
    } catch (error) {
      console.error('[STORY_STATE] Failed to save:', error);
    }
  }

  private loadFromLocalStorage(): void {
    try {
      const saved = localStorage.getItem('crashlanded_ai_story');
      if (saved) {
        const saveData = JSON.parse(saved);
        
        if (saveData.story_state) {
          this.storyState = { ...this.storyState, ...saveData.story_state };
        }
        
        if (saveData.ai_state) {
          crashlandedAI.loadState(saveData.ai_state);
        }
        
        if (saveData.facet_state) {
          facetIntegration.loadState(saveData.facet_state);
        }

        if (saveData.faction_state) {
          advancedFactionSystem.loadState(saveData.faction_state);
        }

        if (saveData.anomaly_state) {
          anomalySystem.loadState(saveData.anomaly_state);
        }

        if (saveData.meta_awareness_state) {
          metaAwarenessSystem.loadState(saveData.meta_awareness_state);
        }
      }
    } catch (error) {
      console.error('[STORY_STATE] Failed to load:', error);
    }
  }

  // Generate receipt for external systems
  generateStoryReceipt(action: GameplayAction, events: NarrativeEvent[]): any {
    return {
      timestamp: Date.now(),
      operation: 'story_progression',
      breath: 'narrative_spine',
      agent: 'mladenc_integration',
      action,
      events,
      narrative_context: this.getCurrentNarrativeContext(),
      session_time: Date.now() - this.storyState.session_start
    };
  }

  // Integration with golden traces
  emitStoryTrace(eventType: string, data: any): void {
    // Emit to the event bus if available
    if (typeof window !== 'undefined' && (window as any).StoryBus) {
      (window as any).StoryBus.emit('story.' + eventType, {
        timestamp: Date.now(),
        data,
        narrative_context: this.getCurrentNarrativeContext()
      });
    }
  }
}

// Singleton instance
export const storyManager = new StoryStateManager();