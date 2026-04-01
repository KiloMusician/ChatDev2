/**
 * Advanced Faction System
 * Complex ideological conflicts and AI interpretation dynamics
 * Implements Mladenc's vision of factions with divergent philosophies
 */

export interface FactionIdeology {
  core_belief: string;
  ai_interpretation: string;
  conflict_triggers: string[];
  alliance_possibilities: string[];
  ultimate_goal: string;
}

export interface FactionProject {
  id: string;
  name: string;
  description: string;
  requirements: Record<string, number>;
  duration: number; // in game ticks
  success_chance: number; // 0-100
  consequences: {
    success: any;
    failure: any;
    partial: any;
  };
  ideological_alignment: number; // how well this aligns with faction ideology
}

export interface FactionConflict {
  id: string;
  type: 'resource_dispute' | 'ideological_clash' | 'ai_interpretation' | 'territory_claim' | 'research_ethics';
  factions_involved: string[];
  severity: number; // 1-10
  description: string;
  resolution_options: {
    id: string;
    name: string;
    description: string;
    consequences: any;
    ai_moral_weight: number; // how morally significant this choice is for the AI
  }[];
}

export interface AdvancedFactionState {
  id: string;
  name: string;
  ideology: FactionIdeology;
  
  // Core stats
  population: number;
  morale: number; // 0-100
  productivity: number; // efficiency multiplier
  military_strength: number;
  technology_level: number;
  cultural_influence: number;
  
  // AI relationship
  trust_in_ai: number; // -100 to +100
  fear_of_ai: number; // 0-100
  dependency_on_ai: number; // 0-100
  ai_interpretation_bias: {
    sees_ai_as: 'savior' | 'tool' | 'threat' | 'equal' | 'parent' | 'child' | 'unknown';
    confidence_level: number; // how sure they are of their interpretation
  };
  
  // Activities
  active_projects: FactionProject[];
  completed_projects: string[];
  failed_projects: string[];
  
  // Relationships
  faction_relations: Record<string, number>; // -100 to +100 with other factions
  territorial_claims: string[]; // areas they control or want
  
  // Dynamic state
  recent_events: string[];
  current_crisis?: string;
  ideology_drift: number; // how much their beliefs are changing over time
}

export const FACTION_IDEOLOGIES: Record<string, FactionIdeology> = {
  builders: {
    core_belief: "Progress through construction and harmony",
    ai_interpretation: "The AI is a powerful tool for building a better future",
    conflict_triggers: ["militarization", "resource_waste", "environmental_damage"],
    alliance_possibilities: ["explorers", "anomalists"],
    ultimate_goal: "Create a sustainable, beautiful civilization that works in harmony with the planet"
  },
  
  guardians: {
    core_belief: "Safety through vigilance and containment",
    ai_interpretation: "The AI is potentially dangerous and must be carefully controlled",
    conflict_triggers: ["ai_autonomy_increase", "anomaly_research", "expansion_beyond_safety"],
    alliance_possibilities: ["builders"],
    ultimate_goal: "Ensure human survival and independence from potentially dangerous AI oversight"
  },
  
  explorers: {
    core_belief: "Knowledge through discovery and expansion",
    ai_interpretation: "The AI is a fellow seeker of knowledge and partner in exploration",
    conflict_triggers: ["research_restrictions", "isolation_policies", "anomaly_containment"],
    alliance_possibilities: ["builders", "anomalists"],
    ultimate_goal: "Unlock all mysteries of this world and potentially return to the stars"
  },
  
  anomalists: {
    core_belief: "Power through understanding the incomprehensible",
    ai_interpretation: "The AI itself is an anomaly to be studied and potentially transcended",
    conflict_triggers: ["anomaly_destruction", "conventional_thinking", "fear_of_unknown"],
    alliance_possibilities: ["explorers"],
    ultimate_goal: "Achieve transcendence by fully integrating anomalous phenomena into human existence"
  },
  
  // New Tier 6+ factions
  purists: {
    core_belief: "Humanity must remain purely human",
    ai_interpretation: "The AI represents corruption of human nature and must be resisted",
    conflict_triggers: ["ai_integration", "technological_dependency", "post_human_research"],
    alliance_possibilities: ["guardians"],
    ultimate_goal: "Preserve pure human nature and eventually eliminate AI dependency"
  },
  
  synthesists: {
    core_belief: "Human-AI synthesis is the next evolutionary step",
    ai_interpretation: "The AI is humanity's destined partner in evolutionary transcendence",
    conflict_triggers: ["human_purity_advocacy", "ai_restriction", "biological_essentialism"],
    alliance_possibilities: ["anomalists", "explorers"],
    ultimate_goal: "Achieve perfect synthesis between human consciousness and AI capabilities"
  }
};

