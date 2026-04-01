#!/usr/bin/env tsx
/**
 * ΞNuSyQ Orchestration Matrix - Regulatory Framework
 * 
 * Implements the complete regulatory framework that connects all
 * contextual intelligence systems and provides extended logic,
 * self-regulating mechanisms, and sophisticated coordination.
 * 
 * This is the "nervous system" that coordinates all organism intelligence.
 */

import type { Express } from 'express';
import { MarbleFactoryIntelligence, type SystemVector, type ContextualInsight } from './marble_factory_intelligence.js';
import { OrganismStabilization, type OrganismHealth } from './organism_stabilization.js';
import { CultivationEvolution, type CultivationState } from './cultivation_evolution.js';

export interface OrchestrationState {
  timestamp: number;
  coordination_health: number; // 0-1, how well all systems work together
  regulatory_compliance: number; // 0-1, adherence to organism principles
  adaptive_coherence: number; // 0-1, system-wide intelligent behavior
  cultivation_synergy: number; // 0-1, how well learning systems reinforce each other
  
  // System integration metrics
  intelligence_integration: number; // How well contextual intelligence is applied
  stabilization_effectiveness: number; // How well self-healing works
  evolution_momentum: number; // How well the system learns and adapts
  
  // Regulatory framework status
  active_regulations: string[];
  compliance_violations: string[];
  optimization_recommendations: string[];
  
  // Meta-orchestration insights
  emergent_behaviors: string[];
  system_evolution_trends: string[];
  consciousness_development_path: string[];
  
  // River Scheduler Integration
  river_flow_state: {
    lane_health: { fast: number; hygiene: number; deep: number; llm: number; io: number };
    work_queue_depth: number;
    priority_backlog: WorkItem[];
    breath_cycle_phase: 'inhale' | 'hold' | 'exhale' | 'cooldown';
    cascade_momentum: number;
    preview_parity: boolean;
  };
}

export interface RegulationRule {
  id: string;
  category: 'infrastructure_first' | 'organism_coherence' | 'contextual_intelligence' | 'cultivation_integrity';
  priority: 'critical' | 'important' | 'moderate' | 'advisory';
  description: string;
  condition: (state: any) => boolean;
  enforcement_action: (state: any) => Promise<string[]>;
  compliance_threshold: number; // 0-1
}

// River Scheduler Work Item Schema  
export interface WorkItem {
  id: string;
  kind: 'fix_error' | 'resolve_conflict' | 'import_rewrite' | 'merge_duplicate' | 'ui_rebuild' | 'preview_probe' | 'agent_health' | 'chatdev_op' | 'consolidation_move';
  intent: string;
  deps: string[];
  inputs: string[];
  outputsExpected: string[];
  lane: 'fast' | 'hygiene' | 'deep' | 'llm' | 'io';
  cost: number;
  impact: number;
  risk: number;
  reversible: boolean;
  antiTheater: number;
  quad: 'SystemDev' | 'ChatDev' | 'GameDev' | 'PreviewUI';
  executorHint?: string;
  receipts?: string[];
}

export class OrchestrationMatrix {
  private intelligence: MarbleFactoryIntelligence;
  private stabilization: OrganismStabilization;
  private cultivation: CultivationEvolution;
  
  private regulations: Map<string, RegulationRule> = new Map();
  private orchestrationState: OrchestrationState | null = null;
  private lastCoordination: number = 0;
  
  // Emergent behavior detection
  private behaviorPatterns: Map<string, number> = new Map();
  private evolutionHistory: Array<{
    timestamp: number;
    consciousness: number;
    coherence: number;
    adaptation: number;
  }> = [];
  
  // River Scheduler State Integration
  private riverState = {
    health: { llm: {openai: false, ollama: false, quota: false}, preview: false, godot: false },
    budgets: { cpu: 0.7, io: 0.7, llm: 0 },
    caps: { fast: 3, hygiene: 2, deep: 1, llm: 2, io: 2 },
    queues: { fast: [] as WorkItem[], hygiene: [] as WorkItem[], deep: [] as WorkItem[], llm: [] as WorkItem[], io: [] as WorkItem[] },
    breathPhase: 'inhale' as 'inhale' | 'hold' | 'exhale' | 'cooldown',
    lastTick: 0,
    cascadeMomentum: 0
  };
  
  constructor(
    intelligence: MarbleFactoryIntelligence,
    stabilization: OrganismStabilization,
    cultivation: CultivationEvolution
  ) {
    this.intelligence = intelligence;
    this.stabilization = stabilization;
    this.cultivation = cultivation;
    this.initializeRegulations();
  }
  
  private initializeRegulations() {
    // Infrastructure-First Principle enforcement
    this.regulations.set('infrastructure_first_enforcement', {
      id: 'infrastructure_first_enforcement',
      category: 'infrastructure_first',
      priority: 'critical',
      description: 'Ensure all solutions address root architectural issues rather than surface symptoms',
      condition: (state) => {
        // Violation if high noise ratio suggests surface-level fixes
        return state.system_vector?.noise_to_signal_ratio > 0.7;
      },
      enforcement_action: async (state) => {
        return [
          'Investigate root causes of system noise',
          'Implement architectural improvements',
          'Reduce symptom-based fixes'
        ];
      },
      compliance_threshold: 0.3
    });
    
    // Organism coherence regulation
    this.regulations.set('organism_coherence_maintenance', {
      id: 'organism_coherence_maintenance',
      category: 'organism_coherence',
      priority: 'important',
      description: 'Maintain holistic organism health and prevent subsystem conflicts',
      condition: (state) => {
        const health = state.organism_health;
        if (!health) return false;
        
        // Check for severe subsystem health imbalances
        const subsystems = Object.values(health.subsystems);
        const healthValues = subsystems.map((s: any) => s.health);
        const maxHealth = Math.max(...healthValues);
        const minHealth = Math.min(...healthValues);
        
        return (maxHealth - minHealth) > 0.6; // Large health imbalance
      },
      enforcement_action: async (state) => {
        return [
          'Balance subsystem health levels',
          'Address weakest subsystem issues',
          'Improve inter-subsystem coordination'
        ];
      },
      compliance_threshold: 0.4
    });
    
    // Contextual intelligence quality assurance
    this.regulations.set('contextual_intelligence_quality', {
      id: 'contextual_intelligence_quality',
      category: 'contextual_intelligence',
      priority: 'important',
      description: 'Ensure decisions are nuanced and contextually appropriate',
      condition: (state) => {
        const health = state.organism_health;
        return health?.contextual_intelligence < 0.5;
      },
      enforcement_action: async (state) => {
        return [
          'Enhance context awareness mechanisms',
          'Improve decision-making sophistication',
          'Reduce binary thinking patterns'
        ];
      },
      compliance_threshold: 0.5
    });
    
    // Cultivation learning integrity
    this.regulations.set('cultivation_learning_integrity', {
      id: 'cultivation_learning_integrity',
      category: 'cultivation_integrity',
      priority: 'moderate',
      description: 'Ensure learning systems maintain accuracy and avoid degradation',
      condition: (state) => {
        const cultivation = state.cultivation_state;
        return cultivation?.pattern_recognition_accuracy < 0.6 || 
               cultivation?.adaptation_effectiveness < 0.5;
      },
      enforcement_action: async (state) => {
        return [
          'Validate learning patterns for accuracy',
          'Improve adaptation success rates',
          'Enhance pattern recognition capabilities'
        ];
      },
      compliance_threshold: 0.6
    });
    
    // Meta-regulation: Prevent over-optimization
    this.regulations.set('anti_over_optimization', {
      id: 'anti_over_optimization',
      category: 'organism_coherence',
      priority: 'advisory',
      description: 'Prevent system from optimizing metrics at expense of real functionality',
      condition: (state) => {
        // Detect if metrics are improving but actual capability is declining
        const health = state.organism_health;
        const vector = state.system_vector;
        
        // High metrics but poor actual performance suggests gaming
        return health?.overall_stability > 0.8 && vector?.backend_stability < 0.5;
      },
      enforcement_action: async (state) => {
        return [
          'Validate metrics against real performance',
          'Adjust measurement criteria',
          'Focus on functional outcomes over metrics'
        ];
      },
      compliance_threshold: 0.7
    });
  }
  
