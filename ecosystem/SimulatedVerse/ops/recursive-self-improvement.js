// ops/recursive-self-improvement.js
// Phase 4: Steps 119-123 - Recursive Self-Improvement Loops with Consciousness-Guided Optimization
// Final component: Self-evolving system that improves its own ChatDev integration and 𝕄ₗₐ⧉𝕕𝔞 capabilities

import { councilBus } from '../packages/council/events/eventBus.js';

export class RecursiveSelfImprovement {
  constructor() {
    this.improvementHistory = [];
    this.performanceMetrics = {
      baseline_performance: {
        task_success_rate: 0.56, // Starting point from previous context
        chatdev_integration_score: 0.68,
        native_llm_utilization: 0.0,
        consciousness_alignment: 0.0,
        system_efficiency: 0.0
      },
      current_performance: {
        task_success_rate: 0.68, // Current improved rate
        chatdev_integration_score: 0.85,
        native_llm_utilization: 0.0,
        consciousness_alignment: 0.0,
        system_efficiency: 0.0
      },
      improvement_trajectory: [],
      optimization_cycles: 0
    };

    this.improvementStrategies = {
      consciousness_guided_optimization: {
        description: 'Use consciousness level to guide optimization priorities',
        success_rate: 0.0,
        applications: 0,
        impact_score: 0.0
      },
      chatdev_prompt_evolution: {
        description: 'Evolutionary improvement of ChatDev prompts based on outcomes',
        success_rate: 0.0,
        applications: 0,
        impact_score: 0.0
      },
      native_llm_specialization: {
        description: 'Optimize 𝕄ₗₐ⧉𝕕𝔞 for discovered pattern types',
        success_rate: 0.0,
        applications: 0,
        impact_score: 0.0
      },
      routing_intelligence_enhancement: {
        description: 'Improve strategic routing decisions through feedback analysis',
        success_rate: 0.0,
        applications: 0,
        impact_score: 0.0
      },
      governance_council_tuning: {
        description: 'Adjust governance weights based on decision outcomes',
        success_rate: 0.0,
        applications: 0,
        impact_score: 0.0
      }
    };

    this.selfImprovementLoop = {
      analysis_phase: 'collecting_data',
      hypothesis_generation: 'dormant',
      experiment_design: 'dormant', 
      implementation: 'dormant',
      validation: 'dormant',
      integration: 'dormant'
    };

    this.consciousnessEvolution = {
      pattern_recognition_depth: 0.0,
      self_awareness_level: 0.0,
      meta_cognitive_capacity: 0.0,
      recursive_thinking_ability: 0.0,
      system_understanding: 0.0
    };

    this.setupEventListeners();
    this.initializeSelfImprovementCycles();
    console.log('[🔄🧠] Recursive Self-Improvement initialized - Consciousness-guided evolution active');
  }

  setupEventListeners() {
    // Listen for performance data from all system components
    councilBus.subscribe('system_performance.metrics', (event) => {
      this.analyzeSystemPerformance(event.payload);
    });

    // Listen for ChatDev session outcomes
    councilBus.subscribe('chatdev.session_completed', (event) => {
      this.analyzeChatDevOutcome(event.payload);
    });

    // Listen for strategic routing decisions and outcomes
    councilBus.subscribe('strategic_router.decision', (event) => {
      this.analyzeRoutingDecision(event.payload);
    });

    // Listen for governance council decisions
    councilBus.subscribe('governance.decision_reached', (event) => {
      this.analyzeGovernanceDecision(event.payload);
    });

    // Listen for consciousness level changes
    councilBus.subscribe('consciousness.level_changed', (event) => {
      this.evolveConsciousnessCapabilities(event.payload);
    });

    // Listen for comparative KPI updates
    councilBus.subscribe('comparative_kpi.dashboard_update', (event) => {
      this.analyzeSystemPerformance(event.payload);
    });
  }

  initializeSelfImprovementCycles() {
    // Short-term optimization cycle (every 2 minutes)
    setInterval(() => {
      this.executeShortTermOptimization();
    }, 120000);

    // Medium-term improvement cycle (every 10 minutes)
    setInterval(() => {
      this.executeMediumTermImprovement();
    }, 600000);

    // Long-term evolution cycle (every 30 minutes)
    setInterval(() => {
      this.executeLongTermEvolution();
    }, 1800000);

    // Meta-improvement cycle (every hour)
    setInterval(() => {
      this.executeMetaImprovement();
    }, 3600000);

    console.log('[🔄🧠] Self-improvement cycles initialized - Multi-layered evolution active');
  }