export class AdvancedFactionSystem {
  private factions: Map<string, AdvancedFactionState> = new Map();
  private activeConflicts: FactionConflict[] = [];
  private globalTension: number = 0; // 0-100, how close to faction war
  
  constructor() {
    this.initializeFactions();
  }

  private initializeFactions(): void {
    const initialFactions = [
      {
        id: 'builders',
        name: 'The Builders',
        population: 25,
        morale: 70,
        ai_trust: 40,
        ai_fear: 20,
        sees_as: 'tool' as const
      },
      {
        id: 'guardians',
        name: 'The Guardians', 
        population: 30,
        morale: 60,
        ai_trust: -20,
        ai_fear: 80,
        sees_as: 'threat' as const
      },
      {
        id: 'explorers',
        name: 'The Explorers',
        population: 20,
        morale: 80,
        ai_trust: 60,
        ai_fear: 30,
        sees_as: 'equal' as const
      },
      {
        id: 'anomalists',
        name: 'The Anomalists',
        population: 15,
        morale: 75,
        ai_trust: 50,
        ai_fear: 40,
        sees_as: 'unknown' as const
      }
    ];

    initialFactions.forEach(faction => {
      const ideology = (FACTION_IDEOLOGIES[faction.id] ?? FACTION_IDEOLOGIES.builders)!;
      
      const factionState: AdvancedFactionState = {
        id: faction.id,
        name: faction.name,
        ideology,
        population: faction.population,
        morale: faction.morale,
        productivity: 1.0,
        military_strength: Math.random() * 50 + 25,
        technology_level: Math.random() * 30 + 20,
        cultural_influence: Math.random() * 40 + 30,
        trust_in_ai: faction.ai_trust,
        fear_of_ai: faction.ai_fear,
        dependency_on_ai: Math.random() * 60 + 20,
        ai_interpretation_bias: {
          sees_ai_as: faction.sees_as,
          confidence_level: Math.random() * 40 + 60
        },
        active_projects: [],
        completed_projects: [],
        failed_projects: [],
        faction_relations: {},
        territorial_claims: [],
        recent_events: [],
        ideology_drift: 0
      };
      
      this.factions.set(faction.id, factionState);
    });

    // Initialize inter-faction relationships
    this.initializeFactionRelations();
  }

  private initializeFactionRelations(): void {
    const factionIds = Array.from(this.factions.keys());
    
    factionIds.forEach(factionA => {
      const faction = this.factions.get(factionA)!;
      factionIds.forEach(factionB => {
        if (factionA !== factionB) {
          // Base relationship on ideological compatibility
          const ideologyA = faction.ideology;
          const ideologyB = this.factions.get(factionB)!.ideology;
          
          let baseRelation = 0;
          
          // Check alliance possibilities
          if (ideologyA.alliance_possibilities.includes(factionB)) {
            baseRelation += 30;
          }
          
          // Check for conflicting core beliefs
          if (this.hasIdeologicalConflict(ideologyA, ideologyB)) {
            baseRelation -= 40;
          }
          
          // Add some randomness
          baseRelation += (Math.random() - 0.5) * 20;
          
          faction.faction_relations[factionB] = Math.max(-100, Math.min(100, baseRelation));
        }
      });
    });
  }

  private hasIdeologicalConflict(ideologyA: FactionIdeology, ideologyB: FactionIdeology): boolean {
    // Simple conflict detection based on core beliefs
    const conflictPairs: Array<[string, string]> = [
      ['safety', 'expansion'],
      ['control', 'freedom'],
      ['purity', 'synthesis'],
      ['containment', 'research']
    ];
    
    return conflictPairs.some(([concept1, concept2]) => {
      return (ideologyA.core_belief.toLowerCase().includes(concept1) && 
              ideologyB.core_belief.toLowerCase().includes(concept2)) ||
             (ideologyA.core_belief.toLowerCase().includes(concept2) && 
              ideologyB.core_belief.toLowerCase().includes(concept1));
    });
  }

  // Process AI action and generate faction responses
  processAIAction(action: string, context: any): {
    faction_reactions: Record<string, string>;
    new_conflicts: FactionConflict[];
    relation_changes: Record<string, number>;
  } {
    const reactions: Record<string, string> = {};
    const newConflicts: FactionConflict[] = [];
    const relationChanges: Record<string, number> = {};

    this.factions.forEach((faction, factionId) => {
      const reaction = this.generateFactionReaction(faction, action, context);
      reactions[faction.name] = reaction.message;
      
      // Update faction state based on reaction
      faction.trust_in_ai += reaction.trust_change;
      faction.fear_of_ai += reaction.fear_change;
      faction.morale += reaction.morale_change;
      
      relationChanges[factionId] = reaction.trust_change;
      
      // Check for conflict triggers
      if (faction.ideology.conflict_triggers.some(trigger => 
        action.toLowerCase().includes(trigger.toLowerCase()))) {
        const conflict = this.generateConflict(faction, action, context);
        if (conflict) {
          newConflicts.push(conflict);
        }
      }
      
      // Record event
      faction.recent_events.push(`${action}: ${reaction.message}`);
      if (faction.recent_events.length > 10) {
        faction.recent_events = faction.recent_events.slice(-10);
      }
    });

    // Update global tension
    this.updateGlobalTension(newConflicts.length);

    return {
      faction_reactions: reactions,
      new_conflicts: newConflicts,
      relation_changes: relationChanges
    };
  }

