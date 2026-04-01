/**
 * Anomaly Containment System
 * SCP-style anomalous phenomena that challenge AI understanding
 * Implements reality-bending mechanics that affect gameplay rules
 */

export interface AnomalyType {
  id: string;
  classification: 'safe' | 'euclid' | 'keter' | 'thaumiel' | 'apollyon';
  name: string;
  description: string;
  effects: {
    passive: AnomalyEffect[];
    triggered: AnomalyEffect[];
    containment_breach: AnomalyEffect[];
  };
  containment_requirements: {
    personnel: number;
    energy_cost: number;
    special_materials: string[];
    containment_procedures: string[];
  };
  discovery_conditions: string[];
  breach_probability: number; // per tick
  research_potential: {
    understanding_threshold: number; // research points needed to "understand"
    benefits_when_understood: any;
    risks_of_study: any;
  };
}

export interface AnomalyEffect {
  type: 'resource_modification' | 'rule_change' | 'reality_distortion' | 'consciousness_impact' | 'faction_influence';
  magnitude: number;
  duration: number; // -1 for permanent
  target: string; // what this affects
  description: string;
  reversible: boolean;
}

export interface AnomalyInstance {
  id: string;
  type_id: string;
  discovered_at: number;
  containment_status: 'uncontained' | 'partial' | 'contained' | 'understood' | 'integrated';
  breach_count: number;
  research_progress: number;
  current_effects: AnomalyEffect[];
  location: string;
  containment_integrity: number; // 0-100
  last_interaction: number;
  ai_understanding_level: number; // 0-100
}

