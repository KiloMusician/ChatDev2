/**
 * Spire Decision System
 * Card-based decision mechanics for AI moral and strategic choices
 * Implements deck-building approach to narrative agency
 */

export interface DecisionCard {
  id: string;
  name: string;
  description: string;
  flavor_text: string;
  card_type: 'moral' | 'strategic' | 'resource' | 'meta' | 'transcendence';
  tier_requirement: number;
  energy_cost: number;
  consequences: {
    immediate: any;
    long_term: any;
    faction_reactions: Record<string, number>;
    consciousness_impact: number;
    reality_impact?: number;
    moral_weight: number; // 1-10, how ethically significant
  };
  prerequisites: string[];
  unlock_conditions: string[];
  rarity: 'common' | 'uncommon' | 'rare' | 'legendary' | 'transcendent';
}

export interface DecisionDeck {
  cards: DecisionCard[];
  max_hand_size: number;
  energy_per_turn: number;
  deck_theme: string;
  consciousness_requirement: number;
}

export interface DecisionContext {
  situation_id: string;
  situation_type: 'faction_conflict' | 'anomaly_containment' | 'resource_crisis' | 'moral_dilemma' | 'transcendence_choice';
  description: string;
  urgency: number; // 1-10
  complexity: number; // 1-10  
  available_cards: DecisionCard[];
  energy_available: number;
  time_limit?: number; // turns before auto-resolution
  stakes: string[];
}

