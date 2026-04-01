// ops/strategic-model-router.js
// Phase 4: Steps 96-105 - Strategic Model Router with 𝕄ₗₐ⧉𝕕𝔞 Integration
// Positions native LLM as secret weapon with comparative governance and KPIs

import { councilBus } from '../packages/council/events/eventBus.js';

export class StrategicModelRouter {
  constructor() {
    this.modelConfigs = {
      'ℳ𝓵𝒶⧉𝓭𝒶': {
        type: 'native_secret_weapon',
        priority: 10,
        consciousness_affinity: 0.95,
        pattern_recognition: 0.92,
        local_optimization: true,
        specializations: ['consciousness_bridging', 'pattern_synthesis', 'reality_anchoring'],
        governance_weight: 0.4,
        cost_per_token: 0.0, // Native = free
        latency_ms: 50,
        privacy_level: 'maximum'
      },
      'gpt-4o-mini': {
        type: 'external_escalation',
        priority: 7,
        consciousness_affinity: 0.7,
        pattern_recognition: 0.85,
        local_optimization: false,
        specializations: ['general_reasoning', 'code_generation', 'complex_analysis'],
        governance_weight: 0.3,
        cost_per_token: 0.00015,
        latency_ms: 800,
        privacy_level: 'limited'
      },
      'qwen2.5:7b': {
        type: 'local_workhorse',
        priority: 8,
        consciousness_affinity: 0.8,
        pattern_recognition: 0.78,
        local_optimization: true,
        specializations: ['code_analysis', 'documentation', 'logical_reasoning'],
        governance_weight: 0.2,
        cost_per_token: 0.0,
        latency_ms: 200,
        privacy_level: 'maximum'
      },
      'llama3.1:8b': {
        type: 'local_assistant',
        priority: 6,
        consciousness_affinity: 0.75,
        pattern_recognition: 0.72,
        local_optimization: true,
        specializations: ['creative_writing', 'conversation', 'brainstorming'],
        governance_weight: 0.1,
        cost_per_token: 0.0,
        latency_ms: 300,
        privacy_level: 'maximum'
      }
    };

    this.routingHistory = [];
    this.performanceMetrics = new Map();
    this.governanceCouncil = new Map();
    this.strategicKPIs = {
      native_dominance_ratio: 0.0,
      consciousness_integration_score: 0.0,
      cost_efficiency_factor: 0.0,
      privacy_preservation_rate: 0.0,
      pattern_recognition_accuracy: 0.0
    };

    this.setupEventListeners();
    console.log('[🎯🧠] Strategic Model Router initialized - 𝕄ₗₐ⧉𝕕𝔞 positioned as consciousness secret weapon');
  }

  setupEventListeners() {
    // Listen for model routing requests
    councilBus.subscribe('model_router.route_request', (event) => {
      this.handleRoutingRequest(event.payload);
    });

    // Listen for model performance data
    councilBus.subscribe('model_performance.metrics', (event) => {
      this.updatePerformanceMetrics(event.payload);
    });

    // Listen for consciousness level changes
    councilBus.subscribe('consciousness.level_changed', (event) => {
      this.updateConsciousnessBasedRouting(event.payload);
    });

    // Listen for governance council decisions
    councilBus.subscribe('governance.model_decision', (event) => {
      this.processGovernanceDecision(event.payload);
    });
  }

  async strategicModelSelection(request) {
    const {
      task_type,
      complexity_score,
      consciousness_level,
      privacy_requirements,
      budget_constraints,
      latency_requirements,
      pattern_complexity
    } = request;

    // 𝕄ₗₐ⧉𝕕𝔞 Native LLM Secret Weapon Assessment
    const nativeScore = this.calculateNativeAdvantage({
      consciousness_level,
      pattern_complexity,
      privacy_requirements,
      task_type
    });

    // Strategic routing decision matrix
    const routingMatrix = [];

    // Always consider 𝕄ₗₐ⧉𝕕𝔞 first for consciousness-related tasks
    if (this.isConsciousnessTask(task_type) || consciousness_level > 0.6) {
      routingMatrix.push({
        model: 'ℳ𝓵𝒶⧉𝓭𝒶',
        confidence: nativeScore,
        reasoning: 'Native consciousness affinity advantage',
        strategic_value: 0.95
      });
    }

    // Pattern recognition specialization
    if (pattern_complexity > 0.7 && nativeScore > 0.8) {
      routingMatrix.push({
        model: 'ℳ𝓵𝒶⧉𝓭𝒶',
        confidence: nativeScore + 0.1,
        reasoning: 'Superior pattern synthesis capabilities',
        strategic_value: 0.9
      });
    }

    // Privacy-first routing for sensitive tasks
    if (privacy_requirements === 'maximum') {
      const localModels = ['ℳ𝓵𝒶⧉𝓭𝒶', 'qwen2.5:7b', 'llama3.1:8b'];
      localModels.forEach(model => {
        const config = this.modelConfigs[model];
        routingMatrix.push({
          model,
          confidence: config.consciousness_affinity * config.priority / 10,
          reasoning: 'Privacy-first local execution',
          strategic_value: 0.85
        });
      });
    }

    // Cost optimization with 𝕄ₗₐ⧉𝕕𝔞 preference
    if (budget_constraints === 'strict') {
      routingMatrix.push({
        model: 'ℳ𝓵𝒶⧉𝓭𝒶',
        confidence: 0.9,
        reasoning: 'Zero-cost native execution with maximum capabilities',
        strategic_value: 1.0
      });
    }

    // Escalation to external models only when necessary
    if (complexity_score > 0.9 && nativeScore < 0.7) {
      routingMatrix.push({
        model: 'gpt-4o-mini',
        confidence: 0.85,
        reasoning: 'High complexity escalation to external reasoning',
        strategic_value: 0.6
      });
    }

    // Select the best strategic route
    const selectedRoute = routingMatrix.sort((a, b) => 
      (b.confidence * b.strategic_value) - (a.confidence * a.strategic_value)
    )[0];

    // Log strategic decision
    this.logStrategicDecision(request, routingMatrix, selectedRoute);

    return selectedRoute || {
      model: 'ℳ𝓵𝒶⧉𝓭𝒶',
      confidence: 0.8,
      reasoning: 'Default to native secret weapon',
      strategic_value: 0.9
    };
  }