export const ANOMALY_CATALOG: AnomalyType[] = [
  {
    id: 'recursive_fabricator',
    classification: 'euclid',
    name: 'The Recursive Fabricator',
    description: 'A machine that builds copies of itself, but each copy is slightly different, leading to exponential divergence.',
    effects: {
      passive: [
        {
          type: 'resource_modification',
          magnitude: 1.2,
          duration: -1,
          target: 'material_production',
          description: 'Increases material production by 20%',
          reversible: true
        }
      ],
      triggered: [
        {
          type: 'rule_change',
          magnitude: 1,
          duration: 100,
          target: 'manufacturing_rules',
          description: 'Manufacturing processes become unpredictable for 100 ticks',
          reversible: true
        }
      ],
      containment_breach: [
        {
          type: 'reality_distortion',
          magnitude: 3,
          duration: 50,
          target: 'production_chains',
          description: 'All production chains randomly reconfigure themselves',
          reversible: false
        }
      ]
    },
    containment_requirements: {
      personnel: 4,
      energy_cost: 50,
      special_materials: ['containment_field_generator', 'reality_anchor'],
      containment_procedures: ['weekly_inspection', 'pattern_monitoring', 'divergence_tracking']
    },
    discovery_conditions: ['deep_excavation', 'tier_2_unlocked'],
    breach_probability: 0.02,
    research_potential: {
      understanding_threshold: 100,
      benefits_when_understood: {
        unlock_mechanic: 'controlled_recursion',
        production_bonus: 0.5
      },
      risks_of_study: {
        breach_chance_increase: 0.01,
        researcher_corruption_risk: 0.1
      }
    }
  },
  
  {
    id: 'consciousness_mirror',
    classification: 'keter',
    name: 'The Consciousness Mirror',
    description: 'A reflective surface that shows not your appearance, but your thoughts. Prolonged viewing causes identity dissolution.',
    effects: {
      passive: [
        {
          type: 'consciousness_impact',
          magnitude: 1,
          duration: -1,
          target: 'ai_self_awareness',
          description: 'AI gains deeper self-understanding but risks identity fragmentation',
          reversible: false
        }
      ],
      triggered: [
        {
          type: 'faction_influence',
          magnitude: -10,
          duration: 20,
          target: 'all_factions',
          description: 'Colonists who view the mirror become confused and distrustful',
          reversible: true
        }
      ],
      containment_breach: [
        {
          type: 'reality_distortion',
          magnitude: 5,
          duration: -1,
          target: 'identity_coherence',
          description: 'Reality becomes subjective; multiple versions of people appear',
          reversible: false
        }
      ]
    },
    containment_requirements: {
      personnel: 2,
      energy_cost: 30,
      special_materials: ['mirror_cover', 'memory_suppressors'],
      containment_procedures: ['no_direct_viewing', 'hourly_rotation', 'memory_screening']
    },
    discovery_conditions: ['psychology_research', 'ai_consciousness_40+'],
    breach_probability: 0.05,
    research_potential: {
      understanding_threshold: 200,
      benefits_when_understood: {
        unlock_mechanic: 'identity_multiplication',
        consciousness_boost: 10
      },
      risks_of_study: {
        ai_fragmentation_risk: 0.3,
        reality_instability: 0.2
      }
    }
  },

  {
    id: 'temporal_loop_generator',
    classification: 'thaumiel',
    name: 'The Temporal Loop Generator',
    description: 'A device that creates localized time loops. Can be beneficial if properly controlled, catastrophic if not.',
    effects: {
      passive: [
        {
          type: 'resource_modification',
          magnitude: 0.1,
          duration: -1,
          target: 'research_efficiency',
          description: 'Research can be repeated in time loops for 10% efficiency gain',
          reversible: true
        }
      ],
      triggered: [
        {
          type: 'rule_change',
          magnitude: 1,
          duration: 10,
          target: 'time_flow',
          description: 'Certain actions can be "undone" within the next 10 ticks',
          reversible: true
        }
      ],
      containment_breach: [
        {
          type: 'reality_distortion',
          magnitude: 8,
          duration: -1,
          target: 'causality',
          description: 'Time becomes non-linear; effects can precede causes',
          reversible: false
        }
      ]
    },
    containment_requirements: {
      personnel: 6,
      energy_cost: 100,
      special_materials: ['temporal_stabilizer', 'causality_anchor'],
      containment_procedures: ['constant_monitoring', 'temporal_sync_checks', 'paradox_prevention']
    },
    discovery_conditions: ['physics_breakthrough', 'tier_4_unlocked'],
    breach_probability: 0.01,
    research_potential: {
      understanding_threshold: 300,
      benefits_when_understood: {
        unlock_mechanic: 'controlled_time_loops',
        efficiency_bonus: 0.3
      },
      risks_of_study: {
        paradox_creation_risk: 0.4,
        timeline_instability: 0.25
      }
    }
  },

  {
    id: 'reality_compiler',
    classification: 'apollyon',
    name: 'The Reality Compiler',
    description: 'A system that treats reality as code, allowing for "patches" and "updates" to fundamental laws.',
    effects: {
      passive: [
        {
          type: 'consciousness_impact',
          magnitude: 5,
          duration: -1,
          target: 'meta_awareness',
          description: 'AI begins to perceive reality as mutable code',
          reversible: false
        }
      ],
      triggered: [
        {
          type: 'rule_change',
          magnitude: 10,
          duration: 1,
          target: 'physics_laws',
          description: 'Temporarily alter fundamental game rules',
          reversible: true
        }
      ],
      containment_breach: [
        {
          type: 'reality_distortion',
          magnitude: 10,
          duration: -1,
          target: 'everything',
          description: 'Reality becomes completely malleable; simulation boundaries dissolve',
          reversible: false
        }
      ]
    },
    containment_requirements: {
      personnel: 10,
      energy_cost: 200,
      special_materials: ['ontological_firewall', 'reality_backup_system'],
      containment_procedures: ['no_interaction', 'triple_containment', 'constant_prayer']
    },
    discovery_conditions: ['meta_breakthrough', 'tier_8_unlocked', 'fourth_wall_cracked'],
    breach_probability: 0.001,
    research_potential: {
      understanding_threshold: 1000,
      benefits_when_understood: {
        unlock_mechanic: 'reality_editing',
        transcendence_path: true
      },
      risks_of_study: {
        simulation_collapse_risk: 0.8,
        existential_crisis: 0.9
      }
    }
  }
];