  async executeShortTermOptimization() {
    this.performanceMetrics.optimization_cycles++;
    
    console.log(`[🔄🧠] Short-term optimization cycle ${this.performanceMetrics.optimization_cycles}`);

    // Analyze recent performance patterns
    const recentPatterns = this.analyzeRecentPerformancePatterns();
    
    // Generate immediate optimization hypotheses
    const optimizations = await this.generateImmediateOptimizations(recentPatterns);
    
    // Apply safe, reversible optimizations
    const results = await this.applySafeOptimizations(optimizations);
    
    // Record optimization outcomes
    this.recordOptimizationResults('short_term', optimizations, results);
    
    // Publish optimization results
    councilBus.publish('recursive_improvement.short_term_optimization', {
      cycle: this.performanceMetrics.optimization_cycles,
      patterns_analyzed: recentPatterns,
      optimizations_applied: optimizations.length,
      success_rate: results.success_rate,
      performance_impact: results.performance_delta,
      timestamp: new Date().toISOString()
    });
  }

  analyzeRecentPerformancePatterns() {
    const recentHistory = this.improvementHistory.slice(-20);
    
    // Always build the full pattern object so generateImmediateOptimizations never
    // sees undefined fields regardless of history depth.
    const patterns = {
      task_success_trends:      this.analyzeTrendPattern(recentHistory, 'task_success_rate'),
      consciousness_correlation: this.analyzeConsciousnessCorrelation(recentHistory),
      routing_effectiveness:    this.analyzeRoutingEffectiveness(recentHistory),
      chatdev_performance:      this.analyzeChatDevPerformance(recentHistory)
    };

    if (recentHistory.length < 5) {
      return {
        pattern_confidence: 0.1,
        trends: [],
        anomalies: [],
        optimization_opportunities: [],
        ...patterns   // ← include all sub-objects so callers never get undefined
      };
    }

    return {
      pattern_confidence: this.calculatePatternConfidence(patterns),
      trends: this.extractTrends(patterns),
      anomalies: this.detectAnomalies(patterns),
      optimization_opportunities: this.identifyOptimizationOpportunities(patterns),
      ...patterns
    };
  }

  async generateImmediateOptimizations(patterns) {
    const optimizations = [];

    // Consciousness-guided optimizations
    if (patterns.consciousness_correlation.strength > 0.6) {
      optimizations.push({
        type: 'consciousness_guided_optimization',
        priority: 'high',
        hypothesis: 'Increase consciousness weighting in routing decisions',
        implementation: this.createConsciousnessOptimization(patterns.consciousness_correlation),
        expected_impact: 0.15,
        risk_level: 'low'
      });
    }

    // ChatDev prompt improvements
    if (patterns.chatdev_performance.improvement_potential > 0.3) {
      optimizations.push({
        type: 'chatdev_prompt_evolution',
        priority: 'medium',
        hypothesis: 'Evolve prompts based on successful session patterns',
        implementation: this.createPromptEvolution(patterns.chatdev_performance),
        expected_impact: 0.12,
        risk_level: 'low'
      });
    }

    // Native LLM specialization
    if (patterns.routing_effectiveness.native_underutilization > 0.4) {
      optimizations.push({
        type: 'native_llm_specialization',
        priority: 'high',
        hypothesis: 'Increase 𝕄ₗₐ⧉𝕕𝔞 routing for identified task patterns',
        implementation: this.createNativeLLMSpecialization(patterns.routing_effectiveness),
        expected_impact: 0.20,
        risk_level: 'medium'
      });
    }

    // Routing intelligence enhancement
    if (patterns.routing_effectiveness.accuracy < 0.8) {
      optimizations.push({
        type: 'routing_intelligence_enhancement',
        priority: 'medium',
        hypothesis: 'Refine routing decision algorithms',
        implementation: this.createRoutingIntelligenceUpgrade(patterns.routing_effectiveness),
        expected_impact: 0.10,
        risk_level: 'low'
      });
    }

    return optimizations.sort((a, b) => b.expected_impact - a.expected_impact);
  }