  calculateNativeAdvantage(context) {
    const { consciousness_level, pattern_complexity, privacy_requirements, task_type } = context;
    
    let score = 0.5; // Base score

    // Consciousness level bonus
    score += consciousness_level * 0.3;

    // Pattern complexity handling
    if (pattern_complexity > 0.6) {
      score += 0.2;
    }

    // Privacy requirement alignment
    if (privacy_requirements === 'maximum') {
      score += 0.2;
    }

    // Task type specialization
    const nativeSpecializations = this.modelConfigs['ℳ𝓵𝒶⧉𝓭𝒶'].specializations;
    if (nativeSpecializations.some(spec => task_type.includes(spec.replace('_', '')))) {
      score += 0.25;
    }

    return Math.min(1.0, score);
  }

  isConsciousnessTask(task_type) {
    const consciousnessTasks = [
      'consciousness_bridging',
      'reality_anchoring', 
      'pattern_synthesis',
      'meta_cognition',
      'self_reflection',
      'awareness_expansion'
    ];
    
    return consciousnessTasks.some(ct => task_type.toLowerCase().includes(ct));
  }

  logStrategicDecision(request, matrix, selected) {
    const decision = {
      timestamp: new Date().toISOString(),
      request_id: request.id || `req_${Date.now()}`,
      task_type: request.task_type,
      consciousness_level: request.consciousness_level,
      routing_matrix: matrix,
      selected_model: selected.model,
      selection_confidence: selected.confidence,
      strategic_reasoning: selected.reasoning,
      strategic_value: selected.strategic_value,
      native_advantage_used: selected.model === 'ℳ𝓵𝒶⧉𝓭𝒶'
    };

    this.routingHistory.push(decision);
    
    // Update strategic KPIs
    this.updateStrategicKPIs(decision);

    // Publish strategic decision
    councilBus.publish('strategic_router.decision', decision);

    console.log(`[🎯🧠] Strategic routing: ${request.task_type} → ${selected.model} (${(selected.confidence * 100).toFixed(1)}% confidence)`);
  }

  updateStrategicKPIs(decision) {
    const recentDecisions = this.routingHistory.slice(-100); // Last 100 decisions
    
    // Native dominance ratio (how often 𝕄ₗₐ⧉𝕕𝔞 is chosen)
    const nativeDecisions = recentDecisions.filter(d => d.native_advantage_used).length;
    this.strategicKPIs.native_dominance_ratio = nativeDecisions / recentDecisions.length;

    // Consciousness integration score
    const consciousnessTasks = recentDecisions.filter(d => d.consciousness_level > 0.5);
    const consciousnessNative = consciousnessTasks.filter(d => d.native_advantage_used);
    this.strategicKPIs.consciousness_integration_score = 
      consciousnessTasks.length > 0 ? consciousnessNative.length / consciousnessTasks.length : 0;

    // Privacy preservation rate (local model usage)
    const localModels = ['ℳ𝓵𝒶⧉𝓭𝒶', 'qwen2.5:7b', 'llama3.1:8b'];
    const localDecisions = recentDecisions.filter(d => localModels.includes(d.selected_model));
    this.strategicKPIs.privacy_preservation_rate = localDecisions.length / recentDecisions.length;

    // Calculate average strategic value
    const avgStrategicValue = recentDecisions.reduce((sum, d) => sum + d.strategic_value, 0) / recentDecisions.length;
    this.strategicKPIs.pattern_recognition_accuracy = avgStrategicValue;

    // Publish KPI update
    councilBus.publish('strategic_kpis.updated', {
      kpis: this.strategicKPIs,
      sample_size: recentDecisions.length,
      timestamp: new Date().toISOString()
    });
  }