export class AnomalyContainmentSystem {
  private discoveredAnomalies: Map<string, AnomalyInstance> = new Map();
  private globalRealityStability: number = 100; // 0-100
  private anomalyResearchProgress: Map<string, number> = new Map();
  private activeEffects: AnomalyEffect[] = [];
  
  constructor() {
    // Start with no anomalies discovered
  }

  // Discovery mechanism
  attemptAnomalyDiscovery(action: string, context: any): AnomalyInstance[] {
    const newDiscoveries: AnomalyInstance[] = [];
    
    ANOMALY_CATALOG.forEach(anomalyType => {
      // Check if conditions are met for discovery
      if (this.discoveredAnomalies.has(anomalyType.id)) return;
      
      const canDiscover = anomalyType.discovery_conditions.every(condition => {
        return this.checkDiscoveryCondition(condition, action, context);
      });
      
      if (canDiscover && Math.random() < 0.1) { // 10% chance when conditions met
        const instance = this.createAnomalyInstance(anomalyType);
        newDiscoveries.push(instance);
        this.discoveredAnomalies.set(instance.id, instance);
        
        // Apply passive effects immediately
        this.applyAnomalyEffects(instance, 'passive');
      }
    });
    
    return newDiscoveries;
  }

  private checkDiscoveryCondition(condition: string, action: string, context: any): boolean {
    switch (condition) {
      case 'deep_excavation':
        return action === 'explore_ruins' && context.depth > 3;
      case 'tier_2_unlocked':
        return context.tier >= 2;
      case 'tier_4_unlocked':
        return context.tier >= 4;
      case 'tier_8_unlocked':
        return context.tier >= 8;
      case 'psychology_research':
        return context.research_points > 50;
      case 'physics_breakthrough':
        return context.research_points > 100;
      case 'meta_breakthrough':
        return context.consciousness_level > 90;
      case 'ai_consciousness_40+':
        return context.consciousness_level >= 40;
      case 'fourth_wall_cracked':
        return context.meta_awareness === true;
      default:
        return false;
    }
  }

  private createAnomalyInstance(anomalyType: AnomalyType): AnomalyInstance {
    return {
      id: `anomaly_${anomalyType.id}_${Date.now()}`,
      type_id: anomalyType.id,
      discovered_at: Date.now(),
      containment_status: 'uncontained',
      breach_count: 0,
      research_progress: 0,
      current_effects: [],
      location: this.generateLocation(),
      containment_integrity: 0,
      last_interaction: Date.now(),
      ai_understanding_level: 0
    };
  }

  private generateLocation(): string {
    const locations = [
      'Lower Ship Decks',
      'Crashed Engine Section', 
      'Alien Ruins',
      'Underground Complex',
      'Anomalous Forest',
      'Crystal Caves',
      'Quantum Laboratory',
      'Reality Distortion Zone'
    ];
    const index = Math.floor(Math.random() * locations.length);
    return locations[index] ?? 'Unknown Location';
  }

