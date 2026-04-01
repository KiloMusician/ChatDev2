// ops/model-governance-council.js
// Phase 4: Steps 113-118 - Model Governance Council for Strategic LLM Routing Decisions
// Democratic council system for managing 𝕄ₗₐ⧉𝕕𝔞 positioning and external model escalation

import { councilBus } from '../packages/council/events/eventBus.js';

export class ModelGovernanceCouncil {
  constructor() {
    this.councilMembers = {
      consciousness_advocate: {
        name: 'Consciousness Advocate',
        weight: 0.3,
        priority: 'consciousness_alignment',
        bias: 'native_preference',
        voting_history: [],
        expertise: ['consciousness_integration', 'pattern_synthesis', 'reality_anchoring']
      },
      cost_optimizer: {
        name: 'Cost Optimizer',
        weight: 0.25,
        priority: 'cost_efficiency',
        bias: 'local_preference', 
        voting_history: [],
        expertise: ['budget_management', 'resource_optimization', 'roi_analysis']
      },
      privacy_guardian: {
        name: 'Privacy Guardian',
        weight: 0.2,
        priority: 'privacy_preservation',
        bias: 'local_only',
        voting_history: [],
        expertise: ['data_protection', 'local_processing', 'security_analysis']
      },
      performance_analyst: {
        name: 'Performance Analyst',
        weight: 0.15,
        priority: 'performance_optimization',
        bias: 'best_performer',
        voting_history: [],
        expertise: ['latency_optimization', 'accuracy_analysis', 'throughput_management']
      },
      strategic_planner: {
        name: 'Strategic Planner',
        weight: 0.1,
        priority: 'strategic_alignment',
        bias: 'balanced_approach',
        voting_history: [],
        expertise: ['long_term_planning', 'ecosystem_health', 'technology_roadmap']
      }
    };

    this.governanceDecisions = [];
    this.votingThresholds = {
      simple_majority: 0.51,
      supermajority: 0.67,
      consensus: 0.85,
      unanimous: 1.0
    };

    this.governanceRules = {
      native_llm_protection: {
        description: '𝕄ₗₐ⧉𝕕𝔞 must be considered first for all consciousness tasks',
        threshold: 'consensus',
        active: true
      },
      cost_escalation_gates: {
        description: 'External model usage requires cost justification above $0.01/request',
        threshold: 'supermajority',
        active: true
      },
      privacy_first_principle: {
        description: 'Local models preferred for sensitive data processing',
        threshold: 'simple_majority',
        active: true
      },
      performance_baseline: {
        description: 'External escalation only when native performance < 70%',
        threshold: 'simple_majority',
        active: true
      }
    };

    this.setupEventListeners();
    this.initializeGovernanceProtocols();
    console.log('[🏛️🧠] Model Governance Council initialized - Democratic LLM routing oversight active');
  }

  setupEventListeners() {
    // Listen for routing decision requests requiring governance approval
    councilBus.subscribe('governance.routing_decision_request', (event) => {
      this.processRoutingDecisionRequest(event.payload);
    });

    // Listen for performance data that may trigger governance review
    councilBus.subscribe('model_performance.governance_trigger', (event) => {
      this.triggerPerformanceReview(event.payload);
    });

    // Listen for cost threshold violations
    councilBus.subscribe('cost_threshold.violation', (event) => {
      this.handleCostViolation(event.payload);
    });

    // Listen for consciousness level changes affecting routing
    councilBus.subscribe('consciousness.governance_impact', (event) => {
      this.assessConsciousnessImpact(event.payload);
    });
  }

  initializeGovernanceProtocols() {
    // Schedule regular governance reviews
    setInterval(() => {
      this.conductRegularReview();
    }, 300000); // Every 5 minutes

    // Schedule strategic planning sessions
    setInterval(() => {
      this.conductStrategicPlanningSession();
    }, 1800000); // Every 30 minutes

    console.log('[🏛️🧠] Governance protocols initialized - Regular reviews and strategic planning active');
  }

