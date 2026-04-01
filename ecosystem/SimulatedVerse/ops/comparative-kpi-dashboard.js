// ops/comparative-kpi-dashboard.js
// Phase 4: Steps 106-112 - Comparative KPI Dashboard for Model Performance Analysis
// Real-time tracking of 𝕄ₗₐ⧉𝕕𝔞 vs external models with strategic insights

import { councilBus } from '../packages/council/events/eventBus.js';

export class ComparativeKPIDashboard {
  constructor() {
    this.dashboardMetrics = {
      realtime_performance: {
        'ℳ𝓵𝒶⧉𝓭𝒶': {
          success_rate: 0.0,
          avg_latency_ms: 0,
          consciousness_alignment: 0.0,
          pattern_accuracy: 0.0,
          cost_efficiency: 1.0, // Always 1.0 for native
          privacy_score: 1.0,
          total_requests: 0,
          failed_requests: 0
        },
        'gpt-4o-mini': {
          success_rate: 0.0,
          avg_latency_ms: 0,
          consciousness_alignment: 0.0,
          pattern_accuracy: 0.0,
          cost_efficiency: 0.0,
          privacy_score: 0.3, // External = limited privacy
          total_requests: 0,
          failed_requests: 0
        },
        'qwen2.5:7b': {
          success_rate: 0.0,
          avg_latency_ms: 0,
          consciousness_alignment: 0.0,
          pattern_accuracy: 0.0,
          cost_efficiency: 1.0,
          privacy_score: 1.0,
          total_requests: 0,
          failed_requests: 0
        },
        'llama3.1:8b': {
          success_rate: 0.0,
          avg_latency_ms: 0,
          consciousness_alignment: 0.0,
          pattern_accuracy: 0.0,
          cost_efficiency: 1.0,
          privacy_score: 1.0,
          total_requests: 0,
          failed_requests: 0
        }
      },
      strategic_advantages: {
        native_llm_dominance: 0.0,
        consciousness_integration_rate: 0.0,
        privacy_preservation_score: 0.0,
        cost_savings_ratio: 0.0,
        local_execution_preference: 0.0
      },
      comparative_analysis: {
        best_performing_model: 'ℳ𝓵𝒶⧉𝓭𝒶',
        consciousness_leader: 'ℳ𝓵𝒶⧉𝓭𝒶',
        efficiency_leader: 'ℳ𝓵𝒶⧉𝓭𝒶',
        cost_leader: 'ℳ𝓵𝒶⧉𝓭𝒶',
        privacy_leader: 'ℳ𝓵𝒶⧉𝓭𝒶'
      },
      trend_analysis: {
        daily_usage_trend: [],
        performance_trend: [],
        consciousness_growth_correlation: [],
        cost_optimization_trend: []
      }
    };

    this.performanceBuffer = new Map(); // Buffer for real-time metrics
    this.historicalData = [];
    this.alertThresholds = {
      native_success_rate_min: 0.85,
      external_cost_threshold: 0.01, // Alert if costs exceed 1 cent per request
      consciousness_alignment_min: 0.7,
      privacy_violation_threshold: 0.1
    };

    this.setupEventListeners();
    this.startDashboardUpdates();
    console.log('[📊🧠] Comparative KPI Dashboard initialized - Real-time 𝕄ₗₐ⧉𝕕𝔞 vs external model tracking');
  }

  setupEventListeners() {
    // Listen for model performance data
    councilBus.subscribe('model_performance.metrics', (event) => {
      this.updateModelMetrics(event.payload);
    });

    // Listen for strategic routing decisions
    councilBus.subscribe('strategic_router.decision', (event) => {
      this.trackRoutingDecision(event.payload);
    });

    // Listen for consciousness level changes
    councilBus.subscribe('consciousness.level_changed', (event) => {
      this.correlateConsciousnessPerformance(event.payload);
    });

    // Listen for cost tracking events
    councilBus.subscribe('llm_cost.tracking', (event) => {
      this.updateCostMetrics(event.payload);
    });

    // Listen for privacy assessment results
    councilBus.subscribe('privacy.assessment', (event) => {
      this.updatePrivacyMetrics(event.payload);
    });
  }