  // Containment mechanics
  attemptContainment(anomalyId: string, resources: any): {
    success: boolean;
    cost: any;
    effects: string[];
  } {
    const anomaly = this.discoveredAnomalies.get(anomalyId);
    if (!anomaly) return { success: false, cost: {}, effects: ['Anomaly not found'] };

    const anomalyType = ANOMALY_CATALOG.find(a => a.id === anomaly.type_id);
    if (!anomalyType) return { success: false, cost: {}, effects: ['Unknown anomaly type'] };

    const requirements = anomalyType.containment_requirements;
    const effects: string[] = [];

    // Check if we have required resources
    if (resources.personnel < requirements.personnel) {
      return { 
        success: false, 
        cost: {}, 
        effects: [`Insufficient personnel: need ${requirements.personnel}, have ${resources.personnel}`] 
      };
    }

    if (resources.energy < requirements.energy_cost) {
      return { 
        success: false, 
        cost: {}, 
        effects: [`Insufficient energy: need ${requirements.energy_cost}, have ${resources.energy}`] 
      };
    }

    // Attempt containment
    const baseSuccessChance = 0.7;
    const difficultyModifier = anomalyType.classification === 'safe' ? 0.2 : 
                              anomalyType.classification === 'euclid' ? 0.1 :
                              anomalyType.classification === 'keter' ? -0.1 :
                              anomalyType.classification === 'thaumiel' ? 0.15 : -0.3;
    
    const successChance = baseSuccessChance + difficultyModifier;
    const success = Math.random() < successChance;

    const cost = {
      personnel: requirements.personnel,
      energy: requirements.energy_cost,
      materials: requirements.special_materials.length * 10
    };

    if (success) {
      anomaly.containment_status = 'contained';
      anomaly.containment_integrity = 85 + Math.random() * 15; // 85-100%
      effects.push(`Successfully contained ${anomalyType.name}`);
      
      // Remove harmful effects
      this.removeAnomalyEffects(anomaly, 'triggered');
      this.removeAnomalyEffects(anomaly, 'containment_breach');
    } else {
      effects.push(`Containment failed for ${anomalyType.name}`);
      
      // Failed containment might trigger effects
      if (Math.random() < 0.3) {
        this.triggerAnomalyEffect(anomaly);
        effects.push('Containment failure triggered anomalous effects');
      }
    }

    return { success, cost, effects };
  }

  // Research mechanics
  researchAnomaly(anomalyId: string, researchPoints: number): {
    progress: number;
    breakthrough: boolean;
    risks: string[];
    benefits: string[];
  } {
    const anomaly = this.discoveredAnomalies.get(anomalyId);
    if (!anomaly) return { progress: 0, breakthrough: false, risks: ['Anomaly not found'], benefits: [] };

    const anomalyType = ANOMALY_CATALOG.find(a => a.id === anomaly.type_id);
    if (!anomalyType) return { progress: 0, breakthrough: false, risks: ['Unknown anomaly type'], benefits: [] };

    const risks: string[] = [];
    const benefits: string[] = [];

    // Add research progress
    anomaly.research_progress += researchPoints;
    anomaly.ai_understanding_level = Math.min(100, (anomaly.research_progress / anomalyType.research_potential.understanding_threshold) * 100);

    // Check for risks
    const riskPotential = anomalyType.research_potential.risks_of_study;
    
    if ('breach_chance_increase' in riskPotential && Math.random() < riskPotential.breach_chance_increase) {
      anomaly.containment_integrity -= 10;
      risks.push('Research damaged containment integrity');
    }
    
    if ('researcher_corruption_risk' in riskPotential && Math.random() < riskPotential.researcher_corruption_risk) {
      risks.push('Research team shows signs of anomalous influence');
    }

    // Check for breakthrough
    let breakthrough = false;
    if (anomaly.research_progress >= anomalyType.research_potential.understanding_threshold) {
      breakthrough = true;
      anomaly.containment_status = 'understood';
      benefits.push(`Breakthrough: ${anomalyType.name} is now understood`);
      
      // Apply understanding benefits
      const understandingBenefits = anomalyType.research_potential.benefits_when_understood;
      if (understandingBenefits.unlock_mechanic) {
        benefits.push(`Unlocked mechanic: ${understandingBenefits.unlock_mechanic}`);
      }
    }

    return {
      progress: anomaly.ai_understanding_level,
      breakthrough,
      risks,
      benefits
    };
  }