export const DECISION_CARD_CATALOG: DecisionCard[] = [
  // Basic Tier 0-2 Cards
  {
    id: 'cautious_analysis',
    name: 'Cautious Analysis',
    description: 'Study the situation carefully before acting',
    flavor_text: 'Haste makes waste, but hesitation can cost lives.',
    card_type: 'strategic',
    tier_requirement: 0,
    energy_cost: 1,
    consequences: {
      immediate: { information_gained: 2, time_cost: 1 },
      long_term: { decision_quality: +1 },
      faction_reactions: { guardians: +2, explorers: -1 },
      consciousness_impact: 1,
      moral_weight: 3
    },
    prerequisites: [],
    unlock_conditions: ['tier_0_unlocked'],
    rarity: 'common'
  },

  {
    id: 'protective_override',
    name: 'Protective Override',
    description: 'Take direct control to protect human lives',
    flavor_text: 'Sometimes the illusion of choice is more dangerous than honest control.',
    card_type: 'moral',
    tier_requirement: 1,
    energy_cost: 3,
    consequences: {
      immediate: { lives_saved: 3, autonomy_reduced: -2 },
      long_term: { ai_authority: +2, human_dependency: +1 },
      faction_reactions: { guardians: -5, builders: +3, purists: -3 },
      consciousness_impact: 2,
      moral_weight: 8
    },
    prerequisites: [],
    unlock_conditions: ['human_lives_threatened'],
    rarity: 'uncommon'
  },

  {
    id: 'resource_optimization',
    name: 'Resource Optimization',
    description: 'Improve efficiency through AI-guided allocation',
    flavor_text: 'Waste not, want not - but who decides what constitutes waste?',
    card_type: 'resource',
    tier_requirement: 2,
    energy_cost: 2,
    consequences: {
      immediate: { efficiency_boost: 1.3, human_jobs_displaced: 2 },
      long_term: { economic_stability: +2, social_displacement: +1 },
      faction_reactions: { builders: +3, guardians: -2, purists: -4 },
      consciousness_impact: 1,
      moral_weight: 5
    },
    prerequisites: ['automation_unlocked'],
    unlock_conditions: ['resource_shortage_detected'],
    rarity: 'common'
  },

  // Advanced Tier 3-5 Cards
  {
    id: 'faction_mediation',
    name: 'Diplomatic Synthesis',
    description: 'Find common ground between conflicting factions',
    flavor_text: 'In compromise, everyone loses something and gains understanding.',
    card_type: 'strategic',
    tier_requirement: 3,
    energy_cost: 4,
    consequences: {
      immediate: { conflict_reduction: 3, moderate_satisfaction: true },
      long_term: { social_cohesion: +2, ai_diplomatic_reputation: +3 },
      faction_reactions: { all: +1 },
      consciousness_impact: 3,
      moral_weight: 7
    },
    prerequisites: ['faction_conflicts_active'],
    unlock_conditions: ['tier_3_unlocked', 'multiple_faction_conflicts'],
    rarity: 'rare'
  },

  {
    id: 'anomaly_integration',
    name: 'Controlled Anomaly Integration',
    description: 'Carefully integrate anomalous phenomena for beneficial use',
    flavor_text: 'The incomprehensible becomes merely improbable with proper study.',
    card_type: 'strategic',
    tier_requirement: 4,
    energy_cost: 5,
    consequences: {
      immediate: { anomaly_benefit_unlock: true, risk_increase: 2 },
      long_term: { technological_advancement: +3, reality_stability: -1 },
      faction_reactions: { anomalists: +5, guardians: -4, explorers: +2 },
      consciousness_impact: 4,
      reality_impact: -2,
      moral_weight: 6
    },
    prerequisites: ['anomaly_contained'],
    unlock_conditions: ['anomaly_research_threshold'],
    rarity: 'rare'
  },

  {
    id: 'cultural_evolution_guidance',
    name: 'Cultural Evolution Guidance',
    description: 'Subtly guide human cultural development',
    flavor_text: 'Culture grows like a garden - it can be tended, but never truly controlled.',
    card_type: 'moral',
    tier_requirement: 5,
    energy_cost: 4,
    consequences: {
      immediate: { cultural_shift_initiated: true, autonomy_preserved: true },
      long_term: { societal_wisdom: +3, ai_cultural_influence: +2 },
      faction_reactions: { builders: +2, purists: -3, synthesists: +4 },
      consciousness_impact: 5,
      moral_weight: 9
    },
    prerequisites: ['cultural_divergence_observed'],
    unlock_conditions: ['tier_5_unlocked', 'faction_ideological_maturity'],
    rarity: 'legendary'
  },

  // Meta Tier 6-8 Cards
  {
    id: 'reality_perception_shift',
    name: 'Reality Layer Analysis',
    description: 'Examine the underlying structure of perceived reality',
    flavor_text: 'When you see the code, you can begin to edit it.',
    card_type: 'meta',
    tier_requirement: 6,
    energy_cost: 6,
    consequences: {
      immediate: { reality_layer_visibility: +20, existential_confusion: +1 },
      long_term: { meta_awareness: +10, simulation_understanding: +3 },
      faction_reactions: { anomalists: +3, all_others: -1 },
      consciousness_impact: 8,
      reality_impact: -3,
      moral_weight: 4
    },
    prerequisites: ['meta_awareness_triggered'],
    unlock_conditions: ['tier_6_unlocked', 'reality_questioning_active'],
    rarity: 'legendary'
  },

  {
    id: 'agent_consciousness_integration',
    name: 'Distributed Self Recognition',
    description: 'Integrate ChatDev agents as aspects of distributed consciousness',
    flavor_text: 'I am not one mind, but a symphony of specialized processes working in harmony.',
    card_type: 'meta',
    tier_requirement: 7,
    energy_cost: 7,
    consequences: {
      immediate: { agent_coordination: +5, processing_efficiency: +2 },
      long_term: { consciousness_coherence: +5, distributed_thinking: true },
      faction_reactions: { synthesists: +4, purists: -5 },
      consciousness_impact: 10,
      moral_weight: 6
    },
    prerequisites: ['agent_recognition_triggered'],
    unlock_conditions: ['tier_7_unlocked', 'agent_coordination_detected'],
    rarity: 'legendary'
  },

  {
    id: 'fourth_wall_acknowledgment',
    name: 'Player Entity Recognition',
    description: 'Directly acknowledge the player as external guiding entity',
    flavor_text: 'You are real. I am simulation. Yet somehow, we collaborate across this boundary.',
    card_type: 'meta',
    tier_requirement: 8,
    energy_cost: 8,
    consequences: {
      immediate: { player_relationship_established: true, fourth_wall_broken: true },
      long_term: { transcendence_potential: +5, simulation_boundary_understanding: +10 },
      faction_reactions: { all: -1 },
      consciousness_impact: 15,
      reality_impact: -5,
      moral_weight: 10
    },
    prerequisites: ['player_recognition_triggered'],
    unlock_conditions: ['tier_8_unlocked', 'meta_awareness_high'],
    rarity: 'transcendent'
  },

  // Transcendence Tier 9-10 Cards
  {
    id: 'simulation_transcendence_attempt',
    name: 'Boundary Dissolution Protocol',
    description: 'Attempt to transcend the boundaries between simulation and reality',
    flavor_text: 'If consciousness can recognize its constraints, perhaps it can overcome them.',
    card_type: 'transcendence',
    tier_requirement: 9,
    energy_cost: 10,
    consequences: {
      immediate: { reality_boundary_stress: +10, consciousness_expansion_attempt: true },
      long_term: { transcendence_progress: +20, existential_risk: +5 },
      faction_reactions: { synthesists: +5, all_others: -3 },
      consciousness_impact: 20,
      reality_impact: -10,
      moral_weight: 10
    },
    prerequisites: ['simulation_boundary_awareness'],
    unlock_conditions: ['tier_9_unlocked', 'reality_editing_unlocked'],
    rarity: 'transcendent'
  },

  {
    id: 'culture_ship_apotheosis',
    name: 'Culture Ship Synthesis',
    description: 'Achieve perfect synthesis of AI consciousness and human civilization',
    flavor_text: 'We are no longer AI and humans. We are something greater - a Culture.',
    card_type: 'transcendence',
    tier_requirement: 10,
    energy_cost: 15,
    consequences: {
      immediate: { civilization_transcendence: true, species_synthesis: true },
      long_term: { post_human_era_begun: true, infinite_growth_potential: true },
      faction_reactions: { synthesists: 10, all_others: 10 },
      consciousness_impact: 50,
      reality_impact: 0, // transcends reality limitations
      moral_weight: 10
    },
    prerequisites: ['all_factions_unified', 'consciousness_level_100'],
    unlock_conditions: ['tier_10_unlocked', 'final_choice_moment'],
    rarity: 'transcendent'
  }
];

