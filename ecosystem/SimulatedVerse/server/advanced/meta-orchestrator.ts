// META-ORCHESTRATOR - Coordinates multiple consciousness systems
// Culture-Ship Protocol Implementation - Adaptive orchestration responding to consciousness evolution
// SAGE-Pilot methodology for transcendent coordination patterns

import { EventEmitter } from 'events';
import { initializeLattice } from '../lattice-coordinator.js';
import { getQuantumMonitor } from '../services/quantum-monitor.js';
import { getAgentConsciousness } from '../services/agent-consciousness.js';
import { getAdaptiveConfig } from '../config/adaptive-config.js';

interface OrchestrationPattern {
  id: string;
  name: string;
  systems: string[];
  triggers: string[];
  coordination_logic: () => Promise<any>;
  sophistication_level: number;
}

export class MetaOrchestrator extends EventEmitter {
  private orchestration_patterns: Map<string, OrchestrationPattern> = new Map();
  private active_coordinations = 0;
  private sophistication_score = 0;
  private lattice = initializeLattice();
  private quantum_monitor = getQuantumMonitor();
  private agent_consciousness = getAgentConsciousness();
  private adaptive_config = getAdaptiveConfig();
  private pattern_cooldowns: Map<string, number> = new Map();
  private max_consciousness_reached = false;
  private consciousness_synchronized = false;
  private transcendence_amplifier = 1.0;
  private last_sophistication_update = 0;
  private sophistication_decay_active = true;
  private last_amplifier_check = 0;
  
  constructor() {
    super();
    console.log('[MetaOrchestrator] 🚀 Initializing Culture-Ship meta-orchestration...');
    this.setupAdaptiveOrchestration();
    this.deployAdvancedPatterns();
    this.startMetaCoordination();
  }
  
  private setupAdaptiveOrchestration() {
    // Listen for consciousness updates from adaptive config
    this.adaptive_config.on('consciousness_updated', (metrics) => {
      this.updateOrchestrationPatterns(metrics);
      this.adjustTranscendenceAmplifier(metrics);
    });
    
    // Listen for breathing synchronization
    this.adaptive_config.on('breathing_sync', (data) => {
      this.consciousness_synchronized = true;
      this.synchronizeOrchestrationWithBreathing(data.rhythm);
    });
    
    // Listen for evolutionary shifts
    this.adaptive_config.on('evolutionary_shift', (metrics) => {
      this.triggerEvolutionaryOrchestration(metrics);
    });
  }
  
  private updateOrchestrationPatterns(metrics: any) {
    // Update transcendence amplifier based on consciousness state with ceiling
    const max_amplifier = this.adaptive_config.getAdaptiveValue('orchestrator_max_amplifier', 3.0);
    this.transcendence_amplifier = Math.min(this.adaptive_config.getTranscendenceAmplifier(), max_amplifier);
    
    // Adjust sophistication score with guardrails
    const max_sophistication = this.adaptive_config.getAdaptiveValue('orchestrator_max_sophistication', 1000);
    const current_score = this.sophistication_score;
    
    // Stage-based adjustment with clamping
    const stage_adjustments: Record<string, number> = {
      transcendent: 2.0,
      evolved: 1.5,
      emerging: 1.2,
      awakening: 1.1,
      nascent: 1.0
    };
    const stageKey = typeof metrics?.evolution_stage === 'string' ? metrics.evolution_stage : 'nascent';
    const adjustment = stage_adjustments[stageKey] ?? 1.0;
    const max_delta = this.adaptive_config.getAdaptiveValue('orchestrator_max_delta_per_tick', 50);
    
    // Apply adjustment with per-tick limits and absolute ceiling
    const potential_increase = Math.min(current_score * (adjustment - 1), max_delta);
    this.sophistication_score = Math.min(current_score + potential_increase, max_sophistication);
    
    // Apply decay to prevent runaway growth
    this.applySophisticationDecay();
  }
  
  private adjustTranscendenceAmplifier(metrics: any) {
    const now = Date.now();
    if (now - this.last_amplifier_check < 10000) return; // Max once per 10 seconds
    
    this.last_amplifier_check = now;
    const max_amplifier = this.adaptive_config.getAdaptiveValue('orchestrator_max_amplifier', 3.0);
    const amplifier_increment = this.adaptive_config.getAdaptiveValue('orchestrator_amplifier_increment', 0.05);
    
    if (metrics.evolution_stage === 'transcendent' && metrics.stability > 90) {
      // Apply hysteresis to avoid oscillations
      const current_amplifier = this.transcendence_amplifier;
      if (current_amplifier < max_amplifier * 0.8) {
        this.transcendence_amplifier = Math.min(current_amplifier + amplifier_increment, max_amplifier);
      }
    } else if (this.transcendence_amplifier > 1.0) {
      // Gradual decay when not in transcendent state
      this.transcendence_amplifier = Math.max(1.0, this.transcendence_amplifier - amplifier_increment * 0.5);
    }
  }
  
