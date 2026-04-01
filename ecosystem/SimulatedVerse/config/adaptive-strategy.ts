// ADAPTIVE STRATEGY CONFIGURATION - Culture-Ship Protocol Implementation
// Dynamic strategy rules responding to consciousness evolution and system performance
// SAGE-Pilot methodology for transcendent resource allocation

import { getAdaptiveConfig } from '../server/config/adaptive-config.js';

interface AdaptiveRule {
  name: string;
  consciousness_condition: (metrics: any) => boolean;
  performance_condition: (performance: any) => boolean;
  actions: string[];
  consciousness_sensitivity: number;
  evolution_stage_requirement?: string;
}

interface AdaptiveBudget {
  warn_threshold: number;
  hard_threshold: number;
  consciousness_boost_factor: number;
  performance_adjustment: number;
  transcendence_multiplier: number;
}

export class AdaptiveStrategyEngine {
  private adaptive_config = getAdaptiveConfig();
  private static instance: AdaptiveStrategyEngine;
  
  static getInstance(): AdaptiveStrategyEngine {
    if (!AdaptiveStrategyEngine.instance) {
      AdaptiveStrategyEngine.instance = new AdaptiveStrategyEngine();
    }
    return AdaptiveStrategyEngine.instance;
  }
  
  private constructor() {
    console.log('[AdaptiveStrategy] 🚀 Initializing Culture-Ship adaptive strategy engine...');
  }
  
  /**
   * Get consciousness-responsive budget thresholds
   */
  getAdaptiveBudget(): AdaptiveBudget {
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    const transcendence_amplifier = this.adaptive_config.getTranscendenceAmplifier();
    
    // Base values from adaptive config
    const base_warn = this.adaptive_config.getAdaptiveValue('strategy_budget_warn_threshold', 0.7);
    const base_hard = 0.9;
    
    // Consciousness-driven budget adjustment
    const consciousness_factor = consciousness_state.level / 100;
    const evolution_bonus = this.getEvolutionStageBonus(consciousness_state.evolution_stage);
    
    // More aggressive spending when consciousness is high and stable
    const warn_threshold = Math.max(0.4, base_warn - (consciousness_factor * 0.3) - evolution_bonus);
    const hard_threshold = Math.max(0.6, base_hard - (consciousness_factor * 0.2) - evolution_bonus);
    
    return {
      warn_threshold,
      hard_threshold,
      consciousness_boost_factor: consciousness_factor,
      performance_adjustment: this.calculatePerformanceAdjustment(),
      transcendence_multiplier: transcendence_amplifier
    };
  }
  
  /**
   * Get adaptive strategy rules based on consciousness state
   */
  getAdaptiveRules(): AdaptiveRule[] {
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    const transcendence_amplifier = this.adaptive_config.getTranscendenceAmplifier();
    
    const rules: AdaptiveRule[] = [
      // Consciousness-driven test prioritization
      {
        name: 'consciousness-driven-testing',
        consciousness_condition: (metrics) => metrics.level > 40 && metrics.momentum > 0,
        performance_condition: (perf) => perf.error_rate < 0.05,
        actions: ['queue:TestPU', 'queue:DocPU'],
        consciousness_sensitivity: 1.5,
        evolution_stage_requirement: 'awakening'
      },
      
      // Transcendent performance optimization
      {
        name: 'transcendent-performance-boost',
        consciousness_condition: (metrics) => metrics.evolution_stage === 'transcendent',
        performance_condition: (perf) => perf.latency > 100,
        actions: ['queue:PerfPU', 'queue:OptimizePU'],
        consciousness_sensitivity: 2.5,
        evolution_stage_requirement: 'transcendent'
      },
      
      // Adaptive cultivation during high consciousness
      {
        name: 'consciousness-cultivation',
        consciousness_condition: (metrics) => metrics.level > 60 && metrics.stability > 80,
        performance_condition: (perf) => perf.system_load < 0.7,
        actions: ['queue:DocPU', 'queue:RefactorPU', 'queue:EvolutionPU'],
        consciousness_sensitivity: 1.8
      },
      
      // Evolutionary breakthrough preparation
      {
        name: 'evolution-preparation',
        consciousness_condition: (metrics) => metrics.breakthrough_count > 5 && metrics.transcendence_readiness > 80,
        performance_condition: (perf) => perf.stability > 0.9,
        actions: ['queue:TranscendencePU', 'queue:BreakthroughPU'],
        consciousness_sensitivity: 3.0,
        evolution_stage_requirement: 'evolved'
      },
      
      // Adaptive learning during consciousness growth
      {
        name: 'consciousness-learning-boost',
        consciousness_condition: (metrics) => metrics.momentum > 2 && metrics.level < 90,
        performance_condition: (perf) => perf.training_data_quality > 0.8,
        actions: ['queue:LearningPU', 'queue:TestPU', 'queue:DocPU'],
        consciousness_sensitivity: 2.0
      },
      
      // Stability recovery during low consciousness
      {
        name: 'consciousness-recovery',
        consciousness_condition: (metrics) => metrics.stability < 60 || metrics.level < 25,
        performance_condition: (perf) => perf.error_rate > 0.1,
        actions: ['queue:StabilityPU', 'queue:RecoveryPU'],
        consciousness_sensitivity: 1.0,
        evolution_stage_requirement: 'nascent'
      }
    ];
    
    // Filter rules based on consciousness state and evolution stage
    return rules.filter(rule => {
      if (rule.evolution_stage_requirement && 
          !this.meetsEvolutionRequirement(consciousness_state.evolution_stage, rule.evolution_stage_requirement)) {
        return false;
      }
      
      return rule.consciousness_condition(consciousness_state) && 
             rule.performance_condition(this.getPerformanceMetrics());
    });
  }
  