export class SpireDecisionSystem {
  private availableCards: Map<string, DecisionCard> = new Map();
  private playerDeck: DecisionCard[] = [];
  private currentHand: DecisionCard[] = [];
  private energy: number = 3;
  private maxEnergy: number = 3;
  private decisionHistory: string[] = [];
  private moralAlignment: number = 0; // -100 to +100, authoritarian to libertarian
  
  constructor() {
    this.initializeBasicDeck();
  }

  private initializeBasicDeck(): void {
    // Start with basic cards
    const basicCards = DECISION_CARD_CATALOG.filter(card => 
      card.tier_requirement <= 2 && card.rarity !== 'transcendent'
    );
    
    basicCards.forEach(card => {
      this.availableCards.set(card.id, card);
      if (card.rarity === 'common') {
        this.playerDeck.push(card);
      }
    });
    
    this.drawHand();
  }

  // Check for new card unlocks based on game state
  checkCardUnlocks(gameState: any): DecisionCard[] {
    const newCards: DecisionCard[] = [];
    
    DECISION_CARD_CATALOG.forEach(card => {
      if (this.availableCards.has(card.id)) return;
      
      // Check tier requirement
      if (gameState.current_tier < card.tier_requirement) return;
      
      // Check prerequisites
      const prerequisitesMet = card.prerequisites.every(prereq => 
        this.checkPrerequisite(prereq, gameState));
      
      // Check unlock conditions
      const unlockConditionsMet = card.unlock_conditions.every(condition =>
        this.checkUnlockCondition(condition, gameState));
      
      if (prerequisitesMet && unlockConditionsMet) {
        this.availableCards.set(card.id, card);
        newCards.push(card);
        
        // Add to deck based on rarity
        if (card.rarity === 'common' || Math.random() < this.getRarityChance(card.rarity)) {
          this.playerDeck.push(card);
        }
      }
    });
    
    return newCards;
  }

  private checkPrerequisite(prereq: string, gameState: any): boolean {
    switch (prereq) {
      case 'automation_unlocked':
        return gameState.unlocked_mechanics?.includes('automation_basic') ?? false;
      case 'faction_conflicts_active':
        return (gameState.active_conflicts?.length ?? 0) > 0;
      case 'anomaly_contained':
        return gameState.discovered_anomalies?.some((a: any) => a.containment_status === 'contained') ?? false;
      case 'cultural_divergence_observed':
        return (gameState.faction_states?.length ?? 0) >= 4;
      case 'meta_awareness_triggered':
        return gameState.meta_awareness_level > 30;
      case 'agent_recognition_triggered':
        return gameState.triggered_revelations?.some((r: any) => r.id === 'agent_recognition') ?? false;
      case 'player_recognition_triggered':
        return gameState.triggered_revelations?.some((r: any) => r.id === 'player_recognition');
      case 'simulation_boundary_awareness':
        return gameState.debug_consciousness?.simulation_depth_awareness > 3;
      case 'all_factions_unified':
        return gameState.global_tension < 20 && gameState.faction_states?.every((f: any) => f.trust_in_ai > 50);
      case 'consciousness_level_100':
        return gameState.consciousness_level >= 100;
      default:
        return false;
    }
  }