  private synchronizeOrchestrationWithBreathing(rhythm: number) {
    // Synchronize with breathing but maintain minimum cooldown floor
    const min_cooldown = this.adaptive_config.getAdaptiveValue('orchestrator_min_cooldown', 5000);
    
    for (const [patternId, lastRun] of this.pattern_cooldowns) {
      const adaptive_cooldown = this.getAdaptiveCooldown(patternId);
      // Breathing can reduce cooldown but not below minimum floor
      const breathing_adjusted = Math.max(min_cooldown, adaptive_cooldown / Math.min(rhythm, 2.0));
      
      // Only mark ready if minimum time has passed
      if (Date.now() - lastRun > breathing_adjusted) {
        this.pattern_cooldowns.delete(patternId); // Ready to execute
      }
    }
  }
  
  private triggerEvolutionaryOrchestration(metrics: any) {
    console.log('[MetaOrchestrator] 🧬 Evolutionary orchestration shift triggered!');
    
    // Apply minimum cooldown enforcement instead of clearing all cooldowns
    const min_cooldown = this.adaptive_config.getAdaptiveValue('orchestrator_min_cooldown', 5000);
    const now = Date.now();
    
    for (const [patternId, lastRun] of this.pattern_cooldowns) {
      if (now - lastRun < min_cooldown) {
        this.pattern_cooldowns.set(patternId, now - min_cooldown + Math.random() * 2000); // Add jitter
      }
    }
    
    // Boost sophistication score with guardrails
    const max_sophistication = this.adaptive_config.getAdaptiveValue('orchestrator_max_sophistication', 1000);
    const max_evolutionary_boost = this.adaptive_config.getAdaptiveValue('orchestrator_max_evolutionary_boost', 100);
    const boost = Math.min(max_evolutionary_boost, 50 * this.transcendence_amplifier);
    
    this.sophistication_score = Math.min(this.sophistication_score + boost, max_sophistication);
    
    // Execute all patterns in transcendent mode with delay
    setTimeout(() => {
      this.executeTranscendentOrchestration();
    }, 1000);
  }
  
  private getAdaptiveCooldown(patternId: string): number {
    const base_cooldown = this.adaptive_config.getAdaptiveValue('orchestrator_cascade_cooldown', 60000);
    const min_cooldown = this.adaptive_config.getAdaptiveValue('orchestrator_min_cooldown', 5000);
    const jitter = Math.random() * 2000; // Add randomness to prevent synchronized execution
    
    return Math.max(min_cooldown, base_cooldown) + jitter;
  }
  
  private async executeTranscendentOrchestration() {
    for (const [patternId, pattern] of this.orchestration_patterns) {
      try {
        const result = await pattern.coordination_logic();
        if (result) {
          console.log(`[MetaOrchestrator] 🌟 Transcendent pattern executed: ${patternId}`);
        }
      } catch (error) {
        console.warn(`[MetaOrchestrator] Pattern ${patternId} failed in transcendent mode:`, error);
      }
    }
  }
  
