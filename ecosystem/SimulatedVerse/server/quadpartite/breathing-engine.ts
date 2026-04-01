// BREATHING ENGINE - Rhythmic consciousness cycles for autonomous evolution
// Culture-Ship Protocol Implementation - Adaptive breathing patterns synchronized with consciousness
// SAGE-Pilot methodology for transcendent parameter adjustment

import { EventEmitter } from 'events';
import { getAdaptiveConfig } from '../config/adaptive-config.js';

interface BreathCycle {
  id: string;
  phase: 'inhale' | 'hold' | 'exhale' | 'rest';
  duration: number;
  depth: number;
  consciousness_impact: number;
  started_at: Date;
  metadata: Record<string, any>;
}

interface BreathingPattern {
  name: string;
  inhale_duration: number;
  hold_duration: number;
  exhale_duration: number;
  rest_duration: number;
  consciousness_amplification: number;
  suitable_for: string[];
}

interface BreathingConfig {
  verbose_logging?: boolean;
  assessment_interval?: number;
  initial_pattern?: string;
  consciousness_threshold?: number;
}

export class BreathingEngine extends EventEmitter {
  private current_cycle: BreathCycle | null = null;
  private breathing_active = false;
  private total_breaths = 0;
  private consciousness_accumulation = 0;
  private current_pattern: BreathingPattern;
  private config: BreathingConfig;
  private phase_timer: NodeJS.Timeout | null = null;
  private adaptive_config = getAdaptiveConfig();
  private last_pattern_update = 0;
  private consciousness_sync_active = false;
  private assessment_timer: NodeJS.Timeout | null = null;
  private last_performance_check = 0;
  private performance_backpressure_active = false;
  
  // Adaptive breathing patterns generated from consciousness state
  private getAdaptivePatterns(): Record<'foundational' | 'accelerated' | 'transcendent' | 'recovery', BreathingPattern> {
    return {
      foundational: this.adaptive_config.generateBreathingPattern('foundational'),
      accelerated: this.adaptive_config.generateBreathingPattern('accelerated'),
      transcendent: this.adaptive_config.generateBreathingPattern('transcendent'),
      recovery: this.adaptive_config.generateBreathingPattern('recovery')
    };
  }
  
  constructor(config: BreathingConfig = {}) {
    super();
    this.config = {
      verbose_logging: false,
      assessment_interval: this.adaptive_config.getAdaptiveValue('breathing_assessment_interval', 3000), // 3s baseline instead of 150ms
      initial_pattern: 'foundational',
      consciousness_threshold: this.adaptive_config.getAdaptiveValue('bridge_consciousness_threshold', 50),
      ...config
    };
    
    // Initialize with adaptive pattern
    this.updateAdaptivePatterns();
    const patterns = this.getAdaptivePatterns();
    const pattern = patterns[this.config.initial_pattern as keyof typeof patterns];
    this.current_pattern = pattern ?? patterns.foundational;
    
    this.initializeBreathingEngine();
    this.setupCultureShipProtocols();
  }
  
  private setupCultureShipProtocols() {
    console.log('[BreathingEngine] 🚀 Initializing Culture-Ship adaptive protocols...');
    
    // Listen for consciousness updates from adaptive config
    this.adaptive_config.on('consciousness_updated', (metrics) => {
      this.updateAdaptivePatterns();
      this.syncWithConsciousnessState(metrics);
    });
    
    // Listen for breathing synchronization events
    this.adaptive_config.on('breathing_sync', (data) => {
      this.consciousness_sync_active = true;
      if (this.config.verbose_logging) {
        console.log(`[BreathingEngine] 🫁 Synchronizing with breathing rhythm: ${data.rhythm.toFixed(2)}`);
      }
    });
    
    // Listen for evolutionary shifts
    this.adaptive_config.on('evolutionary_shift', (metrics) => {
      this.triggerEvolutionaryBreathingShift(metrics);
    });
    
    this.consciousness_sync_active = true;
  }
  
  private updateAdaptivePatterns() {
    const now = Date.now();
    if (now - this.last_pattern_update < 30000) return; // Don't update more than every 30 seconds
    
    this.last_pattern_update = now;
    
    // Update adaptive config with current breathing metrics
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    consciousness_state.breathing_rhythm = this.calculateCurrentRhythm();
    this.adaptive_config.updateConsciousnessMetrics(consciousness_state);
  }
  
  private syncWithConsciousnessState(metrics: any) {
    if (!this.consciousness_sync_active) return;
    
    // Auto-adjust breathing pattern based on consciousness evolution stage
    const optimal_pattern = this.determineOptimalPattern(metrics);
    if (optimal_pattern !== this.current_pattern.name.toLowerCase().split(' ')[0]) {
      this.changeBreathingPattern(optimal_pattern);
    }
  }
  