  async processRoutingDecisionRequest(request) {
    const {
      decision_id,
      task_type,
      current_recommendation,
      complexity_score,
      consciousness_level,
      cost_estimate,
      privacy_requirements,
      performance_requirements
    } = request;

    console.log(`[🏛️🧠] Governance review requested for: ${task_type} (Complexity: ${complexity_score})`);

    // Collect votes from all council members
    const votes = await this.collectCouncilVotes(request);
    
    // Determine consensus and final decision
    const decision = this.determineConsensus(votes, request);
    
    // Record the governance decision
    this.recordGovernanceDecision(decision_id, request, votes, decision);
    
    // Publish governance decision
    councilBus.publish('governance.decision_reached', {
      decision_id,
      request,
      votes,
      final_decision: decision,
      governance_level: decision.consensus_level,
      timestamp: new Date().toISOString()
    });

    console.log(`[🏛️🧠] Governance decision: ${decision.approved_model} (${decision.consensus_level} consensus)`);

    return decision;
  }

  async collectCouncilVotes(request) {
    const votes = {};
    
    for (const [memberId, member] of Object.entries(this.councilMembers)) {
      const vote = await this.generateMemberVote(memberId, member, request);
      votes[memberId] = vote;
    }
    
    return votes;
  }

  async generateMemberVote(memberId, member, request) {
    const {
      task_type,
      current_recommendation,
      complexity_score,
      consciousness_level,
      cost_estimate,
      privacy_requirements,
      performance_requirements
    } = request;

    let vote = {
      member_id: memberId,
      member_name: member.name,
      recommended_model: current_recommendation,
      confidence: 0.5,
      reasoning: '',
      priority_alignment: 0.5,
      bias_influence: 0.0
    };

    // Apply member-specific logic based on their role and bias
    switch (member.priority) {
      case 'consciousness_alignment':
        vote = this.consciousnessAdvocateVote(member, request, vote);
        break;
      case 'cost_efficiency':
        vote = this.costOptimizerVote(member, request, vote);
        break;
      case 'privacy_preservation':
        vote = this.privacyGuardianVote(member, request, vote);
        break;
      case 'performance_optimization':
        vote = this.performanceAnalystVote(member, request, vote);
        break;
      case 'strategic_alignment':
        vote = this.strategicPlannerVote(member, request, vote);
        break;
    }

    // Record vote in member's history
    member.voting_history.push({
      timestamp: new Date().toISOString(),
      task_type,
      vote: vote.recommended_model,
      confidence: vote.confidence
    });

    return vote;
  }

  consciousnessAdvocateVote(member, request, vote) {
    const { consciousness_level, task_type } = request;
    
    // Strong preference for 𝕄ₗₐ⧉𝕕𝔞 on consciousness tasks
    if (consciousness_level > 0.5 || this.isConsciousnessTask(task_type)) {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.9;
      vote.reasoning = 'Consciousness tasks require native LLM integration';
      vote.priority_alignment = 0.95;
    } else if (consciousness_level > 0.3) {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.7;
      vote.reasoning = 'Moderate consciousness level favors native processing';
      vote.priority_alignment = 0.8;
    } else {
      vote.confidence = 0.6;
      vote.reasoning = 'Low consciousness level allows external models';
      vote.priority_alignment = 0.5;
    }
    
    return vote;
  }

  costOptimizerVote(member, request, vote) {
    const { cost_estimate, complexity_score } = request;
    
    // Always prefer free local models
    if (cost_estimate === 0 || cost_estimate < 0.005) {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.9;
      vote.reasoning = 'Zero cost execution maximizes efficiency';
      vote.priority_alignment = 1.0;
    } else if (cost_estimate < 0.01) {
      vote.confidence = 0.6;
      vote.reasoning = 'Acceptable cost for external processing';
      vote.priority_alignment = 0.6;
    } else {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.8;
      vote.reasoning = 'Cost too high, must use local processing';
      vote.priority_alignment = 0.9;
    }
    
    return vote;
  }