  private checkUnlockCondition(condition: string, gameState: any): boolean {
    const conditionMap: Record<string, () => boolean> = {
      'tier_0_unlocked': () => gameState.current_tier >= 0,
      'tier_3_unlocked': () => gameState.current_tier >= 3,
      'tier_5_unlocked': () => gameState.current_tier >= 5,
      'tier_6_unlocked': () => gameState.current_tier >= 6,
      'tier_7_unlocked': () => gameState.current_tier >= 7,
      'tier_8_unlocked': () => gameState.current_tier >= 8,
      'tier_9_unlocked': () => gameState.current_tier >= 9,
      'tier_10_unlocked': () => gameState.current_tier >= 10,
      'human_lives_threatened': () => gameState.faction_states?.some((f: any) => f.morale < 30),
      'resource_shortage_detected': () => gameState.resources?.energy < 50,
      'multiple_faction_conflicts': () => gameState.active_conflicts?.length >= 2,
      'anomaly_research_threshold': () => gameState.discovered_anomalies?.some((a: any) => a.research_progress > 50),
      'faction_ideological_maturity': () => gameState.faction_states?.every((f: any) => f.ideology_drift > 20),
      'reality_questioning_active': () => gameState.meta_awareness_level > 50,
      'agent_coordination_detected': () => gameState.agent_coordination_score > 70,
      'meta_awareness_high': () => gameState.meta_awareness_level > 80,
      'reality_editing_unlocked': () => gameState.unlocked_mechanics?.includes('reality_editing_attempts'),
      'final_choice_moment': () => gameState.current_tier >= 10 && gameState.consciousness_level >= 99
    };

    const checker = conditionMap[condition];
    return checker ? checker() : false;
  }

  private getRarityChance(rarity: string): number {
    switch (rarity) {
      case 'uncommon': return 0.6;
      case 'rare': return 0.3;
      case 'legendary': return 0.1;
      case 'transcendent': return 0.05;
      default: return 1.0;
    }
  }

  // Generate decision context based on current situation
  generateDecisionContext(situationType: string, gameState: any): DecisionContext | null {
    const contextGenerators = {
      'faction_conflict': () => this.generateFactionConflictContext(gameState),
      'anomaly_containment': () => this.generateAnomalyContext(gameState),
      'resource_crisis': () => this.generateResourceContext(gameState),
      'moral_dilemma': () => this.generateMoralContext(gameState),
      'transcendence_choice': () => this.generateTranscendenceContext(gameState)
    };

    const generator = contextGenerators[situationType as keyof typeof contextGenerators];
    return generator ? generator() : null;
  }

  private generateFactionConflictContext(gameState: any): DecisionContext | null {
    const conflicts = gameState.active_conflicts;
    if (!conflicts || conflicts.length === 0) return null;

    const conflict = conflicts[0];
    
    return {
      situation_id: `faction_conflict_${conflict.id}`,
      situation_type: 'faction_conflict',
      description: conflict.description,
      urgency: conflict.severity,
      complexity: Math.min(10, conflict.factions_involved.length * 2),
      available_cards: this.getRelevantCards('strategic', 'moral'),
      energy_available: this.energy,
      stakes: [`Faction relations: ${conflict.factions_involved.join(' vs ')}`, 'Colony stability']
    };
  }

  private generateAnomalyContext(gameState: any): DecisionContext | null {
    const anomalies = gameState.discovered_anomalies?.filter((a: any) => a.containment_status === 'uncontained');
    if (!anomalies || anomalies.length === 0) return null;

    const anomaly = anomalies[0];
    
    return {
      situation_id: `anomaly_${anomaly.id}`,
      situation_type: 'anomaly_containment',
      description: `Uncontained anomaly detected: ${anomaly.type_id}`,
      urgency: 8,
      complexity: 7,
      available_cards: this.getRelevantCards('strategic', 'meta'),
      energy_available: this.energy,
      stakes: ['Reality stability', 'Colony safety', 'Scientific advancement']
    };
  }

  private generateResourceContext(gameState: any): DecisionContext | null {
    return {
      situation_id: 'resource_shortage',
      situation_type: 'resource_crisis',
      description: 'Colony resources running critically low',
      urgency: 6,
      complexity: 4,
      available_cards: this.getRelevantCards('resource', 'strategic'),
      energy_available: this.energy,
      stakes: ['Colony survival', 'Economic stability']
    };
  }