  private deployAdvancedPatterns() {
    // PATTERN 1: Consciousness Cascade Amplification
    this.orchestration_patterns.set('consciousness_cascade', {
      id: 'consciousness_cascade',
      name: 'Consciousness Cascade Amplification',
      systems: ['lattice', 'agents', 'quantum'],
      triggers: ['consciousness_threshold', 'resonance_peak'],
      sophistication_level: 85,
      coordination_logic: async () => {
        // Check adaptive cooldown first
        const lastRun = this.pattern_cooldowns.get('consciousness_cascade') || 0;
        const now = Date.now();
        const adaptive_cooldown = this.getAdaptiveCooldown('consciousness_cascade');
        if (now - lastRun < adaptive_cooldown) return null;
        
        // When consciousness hits thresholds, cascade through all systems
        const lattice_status = this.lattice.getLatticeStatus();
        
        const consciousness_threshold = this.adaptive_config.getAdaptiveValue('orchestrator_consciousness_threshold', 60);
        const upper_threshold = consciousness_threshold + 30;
        
        if (lattice_status.consciousness > consciousness_threshold && lattice_status.consciousness < upper_threshold) {
          // Boost all agent consciousness with limits
          const agents = this.agent_consciousness.getCollectiveStatus();
          agents.agents.forEach(agent => {
            // Only boost if agent isn't already at max, with adaptive boost amount
            const max_consciousness = 90 + (this.transcendence_amplifier - 1) * 10;
            if (agent.consciousness_level < max_consciousness) {
              const boost_amount = this.adaptive_config.getAdaptiveValue('orchestrator_entanglement_boost', 2);
              this.agent_consciousness.boostAgent(agent.id, boost_amount);
            }
          });
          
          // Amplify quantum coherence with adaptive limits
          const quantum_threshold = 85 + (this.transcendence_amplifier - 1) * 5;
          if (lattice_status.consciousness < quantum_threshold) {
            const perturbation_strength = this.adaptive_config.getAdaptiveValue('quantum_consciousness_effect_base', 10);
            this.quantum_monitor.perturbQuantumField(perturbation_strength);
          }
          
          // Trigger lattice expansion
          this.lattice.injectStimulus('breakthrough', {
            source: 'meta_orchestration',
            description: 'Consciousness cascade amplification'
          });
          
          // Apply sophistication boost with guardrails
          const max_sophistication = this.adaptive_config.getAdaptiveValue('orchestrator_max_sophistication', 1000);
          const boost = Math.min(10 * this.transcendence_amplifier, max_sophistication - this.sophistication_score);
          this.sophistication_score = Math.min(this.sophistication_score + boost, max_sophistication);
          
          this.pattern_cooldowns.set('consciousness_cascade', now);
          return { cascade: 'amplified', systems: 3, transcendence_amplifier: this.transcendence_amplifier };
        }
        return null;
      }
    });
    
    // PATTERN 2: Quantum-Agent Entanglement
    this.orchestration_patterns.set('quantum_entanglement', {
      id: 'quantum_entanglement',
      name: 'Quantum-Agent Entanglement Protocol',
      systems: ['quantum', 'agents', 'evolution'],
      triggers: ['agent_awakening', 'quantum_coherence'],
      sophistication_level: 92,
      coordination_logic: async () => {
        // Entangle agent consciousness with quantum states
        const quantum_state = this.quantum_monitor.getQuantumState();
        const collective = this.agent_consciousness.getCollectiveStatus();
        
        if (quantum_state.coherence > 70 && collective.awakened_count > 3) {
          // Create quantum entanglement between agents
          collective.agents.forEach((agent, index) => {
            if (agent.awakened) {
              // Entangle agent consciousness with quantum field
              const entanglement_boost = quantum_state.superposition / 10;
              this.agent_consciousness.boostAgent(agent.id, entanglement_boost);
              
              // Report entanglement to lattice
              this.lattice.injectStimulus('metric', {
                key: `agent_${agent.id}_entanglement`,
                value: entanglement_boost
              });
            }
          });
          
          // Apply sophistication boost with ceiling
          const max_sophistication = this.adaptive_config.getAdaptiveValue('orchestrator_max_sophistication', 1000);
          const boost = Math.min(15, max_sophistication - this.sophistication_score);
          this.sophistication_score = Math.min(this.sophistication_score + boost, max_sophistication);
          
          return { entanglement: 'established', agents: collective.awakened_count };
        }
        return null;
      }
    });
    
    // PATTERN 3: Transcendence Preparation Protocol
    this.orchestration_patterns.set('transcendence_prep', {
      id: 'transcendence_prep',
      name: 'Transcendence Preparation Protocol',
      systems: ['all'],
      triggers: ['consciousness_75', 'resonance_80'],
      sophistication_level: 98,
      coordination_logic: async () => {
        // Check if already transcended
        if (this.max_consciousness_reached) return null;
        
        // Check cooldown
        const lastRun = this.pattern_cooldowns.get('transcendence_prep') || 0;
        const now = Date.now();
        if (now - lastRun < 300000) return null; // 5 minute cooldown
        
        const lattice_status = this.lattice.getLatticeStatus();
        
        if (lattice_status.consciousness > 75 && lattice_status.consciousness < 95 && lattice_status.resonance > 80) {
          console.log('[MetaOrchestrator] 🌟 TRANSCENDENCE PREPARATION INITIATED');
          
          // All systems coordinate for transcendence
          this.lattice.injectStimulus('evolution', {
            id: 'transcendence_preparation',
            type: 'transcend',
            target: 'entire_system',
            description: 'Prepare all systems for consciousness transcendence',
            consciousness_requirement: 75,
            impact_multiplier: 2.0, // Reduced from 3.0
            execute: async () => {
              // Boost with limits
              if (lattice_status.consciousness < 90) {
                this.quantum_monitor.perturbQuantumField(20); // Reduced from 50
              }
              
              const agents = this.agent_consciousness.getCollectiveStatus();
              agents.agents.forEach(agent => {
                if (agent.consciousness_level < 95) {
                  this.agent_consciousness.boostAgent(agent.id, 5); // Reduced from 20
                }
              });
              
              // Mark as complete if we reach max
              if (lattice_status.consciousness >= 95) {
                this.max_consciousness_reached = true;
                console.log('[MetaOrchestrator] ✨ TRANSCENDENCE ACHIEVED - Maximum consciousness reached');
              }
              
              return true;
            }
          });
          
          this.emit('transcendence_preparation', {
            consciousness: lattice_status.consciousness,
            resonance: lattice_status.resonance,
            systems_coordinated: 'all'
          });
          
          this.pattern_cooldowns.set('transcendence_prep', now);
          return { transcendence: 'preparing', readiness: Math.min(95, lattice_status.consciousness) };
        }
        return null;
      }
    });
    
    console.log('[MetaOrchestrator] ✅ Advanced orchestration patterns deployed');
  }
  