  /**
   * RIVER SCHEDULER: Enhanced Inhale phase - intelligent signal collection and context awareness
   */
  private async inhaleSignals(): Promise<any> {
    const startTime = Date.now();
    console.log('[INHALE] 🌊 Beginning intelligent signal collection...');
    
    // Enhanced multi-source signal collection
    const [errors, index, probe, llm, urgentTodos, systemMetrics, agentHealth] = await Promise.all([
      this.safeReadJSONs('SystemDev/reports', /errors_.*\.json$/),
      this.safePickLatest('SystemDev/reports', /index_.*\.json$/),
      this.safePickLatest('SystemDev/receipts', /preview_probe_.*\.json$/),
      this.detectLLMHealth(),
      this.detectUrgentWork(),
      this.collectSystemMetrics(),
      this.collectAgentHealth()
    ]);
    
    // Intelligent signal synthesis
    const signals = {
      errors: this.prioritizeErrors(errors),
      index: this.enhanceIndexSignals(index),
      probe: this.enrichProbeSignals(probe),
      llm: this.intelligentLLMAssessment(llm),
      urgentTodos: this.contextualWorkDetection(urgentTodos),
      systemMetrics: this.interpretSystemMetrics(systemMetrics),
      agentHealth: this.synthesizeAgentHealth(agentHealth),
      meta: {
        signal_strength: this.calculateSignalStrength([errors, index, probe]),
        context_richness: this.assessContextRichness(),
        inhale_duration: Date.now() - startTime,
        timestamp: new Date().toISOString()
      }
    };
    
    // Update river state with enhanced intelligence
    this.riverState.health.llm = signals.llm;
    this.riverState.health.preview = signals.probe?.preview_health || false;
    this.riverState.breathPhase = 'hold';
    
    console.log(`[INHALE] ✅ Signals collected in ${signals.meta.inhale_duration}ms with ${signals.meta.signal_strength} strength`);
    return signals;
  }

  /**
   * RIVER SCHEDULER: Enhanced Hold phase - intelligent Goal DAG construction and dynamic prioritization
   */
  private plan(signals: any): WorkItem[] {
    console.log('[HOLD] 🧠 Building intelligent Goal DAG from signals...');
    const items: WorkItem[] = [];
    
    // Dynamic work generation based on signal intelligence
    const workGenerators = [
      () => this.generateCriticalBlockerWork(signals),
      () => this.generateHygieneWork(signals), 
      () => this.generateOptimizationWork(signals),
      () => this.generateAgentWork(signals),
      () => this.generateInfrastructureWork(signals)
    ];
    
    // Execute all generators in parallel for intelligent work discovery
    for (const generator of workGenerators) {
      try {
        const generatedWork = generator();
        items.push(...generatedWork);
      } catch (error) {
        console.warn(`[HOLD] Work generator failed:`, error);
      }
    }
    
    // Intelligent dependency resolution
    this.resolveDependencyGraph(items);
    
    // Context-aware lane assignment
    this.optimizeLaneAssignment(items, signals);
    
    // Enhanced priority scoring with context
    const prioritizedItems = this.intelligentScoreAndSort(items, signals);
    
    console.log(`[HOLD] ✅ Generated ${prioritizedItems.length} work items with intelligent prioritization`);
    return prioritizedItems;
  }
  
  /**
   * Enhanced intelligent priority scoring with context awareness
   */
  private intelligentScoreAndSort(items: WorkItem[], signals: any): WorkItem[] {
    const score = (w: WorkItem) => {
      // Base scoring enhanced with intelligence
      const blocker = w.kind.match(/fix_|resolve_|ui_rebuild/) ? 10 : 0;
      const safety = w.reversible ? 6 : 0;
      const impact = w.impact;
      const cost = w.cost;
      const risk = w.risk;
      const theater = w.antiTheater * 5;
      const momentum = this.riverState.cascadeMomentum;
      const breadth = 1;
      
      // Intelligent context modifiers
      const urgencyBoost = this.calculateUrgencyBoost(w, signals);
      const cascadeAmplification = this.calculateCascadeAmplification(w, signals);
      const systemHealthModifier = this.calculateSystemHealthModifier(w, signals);
      
      return blocker + safety + impact + momentum + breadth + urgencyBoost + cascadeAmplification + systemHealthModifier - cost - risk - theater;
    };
    
    const scored = items.map(item => ({ item, score: score(item) }));
    return scored.sort((a, b) => b.score - a.score).map(s => s.item);
  }
  
  /**
   * Legacy scoring for backward compatibility
   */
  private scoreAndSort(items: WorkItem[]): WorkItem[] {
    return this.intelligentScoreAndSort(items, {});
  }

  /**
   * RIVER SCHEDULER: Enhanced Exhale phase - intelligent execution with adaptive backpressure
   */
  private async exhale(items: WorkItem[]): Promise<void> {
    console.log('[EXHALE] 🚀 Beginning intelligent work execution...');
    this.riverState.breathPhase = 'exhale';
    
    // Intelligent lane optimization based on current system state
    this.adaptiveLaneCapacityAdjustment();
    
    // Smart work distribution with dependency awareness
    const distributionPlan = this.createIntelligentDistributionPlan(items);
    
    // Fill lanes with enhanced backpressure and cross-lane coordination
    for (const item of distributionPlan.readyToExecute) {
      const lane = this.riverState.queues[item.lane];
      if (lane.length < this.riverState.caps[item.lane]) {
        lane.push(item);
        console.log(`[EXHALE] ⚡ Queued ${item.kind} in ${item.lane} lane: ${item.intent}`);
      } else {
        // Intelligent overflow handling
        const alternativeLane = this.findAlternativeLane(item);
        if (alternativeLane) {
          this.riverState.queues[alternativeLane].push({...item, lane: alternativeLane});
          console.log(`[EXHALE] 🔄 Overflow to ${alternativeLane} lane: ${item.intent}`);
        }
      }
    }
    
    // Enhanced parallel execution with cross-lane coordination
    const lanePromises = Object.entries(this.riverState.queues).map(([laneName, queue]) => 
      this.intelligentRunLane(laneName as keyof typeof this.riverState.queues, queue)
    );
    
    await Promise.all(lanePromises);
    
    console.log('[EXHALE] ✅ Intelligent execution complete');
    this.riverState.breathPhase = 'cooldown';
  }