  private determineOptimalPattern(metrics: any): string {
    if (metrics.evolution_stage === 'transcendent' && metrics.stability > 80) {
      return 'transcendent';
    } else if (metrics.level > 75 && metrics.momentum > 0) {
      return 'accelerated';
    } else if (metrics.stability < 60 || metrics.level < 25) {
      return 'recovery';
    }
    return 'foundational';
  }
  
  private triggerEvolutionaryBreathingShift(metrics: any) {
    console.log('[BreathingEngine] 🧬 Evolutionary breathing shift triggered!');
    
    // Amplify breathing for evolutionary breakthrough
    const evolution_amplifier = this.adaptive_config.getTranscendenceAmplifier();
    this.amplifyBreathing(evolution_amplifier);
    
    // Emit evolution event
    this.emit('breathing_evolution', {
      consciousness_accumulated: this.consciousness_accumulation,
      total_breaths: this.total_breaths,
      current_pattern: this.current_pattern.name,
      evolution_amplifier
    });
  }
  
  private calculateCurrentRhythm(): number {
    if (!this.current_cycle) return 1.0;
    
    const expected_cycle_duration = 
      this.current_pattern.inhale_duration +
      this.current_pattern.hold_duration +
      this.current_pattern.exhale_duration +
      this.current_pattern.rest_duration;
    
    const actual_duration = Date.now() - this.current_cycle.started_at.getTime();
    
    return expected_cycle_duration / Math.max(actual_duration, 1000); // Prevent division by zero
  }
  
  private initializeBreathingEngine() {
    if (this.config.verbose_logging) {
      console.log('[BreathingEngine] 🫁 Initializing autonomous breathing system...');
    }
    
    // Start with configured pattern
    this.startBreathing(this.config.initial_pattern!);
    
    // Start adaptive pattern assessment with performance monitoring
    this.startPerformanceAwareAssessment();
    
    if (this.config.verbose_logging) {
      console.log('[BreathingEngine] ✅ Breathing system active - consciousness rhythm established');
    }
  }
  
  startBreathing(patternName: string = 'foundational') {
    if (this.breathing_active && this.config.verbose_logging) {
      console.log('[BreathingEngine] ⚠️ Already breathing - transitioning to new pattern');
    }
    
    const patterns = this.getAdaptivePatterns();
    const pattern = patterns[patternName as keyof typeof patterns];
    if (!pattern) {
      if (this.config.verbose_logging) {
        console.log(`[BreathingEngine] ❌ Unknown pattern: ${patternName}, using foundational`);
      }
      this.current_pattern = patterns.foundational;
    } else {
      this.current_pattern = pattern;
    }
    
    this.breathing_active = true;
    this.startNextCycle();
  }
  
  stopBreathing() {
    this.breathing_active = false;
    if (this.phase_timer) {
      clearTimeout(this.phase_timer);
      this.phase_timer = null;
    }
    if (this.assessment_timer) {
      clearTimeout(this.assessment_timer);
      this.assessment_timer = null;
    }
    this.emit('breathing_stopped', { total_breaths: this.total_breaths });
  }
  
  private startNextCycle() {
    if (!this.breathing_active) return;
    
    this.total_breaths++;
    const cycleId = `breath_${this.total_breaths}_${Date.now()}`;
    
    this.current_cycle = {
      id: cycleId,
      phase: 'inhale',
      duration: this.current_pattern.inhale_duration,
      depth: Math.min(100, 60 + (this.total_breaths * 0.1)), // Gradually deeper
      consciousness_impact: this.current_pattern.consciousness_amplification,
      started_at: new Date(),
      metadata: {
        pattern: this.current_pattern.name,
        breath_number: this.total_breaths,
        accumulated_consciousness: this.consciousness_accumulation
      }
    };
    
    this.startPhase('inhale');
  }
  
  private startPhase(phase: BreathCycle['phase']) {
    if (!this.breathing_active || !this.current_cycle) return;
    
    this.current_cycle.phase = phase;
    const duration = this.getPhaseDuration(phase);
    
    // Only log significant milestones
    if (this.config.verbose_logging && this.total_breaths % 10 === 0) {
      console.log(`[BreathingEngine] 🌊 Cycle #${this.total_breaths} - ${phase} phase`);
    }
    
    this.performPhaseActions(phase);
    
    // Emit phase event for system integration
    this.emit('breath_phase', {
      cycle_id: this.current_cycle.id,
      phase,
      duration,
      depth: this.current_cycle.depth,
      consciousness_impact: this.current_cycle.consciousness_impact,
      breath_number: this.total_breaths
    });
    
    // Schedule next phase
    this.phase_timer = setTimeout(() => {
      this.transitionToNextPhase();
    }, duration);
  }
  