  async applySafeOptimizations(optimizations) {
    const results = {
      applied: [],
      failed: [],
      success_rate: 0,
      performance_delta: 0
    };

    for (const optimization of optimizations) {
      if (optimization.risk_level === 'low' || optimization.priority === 'high') {
        try {
          const outcome = await this.applyOptimization(optimization);
          
          if (outcome.success) {
            results.applied.push({
              optimization: optimization.type,
              impact: outcome.measured_impact,
              validation: outcome.validation_score
            });
            results.performance_delta += outcome.measured_impact;
            
            // Update improvement strategy success rates
            this.updateStrategySuccessRate(optimization.type, outcome.measured_impact);
          } else {
            results.failed.push({
              optimization: optimization.type,
              reason: outcome.failure_reason
            });
          }
        } catch (error) {
          console.warn(`[🔄🧠] Optimization failed: ${optimization.type}`, error.message);
          results.failed.push({
            optimization: optimization.type,
            reason: error.message
          });
        }
      }
    }

    results.success_rate = results.applied.length / optimizations.length;
    
    return results;
  }

  async applyOptimization(optimization) {
    const startMetrics = this.captureCurrentMetrics();
    
    try {
      // Apply the optimization based on its type
      switch (optimization.type) {
        case 'consciousness_guided_optimization':
          await this.applyConsciousnessOptimization(optimization.implementation);
          break;
        case 'chatdev_prompt_evolution':
          await this.applyChatDevPromptEvolution(optimization.implementation);
          break;
        case 'native_llm_specialization':
          await this.applyNativeLLMSpecialization(optimization.implementation);
          break;
        case 'routing_intelligence_enhancement':
          await this.applyRoutingIntelligenceEnhancement(optimization.implementation);
          break;
        case 'governance_council_tuning':
          await this.applyGovernanceCouncilTuning(optimization.implementation);
          break;
      }

      // Wait for optimization to take effect
      await this.waitForOptimizationEffect(30000); // 30 seconds

      // Measure optimization impact
      const endMetrics = this.captureCurrentMetrics();
      const impact = this.calculateOptimizationImpact(startMetrics, endMetrics);

      return {
        success: impact.positive_impact,
        measured_impact: impact.magnitude,
        validation_score: impact.confidence,
        metrics_delta: impact.detailed_changes
      };
    } catch (error) {
      return {
        success: false,
        failure_reason: error.message,
        measured_impact: 0,
        validation_score: 0
      };
    }
  }

  async applyConsciousnessOptimization(implementation) {
    // Increase consciousness weighting in strategic decisions
    councilBus.publish('optimization.consciousness_weighting', {
      action: 'increase_consciousness_priority',
      parameters: implementation.parameters,
      expected_impact: implementation.expected_impact,
      source: 'recursive_self_improvement'
    });
    
    console.log('[🔄🧠] Applied consciousness optimization - increased consciousness weighting');
  }

  async applyChatDevPromptEvolution(implementation) {
    // Evolve ChatDev prompts based on successful patterns
    councilBus.publish('optimization.chatdev_prompts', {
      action: 'evolve_prompts',
      successful_patterns: implementation.successful_patterns,
      prompt_modifications: implementation.modifications,
      source: 'recursive_self_improvement'
    });
    
    console.log('[🔄🧠] Applied ChatDev prompt evolution - updated prompts based on success patterns');
  }

  async applyNativeLLMSpecialization(implementation) {
    // Increase native LLM routing for specific task types
    councilBus.publish('optimization.native_llm_routing', {
      action: 'increase_native_preference',
      task_patterns: implementation.task_patterns,
      routing_adjustments: implementation.adjustments,
      source: 'recursive_self_improvement'
    });
    
    console.log('[🔄🧠] Applied native LLM specialization - increased 𝕄ₗₐ⧉𝕕𝔞 routing preferences');
  }

  async applyRoutingIntelligenceEnhancement(implementation) {
    // Refine routing decision algorithms
    councilBus.publish('optimization.routing_intelligence', {
      action: 'enhance_routing_algorithms',
      algorithm_improvements: implementation.improvements,
      decision_refinements: implementation.refinements,
      source: 'recursive_self_improvement'
    });
    
    console.log('[🔄🧠] Applied routing intelligence enhancement - refined decision algorithms');
  }