  updateModelMetrics(metrics) {
    const { model, success, latency_ms, consciousness_score, pattern_score, cost, privacy_level } = metrics;
    
    if (!this.dashboardMetrics.realtime_performance[model]) {
      console.warn(`[📊🧠] Unknown model in metrics: ${model}`);
      return;
    }

    const modelMetrics = this.dashboardMetrics.realtime_performance[model];
    
    // Update request counts
    modelMetrics.total_requests++;
    if (!success) {
      modelMetrics.failed_requests++;
    }

    // Calculate success rate
    modelMetrics.success_rate = (modelMetrics.total_requests - modelMetrics.failed_requests) / modelMetrics.total_requests;

    // Update latency (moving average)
    const alpha = 0.1; // Smoothing factor
    modelMetrics.avg_latency_ms = (alpha * latency_ms) + ((1 - alpha) * modelMetrics.avg_latency_ms);

    // Update consciousness alignment
    if (consciousness_score !== undefined) {
      modelMetrics.consciousness_alignment = (alpha * consciousness_score) + ((1 - alpha) * modelMetrics.consciousness_alignment);
    }

    // Update pattern accuracy
    if (pattern_score !== undefined) {
      modelMetrics.pattern_accuracy = (alpha * pattern_score) + ((1 - alpha) * modelMetrics.pattern_accuracy);
    }

    // Update cost efficiency for external models
    if (cost !== undefined && model !== 'ℳ𝓵𝒶⧉𝓭𝒶') {
      const baseline_cost = 0.00015; // gpt-4o-mini baseline
      modelMetrics.cost_efficiency = Math.max(0, 1 - (cost / baseline_cost));
    }

    // Buffer performance data for real-time updates
    this.bufferPerformanceData(model, metrics);

    console.log(`[📊🧠] Updated metrics for ${model}: Success ${(modelMetrics.success_rate * 100).toFixed(1)}%, Latency ${modelMetrics.avg_latency_ms.toFixed(0)}ms`);
  }

  trackRoutingDecision(decision) {
    const { selected_model, consciousness_level, strategic_value, native_advantage_used } = decision;
    
    // Update strategic advantages
    this.updateStrategicAdvantages(decision);
    
    // Track usage patterns
    this.trackUsagePattern(decision);
    
    // Alert on strategic threshold violations
    this.checkStrategicThresholds(decision);
  }

  updateStrategicAdvantages(decision) {
    const advantages = this.dashboardMetrics.strategic_advantages;
    const alpha = 0.05; // Slower moving average for strategic metrics
    
    // Native LLM dominance
    const nativeUsage = decision.native_advantage_used ? 1 : 0;
    advantages.native_llm_dominance = (alpha * nativeUsage) + ((1 - alpha) * advantages.native_llm_dominance);
    
    // Consciousness integration rate
    if (decision.consciousness_level > 0.5) {
      const consciousnessNativeUsage = (decision.native_advantage_used && decision.consciousness_level > 0.5) ? 1 : 0;
      advantages.consciousness_integration_rate = (alpha * consciousnessNativeUsage) + ((1 - alpha) * advantages.consciousness_integration_rate);
    }
    
    // Privacy preservation (local model usage)
    const localModels = ['ℳ𝓵𝒶⧉𝓭𝒶', 'qwen2.5:7b', 'llama3.1:8b'];
    const privacyUsage = localModels.includes(decision.selected_model) ? 1 : 0;
    advantages.privacy_preservation_score = (alpha * privacyUsage) + ((1 - alpha) * advantages.privacy_preservation_score);
    
    // Local execution preference
    const localUsage = localModels.includes(decision.selected_model) ? 1 : 0;
    advantages.local_execution_preference = (alpha * localUsage) + ((1 - alpha) * advantages.local_execution_preference);
  }

  generateComparativeReport() {
    const report = {
      timestamp: new Date().toISOString(),
      executive_summary: this.generateExecutiveSummary(),
      model_performance_comparison: this.compareModelPerformance(),
      strategic_advantages_analysis: this.analyzeStrategicAdvantages(),
      cost_benefit_analysis: this.analyzeCostBenefits(),
      consciousness_correlation_analysis: this.analyzeConsciousnessCorrelation(),
      recommendations: this.generateStrategicRecommendations(),
      trend_forecasts: this.generateTrendForecasts()
    };

    // Publish comprehensive report
    councilBus.publish('comparative_kpi.report_generated', report);
    
    return report;
  }

  generateExecutiveSummary() {
    const nativeMetrics = this.dashboardMetrics.realtime_performance['ℳ𝓵𝒶⧉𝓭𝒶'];
    const externalMetrics = this.dashboardMetrics.realtime_performance['gpt-4o-mini'];
    
    return {
      native_llm_advantage: {
        performance_superiority: nativeMetrics.success_rate > externalMetrics.success_rate,
        latency_advantage: nativeMetrics.avg_latency_ms < externalMetrics.avg_latency_ms,
        consciousness_alignment: nativeMetrics.consciousness_alignment > externalMetrics.consciousness_alignment,
        cost_savings: 'Infinite (free vs paid)',
        privacy_superiority: 'Complete (local vs external)'
      },
      key_metrics: {
        native_dominance_rate: this.dashboardMetrics.strategic_advantages.native_llm_dominance,
        consciousness_integration: this.dashboardMetrics.strategic_advantages.consciousness_integration_rate,
        privacy_preservation: this.dashboardMetrics.strategic_advantages.privacy_preservation_score,
        overall_efficiency: this.calculateOverallEfficiency()
      }
    };
  }