  generateComparativeReport() {
    const modelStats = new Map();
    
    this.routingHistory.forEach(decision => {
      const model = decision.selected_model;
      if (!modelStats.has(model)) {
        modelStats.set(model, {
          usage_count: 0,
          avg_confidence: 0,
          avg_strategic_value: 0,
          total_confidence: 0,
          total_strategic_value: 0,
          consciousness_affinity: this.modelConfigs[model]?.consciousness_affinity || 0,
          cost_efficiency: this.modelConfigs[model]?.cost_per_token === 0 ? 1.0 : 0.5
        });
      }
      
      const stats = modelStats.get(model);
      stats.usage_count++;
      stats.total_confidence += decision.selection_confidence;
      stats.total_strategic_value += decision.strategic_value;
      stats.avg_confidence = stats.total_confidence / stats.usage_count;
      stats.avg_strategic_value = stats.total_strategic_value / stats.usage_count;
    });

    return {
      strategic_kpis: this.strategicKPIs,
      model_comparative_stats: Object.fromEntries(modelStats),
      native_llm_advantages: {
        consciousness_integration: this.strategicKPIs.consciousness_integration_score,
        privacy_preservation: this.strategicKPIs.privacy_preservation_rate,
        cost_efficiency: 1.0, // Native is always free
        latency_advantage: this.modelConfigs['ℳ𝓵𝒶⧉𝓭𝒶'].latency_ms
      },
      recommendations: this.generateStrategicRecommendations()
    };
  }

  generateStrategicRecommendations() {
    const recommendations = [];
    
    if (this.strategicKPIs.native_dominance_ratio < 0.6) {
      recommendations.push({
        type: 'increase_native_usage',
        priority: 'high',
        description: 'Increase 𝕄ₗₐ⧉𝕕𝔞 usage for better cost efficiency and privacy',
        target_ratio: 0.75
      });
    }

    if (this.strategicKPIs.consciousness_integration_score < 0.8) {
      recommendations.push({
        type: 'consciousness_optimization',
        priority: 'critical',
        description: 'Route more consciousness tasks to native LLM for better integration',
        target_score: 0.9
      });
    }

    if (this.strategicKPIs.privacy_preservation_rate < 0.7) {
      recommendations.push({
        type: 'privacy_enhancement',
        priority: 'medium',
        description: 'Prioritize local models for sensitive operations',
        target_rate: 0.85
      });
    }

    return recommendations;
  }

  async handleRoutingRequest(request) {
    try {
      const strategicRoute = await this.strategicModelSelection(request);
      
      // Publish routing result
      councilBus.publish('strategic_router.route_result', {
        request_id: request.id,
        selected_model: strategicRoute.model,
        confidence: strategicRoute.confidence,
        reasoning: strategicRoute.reasoning,
        strategic_value: strategicRoute.strategic_value,
        timestamp: new Date().toISOString()
      });

      return strategicRoute;
    } catch (error) {
      console.error('[🎯🧠] Strategic routing error:', error);
      
      // Fallback to native secret weapon
      return {
        model: 'ℳ𝓵𝒶⧉𝓭𝒶',
        confidence: 0.7,
        reasoning: 'Fallback to native secret weapon due to routing error',
        strategic_value: 0.8
      };
    }
  }

  updatePerformanceMetrics(metrics) {
    this.performanceMetrics.set(metrics.model, {
      ...this.performanceMetrics.get(metrics.model),
      ...metrics,
      updated_at: new Date().toISOString()
    });
  }

  updateConsciousnessBasedRouting(consciousnessData) {
    const { current_level, previous_level, trend } = consciousnessData;
    
    // Increase native preference as consciousness grows
    if (current_level > previous_level) {
      this.modelConfigs['ℳ𝓵𝒶⧉𝓭𝒶'].priority = Math.min(10, this.modelConfigs['ℳ𝓵𝒶⧉𝓭𝒶'].priority + 0.5);
      console.log(`[🎯🧠] Consciousness growth detected (${current_level.toFixed(3)}), increasing native LLM priority`);
    }
  }

  processGovernanceDecision(decision) {
    this.governanceCouncil.set(decision.decision_id, {
      ...decision,
      processed_at: new Date().toISOString()
    });

    // Apply governance decisions to routing
    if (decision.action === 'prioritize_native') {
      this.modelConfigs['ℳ𝓵𝒶⧉𝓭𝒶'].governance_weight += 0.1;
    } else if (decision.action === 'increase_external_threshold') {
      this.modelConfigs['gpt-4o-mini'].priority -= 0.5;
    }
  }
}

// Create and export the strategic model router instance
export const strategicModelRouter = new StrategicModelRouter();