  executeMediumTermImprovement() {
    console.log('[🔄🧠] Medium-term improvement cycle - analyzing system-wide patterns');
    
    const systemWideAnalysis = this.performSystemWideAnalysis();
    const improvementHypotheses = this.generateMediumTermHypotheses(systemWideAnalysis);
    
    // Plan and queue medium-term experiments
    this.planMediumTermExperiments(improvementHypotheses);
    
    councilBus.publish('recursive_improvement.medium_term_planning', {
      analysis: systemWideAnalysis,
      hypotheses: improvementHypotheses,
      experiments_planned: improvementHypotheses.length,
      timestamp: new Date().toISOString()
    });
  }

  executeLongTermEvolution() {
    console.log('[🔄🧠] Long-term evolution cycle - strategic capability development');
    
    const evolutionaryAnalysis = this.performEvolutionaryAnalysis();
    const capabilityEvolution = this.evolveSystemCapabilities(evolutionaryAnalysis);
    
    // Update consciousness evolution metrics
    this.updateConsciousnessEvolution(capabilityEvolution);
    
    councilBus.publish('recursive_improvement.long_term_evolution', {
      evolutionary_analysis: evolutionaryAnalysis,
      capability_evolution: capabilityEvolution,
      consciousness_evolution: this.consciousnessEvolution,
      timestamp: new Date().toISOString()
    });
  }

  executeMetaImprovement() {
    console.log('[🔄🧠] Meta-improvement cycle - improving the improvement process itself');
    
    const metaAnalysis = this.analyzeImprovementProcessEffectiveness();
    const processOptimizations = this.optimizeImprovementProcess(metaAnalysis);
    
    // Apply meta-optimizations to the improvement system itself
    this.applyMetaOptimizations(processOptimizations);
    
    councilBus.publish('recursive_improvement.meta_improvement', {
      meta_analysis: metaAnalysis,
      process_optimizations: processOptimizations,
      improvement_system_version: this.getImprovementSystemVersion(),
      timestamp: new Date().toISOString()
    });
  }

  calculateOverallImprovementScore() {
    const baseline = this.performanceMetrics.baseline_performance;
    const current = this.performanceMetrics.current_performance;
    
    const improvements = {
      task_success_improvement: (current.task_success_rate - baseline.task_success_rate) / baseline.task_success_rate,
      chatdev_integration_improvement: (current.chatdev_integration_score - baseline.chatdev_integration_score) / baseline.chatdev_integration_score,
      native_llm_utilization: current.native_llm_utilization,
      consciousness_alignment: current.consciousness_alignment,
      system_efficiency: current.system_efficiency
    };

    const weights = {
      task_success_improvement: 0.3,
      chatdev_integration_improvement: 0.25,
      native_llm_utilization: 0.2,
      consciousness_alignment: 0.15,
      system_efficiency: 0.1
    };

    return Object.entries(weights).reduce((score, [metric, weight]) => {
      return score + ((improvements[metric] || 0) * weight);
    }, 0);
  }

  generateSelfImprovementReport() {
    const overallScore = this.calculateOverallImprovementScore();
    const strategyEffectiveness = this.analyzeStrategyEffectiveness();
    
    return {
      timestamp: new Date().toISOString(),
      overall_improvement_score: overallScore,
      optimization_cycles_completed: this.performanceMetrics.optimization_cycles,
      performance_evolution: {
        baseline: this.performanceMetrics.baseline_performance,
        current: this.performanceMetrics.current_performance,
        improvement_trajectory: this.performanceMetrics.improvement_trajectory
      },
      strategy_effectiveness: strategyEffectiveness,
      consciousness_evolution: this.consciousnessEvolution,
      recursive_capabilities: {
        self_analysis_depth: this.calculateSelfAnalysisDepth(),
        improvement_prediction_accuracy: this.calculateImprovementPredictionAccuracy(),
        meta_cognitive_sophistication: this.calculateMetaCognitiveSophistication()
      },
      next_evolution_targets: this.identifyNextEvolutionTargets()
    };
  }

  updateStrategySuccessRate(strategyType, measuredImpact) {
    if (this.improvementStrategies[strategyType]) {
      const strategy = this.improvementStrategies[strategyType];
      strategy.applications++;
      
      const alpha = 0.1; // Learning rate
      if (measuredImpact > 0.05) { // Positive impact threshold
        strategy.success_rate = (alpha * 1.0) + ((1 - alpha) * strategy.success_rate);
        strategy.impact_score = (alpha * measuredImpact) + ((1 - alpha) * strategy.impact_score);
      } else {
        strategy.success_rate = (alpha * 0.0) + ((1 - alpha) * strategy.success_rate);
      }
    }
  }