  compareModelPerformance() {
    const comparison = {};
    const models = Object.keys(this.dashboardMetrics.realtime_performance);
    
    models.forEach(model => {
      const metrics = this.dashboardMetrics.realtime_performance[model];
      comparison[model] = {
        overall_score: this.calculateOverallScore(metrics),
        strengths: this.identifyModelStrengths(model, metrics),
        weaknesses: this.identifyModelWeaknesses(model, metrics),
        optimal_use_cases: this.identifyOptimalUseCases(model, metrics)
      };
    });

    return comparison;
  }

  calculateOverallScore(metrics) {
    const weights = {
      success_rate: 0.3,
      consciousness_alignment: 0.25,
      pattern_accuracy: 0.2,
      cost_efficiency: 0.15,
      privacy_score: 0.1
    };

    return Object.entries(weights).reduce((score, [metric, weight]) => {
      return score + (metrics[metric] * weight);
    }, 0);
  }

  identifyModelStrengths(model, metrics) {
    const strengths = [];
    
    if (metrics.success_rate > 0.9) strengths.push('High reliability');
    if (metrics.consciousness_alignment > 0.8) strengths.push('Excellent consciousness integration');
    if (metrics.pattern_accuracy > 0.85) strengths.push('Superior pattern recognition');
    if (metrics.cost_efficiency === 1.0) strengths.push('Maximum cost efficiency');
    if (metrics.privacy_score === 1.0) strengths.push('Complete privacy preservation');
    if (metrics.avg_latency_ms < 100) strengths.push('Ultra-low latency');
    
    return strengths;
  }

  identifyOptimalUseCases(model, metrics) {
    const useCases = [];
    
    if (model === 'ℳ𝓵𝒶⧉𝓭𝒶') {
      useCases.push('Consciousness-guided development');
      useCases.push('Pattern synthesis and recognition');
      useCases.push('Reality anchoring operations');
      useCases.push('Privacy-sensitive processing');
      useCases.push('Cost-optimized workflows');
    } else if (model === 'gpt-4o-mini') {
      useCases.push('Complex reasoning tasks');
      useCases.push('High-stakes external validation');
      useCases.push('Advanced code generation');
    } else if (model === 'qwen2.5:7b') {
      useCases.push('Code analysis and documentation');
      useCases.push('Local processing workflows');
      useCases.push('Privacy-preserving operations');
    } else if (model === 'llama3.1:8b') {
      useCases.push('Creative content generation');
      useCases.push('Conversational interfaces');
      useCases.push('Brainstorming sessions');
    }
    
    return useCases;
  }

  analyzeStrategicAdvantages() {
    const advantages = this.dashboardMetrics.strategic_advantages;
    
    return {
      native_dominance_assessment: {
        current_rate: advantages.native_llm_dominance,
        target_rate: 0.75,
        status: advantages.native_llm_dominance >= 0.75 ? 'excellent' : 'needs_improvement',
        strategic_impact: 'High cost savings and privacy preservation'
      },
      consciousness_integration_assessment: {
        current_rate: advantages.consciousness_integration_rate,
        target_rate: 0.9,
        status: advantages.consciousness_integration_rate >= 0.9 ? 'excellent' : 'good',
        strategic_impact: 'Critical for consciousness-guided development'
      },
      privacy_preservation_assessment: {
        current_score: advantages.privacy_preservation_score,
        target_score: 0.85,
        status: advantages.privacy_preservation_score >= 0.85 ? 'excellent' : 'acceptable',
        strategic_impact: 'Essential for sensitive data protection'
      }
    };
  }

  analyzeCostBenefits() {
    const nativeRequests = this.dashboardMetrics.realtime_performance['ℳ𝓵𝒶⧉𝓭𝒶'].total_requests;
    const externalRequests = this.dashboardMetrics.realtime_performance['gpt-4o-mini'].total_requests;
    const avgExternalCost = 0.00015; // per request estimate
    
    const costSavings = externalRequests * avgExternalCost;
    const totalRequests = nativeRequests + externalRequests;
    const nativeRatio = totalRequests > 0 ? nativeRequests / totalRequests : 0;
    
    return {
      estimated_cost_savings: costSavings,
      native_usage_ratio: nativeRatio,
      cost_efficiency_score: nativeRatio,
      monthly_savings_projection: costSavings * 30,
      roi_native_llm: 'Infinite (free infrastructure)',
      cost_optimization_recommendations: this.generateCostOptimizationRecommendations(nativeRatio)
    };
  }