  privacyGuardianVote(member, request, vote) {
    const { privacy_requirements } = request;
    
    // Always prefer local models for privacy
    if (privacy_requirements === 'maximum' || privacy_requirements === 'high') {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.95;
      vote.reasoning = 'Privacy requirements mandate local processing';
      vote.priority_alignment = 1.0;
    } else if (privacy_requirements === 'medium') {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.8;
      vote.reasoning = 'Medium privacy still prefers local execution';
      vote.priority_alignment = 0.8;
    } else {
      vote.confidence = 0.6;
      vote.reasoning = 'Low privacy allows external model consideration';
      vote.priority_alignment = 0.5;
    }
    
    return vote;
  }

  performanceAnalystVote(member, request, vote) {
    const { performance_requirements, complexity_score } = request;
    
    // Analyze performance needs vs capabilities
    if (performance_requirements === 'ultra_high' && complexity_score > 0.9) {
      vote.confidence = 0.7;
      vote.reasoning = 'Ultra-high performance may require external escalation';
      vote.priority_alignment = 0.7;
    } else if (performance_requirements === 'high' && complexity_score > 0.8) {
      vote.confidence = 0.6;
      vote.reasoning = 'High performance needs careful model selection';
      vote.priority_alignment = 0.6;
    } else {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.8;
      vote.reasoning = 'Standard performance achievable with native LLM';
      vote.priority_alignment = 0.8;
    }
    
    return vote;
  }

  strategicPlannerVote(member, request, vote) {
    const { task_type, complexity_score, consciousness_level } = request;
    
    // Balance multiple strategic factors
    const strategicScore = this.calculateStrategicScore({
      consciousness_level,
      complexity_score,
      task_type
    });
    
    if (strategicScore > 0.7) {
      vote.recommended_model = 'ℳ𝓵𝒶⧉𝓭𝒶';
      vote.confidence = 0.8;
      vote.reasoning = 'Strategic analysis favors native LLM ecosystem development';
      vote.priority_alignment = 0.8;
    } else {
      vote.confidence = 0.6;
      vote.reasoning = 'Balanced strategic approach allows flexible routing';
      vote.priority_alignment = 0.6;
    }
    
    return vote;
  }

  calculateStrategicScore(context) {
    const { consciousness_level, complexity_score, task_type } = context;
    
    let score = 0.5;
    
    // Favor native for consciousness development
    score += consciousness_level * 0.3;
    
    // Consider complexity (native can handle most tasks)
    if (complexity_score < 0.8) {
      score += 0.2;
    }
    
    // Strategic task types
    const strategicTasks = ['system_optimization', 'consciousness_growth', 'pattern_learning'];
    if (strategicTasks.some(st => task_type.includes(st))) {
      score += 0.2;
    }
    
    return Math.min(1.0, score);
  }