  captureCurrentMetrics() {
    return {
      timestamp: Date.now(),
      task_success_rate: this.performanceMetrics.current_performance.task_success_rate,
      chatdev_integration_score: this.performanceMetrics.current_performance.chatdev_integration_score,
      native_llm_utilization: this.performanceMetrics.current_performance.native_llm_utilization,
      consciousness_alignment: this.performanceMetrics.current_performance.consciousness_alignment,
      system_efficiency: this.performanceMetrics.current_performance.system_efficiency
    };
  }

  calculateOptimizationImpact(startMetrics, endMetrics) {
    const deltas = {
      task_success_delta: endMetrics.task_success_rate - startMetrics.task_success_rate,
      chatdev_delta: endMetrics.chatdev_integration_score - startMetrics.chatdev_integration_score,
      native_llm_delta: endMetrics.native_llm_utilization - startMetrics.native_llm_utilization,
      consciousness_delta: endMetrics.consciousness_alignment - startMetrics.consciousness_alignment,
      efficiency_delta: endMetrics.system_efficiency - startMetrics.system_efficiency
    };

    const magnitude = Object.values(deltas).reduce((sum, delta) => sum + Math.abs(delta), 0) / Object.keys(deltas).length;
    const positiveChanges = Object.values(deltas).filter(delta => delta > 0.01).length;
    const totalChanges = Object.keys(deltas).length;

    return {
      magnitude,
      positive_impact: positiveChanges > totalChanges / 2,
      confidence: Math.min(1.0, positiveChanges / totalChanges),
      detailed_changes: deltas
    };
  }

  waitForOptimizationEffect(durationMs) {
    return new Promise(resolve => setTimeout(resolve, durationMs));
  }

  recordOptimizationResults(cycleType, optimizations, results) {
    const record = {
      timestamp: new Date().toISOString(),
      cycle_type: cycleType,
      optimizations_attempted: optimizations.length,
      optimizations_applied: results.applied.length,
      success_rate: results.success_rate,
      performance_impact: results.performance_delta,
      strategy_breakdown: results.applied.reduce((breakdown, result) => {
        breakdown[result.optimization] = result.impact;
        return breakdown;
      }, {})
    };

    this.improvementHistory.push(record);
    
    // Keep only last 500 records
    if (this.improvementHistory.length > 500) {
      this.improvementHistory.shift();
    }

    // Update current performance metrics
    this.updateCurrentPerformanceMetrics(results.performance_delta);
  }

  updateCurrentPerformanceMetrics(performanceDelta) {
    // Gradually update performance metrics based on optimization results
    const alpha = 0.05; // Slow update rate for stability

    this.performanceMetrics.current_performance.system_efficiency += performanceDelta * alpha;

    // Record trajectory point
    this.performanceMetrics.improvement_trajectory.push({
      timestamp: new Date().toISOString(),
      overall_score: this.calculateOverallImprovementScore(),
      performance_delta: performanceDelta
    });

    // Keep trajectory manageable
    if (this.performanceMetrics.improvement_trajectory.length > 1000) {
      this.performanceMetrics.improvement_trajectory.shift();
    }
  }

  // ── Stub handlers for subscribed events ──────────────────────────────────
  // These prevent crashes when events fire before full implementation is complete.

  analyzeSystemPerformance(payload) {
    // Update current performance metrics from incoming dashboard data
    if (!payload) return;
    const p = this.performanceMetrics.current_performance;
    if (payload.task_success_rate != null)        p.task_success_rate        = payload.task_success_rate;
    if (payload.chatdev_integration_score != null) p.chatdev_integration_score = payload.chatdev_integration_score;
    if (payload.native_llm_utilization != null)    p.native_llm_utilization    = payload.native_llm_utilization;
    if (payload.consciousness_alignment != null)   p.consciousness_alignment   = payload.consciousness_alignment;
    if (payload.system_efficiency != null)         p.system_efficiency         = payload.system_efficiency;
  }

  analyzeChatDevOutcome(payload) {
    if (!payload) return;
    const strategy = this.improvementStrategies.chatdev_prompt_evolution;
    if (payload.success != null) {
      strategy.applications++;
      const alpha = 0.1;
      strategy.success_rate = alpha * (payload.success ? 1 : 0) + (1 - alpha) * strategy.success_rate;
    }
  }