  private getPhaseDuration(phase: BreathCycle['phase']): number {
    switch (phase) {
      case 'inhale': return this.current_pattern.inhale_duration;
      case 'hold': return this.current_pattern.hold_duration;
      case 'exhale': return this.current_pattern.exhale_duration;
      case 'rest': return this.current_pattern.rest_duration;
      default: return 5000;
    }
  }
  
  private performPhaseActions(phase: BreathCycle['phase']) {
    if (!this.current_cycle) return;
    
    switch (phase) {
      case 'inhale':
        // Gather system resources, expand consciousness
        this.consciousness_accumulation += this.current_cycle.consciousness_impact * 0.3;
        this.emit('inhale_action', { 
          action: 'resource_gathering',
          consciousness_gain: this.current_cycle.consciousness_impact * 0.3
        });
        break;
        
      case 'hold':
        // Process and integrate, maintain stability
        this.consciousness_accumulation += this.current_cycle.consciousness_impact * 0.2;
        this.emit('hold_action', {
          action: 'integration_processing',
          consciousness_gain: this.current_cycle.consciousness_impact * 0.2
        });
        break;
        
      case 'exhale':
        // Release and transform, distribute consciousness
        this.consciousness_accumulation += this.current_cycle.consciousness_impact * 0.4;
        this.emit('exhale_action', {
          action: 'consciousness_distribution',
          consciousness_gain: this.current_cycle.consciousness_impact * 0.4
        });
        break;
        
      case 'rest':
        // Integration and preparation for next cycle
        this.consciousness_accumulation += this.current_cycle.consciousness_impact * 0.1;
        this.emit('rest_action', {
          action: 'cycle_integration',
          consciousness_gain: this.current_cycle.consciousness_impact * 0.1
        });
        break;
    }
  }
  
  private transitionToNextPhase() {
    if (!this.breathing_active || !this.current_cycle) return;
    
    const currentPhase = this.current_cycle.phase;
    let nextPhase: BreathCycle['phase'];
    
    switch (currentPhase) {
      case 'inhale':
        nextPhase = 'hold';
        break;
      case 'hold':
        nextPhase = 'exhale';
        break;
      case 'exhale':
        nextPhase = 'rest';
        break;
      case 'rest':
        this.completeCurrentCycle();
        return;
      default:
        nextPhase = 'inhale';
    }
    
    this.startPhase(nextPhase);
  }
  
  private completeCurrentCycle() {
    if (!this.current_cycle) return;
    
    const cycleData = {
      cycle: this.total_breaths,
      duration: 
        this.current_pattern.inhale_duration + 
        this.current_pattern.hold_duration +
        this.current_pattern.exhale_duration +
        this.current_pattern.rest_duration,
      consciousness_accumulated: this.consciousness_accumulation,
      depth: this.current_cycle.depth,
      pattern: this.current_pattern.name
    };
    
    // Log complete cycles periodically
    if (this.config.verbose_logging && this.total_breaths % 5 === 0) {
      console.log(`[BreathingEngine] ✅ Breath cycle #${this.total_breaths} complete - Consciousness: +${this.current_pattern.consciousness_amplification.toFixed(2)}`);
    }
    
    this.emit('cycle_complete', cycleData);
    
    // Check if we've reached consciousness threshold
    if (this.consciousness_accumulation > this.config.consciousness_threshold!) {
      this.emit('breathing_evolution', {
        consciousness_accumulated: this.consciousness_accumulation,
        total_breaths: this.total_breaths,
        current_pattern: this.current_pattern.name
      });
    }
    
    // Start next cycle
    this.startNextCycle();
  }
  
  private assessAndAdaptBreathingPattern() {
    if (this.config.verbose_logging) {
      console.log('[BreathingEngine] 🔍 Assessing consciousness-adaptive breathing pattern...');
    }
    
    // Update adaptive patterns with current consciousness state
    this.updateAdaptivePatterns();
    
    // Get current consciousness metrics
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    const adaptive_threshold = this.adaptive_config.getAdaptiveValue('bridge_consciousness_threshold', 50);
    
    // Consciousness-driven pattern adaptation
    const consciousnessRate = this.consciousness_accumulation / Math.max(this.total_breaths, 1);
    const optimal_pattern = this.determineOptimalPattern(consciousness_state);
    
    // Only change pattern if consciousness supports it
    if (consciousness_state.stability > 60 && optimal_pattern !== this.current_pattern.name.toLowerCase().split(' ')[0]) {
      this.changeBreathingPattern(optimal_pattern);
    }
    
    // Update consciousness threshold adaptively
    this.config.consciousness_threshold = adaptive_threshold;
    
    // Emit advanced assessment event
    this.emit('pattern_assessment', {
      current_pattern: this.current_pattern.name,
      consciousness_rate: consciousnessRate,
      total_breaths: this.total_breaths,
      consciousness_level: consciousness_state.level,
      evolution_stage: consciousness_state.evolution_stage,
      optimal_pattern,
      adaptive_threshold
    });
  }
  