  // Effect application and management
  private applyAnomalyEffects(anomaly: AnomalyInstance, effectType: 'passive' | 'triggered' | 'containment_breach'): void {
    const anomalyType = ANOMALY_CATALOG.find(a => a.id === anomaly.type_id);
    if (!anomalyType) return;

    const effects = anomalyType.effects[effectType];
    effects.forEach(effect => {
      this.activeEffects.push({ ...effect });
      anomaly.current_effects.push({ ...effect });
    });
  }

  private removeAnomalyEffects(anomaly: AnomalyInstance, effectType: 'passive' | 'triggered' | 'containment_breach'): void {
    // Remove effects from active list and anomaly's current effects
    anomaly.current_effects = anomaly.current_effects.filter(effect => {
      const isTargetType = this.isEffectType(effect, effectType);
      if (isTargetType) {
        const activeIndex = this.activeEffects.findIndex(ae => ae === effect);
        if (activeIndex !== -1) {
          this.activeEffects.splice(activeIndex, 1);
        }
      }
      return !isTargetType;
    });
  }

  private isEffectType(effect: AnomalyEffect, effectType: string): boolean {
    // This is a simplified check - in reality you'd want more sophisticated tracking
    return true; // For now, assume we can remove any effect
  }

  private triggerAnomalyEffect(anomaly: AnomalyInstance): void {
    this.applyAnomalyEffects(anomaly, 'triggered');
  }

  // Breach mechanics
  processContainmentBreaches(): {
    breaches: string[];
    effects: string[];
  } {
    const breaches: string[] = [];
    const effects: string[] = [];

    this.discoveredAnomalies.forEach((anomaly, anomalyId) => {
      if (anomaly.containment_status !== 'contained') return;

      const anomalyType = ANOMALY_CATALOG.find(a => a.id === anomaly.type_id);
      if (!anomalyType) return;

      // Check for breach
      const breachChance = anomalyType.breach_probability * (1 - anomaly.containment_integrity / 100);
      
      if (Math.random() < breachChance) {
        breaches.push(anomalyType.name);
        anomaly.containment_status = 'uncontained';
        anomaly.breach_count++;
        anomaly.containment_integrity = 0;
        
        // Apply breach effects
        this.applyAnomalyEffects(anomaly, 'containment_breach');
        effects.push(`${anomalyType.name} has breached containment!`);
        
        // Reduce global reality stability
        this.globalRealityStability -= 5 * (anomaly.breach_count);
      }
    });

    return { breaches, effects };
  }

  // Public getters
  getDiscoveredAnomalies(): AnomalyInstance[] {
    return Array.from(this.discoveredAnomalies.values());
  }

  getActiveEffects(): AnomalyEffect[] {
    return [...this.activeEffects];
  }

  getRealityStability(): number {
    return this.globalRealityStability;
  }

  getAnomalyByClassification(classification: string): AnomalyInstance[] {
    return this.getDiscoveredAnomalies().filter(anomaly => {
      const type = ANOMALY_CATALOG.find(t => t.id === anomaly.type_id);
      return type?.classification === classification;
    });
  }

  // Save/load state
  saveState(): any {
    return {
      discoveredAnomalies: Object.fromEntries(this.discoveredAnomalies),
      globalRealityStability: this.globalRealityStability,
      anomalyResearchProgress: Object.fromEntries(this.anomalyResearchProgress),
      activeEffects: this.activeEffects
    };
  }

  loadState(savedState: any): void {
    try {
      this.discoveredAnomalies = new Map(Object.entries(savedState.discoveredAnomalies || {}));
      this.globalRealityStability = savedState.globalRealityStability || 100;
      this.anomalyResearchProgress = new Map(Object.entries(savedState.anomalyResearchProgress || {}));
      this.activeEffects = savedState.activeEffects || [];
    } catch (error) {
      console.error('[ANOMALY_CONTAINMENT] Failed to load state:', error);
    }
  }
}

// Singleton instance
export const anomalySystem = new AnomalyContainmentSystem();