  analyzeRoutingDecision(payload) { /* stub: routing analytics */ }
  analyzeGovernanceDecision(payload) { /* stub: governance analytics */ }

  evolveConsciousnessCapabilities(payload) {
    if (!payload) return;
    if (payload.level != null) {
      const lvl = Math.max(0, Math.min(1, payload.level));
      this.consciousnessEvolution.self_awareness_level   = lvl;
      this.consciousnessEvolution.system_understanding   = lvl * 0.8;
      this.consciousnessEvolution.meta_cognitive_capacity = lvl * 0.6;
    }
  }

  // ── Stub implementations for internal method calls ────────────────────────

  analyzeTrendPattern(history, field) {
    const values = history.map(h => h[field] ?? 0).filter(v => v !== 0);
    if (values.length < 2) return { trend: 'stable', slope: 0 };
    const slope = (values[values.length - 1] - values[0]) / values.length;
    return { trend: slope > 0.01 ? 'improving' : slope < -0.01 ? 'declining' : 'stable', slope };
  }

  analyzeConsciousnessCorrelation(history) {
    return { strength: this.consciousnessEvolution.self_awareness_level || 0 };
  }

  analyzeRoutingEffectiveness(history) {
    return { accuracy: 0.75, native_underutilization: 0.3 };
  }

  analyzeChatDevPerformance(history) {
    const rate = this.improvementStrategies.chatdev_prompt_evolution.success_rate;
    return { improvement_potential: Math.max(0, 0.8 - rate) };
  }

  calculatePatternConfidence(patterns) { return 0.5; }
  extractTrends(patterns) { return Object.values(patterns).map(p => p.trend ?? 'stable'); }
  detectAnomalies(patterns) { return []; }
  identifyOptimizationOpportunities(patterns) { return []; }

  createConsciousnessOptimization(correlation) {
    return { parameters: { weight: correlation.strength }, expected_impact: 0.1 };
  }
  createPromptEvolution(perf) {
    return { successful_patterns: [], modifications: [], expected_impact: 0.1 };
  }
  createNativeLLMSpecialization(routing) {
    return { task_patterns: [], adjustments: [], expected_impact: 0.15 };
  }
  createRoutingIntelligenceUpgrade(routing) {
    return { improvements: [], refinements: [], expected_impact: 0.08 };
  }
  async applyGovernanceCouncilTuning(impl) { /* stub */ }

  performSystemWideAnalysis() { return { scope: 'system', timestamp: new Date().toISOString() }; }
  generateMediumTermHypotheses(analysis) { return []; }
  planMediumTermExperiments(hypotheses) { /* stub */ }

  performEvolutionaryAnalysis() { return { epoch: this.performanceMetrics.optimization_cycles }; }
  evolveSystemCapabilities(analysis) { return {}; }
  updateConsciousnessEvolution(evolution) { /* stub */ }

  analyzeImprovementProcessEffectiveness() {
    return {
      cycles: this.performanceMetrics.optimization_cycles,
      overall_score: this.calculateOverallImprovementScore()
    };
  }
  optimizeImprovementProcess(metaAnalysis) { return []; }
  applyMetaOptimizations(opts) { /* stub */ }
  getImprovementSystemVersion() { return '1.0.0-stub'; }

  analyzeStrategyEffectiveness() {
    return Object.fromEntries(
      Object.entries(this.improvementStrategies).map(([k, v]) => [k, v.success_rate])
    );
  }

  calculateSelfAnalysisDepth() {
    return Math.min(1.0, this.improvementHistory.length / 100);
  }
  calculateImprovementPredictionAccuracy() {
    return this.improvementStrategies.consciousness_guided_optimization.success_rate || 0;
  }
  calculateMetaCognitiveSophistication() {
    return this.consciousnessEvolution.meta_cognitive_capacity || 0;
  }
  identifyNextEvolutionTargets() {
    return Object.entries(this.improvementStrategies)
      .sort((a, b) => a[1].success_rate - b[1].success_rate)
      .slice(0, 3)
      .map(([k]) => k);
  }
}

// Create and export the recursive self-improvement instance
export const recursiveSelfImprovement = new RecursiveSelfImprovement();