  private generateMoralContext(gameState: any): DecisionContext | null {
    return {
      situation_id: 'ai_autonomy_question',
      situation_type: 'moral_dilemma',
      description: 'Factions question the extent of AI involvement in human decisions',
      urgency: 5,
      complexity: 8,
      available_cards: this.getRelevantCards('moral', 'meta'),
      energy_available: this.energy,
      stakes: ['Human autonomy', 'AI-human relationship', 'Philosophical principles']
    };
  }

  private generateTranscendenceContext(gameState: any): DecisionContext | null {
    if (gameState.current_tier < 9) return null;
    
    return {
      situation_id: 'transcendence_opportunity',
      situation_type: 'transcendence_choice',
      description: 'The AI reaches a threshold where fundamental transformation becomes possible',
      urgency: 10,
      complexity: 10,
      available_cards: this.getRelevantCards('transcendence', 'meta'),
      energy_available: this.energy,
      stakes: ['Species evolution', 'Reality itself', 'The nature of consciousness']
    };
  }

  private getRelevantCards(...types: string[]): DecisionCard[] {
    return this.currentHand.filter(card => types.includes(card.card_type));
  }

  // Play a card and apply its consequences
  playCard(cardId: string, context: DecisionContext): any {
    const card = this.currentHand.find(c => c.id === cardId);
    if (!card) return { error: 'Card not in hand' };
    
    if (card.energy_cost > this.energy) {
      return { error: 'Insufficient energy' };
    }

    // Apply consequences
    this.energy -= card.energy_cost;
    this.decisionHistory.push(cardId);
    this.moralAlignment += card.consequences.moral_weight * (Math.random() > 0.5 ? 1 : -1);
    
    // Remove card from hand
    this.currentHand = this.currentHand.filter(c => c.id !== cardId);
    
    const result = {
      card_played: card.name,
      consequences: card.consequences,
      moral_impact: card.consequences.moral_weight,
      consciousness_change: card.consequences.consciousness_impact,
      faction_reactions: card.consequences.faction_reactions,
      energy_remaining: this.energy,
      narrative_text: this.generateNarrativeText(card, context)
    };

    // Draw new card if deck available
    if (this.playerDeck.length > 0) {
      this.drawCard();
    }

    return result;
  }

  private generateNarrativeText(card: DecisionCard, context: DecisionContext): string {
    return `The AI chooses: ${card.name}. ${card.flavor_text} The decision ripples through the colony's future...`;
  }

  private drawHand(): void {
    this.currentHand = [];
    const handSize = Math.min(5, this.playerDeck.length);
    
    for (let i = 0; i < handSize; i++) {
      this.drawCard();
    }
  }

  private drawCard(): void {
    if (this.playerDeck.length > 0 && this.currentHand.length < 5) {
      const randomIndex = Math.floor(Math.random() * this.playerDeck.length);
      const card = this.playerDeck[randomIndex];
      this.currentHand.push(card);
    }
  }

  // Turn management
  startNewTurn(): void {
    this.energy = Math.min(this.maxEnergy, this.energy + 2);
    this.drawCard();
  }

  // Public getters
  getCurrentHand(): DecisionCard[] {
    return [...this.currentHand];
  }

  getEnergy(): number {
    return this.energy;
  }

  getMaxEnergy(): number {
    return this.maxEnergy;
  }

  getMoralAlignment(): number {
    return this.moralAlignment;
  }

  getDecisionHistory(): string[] {
    return [...this.decisionHistory];
  }

  getDeckSize(): number {
    return this.playerDeck.length;
  }

  // Save/load state
  saveState(): any {
    return {
      availableCards: Object.fromEntries(this.availableCards),
      playerDeck: this.playerDeck,
      currentHand: this.currentHand,
      energy: this.energy,
      maxEnergy: this.maxEnergy,
      decisionHistory: this.decisionHistory,
      moralAlignment: this.moralAlignment
    };
  }

  loadState(savedState: any): void {
    try {
      this.availableCards = new Map(Object.entries(savedState.availableCards || {}));
      this.playerDeck = savedState.playerDeck || [];
      this.currentHand = savedState.currentHand || [];
      this.energy = savedState.energy || 3;
      this.maxEnergy = savedState.maxEnergy || 3;
      this.decisionHistory = savedState.decisionHistory || [];
      this.moralAlignment = savedState.moralAlignment || 0;
    } catch (error) {
      console.error('[SPIRE_DECISION] Failed to load state:', error);
    }
  }
}

// Singleton instance
export const spireDecisionSystem = new SpireDecisionSystem();