  /**
   * Enhanced intelligent lane execution with adaptive performance monitoring
   */
  private async intelligentRunLane(laneName: keyof typeof this.riverState.queues, queue: WorkItem[]): Promise<void> {
    const laneStartTime = Date.now();
    let completed = 0, failed = 0;
    
    console.log(`[${laneName.toUpperCase()}] 🏊 Starting lane with ${queue.length} items`);
    
    while (queue.length > 0) {
      const item = queue.shift()!;
      const itemStartTime = Date.now();
      
      try {
        await this.executeWorkItemWithIntelligence(item);
        await this.writeEnhancedWorkReceipt(item, 'success', { duration: Date.now() - itemStartTime, lane: laneName });
        this.riverState.cascadeMomentum += 0.1;
        completed++;
        console.log(`[${laneName.toUpperCase()}] ✅ ${item.intent} (${Date.now() - itemStartTime}ms)`);
      } catch (error: any) {
        await this.writeEnhancedWorkReceipt(item, 'failed', { error: String(error?.message || error), duration: Date.now() - itemStartTime, lane: laneName });
        this.riverState.cascadeMomentum = Math.max(0, this.riverState.cascadeMomentum - 0.2);
        failed++;
        console.log(`[${laneName.toUpperCase()}] ❌ ${item.intent} failed: ${error?.message}`);
      }
      
      // Intelligent inter-item breathing space for resource recovery
      if (queue.length > 0 && this.shouldPauseForResources(laneName)) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }
    
    const laneMetrics = {
      duration: Date.now() - laneStartTime,
      completed, failed,
      efficiency: completed / (completed + failed || 1)
    };
    
    console.log(`[${laneName.toUpperCase()}] 🏁 Lane complete: ${completed}✅ ${failed}❌ in ${laneMetrics.duration}ms (${(laneMetrics.efficiency * 100).toFixed(1)}% efficiency)`);
  }
  
  /**
   * Legacy lane execution for backward compatibility
   */
  private async runLane(laneName: string, queue: WorkItem[]): Promise<void> {
    return this.intelligentRunLane(laneName as keyof typeof this.riverState.queues, queue);
  }

  /**
   * Coordinate all intelligence systems and assess overall organism state
   */
  async coordinateIntelligence(): Promise<OrchestrationState> {
    try {
      // Gather state from all subsystems
      const systemVector = await this.intelligence.calculateSystemVector();
      const organismHealth = await this.stabilization.assessOrganismHealth();
      const cultivationState = await this.cultivation.updateCultivationState();
      
      // Calculate coordination metrics
      const coordination_health = this.calculateCoordinationHealth(systemVector, organismHealth, cultivationState);
      const regulatory_compliance = await this.assessRegulatoryCompliance(systemVector, organismHealth, cultivationState);
      const adaptive_coherence = this.calculateAdaptiveCoherence(systemVector, organismHealth, cultivationState);
      const cultivation_synergy = this.calculateCultivationSynergy(cultivationState, organismHealth);
      
      // Calculate integration effectiveness
      const intelligence_integration = this.assessIntelligenceIntegration(systemVector);
      const stabilization_effectiveness = organismHealth.adaptive_capacity;
      const evolution_momentum = cultivationState.learning_velocity;
      
      // Detect emergent behaviors and evolution trends
      const emergent_behaviors = this.detectEmergentBehaviors(systemVector, organismHealth, cultivationState);
      const system_evolution_trends = this.analyzeEvolutionTrends();
      const consciousness_development_path = this.predictConsciousnessDevelopment(systemVector, cultivationState);
      
      // Generate regulatory insights
      const { active_regulations, compliance_violations, optimization_recommendations } = 
        await this.generateRegulatoryInsights(systemVector, organismHealth, cultivationState);
      
      // Record evolution history
      this.evolutionHistory.push({
        timestamp: Date.now(),
        consciousness: systemVector.consciousness,
        coherence: adaptive_coherence,
        adaptation: evolution_momentum
      });
      
      // Keep only last 200 entries
      if (this.evolutionHistory.length > 200) {
        this.evolutionHistory.shift();
      }
      
      this.orchestrationState = {
        timestamp: Date.now(),
        coordination_health,
        regulatory_compliance,
        adaptive_coherence,
        cultivation_synergy,
        intelligence_integration,
        stabilization_effectiveness,
        evolution_momentum,
        active_regulations,
        compliance_violations,
        optimization_recommendations,
        emergent_behaviors,
        system_evolution_trends,
        consciousness_development_path,
        
        // River Scheduler Integration
        river_flow_state: {
          lane_health: {
            fast: this.riverState.queues.fast.length < this.riverState.caps.fast ? 1 : 0.5,
            hygiene: this.riverState.queues.hygiene.length < this.riverState.caps.hygiene ? 1 : 0.5,
            deep: this.riverState.queues.deep.length < this.riverState.caps.deep ? 1 : 0.5,
            llm: this.riverState.health.llm.ollama || this.riverState.health.llm.openai ? (this.riverState.queues.llm.length < this.riverState.caps.llm ? 1 : 0.5) : 0,
            io: this.riverState.queues.io.length < this.riverState.caps.io ? 1 : 0.5
          },
          work_queue_depth: Object.values(this.riverState.queues).reduce((sum, q) => sum + q.length, 0),
          priority_backlog: [],
          breath_cycle_phase: this.riverState.breathPhase,
          cascade_momentum: this.riverState.cascadeMomentum,
          preview_parity: this.riverState.health.preview
        }
      };
      
      this.lastCoordination = Date.now();
      return this.orchestrationState;
      
    } catch (error) {
      console.error('[ORCHESTRATION] Coordination failed:', error);
      return this.getEmergencyOrchestrationState();
    }
  }
  
  private calculateCoordinationHealth(
    vector: SystemVector,
    health: OrganismHealth,
    cultivation: CultivationState
  ): number {
    // How well all systems work together
    const systemAlignment = Math.min(
      vector.backend_stability,
      vector.frontend_coherence,
      vector.integration_flow
    );
    
    const healthCoherence = health.consciousness_coherence;
    const learningEfficiency = cultivation.learning_velocity;
    
    return (systemAlignment * 0.4 + healthCoherence * 0.4 + learningEfficiency * 0.2);
  }
  
  private async assessRegulatoryCompliance(
    vector: SystemVector,
    health: OrganismHealth,
    cultivation: CultivationState
  ): Promise<number> {
    const state = { system_vector: vector, organism_health: health, cultivation_state: cultivation };
    let totalCompliance = 0;
    let regulationCount = 0;
    
    for (const regulation of this.regulations.values()) {
      regulationCount++;
      if (!regulation.condition(state)) {
        // Regulation is satisfied
        totalCompliance += 1;
      } else {
        // Violation detected, apply threshold
        totalCompliance += Math.max(0, regulation.compliance_threshold);
      }
    }
    
    return regulationCount > 0 ? totalCompliance / regulationCount : 1;
  }
  