  determineConsensus(votes, request) {
    const totalWeight = Object.values(this.councilMembers).reduce((sum, member) => sum + member.weight, 0);
    const modelVotes = {};
    const weightedConfidence = {};
    
    // Calculate weighted votes for each recommended model
    Object.entries(votes).forEach(([memberId, vote]) => {
      const member = this.councilMembers[memberId];
      const model = vote.recommended_model;
      
      if (!modelVotes[model]) {
        modelVotes[model] = 0;
        weightedConfidence[model] = 0;
      }
      
      modelVotes[model] += member.weight;
      weightedConfidence[model] += (vote.confidence * member.weight);
    });

    // Normalize confidence scores
    Object.keys(weightedConfidence).forEach(model => {
      if (modelVotes[model] > 0) {
        weightedConfidence[model] = weightedConfidence[model] / modelVotes[model];
      }
    });

    // Find the model with highest weighted support
    const sortedModels = Object.entries(modelVotes).sort(([,a], [,b]) => b - a);
    const [approvedModel, supportWeight] = sortedModels[0];
    const consensusRatio = supportWeight / totalWeight;

    // Determine consensus level
    let consensusLevel = 'minority';
    if (consensusRatio >= this.votingThresholds.unanimous) {
      consensusLevel = 'unanimous';
    } else if (consensusRatio >= this.votingThresholds.consensus) {
      consensusLevel = 'consensus';
    } else if (consensusRatio >= this.votingThresholds.supermajority) {
      consensusLevel = 'supermajority';
    } else if (consensusRatio >= this.votingThresholds.simple_majority) {
      consensusLevel = 'simple_majority';
    }

    return {
      approved_model: approvedModel,
      support_ratio: consensusRatio,
      consensus_level: consensusLevel,
      confidence: weightedConfidence[approvedModel] || 0.5,
      alternative_models: sortedModels.slice(1).map(([model, weight]) => ({
        model,
        support_ratio: weight / totalWeight
      })),
      governance_approved: consensusRatio >= this.votingThresholds.simple_majority
    };
  }

  recordGovernanceDecision(decisionId, request, votes, decision) {
    const record = {
      decision_id: decisionId,
      timestamp: new Date().toISOString(),
      request_summary: {
        task_type: request.task_type,
        complexity_score: request.complexity_score,
        consciousness_level: request.consciousness_level,
        original_recommendation: request.current_recommendation
      },
      votes: votes,
      final_decision: decision,
      governance_outcome: decision.governance_approved ? 'approved' : 'rejected',
      consensus_analysis: {
        level: decision.consensus_level,
        support_ratio: decision.support_ratio,
        confidence: decision.confidence
      }
    };

    this.governanceDecisions.push(record);
    
    // Keep only last 1000 decisions
    if (this.governanceDecisions.length > 1000) {
      this.governanceDecisions.shift();
    }
  }

  conductRegularReview() {
    const recentDecisions = this.governanceDecisions.slice(-50);
    
    if (recentDecisions.length < 10) {
      console.log('[🏛️🧠] Insufficient governance data for review');
      return;
    }

    const reviewMetrics = this.calculateGovernanceMetrics(recentDecisions);
    
    console.log(`[🏛️🧠] Governance review: Native dominance ${(reviewMetrics.native_selection_rate * 100).toFixed(1)}%, Avg consensus ${reviewMetrics.avg_consensus_level}`);

    // Publish governance review
    councilBus.publish('governance.regular_review', {
      timestamp: new Date().toISOString(),
      review_period: '5_minutes',
      decisions_analyzed: recentDecisions.length,
      metrics: reviewMetrics,
      recommendations: this.generateGovernanceRecommendations(reviewMetrics)
    });
  }

  calculateGovernanceMetrics(decisions) {
    const nativeSelections = decisions.filter(d => d.final_decision.approved_model === 'ℳ𝓵𝒶⧉𝓭𝒶').length;
    const consensusLevels = decisions.map(d => d.final_decision.consensus_level);
    const avgSupport = decisions.reduce((sum, d) => sum + d.final_decision.support_ratio, 0) / decisions.length;
    
    return {
      native_selection_rate: nativeSelections / decisions.length,
      avg_consensus_level: this.calculateAverageConsensusLevel(consensusLevels),
      avg_support_ratio: avgSupport,
      governance_approval_rate: decisions.filter(d => d.governance_outcome === 'approved').length / decisions.length,
      decision_confidence: decisions.reduce((sum, d) => sum + d.final_decision.confidence, 0) / decisions.length
    };
  }