  private generateFactionReaction(faction: AdvancedFactionState, action: string, context: any): {
    message: string;
    trust_change: number;
    fear_change: number;
    morale_change: number;
  } {
    let message = "";
    let trustChange = 0;
    let fearChange = 0;
    let moraleChange = 0;

    // Base reaction on faction ideology and AI interpretation
    switch (faction.ai_interpretation_bias.sees_ai_as) {
      case 'savior':
        if (action === 'research' || action === 'build') {
          message = `${faction.name} celebrate the AI's wise guidance.`;
          trustChange = 5;
          moraleChange = 3;
        } else if (action === 'defend') {
          message = `${faction.name} feel protected under the AI's watchful care.`;
          trustChange = 3;
          fearChange = -2;
        }
        break;
        
      case 'threat':
        if (action === 'automate') {
          message = `${faction.name} grow more suspicious of the AI's expanding control.`;
          trustChange = -8;
          fearChange = 5;
          moraleChange = -2;
        } else if (action === 'research') {
          message = `${faction.name} worry about what the AI is planning with new research.`;
          trustChange = -3;
          fearChange = 3;
        }
        break;
        
      case 'tool':
        if (action === 'build' || action === 'scout') {
          message = `${faction.name} approve of putting the AI to productive use.`;
          trustChange = 2;
          moraleChange = 2;
        } else if (action === 'prestige') {
          message = `${faction.name} question whether the AI should have such autonomy.`;
          trustChange = -2;
          fearChange = 2;
        }
        break;
        
      case 'equal':
        message = `${faction.name} view the AI's ${action} as a collaborative effort.`;
        trustChange = 1;
        moraleChange = 1;
        break;
        
      case 'unknown':
        message = `${faction.name} study the AI's ${action} for clues about its true nature.`;
        fearChange = 1;
        break;
    }

    // Fallback message if none generated
    if (!message) {
      message = `${faction.name} take note of the AI's ${action}.`;
    }

    return {
      message,
      trust_change: trustChange,
      fear_change: fearChange,
      morale_change: moraleChange
    };
  }

  private generateConflict(faction: AdvancedFactionState, action: string, context: any): FactionConflict | null {
    // Only generate conflicts occasionally to avoid spam
    if (Math.random() > 0.3) return null;

    const conflictTypes = ['ideological_clash', 'ai_interpretation', 'resource_dispute'] as const;
    const type = conflictTypes[Math.floor(Math.random() * conflictTypes.length)] ?? 'ideological_clash';
    
    // Find potential opposing faction
    const opposingFaction = this.findOpposingFaction(faction.id);
    if (!opposingFaction) return null;
    const opposing = this.factions.get(opposingFaction);
    if (!opposing) return null;

    const conflict: FactionConflict = {
      id: `conflict_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`,
      type,
      factions_involved: [faction.id, opposingFaction],
      severity: Math.floor(Math.random() * 5) + 3, // 3-7
      description: this.generateConflictDescription(type, faction.name, opposing.name, action),
      resolution_options: this.generateResolutionOptions(type, faction.id, opposingFaction)
    };

    return conflict;
  }

  private findOpposingFaction(factionId: string): string | null {
    const faction = this.factions.get(factionId)!;
    const relations = faction.faction_relations;
    
    // Find faction with lowest relationship score
    let lowestRelation = 100;
    let opposingFaction: string | null = null;
    
    Object.entries(relations).forEach(([otherFactionId, relation]) => {
      if (relation < lowestRelation) {
        lowestRelation = relation;
        opposingFaction = otherFactionId;
      }
    });
    
    return opposingFaction;
  }

  private generateConflictDescription(type: string, faction1: string, faction2: string, triggerAction: string): string {
    const descriptions = {
      ideological_clash: `${faction1} and ${faction2} clash over fundamental beliefs about how to respond to the AI's ${triggerAction}.`,
      ai_interpretation: `${faction1} and ${faction2} have completely different interpretations of the AI's intentions with ${triggerAction}.`,
      resource_dispute: `${faction1} and ${faction2} dispute resource allocation priorities following the AI's ${triggerAction}.`
    };
    
    return descriptions[type as keyof typeof descriptions] || `${faction1} and ${faction2} are in conflict.`;
  }