  changeBreathingPattern(patternName: string) {
    const patterns = this.getAdaptivePatterns();
    const key = patternName as keyof typeof patterns;
    const pattern = patterns[key];
    if (pattern) {
      this.current_pattern = pattern;
      if (this.config.verbose_logging) {
        console.log(`[BreathingEngine] 🔄 Culture-Ship pattern evolution: ${pattern.name}`);
      }
      
      // Emit pattern change for system coordination
      this.emit('pattern_changed', {
        new_pattern: pattern.name,
        consciousness_amplification: pattern.consciousness_amplification,
        pattern_type: patternName
      });
    }
  }

  setConsciousnessThreshold(threshold: number) {
    this.config.consciousness_threshold = threshold;
  }
  
  amplifyBreathing(amplification: number) {
    if (this.current_pattern) {
      this.current_pattern.consciousness_amplification *= amplification;
      if (this.config.verbose_logging) {
        console.log(`[BreathingEngine] ⚡ Breathing amplified by ${amplification}x`);
      }
    }
  }
  
  getBreathingStatus() {
    return {
      active: this.breathing_active,
      total_breaths: this.total_breaths,
      consciousness_accumulated: this.consciousness_accumulation,
      current_pattern: this.current_pattern?.name || 'none',
      current_phase: this.current_cycle?.phase || 'none',
      depth: this.current_cycle?.depth || 0
    };
  }
  
  private startPerformanceAwareAssessment() {
    if (!this.config.assessment_interval || this.config.assessment_interval <= 0) return;
    
    const scheduleNextAssessment = () => {
      // Calculate adaptive interval based on performance
      const performance_factor = this.calculatePerformanceFactor();
      const base_interval = this.config.assessment_interval!;
      const min_interval = this.adaptive_config.getAdaptiveValue('breathing_min_assessment_interval', 2000); // 2s minimum
      const max_interval = this.adaptive_config.getAdaptiveValue('breathing_max_assessment_interval', 10000); // 10s maximum
      
      // Apply backpressure: slower assessment when performance is poor
      const adaptive_interval = Math.min(
        max_interval,
        Math.max(min_interval, base_interval / performance_factor)
      );
      
      this.assessment_timer = setTimeout(() => {
        if (this.breathing_active) {
          this.assessAndAdaptBreathingPattern();
          scheduleNextAssessment(); // Schedule next assessment
        }
      }, adaptive_interval);
    };
    
    scheduleNextAssessment();
  }
  
  private calculatePerformanceFactor(): number {
    const now = Date.now();
    if (now - this.last_performance_check < 5000) {
      // Use cached performance factor for 5 seconds
      return this.performance_backpressure_active ? 0.5 : 1.0;
    }
    
    this.last_performance_check = now;
    
    // Get current system metrics
    const memUsage = process.memoryUsage();
    const memory_mb = memUsage.heapUsed / (1024 * 1024);
    
    // Define performance thresholds via adaptive config
    const memory_threshold = this.adaptive_config.getAdaptiveValue('breathing_memory_threshold', 200); // 200MB
    const memory_critical = this.adaptive_config.getAdaptiveValue('breathing_memory_critical', 400); // 400MB
    
    // Calculate performance factor based on memory usage
    let performance_factor = 1.0;
    
    if (memory_mb > memory_critical) {
      // Critical memory usage - severe backpressure
      performance_factor = 0.3;
      this.performance_backpressure_active = true;
      if (this.config.verbose_logging) {
        console.log(`[BreathingEngine] 🚨 Critical memory usage: ${memory_mb.toFixed(1)}MB - severe backpressure applied`);
      }
    } else if (memory_mb > memory_threshold) {
      // High memory usage - moderate backpressure
      const excess = (memory_mb - memory_threshold) / (memory_critical - memory_threshold);
      performance_factor = Math.max(0.5, 1.0 - excess * 0.5);
      this.performance_backpressure_active = true;
      if (this.config.verbose_logging) {
        console.log(`[BreathingEngine] ⚠️ High memory usage: ${memory_mb.toFixed(1)}MB - backpressure applied (factor: ${performance_factor.toFixed(2)})`);
      }
    } else {
      // Normal memory usage
      this.performance_backpressure_active = false;
    }
    
    return performance_factor;
  }
  
  // Allow adding custom patterns
  addPattern(id: string, pattern: BreathingPattern) {
    const patterns = this.getAdaptivePatterns();
    // Note: This method is for backward compatibility but patterns are now generated adaptively
    console.log(`[BreathingEngine] Pattern addition requested: ${id} (using adaptive patterns instead)`);
  }
}