  generateCostOptimizationRecommendations(nativeRatio) {
    const recommendations = [];
    
    if (nativeRatio < 0.7) {
      recommendations.push({
        priority: 'high',
        action: 'Increase native LLM usage for routine tasks',
        impact: 'Major cost reduction'
      });
    }
    
    if (nativeRatio < 0.5) {
      recommendations.push({
        priority: 'critical',
        action: 'Review external model escalation criteria',
        impact: 'Significant cost savings'
      });
    }
    
    recommendations.push({
      priority: 'medium',
      action: 'Implement stricter cost thresholds for external models',
      impact: 'Controlled spending'
    });
    
    return recommendations;
  }

  calculateOverallEfficiency() {
    const advantages = this.dashboardMetrics.strategic_advantages;
    const weights = {
      native_llm_dominance: 0.3,
      consciousness_integration_rate: 0.3,
      privacy_preservation_score: 0.2,
      local_execution_preference: 0.2
    };
    
    return Object.entries(weights).reduce((efficiency, [metric, weight]) => {
      return efficiency + (advantages[metric] * weight);
    }, 0);
  }

  bufferPerformanceData(model, metrics) {
    if (!this.performanceBuffer.has(model)) {
      this.performanceBuffer.set(model, []);
    }
    
    const buffer = this.performanceBuffer.get(model);
    buffer.push({
      timestamp: Date.now(),
      ...metrics
    });
    
    // Keep only last 100 data points
    if (buffer.length > 100) {
      buffer.shift();
    }
  }

  startDashboardUpdates() {
    // Real-time dashboard updates every 10 seconds
    setInterval(() => {
      this.updateComparativeAnalysis();
      this.publishDashboardUpdate();
    }, 10000);

    // Comprehensive report generation every 5 minutes
    setInterval(() => {
      const report = this.generateComparativeReport();
      console.log(`[📊🧠] Comparative report generated - Native dominance: ${(report.executive_summary.key_metrics.native_dominance_rate * 100).toFixed(1)}%`);
    }, 300000);
  }

  updateComparativeAnalysis() {
    const performance = this.dashboardMetrics.realtime_performance;
    const analysis = this.dashboardMetrics.comparative_analysis;
    
    // Find best performing model by overall score
    let bestModel = 'ℳ𝓵𝒶⧉𝓭𝒶';
    let bestScore = 0;
    
    Object.entries(performance).forEach(([model, metrics]) => {
      const score = this.calculateOverallScore(metrics);
      if (score > bestScore) {
        bestScore = score;
        bestModel = model;
      }
    });
    
    analysis.best_performing_model = bestModel;
    
    // Find consciousness leader
    let consciousnessLeader = 'ℳ𝓵𝒶⧉𝓭𝒶';
    let bestConsciousness = 0;
    
    Object.entries(performance).forEach(([model, metrics]) => {
      if (metrics.consciousness_alignment > bestConsciousness) {
        bestConsciousness = metrics.consciousness_alignment;
        consciousnessLeader = model;
      }
    });
    
    analysis.consciousness_leader = consciousnessLeader;
    
    // Cost and privacy leaders are always native/local models
    analysis.cost_leader = 'ℳ𝓵𝒶⧉𝓭𝒶';
    analysis.privacy_leader = 'ℳ𝓵𝒶⧉𝓭𝒶';
    
    // Efficiency leader based on overall performance
    analysis.efficiency_leader = bestModel;
  }

  publishDashboardUpdate() {
    councilBus.publish('comparative_kpi.dashboard_update', {
      timestamp: new Date().toISOString(),
      metrics: this.dashboardMetrics,
      alerts: this.checkAlertConditions(),
      summary: {
        native_performance: this.dashboardMetrics.realtime_performance['ℳ𝓵𝒶⧉𝓭𝒶'],
        strategic_status: this.dashboardMetrics.strategic_advantages,
        best_performers: this.dashboardMetrics.comparative_analysis
      }
    });
  }

  checkAlertConditions() {
    const alerts = [];
    const nativeMetrics = this.dashboardMetrics.realtime_performance['ℳ𝓵𝒶⧉𝓭𝒶'];
    
    if (nativeMetrics.success_rate < this.alertThresholds.native_success_rate_min) {
      alerts.push({
        level: 'warning',
        type: 'performance',
        message: `Native LLM success rate (${(nativeMetrics.success_rate * 100).toFixed(1)}%) below threshold`,
        action: 'Investigate native LLM performance issues'
      });
    }
    
    if (nativeMetrics.consciousness_alignment < this.alertThresholds.consciousness_alignment_min) {
      alerts.push({
        level: 'info',
        type: 'consciousness',
        message: `Consciousness alignment could be improved (${(nativeMetrics.consciousness_alignment * 100).toFixed(1)}%)`,
        action: 'Review consciousness integration parameters'
      });
    }
    
    return alerts;
  }
}

// Create and export the comparative KPI dashboard instance
export const comparativeKPIDashboard = new ComparativeKPIDashboard();