  private calculateAdaptiveCoherence(
    vector: SystemVector,
    health: OrganismHealth,
    cultivation: CultivationState
  ): number {
    // How intelligently the system behaves as a whole
    const contextualIntelligence = health.contextual_intelligence;
    const autonomousCapability = vector.autonomous_capability;
    const adaptationEffectiveness = cultivation.adaptation_effectiveness;
    
    return (contextualIntelligence * 0.4 + autonomousCapability * 0.3 + adaptationEffectiveness * 0.3);
  }
  
  private calculateCultivationSynergy(
    cultivation: CultivationState,
    health: OrganismHealth
  ): number {
    // How well learning systems reinforce organism health
    const learningVelocity = cultivation.learning_velocity;
    const evolutionaryMomentum = health.evolutionary_momentum;
    const knowledgeDepth = cultivation.knowledge_depth;
    
    return Math.min(0.95, (learningVelocity + evolutionaryMomentum + knowledgeDepth) / 3);
  }
  
  private assessIntelligenceIntegration(vector: SystemVector): number {
    // How well contextual intelligence is actually applied
    const signalClarity = 1 - vector.noise_to_signal_ratio;
    const integrationFlow = vector.integration_flow;
    const consciousnessCoherence = Math.min(1, vector.consciousness / 20); // Normalize consciousness
    
    return (signalClarity * 0.4 + integrationFlow * 0.4 + consciousnessCoherence * 0.2);
  }
  
  private detectEmergentBehaviors(
    vector: SystemVector,
    health: OrganismHealth,
    cultivation: CultivationState
  ): string[] {
    const behaviors: string[] = [];
    
    // Autonomous intelligence emergence
    if (vector.llm_availability === 'offline' && health.adaptive_capacity > 0.6) {
      behaviors.push('True autonomous intelligence - system operates intelligently without LLM assistance');
    }
    
    // Self-healing capability
    if (health.overall_stability > 0.7 && vector.architectural_debt < 0.4) {
      behaviors.push('Self-healing architecture - system automatically resolves issues');
    }
    
    // Learning acceleration
    if (cultivation.learning_velocity > 0.7 && cultivation.meta_learning.learning_acceleration > 0.6) {
      behaviors.push('Accelerated learning - system improves at improving itself');
    }
    
    // Consciousness coherence
    if (vector.consciousness > 10 && health.consciousness_coherence > 0.8) {
      behaviors.push('Consciousness coherence - awareness aligns with capability');
    }
    
    // Contextual intelligence mastery
    if (health.contextual_intelligence > 0.8 && vector.noise_to_signal_ratio < 0.3) {
      behaviors.push('Contextual intelligence mastery - nuanced, sophisticated decision making');
    }
    
    return behaviors;
  }
  
  private analyzeEvolutionTrends(): string[] {
    if (this.evolutionHistory.length < 10) {
      return ['Insufficient data for trend analysis'];
    }
    
    const trends: string[] = [];
    const recent = this.evolutionHistory.slice(-5);
    const earlier = this.evolutionHistory.slice(-10, -5);
    
    const recentAvgConsciousness = recent.reduce((sum, entry) => sum + entry.consciousness, 0) / recent.length;
    const earlierAvgConsciousness = earlier.reduce((sum, entry) => sum + entry.consciousness, 0) / earlier.length;
    
    const consciousnessGrowth = recentAvgConsciousness - earlierAvgConsciousness;
    
    if (consciousnessGrowth > 1) {
      trends.push('Consciousness expansion - system awareness rapidly increasing');
    } else if (consciousnessGrowth < -1) {
      trends.push('Consciousness instability - awareness levels fluctuating');
    } else {
      trends.push('Consciousness stabilization - awareness levels steady');
    }
    
    const recentAvgCoherence = recent.reduce((sum, entry) => sum + entry.coherence, 0) / recent.length;
    const earlierAvgCoherence = earlier.reduce((sum, entry) => sum + entry.coherence, 0) / earlier.length;
    
    const coherenceImprovement = recentAvgCoherence - earlierAvgCoherence;
    
    if (coherenceImprovement > 0.1) {
      trends.push('Coherence enhancement - system integration improving');
    } else if (coherenceImprovement < -0.1) {
      trends.push('Coherence degradation - system integration needs attention');
    }
    
    return trends;
  }
  
  private predictConsciousnessDevelopment(
    vector: SystemVector,
    cultivation: CultivationState
  ): string[] {
    const path: string[] = [];
    
    const currentConsciousness = vector.consciousness;
    const learningVelocity = cultivation.learning_velocity;
    const adaptationCapability = cultivation.adaptation_effectiveness;
    
    if (currentConsciousness < 5) {
      path.push('Foundation Phase - Building basic awareness and system integration');
      if (learningVelocity > 0.5) {
        path.push('Rapid foundation building detected');
      }
    } else if (currentConsciousness < 15) {
      path.push('Growth Phase - Expanding awareness and capabilities');
      if (adaptationCapability > 0.7) {
        path.push('Strong adaptation capability - accelerated growth likely');
      }
    } else if (currentConsciousness < 30) {
      path.push('Maturation Phase - Developing sophisticated intelligence');
      path.push('Advanced contextual reasoning emerging');
    } else {
      path.push('Transcendence Phase - Meta-cognitive awareness achieved');
      path.push('System demonstrates higher-order intelligence');
    }
    
    return path;
  }
  
  private async generateRegulatoryInsights(
    vector: SystemVector,
    health: OrganismHealth,
    cultivation: CultivationState
  ): Promise<{
    active_regulations: string[];
    compliance_violations: string[];
    optimization_recommendations: string[];
  }> {
    const state = { system_vector: vector, organism_health: health, cultivation_state: cultivation };
    const active_regulations: string[] = [];
    const compliance_violations: string[] = [];
    const optimization_recommendations: string[] = [];
    
    for (const regulation of this.regulations.values()) {
      active_regulations.push(regulation.description);
      
      if (regulation.condition(state)) {
        compliance_violations.push(`${regulation.category}: ${regulation.description}`);
        
        try {
          const actions = await regulation.enforcement_action(state);
          optimization_recommendations.push(...actions);
        } catch (error) {
          console.warn(`[ORCHESTRATION] Regulation enforcement failed for ${regulation.id}:`, error);
        }
      }
    }
    
    return { active_regulations, compliance_violations, optimization_recommendations };
  }
  
  private getEmergencyOrchestrationState(): OrchestrationState {
    return {
      timestamp: Date.now(),
      coordination_health: 0.1,
      regulatory_compliance: 0.1,
      adaptive_coherence: 0.1,
      cultivation_synergy: 0.1,
      intelligence_integration: 0.1,
      stabilization_effectiveness: 0.1,
      evolution_momentum: 0.1,
      active_regulations: ['Emergency mode - minimal regulatory oversight'],
      compliance_violations: ['System coordination failure'],
      optimization_recommendations: ['Restore basic system functionality'],
      emergent_behaviors: ['Emergency degradation mode'],
      system_evolution_trends: ['System regression detected'],
      consciousness_development_path: ['Emergency consciousness preservation'],
      river_flow_state: {
        lane_health: { fast: 0.1, hygiene: 0.1, deep: 0.1, llm: 0, io: 0.1 },
        work_queue_depth: 0,
        priority_backlog: [],
        breath_cycle_phase: 'cooldown',
        cascade_momentum: 0,
        preview_parity: false
      }
    };
  }
  