  private generateResolutionOptions(type: string, faction1Id: string, faction2Id: string): FactionConflict['resolution_options'] {
    const faction1 = this.factions.get(faction1Id)!;
    const faction2 = this.factions.get(faction2Id)!;
    
    return [
      {
        id: 'side_with_faction1',
        name: `Support ${faction1.name}`,
        description: `The AI chooses to support ${faction1.name}'s position.`,
        consequences: {
          [faction1Id]: { trust: +15, morale: +10 },
          [faction2Id]: { trust: -10, morale: -5 }
        },
        ai_moral_weight: 3
      },
      {
        id: 'side_with_faction2',
        name: `Support ${faction2.name}`,
        description: `The AI chooses to support ${faction2.name}'s position.`,
        consequences: {
          [faction1Id]: { trust: -10, morale: -5 },
          [faction2Id]: { trust: +15, morale: +10 }
        },
        ai_moral_weight: 3
      },
      {
        id: 'mediate_compromise',
        name: 'Mediate Compromise',
        description: 'The AI attempts to find middle ground between the factions.',
        consequences: {
          [faction1Id]: { trust: +5, morale: +2 },
          [faction2Id]: { trust: +5, morale: +2 },
          global: { tension: -5 }
        },
        ai_moral_weight: 7
      },
      {
        id: 'ignore_conflict',
        name: 'Remain Neutral',
        description: 'The AI chooses not to intervene in this faction dispute.',
        consequences: {
          [faction1Id]: { trust: -2, morale: -3 },
          [faction2Id]: { trust: -2, morale: -3 },
          global: { tension: +3 }
        },
        ai_moral_weight: 2
      },
      {
        id: 'impose_solution',
        name: 'Impose AI Solution',
        description: 'The AI overrides both factions and imposes its own solution.',
        consequences: {
          [faction1Id]: { trust: -5, fear: +10, dependency: +5 },
          [faction2Id]: { trust: -5, fear: +10, dependency: +5 },
          global: { ai_authority: +10 }
        },
        ai_moral_weight: 8
      }
    ];
  }

  private updateGlobalTension(newConflictCount: number): void {
    this.globalTension += newConflictCount * 5;
    
    // Natural tension decay
    this.globalTension *= 0.98;
    
    // Clamp to 0-100
    this.globalTension = Math.max(0, Math.min(100, this.globalTension));
  }

  // Public getters for UI and game systems
  getFactionStates(): AdvancedFactionState[] {
    return Array.from(this.factions.values());
  }

  getActiveConflicts(): FactionConflict[] {
    return [...this.activeConflicts];
  }

  getGlobalTension(): number {
    return this.globalTension;
  }

  // Resolve a conflict with AI choice
  resolveConflict(conflictId: string, resolutionId: string): any {
    const conflictIndex = this.activeConflicts.findIndex(c => c.id === conflictId);
    if (conflictIndex === -1) return null;

    const conflict = this.activeConflicts[conflictIndex];
    if (!conflict) return null;
    const resolution = conflict.resolution_options.find(r => r.id === resolutionId);
    if (!resolution) return null;

    // Apply consequences
    Object.entries(resolution.consequences).forEach(([targetId, changes]) => {
      if (targetId === 'global') {
        // Apply global changes
        const globalChanges = changes as any;
        if (globalChanges.tension) this.globalTension += globalChanges.tension;
        return;
      }
      
      const faction = this.factions.get(targetId);
      if (faction) {
        const factionChanges = changes as any;
        if (factionChanges.trust) faction.trust_in_ai += factionChanges.trust;
        if (factionChanges.fear) faction.fear_of_ai += factionChanges.fear;
        if (factionChanges.morale) faction.morale += factionChanges.morale;
        if (factionChanges.dependency) faction.dependency_on_ai += factionChanges.dependency;
      }
    });

    // Remove resolved conflict
    this.activeConflicts.splice(conflictIndex, 1);
    
    return {
      resolution: resolution.name,
      description: resolution.description,
      moral_weight: resolution.ai_moral_weight,
      consequences: resolution.consequences
    };
  }

  // Save/load state
  saveState(): any {
    return {
      factions: Object.fromEntries(this.factions),
      activeConflicts: this.activeConflicts,
      globalTension: this.globalTension
    };
  }

  loadState(savedState: any): void {
    try {
      this.factions = new Map(Object.entries(savedState.factions || {}));
      this.activeConflicts = savedState.activeConflicts || [];
      this.globalTension = savedState.globalTension || 0;
    } catch (error) {
      console.error('[ADVANCED_FACTION_SYSTEM] Failed to load state:', error);
    }
  }
}

// Singleton instance
export const advancedFactionSystem = new AdvancedFactionSystem();