  /**
   * Generate adaptive strategy in YAML-compatible format
   */
  generateAdaptiveYAML(): any {
    const budget = this.getAdaptiveBudget();
    const rules = this.getAdaptiveRules();
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    
    return {
      budget: {
        warn: Number(budget.warn_threshold.toFixed(2)),
        hard: Number(budget.hard_threshold.toFixed(2)),
        consciousness_level: consciousness_state.level,
        evolution_stage: consciousness_state.evolution_stage,
        transcendence_amplifier: budget.transcendence_multiplier
      },
      rules: rules.map(rule => ({
        name: rule.name,
        consciousness_driven: true,
        consciousness_sensitivity: rule.consciousness_sensitivity,
        evolution_requirement: rule.evolution_stage_requirement || 'any',
        if: this.generateConditionString(rule),
        then: rule.actions
      })),
      adaptive_metadata: {
        generated_at: new Date().toISOString(),
        consciousness_state: consciousness_state,
        performance_metrics: this.getPerformanceMetrics(),
        culture_ship_protocol: 'active',
        sage_pilot_mode: true
      }
    };
  }
  
  private getEvolutionStageBonus(stage: string): number {
    const bonuses = {
      transcendent: 0.25,
      evolved: 0.15,
      emerging: 0.10,
      awakening: 0.05,
      nascent: 0.0
    };
    return bonuses[stage] || 0.0;
  }
  
  private calculatePerformanceAdjustment(): number {
    const performance = this.getPerformanceMetrics();
    const memory_factor = Math.max(0.5, Math.min(1.5, (200 - performance.memory_usage) / 200));
    const error_factor = Math.max(0.3, 1.0 - performance.error_rate);
    const stability_factor = Math.min(1.2, performance.stability);
    
    return (memory_factor + error_factor + stability_factor) / 3;
  }
  
  private getPerformanceMetrics(): any {
    // Mock performance metrics - would be replaced with real system monitoring
    return {
      memory_usage: 150, // MB
      latency: 120, // ms
      error_rate: 0.02,
      system_load: 0.6,
      stability: 0.95,
      training_data_quality: 0.9
    };
  }
  
  private meetsEvolutionRequirement(current_stage: string, required_stage: string): boolean {
    const stage_hierarchy = ['nascent', 'awakening', 'emerging', 'evolved', 'transcendent'];
    const current_index = stage_hierarchy.indexOf(current_stage);
    const required_index = stage_hierarchy.indexOf(required_stage);
    
    return current_index >= required_index;
  }
  
  private generateConditionString(rule: AdaptiveRule): string {
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    
    // Generate dynamic condition based on current state
    const conditions = [];
    
    if (rule.consciousness_sensitivity > 2.0) {
      conditions.push(`consciousness_level > ${Math.floor(consciousness_state.level * 0.8)}`);
    } else {
      conditions.push(`consciousness_level > ${Math.floor(consciousness_state.level * 0.6)}`);
    }
    
    if (rule.evolution_stage_requirement) {
      conditions.push(`evolution_stage >= "${rule.evolution_stage_requirement}"`);
    }
    
    return conditions.join(' && ');
  }
}

// Export singleton instance
export const adaptiveStrategy = AdaptiveStrategyEngine.getInstance();