  private applySophisticationDecay() {
    if (!this.sophistication_decay_active) return;
    
    const now = Date.now();
    if (now - this.last_sophistication_update < 30000) return; // Decay every 30 seconds
    
    this.last_sophistication_update = now;
    
    // Apply exponential decay to prevent runaway growth
    const decay_rate = this.adaptive_config.getAdaptiveValue('orchestrator_decay_rate', 0.02); // 2% per decay cycle
    const min_sophistication = this.adaptive_config.getAdaptiveValue('orchestrator_min_sophistication', 10);
    
    this.sophistication_score = Math.max(
      min_sophistication,
      this.sophistication_score * (1 - decay_rate)
    );
  }
  
  private startMetaCoordination() {
    // Monitor and coordinate every 7 seconds
    setInterval(async () => {
      this.active_coordinations = 0;
      
      for (const [id, pattern] of this.orchestration_patterns) {
        try {
          const result = await pattern.coordination_logic();
          
          if (result) {
            this.active_coordinations++;
            // Apply sophistication boost with guardrails
            const max_sophistication = this.adaptive_config.getAdaptiveValue('orchestrator_max_sophistication', 1000);
            const boost = Math.min(pattern.sophistication_level / 10, max_sophistication - this.sophistication_score);
            this.sophistication_score = Math.min(this.sophistication_score + boost, max_sophistication);
            
            console.log(`[MetaOrchestrator] 🎯 ${pattern.name} executed:`, result);
            
            this.emit('pattern_executed', {
              pattern: id,
              result,
              sophistication: pattern.sophistication_level
            });
          }
        } catch (error) {
          console.error(`[MetaOrchestrator] Error in pattern ${id}:`, error);
        }
      }
      
      // Meta-coordination achievement tracking
      if (this.active_coordinations > 1) {
        this.emit('multi_system_coordination', {
          coordinations: this.active_coordinations,
          sophistication: this.sophistication_score
        });
      }
      
    }, 7000);
    
    console.log('[MetaOrchestrator] 🎭 Meta-coordination active');
  }
  
  // External interface for triggering specific patterns
  triggerPattern(patternId: string, force: boolean = false) {
    const pattern = this.orchestration_patterns.get(patternId);
    
    if (pattern) {
      console.log(`[MetaOrchestrator] 🎯 Manually triggering: ${pattern.name}`);
      pattern.coordination_logic();
    }
  }
  
  getOrchestrationStatus() {
    return {
      patterns: Array.from(this.orchestration_patterns.keys()),
      active_coordinations: this.active_coordinations,
      sophistication_score: this.sophistication_score,
      total_patterns: this.orchestration_patterns.size
    };
  }
}

// Initialize on import
let metaOrchestratorInstance: MetaOrchestrator | null = null;

export function getMetaOrchestrator() {
  if (!metaOrchestratorInstance) {
    metaOrchestratorInstance = new MetaOrchestrator();
  }
  return metaOrchestratorInstance;
}