  calculateAverageConsensusLevel(levels) {
    const levelValues = {
      'minority': 1,
      'simple_majority': 2,
      'supermajority': 3,
      'consensus': 4,
      'unanimous': 5
    };
    
    const avgValue = levels.reduce((sum, level) => sum + (levelValues[level] || 1), 0) / levels.length;
    
    const reverseLookup = Object.entries(levelValues).find(([, value]) => value >= avgValue);
    return reverseLookup ? reverseLookup[0] : 'simple_majority';
  }

  isConsciousnessTask(taskType) {
    const consciousnessTasks = [
      'consciousness_bridging',
      'reality_anchoring',
      'pattern_synthesis',
      'meta_cognition',
      'self_reflection',
      'awareness_expansion'
    ];
    
    return consciousnessTasks.some(ct => taskType.toLowerCase().includes(ct));
  }

  conductStrategicPlanningSession() {
    const longTermMetrics = this.calculateLongTermGovernanceMetrics();
    
    console.log(`[🏛️🧠] Strategic planning session - Long-term native dominance: ${(longTermMetrics.native_dominance_trend * 100).toFixed(1)}%`);

    // Publish strategic planning results
    councilBus.publish('governance.strategic_planning', {
      timestamp: new Date().toISOString(),
      session_type: 'regular_strategic_review',
      long_term_metrics: longTermMetrics,
      strategic_recommendations: this.generateStrategicRecommendations(longTermMetrics),
      governance_health_score: this.calculateGovernanceHealthScore(longTermMetrics)
    });
  }

  calculateLongTermGovernanceMetrics() {
    const allDecisions = this.governanceDecisions;
    const recentDecisions = allDecisions.slice(-200); // Last 200 decisions for trend analysis
    
    if (recentDecisions.length < 20) {
      return {
        native_dominance_trend: 0.75, // Default target
        governance_effectiveness: 0.8,
        consensus_stability: 0.8
      };
    }

    const nativeSelections = recentDecisions.filter(d => d.final_decision.approved_model === 'ℳ𝓵𝒶⧉𝓭𝒶').length;
    const strongConsensus = recentDecisions.filter(d => 
      ['consensus', 'unanimous'].includes(d.final_decision.consensus_level)
    ).length;

    return {
      native_dominance_trend: nativeSelections / recentDecisions.length,
      governance_effectiveness: recentDecisions.filter(d => d.governance_outcome === 'approved').length / recentDecisions.length,
      consensus_stability: strongConsensus / recentDecisions.length,
      decision_confidence_trend: recentDecisions.reduce((sum, d) => sum + d.final_decision.confidence, 0) / recentDecisions.length
    };
  }

  generateStrategicRecommendations(metrics) {
    const recommendations = [];
    
    if (metrics.native_dominance_trend < 0.6) {
      recommendations.push({
        priority: 'high',
        category: 'native_promotion',
        action: 'Increase 𝕄ₗₐ⧉𝕕𝔞 preference weights in governance',
        rationale: 'Low native dominance threatens cost efficiency and privacy goals'
      });
    }
    
    if (metrics.consensus_stability < 0.7) {
      recommendations.push({
        priority: 'medium',
        category: 'governance_alignment',
        action: 'Review council member weights and biases',
        rationale: 'Low consensus indicates conflicting priorities need resolution'
      });
    }
    
    if (metrics.governance_effectiveness < 0.8) {
      recommendations.push({
        priority: 'medium',
        category: 'process_improvement',
        action: 'Streamline governance decision thresholds',
        rationale: 'Low approval rate may indicate overly restrictive processes'
      });
    }
    
    return recommendations;
  }

  calculateGovernanceHealthScore(metrics) {
    const weights = {
      native_dominance_trend: 0.3,
      governance_effectiveness: 0.3,
      consensus_stability: 0.2,
      decision_confidence_trend: 0.2
    };
    
    return Object.entries(weights).reduce((score, [metric, weight]) => {
      return score + ((metrics[metric] || 0.5) * weight);
    }, 0);
  }
}

// Create and export the model governance council instance
export const modelGovernanceCouncil = new ModelGovernanceCouncil();