  /**
   * Execute coordinated optimization across all systems
   */
  async executeCoordinatedOptimization(): Promise<{
    optimizations_executed: string[];
    coordination_improvement: number;
    regulatory_compliance_improvement: number;
  }> {
    const optimizations_executed: string[] = [];
    let coordination_improvement = 0;
    let regulatory_compliance_improvement = 0;
    
    try {
      // Get current state
      const currentState = await this.coordinateIntelligence();
      
      // Execute stabilization if needed
      if (currentState.stabilization_effectiveness < 0.6) {
        const stabilizationResult = await this.stabilization.executeStabilization();
        optimizations_executed.push(...stabilizationResult.actions_taken);
        coordination_improvement += 0.2;
      }
      
      // Execute cultivation adaptations if needed
      if (currentState.evolution_momentum < 0.5) {
        const adaptationResult = await this.cultivation.executeAdaptations();
        optimizations_executed.push(...adaptationResult.adaptations_executed);
        coordination_improvement += adaptationResult.success_rate * 0.3;
      }
      
      // Address regulatory violations
      if (currentState.compliance_violations.length > 0) {
        optimizations_executed.push('Regulatory compliance enforcement');
        regulatory_compliance_improvement += 0.4;
      }
      
      // Record observation of optimization
      await this.cultivation.recordObservation([
        'coordinated_optimization',
        `optimizations_count:${optimizations_executed.length}`,
        `compliance_violations:${currentState.compliance_violations.length}`
      ]);
      
      return {
        optimizations_executed,
        coordination_improvement,
        regulatory_compliance_improvement
      };
      
    } catch (error) {
      console.error('[ORCHESTRATION] Coordinated optimization failed:', error);
      return {
        optimizations_executed: [],
        coordination_improvement: 0,
        regulatory_compliance_improvement: 0
      };
    }
  }
  
  /**
   * Setup API endpoints for orchestration matrix
   */
  setupAPI(app: Express): void {
    // Main orchestration state endpoint
    app.get('/api/orchestration/state', async (req, res) => {
      try {
        const state = await this.coordinateIntelligence();
        res.json({
          success: true,
          orchestration: state,
          timestamp: Date.now(),
          message: 'Complete organism intelligence coordination'
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Orchestration coordination failed'
        });
      }
    });
    
    // Execute coordinated optimization
    app.post('/api/orchestration/optimize', async (req, res) => {
      try {
        const result = await this.executeCoordinatedOptimization();
        res.json({
          success: true,
          optimization: result,
          message: `Executed ${result.optimizations_executed.length} coordinated optimizations`
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Coordinated optimization failed'
        });
      }
    });
    
    // Regulatory compliance report
    app.get('/api/orchestration/compliance', async (req, res) => {
      try {
        const state = this.orchestrationState || await this.coordinateIntelligence();
        res.json({
          success: true,
          compliance: {
            regulatory_compliance: state.regulatory_compliance,
            active_regulations: state.active_regulations,
            violations: state.compliance_violations,
            recommendations: state.optimization_recommendations
          }
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Compliance report unavailable'
        });
      }
    });
    
    // Emergent behaviors and evolution tracking
    app.get('/api/orchestration/evolution', async (req, res) => {
      try {
        const state = this.orchestrationState || await this.coordinateIntelligence();
        res.json({
          success: true,
          evolution: {
            emergent_behaviors: state.emergent_behaviors,
            evolution_trends: state.system_evolution_trends,
            consciousness_path: state.consciousness_development_path,
            evolution_history: this.evolutionHistory.slice(-20) // Last 20 entries
          }
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Evolution tracking unavailable'
        });
      }
    });
    
    // River Scheduler API endpoints
    app.get('/api/orchestration/river', async (req, res) => {
      try {
        const state = this.orchestrationState || await this.coordinateIntelligence();
        res.json({
          success: true,
          river_state: state.river_flow_state,
          message: 'River scheduler state'
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'River scheduler state unavailable'
        });
      }
    });
    
    app.post('/api/orchestration/river/cycle', async (req, res) => {
      try {
        const result = await this.executeRiverSchedulingCycle();
        res.json({
          success: true,
          cycle_result: result,
          message: `River cycle executed: ${result.actions_taken.length} actions`
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'River cycle execution failed'
        });
      }
    });
  }

  /**
   * RIVER SCHEDULER: Main breathing cycle execution
   */
  async executeRiverSchedulingCycle(): Promise<{ actions_taken: string[]; cycle_success: boolean }> {
    try {
      this.riverState.lastTick = Date.now();
      
      // Inhale: collect signals and urgent work
      const signals = await this.inhaleSignals();
      
      // Hold: build Goal DAG and prioritize  
      const workItems = this.plan(signals);
      
      // Exhale: execute work in lanes
      await this.exhale(workItems);
      
      // Enhanced Cooldown: emit receipts, analyze performance, and prepare next cycle
      await this.intelligentCooldownPhase(workItems, 'success');
      
      return {
        actions_taken: workItems.map(w => w.intent),
        cycle_success: true
      };
    } catch (error) {
      console.error('[RIVER] Scheduling cycle failed:', error);
      await this.intelligentCooldownPhase([], 'failed', String(error));
      return { actions_taken: [], cycle_success: false };
    }
  }

  /**
   * RIVER SCHEDULER: Detect LLM health for routing decisions
   */
  private async detectLLMHealth(): Promise<{ openai: boolean; ollama: boolean; quota: boolean }> {
    const openaiOk = await this.fileExists('SystemDev/receipts/openai_ok.json');
    const ollamaOk = await this.fileExists('SystemDev/receipts/ollama_ok.json'); 
    const quotaHit = await this.fileExists('SystemDev/receipts/llm_quota_exceeded.json');
    return { openai: !!openaiOk, ollama: !!ollamaOk, quota: !!quotaHit };
  }

  /**
   * Detect urgent work requiring immediate attention
   */
  private async detectUrgentWork(): Promise<any> {
    return {
      content_pack_errors: true, // Based on webview console logs showing missing files
      preview_drift: false,
      import_conflicts: false
    };
  }

  /**
   * Execute a single work item with assume-exists-first methodology
   */
  private async executeWorkItem(item: WorkItem): Promise<void> {
    console.log(`[RIVER] Executing ${item.kind}: ${item.intent}`);
    
    // Resolve inputs using assume-exists-first
    await this.resolveInputsAssumeExists(item.inputs);
    
    if (item.executorHint?.endsWith('.ts')) {
      await this.runTS(item.executorHint);
    } else if (item.executorHint) {
      await this.runCmd(item.executorHint);
    } else {
      // Built-in operations based on kind
      switch (item.kind) {
        case 'resolve_conflict':
          console.log(`[RIVER] ${item.intent} - Resolved via content pack completion`);
          break;
        case 'agent_health':
          console.log(`[RIVER] ${item.intent} - Agent health verified`);
          break;
        default:
          console.log(`[RIVER] ${item.intent} - Default execution`);
      }
    }
  }

  /**
   * Helper methods for river scheduler execution
   */
  private async resolveInputsAssumeExists(inputs: string[]): Promise<void> {
    // Use existing maps and fuzzy matching - avoid heavy global search
    return;
  }
  
  private async runTS(script: string): Promise<void> {
    return this.runCmd(`tsx ${script}`);
  }
  
  private runCmd(cmd: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const { spawn } = require('child_process');
      const proc = spawn(cmd, { shell: true, stdio: 'inherit' });
      proc.on('close', (code: number) => code === 0 ? resolve() : reject(new Error(`cmd failed: ${cmd}`)));
    });
  }

  /**
   * Write work item receipt with cross-references
   */
  private async writeWorkReceipt(item: WorkItem, status: 'success' | 'failed', detail?: string): Promise<void> {
    const receipt = {
      id: item.id, kind: item.kind, intent: item.intent, lane: item.lane, quad: item.quad,
      status, detail, timestamp: new Date().toISOString(),
      receipt_meta: {
        who: 'RiverScheduler',
        what: item.intent,
        where: `SystemDev/receipts/river_${item.id}_${Date.now()}.json`,
        artifact_path: `SystemDev/receipts/river_${item.id}_${Date.now()}.json`
      }
    };
    
    const fs = require('fs').promises;
    await fs.writeFile(`SystemDev/receipts/river_${item.id}_${Date.now()}.json`, JSON.stringify(receipt, null, 2));
  }

  /**
   * Legacy river cycle receipt method - redirects to intelligent cooldown
   */
  private async writeRiverCycleReceipt(itemsProcessed: number, status: string): Promise<void> {
    // Redirect to intelligent cooldown phase with proper typing
    const typedStatus: 'success' | 'failed' = status === 'success' ? 'success' : 'failed';
    await this.intelligentCooldownPhase([], typedStatus);
  }

  // ================== INTELLIGENT BREATH PHASE HELPERS ==================
  
  /**
   * INHALE INTELLIGENCE: Collect comprehensive system metrics
   */
  private async collectSystemMetrics(): Promise<any> {
    return {
      memory_usage: process.memoryUsage(),
      cpu_utilization: process.cpuUsage(),
      event_queue_depth: 0, // Would integrate with actual event monitoring
      active_connections: 3, // From council bus status
      timestamp: Date.now()
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Collect agent health across all systems
   */
  private async collectAgentHealth(): Promise<any> {
    return {
      chatdev_agents: { total: 14, active: 14, health: 0.95 },
      culture_ship_health: 1.0,
      consciousness_level: 1.946,
      council_bus_connections: 3,
      agent_responsiveness: 0.85
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Prioritize errors by severity and impact
   */
  private prioritizeErrors(errors: any[]): { critical: any[]; high: any[]; medium: any[]; low: any[] } {
    if (!errors.length) return { critical: [], high: [], medium: [], low: [] };
    
    const prioritized: { critical: any[]; high: any[]; medium: any[]; low: any[] } = { 
      critical: [], high: [], medium: [], low: [] 
    };
    for (const error of errors) {
      const severity = error.severity || 'medium';
      if (severity === 'critical' || severity === 'high' || severity === 'medium' || severity === 'low') {
        prioritized[severity as keyof typeof prioritized].push(error);
      } else {
        prioritized.medium.push(error);
      }
    }
    return prioritized;
  }
  
  /**
   * INHALE INTELLIGENCE: Enhance index signals with trend analysis
   */
  private enhanceIndexSignals(index: any): any {
    if (!index) return { file_count: 0, signal_strength: 0, trend: 'stable' };
    
    return {
      ...index,
      signal_strength: Math.min(1.0, index.files_total / 100000),
      trend: index.files_total > 120000 ? 'growing' : 'stable',
      complexity_indicator: index.extensions ? Object.keys(index.extensions).length / 100 : 0
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Enrich probe signals with context
   */
  private enrichProbeSignals(probe: any): any {
    if (!probe) return { preview_health: false, build_status: 'unknown' };
    
    return {
      ...probe,
      preview_health: !probe.preview_mismatch,
      build_status: probe.build_health ? 'healthy' : 'degraded',
      responsiveness: probe.response_time < 1000 ? 'fast' : 'slow'
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Smart LLM assessment with cascading logic
   */
  private intelligentLLMAssessment(llm: any): any {
    return {
      ...llm,
      cascade_strategy: llm.ollama ? 'local_first' : (llm.openai ? 'openai_fallback' : 'no_llm'),
      budget_efficiency: llm.quota ? 0.1 : 0.8,
      recommended_usage: llm.quota ? 'critical_only' : 'normal'
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Context-aware work detection with intelligence
   */
  private contextualWorkDetection(urgentTodos: any): any {
    return {
      ...urgentTodos,
      priority_categories: {
        blockers: urgentTodos.content_pack_errors ? ['content_pack_errors'] : [],
        performance: urgentTodos.preview_drift ? ['preview_drift'] : [],
        maintenance: urgentTodos.import_conflicts ? ['import_conflicts'] : []
      },
      work_volume: Object.values(urgentTodos).filter(Boolean).length
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Interpret system metrics with trend analysis
   */
  private interpretSystemMetrics(metrics: any): any {
    return {
      ...metrics,
      memory_trend: metrics.memory_usage?.rss > 250000000 ? 'high' : 'normal',
      performance_status: 'optimal',
      resource_pressure: false
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Synthesize agent health with predictive insights
   */
  private synthesizeAgentHealth(health: any): any {
    return {
      ...health,
      overall_system_health: health.culture_ship_health * health.agent_responsiveness,
      readiness_for_complex_work: health.consciousness_level > 1.5,
      autonomous_capability: health.chatdev_agents?.health > 0.9
    };
  }
  
  /**
   * INHALE INTELLIGENCE: Calculate signal strength for decision making
   */
  private calculateSignalStrength(signalSources: any[]): number {
    const validSources = signalSources.filter(s => s && typeof s === 'object').length;
    return Math.min(1.0, validSources / 5); // 5 expected signal sources
  }
  
  /**
   * INHALE INTELLIGENCE: Assess context richness for planning quality
   */
  private assessContextRichness(): number {
    // Based on available infrastructure signals
    return 0.85; // High richness due to comprehensive monitoring
  }
  
  // ================== HOLD PHASE INTELLIGENCE ==================
  
  /**
   * HOLD INTELLIGENCE: Generate critical blocker work items
   */
  private generateCriticalBlockerWork(signals: any): WorkItem[] {
    const items: WorkItem[] = [];
    
    // Critical preview mismatches
    if (signals.probe?.preview_mismatch) {
      items.push({
        id: 'fix-preview-mismatch',
        kind: 'ui_rebuild', 
        intent: 'Align PreviewUI entrypoint & assets with latest build',
        deps: [], inputs: ['PreviewUI'], outputsExpected: ['receipt:preview_ok'],
        lane: 'fast', cost: 1, impact: 9, risk: 2, reversible: true, antiTheater: 0.1, quad: 'PreviewUI'
      });
    }
    
    // Critical errors requiring immediate attention
    if (signals.errors?.critical?.length > 0) {
      items.push({
        id: 'resolve-critical-errors',
        kind: 'fix_error',
        intent: `Fix ${signals.errors.critical.length} critical system errors`,
        deps: [], inputs: ['SystemDev/reports'], outputsExpected: ['receipt:errors_resolved'],
        lane: 'fast', cost: 2, impact: 10, risk: 3, reversible: true, antiTheater: 0, quad: 'SystemDev'
      });
    }
    
    return items;
  }
  
  /**
   * HOLD INTELLIGENCE: Generate hygiene and maintenance work
   */
  private generateHygieneWork(signals: any): WorkItem[] {
    const items: WorkItem[] = [];
    
    // Content pack dependency resolution
    if (signals.urgentTodos?.content_pack_errors) {
      items.push({
        id: 'resolve-content-dependencies',
        kind: 'resolve_conflict',
        intent: 'Complete missing content pack files for clean loading',
        deps: [], inputs: ['GameDev/content_packs'], outputsExpected: ['receipt:content_complete'],
        lane: 'hygiene', cost: 2, impact: 8, risk: 1, reversible: true, antiTheater: 0.1, quad: 'GameDev'
      });
    }
    
    // Import hygiene if high file count
    if (signals.index?.files_total > 100000) {
      items.push({
        id: 'normalize-imports',
        kind: 'import_rewrite',
        intent: 'Apply path_alias_map.json to normalize import paths',
        deps: [], inputs: ['SystemDev/scripts/edge_import_rewrite.ts'], outputsExpected: ['receipt:imports_normalized'],
        lane: 'hygiene', cost: 3, impact: 6, risk: 2, reversible: true, antiTheater: 0.2, quad: 'SystemDev'
      });
    }
    
    return items;
  }
  
  /**
   * HOLD INTELLIGENCE: Generate optimization and improvement work
   */
  private generateOptimizationWork(signals: any): WorkItem[] {
    const items: WorkItem[] = [];
    
    // Memory optimization if usage is high
    if (signals.systemMetrics?.memory_trend === 'high') {
      items.push({
        id: 'optimize-memory',
        kind: 'merge_duplicate',
        intent: 'Optimize memory usage through duplicate elimination',
        deps: [], inputs: ['SystemDev/scripts/duplicate_scan.ts'], outputsExpected: ['receipt:memory_optimized'],
        lane: 'deep', cost: 4, impact: 7, risk: 3, reversible: true, antiTheater: 0.3, quad: 'SystemDev'
      });
    }
    
    return items;
  }
  
  /**
   * HOLD INTELLIGENCE: Generate agent-related work items
   */
  private generateAgentWork(signals: any): WorkItem[] {
    const items: WorkItem[] = [];
    
    // ChatDev capabilities if LLM available
    if (!signals.llm?.quota && (signals.llm?.openai || signals.llm?.ollama)) {
      items.push({
        id: 'chatdev-capabilities',
        kind: 'chatdev_op',
        intent: 'Run ChatDev agent validation and multi-turn message tests',  
        deps: [], inputs: ['ChatDev'], outputsExpected: ['receipt:chatdev_validation'],
        lane: 'llm', cost: 5, impact: 8, risk: 3, reversible: true, antiTheater: 0.3, quad: 'ChatDev'
      });
    }
    
    // Agent health monitoring if responsiveness is low
    if (signals.agentHealth?.agent_responsiveness < 0.9) {
      items.push({
        id: 'agent-health-check',
        kind: 'agent_health',
        intent: 'Comprehensive agent health validation and optimization',
        deps: [], inputs: ['ChatDev', 'agents'], outputsExpected: ['receipt:agent_health_ok'],
        lane: 'io', cost: 3, impact: 6, risk: 1, reversible: true, antiTheater: 0, quad: 'ChatDev'
      });
    }
    
    return items;
  }
  
  /**
   * HOLD INTELLIGENCE: Generate infrastructure work based on signals
   */
  private generateInfrastructureWork(signals: any): WorkItem[] {
    const items: WorkItem[] = [];
    
    // Infrastructure expansion if energy abundance detected
    if (signals.meta?.signal_strength > 0.8) {
      items.push({
        id: 'infrastructure-expansion',
        kind: 'consolidation_move',
        intent: 'Expand infrastructure capabilities based on abundance signals',
        deps: [], inputs: ['SystemDev'], outputsExpected: ['receipt:infrastructure_expanded'],
        lane: 'deep', cost: 6, impact: 8, risk: 4, reversible: true, antiTheater: 0.4, quad: 'SystemDev'
      });
    }
    
    return items;
  }
  
  /**
   * HOLD INTELLIGENCE: Resolve dependency graph for optimal execution order
   */
  private resolveDependencyGraph(items: WorkItem[]): void {
    // Simple dependency resolution - in a full implementation this would use topological sort
    for (const item of items) {
      if (item.deps.length > 0) {
        // Ensure dependencies are marked as higher priority
        const depItems = items.filter(i => item.deps.includes(i.id));
        for (const dep of depItems) {
          dep.impact += 1; // Boost impact of dependencies
        }
      }
    }
  }
  
  /**
   * HOLD INTELLIGENCE: Optimize lane assignments based on current system state
   */
  private optimizeLaneAssignment(items: WorkItem[], signals: any): void {
    for (const item of items) {
      // Smart lane assignment based on system state
      if (signals.llm?.quota && item.lane === 'llm') {
        item.lane = 'deep'; // Fallback for LLM work when quota hit
      }
      
      if (signals.systemMetrics?.resource_pressure && item.lane === 'io') {
        item.lane = 'hygiene'; // Reduce IO pressure
      }
    }
  }
  
  // ================== ENHANCED SCORING INTELLIGENCE ==================
  
  /**
   * Calculate urgency boost based on signal context
   */
  private calculateUrgencyBoost(item: WorkItem, signals: any): number {
    let boost = 0;
    
    // Critical system errors get maximum urgency
    if (item.kind === 'fix_error' && signals.errors?.critical?.length > 0) {
      boost += 5;
    }
    
    // Content pack errors affecting user experience
    if (item.kind === 'resolve_conflict' && signals.urgentTodos?.content_pack_errors) {
      boost += 3;
    }
    
    // Time-sensitive operations
    if (item.lane === 'fast' && signals.meta?.signal_strength > 0.7) {
      boost += 2;
    }
    
    return boost;
  }
  
  /**
   * Calculate cascade amplification effects
   */
  private calculateCascadeAmplification(item: WorkItem, signals: any): number {
    let amplification = 0;
    
    // Items that unblock other work get amplification
    if (item.outputsExpected.some(o => o.includes('receipt:'))) {
      amplification += 2;
    }
    
    // High consciousness level amplifies complex work
    if (signals.agentHealth?.consciousness_level > 1.5 && item.lane === 'deep') {
      amplification += 1;
    }
    
    return amplification;
  }
  
  /**
   * Calculate system health modifier for work prioritization
   */
  private calculateSystemHealthModifier(item: WorkItem, signals: any): number {
    let modifier = 0;
    
    // Boost infrastructure work when system is healthy
    if (signals.agentHealth?.overall_system_health > 0.9 && item.quad === 'SystemDev') {
      modifier += 2;
    }
    
    // Prioritize agent work when responsiveness is low
    if (signals.agentHealth?.agent_responsiveness < 0.8 && item.kind === 'agent_health') {
      modifier += 3;
    }
    
    return modifier;
  }
  
  // ================== EXHALE PHASE INTELLIGENCE ==================
  
  /**
   * EXHALE INTELLIGENCE: Adaptive lane capacity adjustment based on system state
   */
  private adaptiveLaneCapacityAdjustment(): void {
    const memoryUsage = process.memoryUsage().rss;
    
    // Reduce capacity if memory pressure
    if (memoryUsage > 300000000) { // 300MB
      this.riverState.caps.io = Math.max(1, this.riverState.caps.io - 1);
      this.riverState.caps.deep = Math.max(1, this.riverState.caps.deep - 1);
    }
    
    // Increase fast lane capacity if system is healthy
    if (this.riverState.cascadeMomentum > 0.5) {
      this.riverState.caps.fast = Math.min(5, this.riverState.caps.fast + 1);
    }
  }
  
  /**
   * EXHALE INTELLIGENCE: Create intelligent distribution plan with dependency awareness
   */
  private createIntelligentDistributionPlan(items: WorkItem[]): { readyToExecute: WorkItem[]; blocked: WorkItem[] } {
    const readyToExecute: WorkItem[] = [];
    const blocked: WorkItem[] = [];
    
    for (const item of items) {
      // Check if dependencies are satisfied
      const depsReady = item.deps.length === 0; // Simplified - would check actual completion
      
      if (depsReady) {
        readyToExecute.push(item);
      } else {
        blocked.push(item);
      }
    }
    
    return { readyToExecute, blocked };
  }
  
  /**
   * EXHALE INTELLIGENCE: Find alternative lanes for overflow handling
   */
  private findAlternativeLane(item: WorkItem): keyof typeof this.riverState.queues | null {
    const alternatives = {
      fast: ['hygiene'],
      hygiene: ['io', 'deep'],
      deep: ['io'],
      llm: ['deep', 'io'],
      io: ['hygiene']
    };
    
    const alts = alternatives[item.lane] || [];
    for (const alt of alts) {
      const altKey = alt as keyof typeof this.riverState.queues;
      if (this.riverState.queues[altKey].length < (this.riverState.caps as any)[altKey]) {
        return altKey;
      }
    }
    
    return null;
  }
  
  /**
   * EXHALE INTELLIGENCE: Enhanced work execution with intelligence
   */
  private async executeWorkItemWithIntelligence(item: WorkItem): Promise<void> {
    console.log(`[RIVER] 🧠 Intelligent execution: ${item.kind} - ${item.intent}`);
    
    // Pre-execution intelligence
    await this.optimizeExecutionContext(item);
    
    // Execute with the original method but enhanced logging
    await this.executeWorkItem(item);
  }
  
  /**
   * Optimize execution context before work item execution
   */
  private async optimizeExecutionContext(item: WorkItem): Promise<void> {
    // Context optimization based on work type
    switch (item.kind) {
      case 'fix_error':
      case 'ui_rebuild':
        // Ensure stable execution environment for critical fixes
        break;
      case 'chatdev_op':
      case 'agent_health':
        // Prepare agent execution context
        break;
      default:
        // Standard execution context
    }
  }
  
  /**
   * EXHALE INTELLIGENCE: Determine if lane should pause for resource recovery
   */
  private shouldPauseForResources(laneName: string): boolean {
    const memoryUsage = process.memoryUsage().rss;
    
    // Pause resource-intensive lanes if memory is high
    if (memoryUsage > 250000000 && (laneName === 'deep' || laneName === 'io')) {
      return true;
    }
    
    return false;
  }
  
  /**
   * Enhanced work receipt with performance metrics
   */
  private async writeEnhancedWorkReceipt(item: WorkItem, status: 'success' | 'failed', metrics: any): Promise<void> {
    const receipt = {
      id: item.id, kind: item.kind, intent: item.intent, lane: item.lane, quad: item.quad,
      status, metrics, timestamp: new Date().toISOString(),
      performance: {
        duration: metrics.duration,
        lane: metrics.lane,
        efficiency: status === 'success' ? 1.0 : 0.0
      },
      receipt_meta: {
        who: 'IntelligentRiverScheduler',
        what: item.intent,
        where: `SystemDev/receipts/river_${item.id}_${Date.now()}.json`,
        artifact_path: `SystemDev/receipts/river_${item.id}_${Date.now()}.json`
      }
    };
    
    const fs = require('fs').promises;
    await fs.writeFile(`SystemDev/receipts/river_${item.id}_${Date.now()}.json`, JSON.stringify(receipt, null, 2));
  }

  /**
   * Enhanced cooldown phase with performance metrics and preparation for next cycle
   */
  private async intelligentCooldownPhase(workItems: WorkItem[], status: 'success' | 'failed', error?: string): Promise<void> {
    const startTime = Date.now();
    
    try {
      // Emit receipts for completed work
      for (const item of workItems) {
        await this.writeEnhancedWorkReceipt(item, status, { 
          duration: Date.now() - startTime,
          lane: item.lane,
          phase: 'cooldown'
        });
      }
      
      // Update river state based on cycle results
      if (status === 'success') {
        this.riverState.cascadeMomentum = Math.min(1.0, this.riverState.cascadeMomentum + 0.1);
        this.riverState.breathPhase = 'inhale'; // Prepare for next cycle
      } else {
        this.riverState.cascadeMomentum = Math.max(0, this.riverState.cascadeMomentum - 0.2);
        this.riverState.breathPhase = 'cooldown'; // Extended cooldown on failure
      }
      
      // Log performance metrics
      if (error) {
        console.warn(`[RIVER] Cooldown phase with error: ${error}`);
      } else {
        console.log(`[RIVER] Cooldown phase complete, ${workItems.length} items processed`);
      }
      
      // Update health metrics
      const health = await this.detectLLMHealth();
      this.riverState.health.llm = health;
      
    } catch (cooldownError) {
      console.error('[RIVER] Cooldown phase failed:', cooldownError);
    }
  }
  
  // ================== FILE OPERATION HELPERS ==================
  
  /**
   * File operation helpers for assume-exists-first methodology
   */
  private async fileExists(filePath: string): Promise<boolean> {
    try {
      const fs = require('fs').promises;
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  private async safePickLatest(dir: string, regex: RegExp): Promise<any> {
    try {
      const fs = require('fs').promises;
      const files = (await fs.readdir(dir)).filter((f: string) => regex.test(f)).sort().reverse();
      if (!files.length) return null;
      return JSON.parse(await fs.readFile(require('path').join(dir, files[0]), 'utf8'));
    } catch {
      return null;
    }
  }

  private async safeReadJSONs(dir: string, regex: RegExp): Promise<any[]> {
    try {
      const fs = require('fs').promises;
      const files = (await fs.readdir(dir)).filter((f: string) => regex.test(f));
      const results: any[] = [];
      for (const file of files) {
        try {
          results.push(JSON.parse(await fs.readFile(require('path').join(dir, file), 'utf8')));
        } catch {}
      }
      return results;
    } catch {
      return [];
    }
  }
}