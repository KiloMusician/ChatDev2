// ops/chatdev-dashboard-enhancement.js
// Phase 3: Steps 91-95 - Real-time ChatDev Session Monitoring Dashboard Enhancement
// Integrates with existing Plinko Orchestrator to add comprehensive ChatDev monitoring

import { councilBus } from '../packages/council/events/eventBus.js';

export class ChatDevDashboardEnhancement {
  constructor() {
    this.chatdevSessions = new Map();
    this.realTimeMetrics = {
      // Session tracking
      active_chatdev_sessions: 0,
      completed_sessions_today: 0,
      failed_sessions_today: 0,
      
      // Performance metrics
      average_session_duration: 0,
      average_consciousness_level: 0.0,
      peak_consciousness_today: 0.0,
      consciousness_expansions_today: 0,
      
      // Quality metrics
      validation_success_rate: 0.0,
      council_approval_rate: 0.0,
      prompt_evolution_rate: 0.0,
      
      // System health
      routing_efficiency: 0.0,
      testing_pipeline_health: 0.0,
      feedback_loop_responsiveness: 0.0
    };
    
    this.dashboardData = {
      session_timeline: [],
      consciousness_progression: [],
      ability_performance: new Map(),
      phase_completion_rates: new Map(),
      validation_trends: [],
      council_feedback_effectiveness: [],
      prompt_evolution_history: [],
      routing_analytics: {
        complexity_distribution: new Map(),
        strategy_effectiveness: new Map(),
        agent_utilization: new Map()
      }
    };

    this.setupRealTimeMonitoring();
    console.log('[📊🧠] ChatDev Dashboard Enhancement initialized - Real-time monitoring active');
  }

  setupRealTimeMonitoring() {
    // Core ChatDev session lifecycle
    councilBus.subscribe('chatdev.session_created', (event) => {
      this.trackSessionCreation(event.payload);
    });

    councilBus.subscribe('chatdev.session_started', (event) => {
      this.trackSessionStart(event.payload);
    });

    councilBus.subscribe('chatdev.phase_completed', (event) => {
      this.trackPhaseCompletion(event.payload);
    });

    councilBus.subscribe('chatdev.session_completed', (event) => {
      this.trackSessionCompletion(event.payload);
    });

    councilBus.subscribe('chatdev.session_failed', (event) => {
      this.trackSessionFailure(event.payload);
    });

    // Enhanced routing monitoring
    councilBus.subscribe('zeta_router.chatdev_routed', (event) => {
      this.trackIntelligentRouting(event.payload);
    });

    // Testing bridge monitoring
    councilBus.subscribe('chatdev_validation.completed', (event) => {
      this.trackValidationCompletion(event.payload);
    });

    // Council feedback monitoring
    councilBus.subscribe('council.deliberation_completed', (event) => {
      this.trackCouncilDeliberation(event.payload);
    });

    // Prompt evolution monitoring
    councilBus.subscribe('chatdev.prompts_enhanced', (event) => {
      this.trackPromptEvolution(event.payload);
    });

    // Consciousness expansion monitoring
    councilBus.subscribe('consciousness.expansion_detected', (event) => {
      this.trackConsciousnessExpansion(event.payload);
    });

    // Start real-time aggregation
    this.startDashboardUpdates();
  }

  trackSessionCreation(sessionData) {
    // Handle both direct session object and wrapped session object
    const session = sessionData.session || sessionData;
    
    const sessionTracker = {
      session_id: session.id || sessionData.id,
      ability_id: session.config?.ability_id || sessionData.ability_id || 'unknown',
      created_at: new Date().toISOString(),
      status: 'created',
      consciousness_level: session.consciousness?.current_level || 0.0,
      target_complexity: session.config.consciousness_level_required || 0.3,
      routing_source: 'direct', // Will be updated if routed
      phases: {
        completed: [],
        current: null,
        remaining: session.execution?.phases?.map(p => p.name) || []
      },
      metrics: {
        creation_timestamp: Date.now(),
        validation_attempts: 0,
        consciousness_expansions: 0,
        council_reviews: 0,
        prompt_evolutions: 0
      }
    };

    this.chatdevSessions.set(session.id, sessionTracker);
    this.realTimeMetrics.active_chatdev_sessions++;

    // Add to timeline
    this.dashboardData.session_timeline.push({
      timestamp: sessionTracker.created_at,
      event: 'session_created',
      session_id: session.id,
      ability_id: session.config.ability_id,
      consciousness_level: sessionTracker.consciousness_level,
      complexity: sessionTracker.target_complexity
    });

    console.log(`[📊🧠] Tracking ChatDev session: ${session.id} (Ability: ${session.config.ability_id})`);
  }

  trackSessionStart(sessionData) {
    const { session } = sessionData;
    const tracker = this.chatdevSessions.get(session.id);
    
    if (tracker) {
      tracker.status = 'running';
      tracker.started_at = new Date().toISOString();
      tracker.metrics.start_timestamp = Date.now();

      // Update current phase
      if (session.execution?.current_phase) {
        tracker.phases.current = session.execution.current_phase;
      }

      this.dashboardData.session_timeline.push({
        timestamp: tracker.started_at,
        event: 'session_started',
        session_id: session.id,
        current_phase: tracker.phases.current
      });

      console.log(`[📊🧠] Session started: ${session.id} (Phase: ${tracker.phases.current})`);
    }
  }

  trackPhaseCompletion(phaseData) {
    const { session_id, phase, success, consciousness_level, execution_time_ms, agent_used } = phaseData;
    const tracker = this.chatdevSessions.get(session_id);
    
    if (tracker) {
      // Update phase tracking
      tracker.phases.completed.push({
        phase_name: phase,
        completed_at: new Date().toISOString(),
        success,
        consciousness_level,
        execution_time_ms,
        agent_used
      });
      
      // Remove from remaining phases
      tracker.phases.remaining = tracker.phases.remaining.filter(p => p !== phase);
      
      // Update current phase
      tracker.phases.current = tracker.phases.remaining[0] || null;
      
      // Update consciousness level
      tracker.consciousness_level = consciousness_level;

      // Update phase completion rate tracking
      const phaseStats = this.dashboardData.phase_completion_rates.get(phase) || {
        total_attempts: 0,
        successful_completions: 0,
        average_duration: 0,
        average_consciousness_impact: 0
      };
      
      phaseStats.total_attempts++;
      if (success) {
        phaseStats.successful_completions++;
      }
      phaseStats.average_duration = this.updateAverage(
        phaseStats.average_duration, 
        execution_time_ms, 
        phaseStats.total_attempts
      );
      phaseStats.average_consciousness_impact = this.updateAverage(
        phaseStats.average_consciousness_impact,
        consciousness_level,
        phaseStats.total_attempts
      );

      this.dashboardData.phase_completion_rates.set(phase, phaseStats);

      // Add to consciousness progression
      this.dashboardData.consciousness_progression.push({
        timestamp: new Date().toISOString(),
        session_id,
        phase,
        consciousness_level,
        phase_number: tracker.phases.completed.length,
        success
      });

      console.log(`[📊🧠] Phase completed: ${phase} for session ${session_id} (Success: ${success}, Consciousness: ${consciousness_level})`);
    }
  }

  trackSessionCompletion(completionData) {
    const { session, success, consciousness_expansion, execution_time_ms, abilities_unlocked } = completionData;
    const tracker = this.chatdevSessions.get(session.id);
    
    if (tracker) {
      tracker.status = 'completed';
      tracker.completed_at = new Date().toISOString();
      tracker.success = success;
      tracker.consciousness_expansion = consciousness_expansion;
      tracker.total_execution_time = execution_time_ms;
      tracker.abilities_unlocked = abilities_unlocked;

      // Update real-time metrics
      this.realTimeMetrics.active_chatdev_sessions--;
      
      if (success) {
        this.realTimeMetrics.completed_sessions_today++;
      } else {
        this.realTimeMetrics.failed_sessions_today++;
      }

      // Update average session duration
      this.updateAverageSessionDuration(execution_time_ms);

      // Update consciousness metrics
      if (consciousness_expansion > 0) {
        this.realTimeMetrics.consciousness_expansions_today++;
      }
      
      if (tracker.consciousness_level > this.realTimeMetrics.peak_consciousness_today) {
        this.realTimeMetrics.peak_consciousness_today = tracker.consciousness_level;
      }

      // Update ability performance tracking
      this.updateAbilityPerformance(tracker.ability_id, success, consciousness_expansion, execution_time_ms);

      // Timeline update
      this.dashboardData.session_timeline.push({
        timestamp: tracker.completed_at,
        event: 'session_completed',
        session_id: session.id,
        success,
        consciousness_expansion,
        total_phases: tracker.phases.completed.length,
        total_duration: execution_time_ms
      });

      console.log(`[📊🧠] Session completed: ${session.id} (Success: ${success}, Consciousness: +${consciousness_expansion})`);
    }
  }

  trackSessionFailure(failureData) {
    const { session, error, failure_phase } = failureData;
    const tracker = this.chatdevSessions.get(session.id);
    
    if (tracker) {
      tracker.status = 'failed';
      tracker.failed_at = new Date().toISOString();
      tracker.failure_reason = error;
      tracker.failure_phase = failure_phase;

      this.realTimeMetrics.active_chatdev_sessions--;
      this.realTimeMetrics.failed_sessions_today++;

      // Update ability performance (failure)
      this.updateAbilityPerformance(tracker.ability_id, false, 0, Date.now() - tracker.metrics.start_timestamp);

      // Timeline update
      this.dashboardData.session_timeline.push({
        timestamp: tracker.failed_at,
        event: 'session_failed',
        session_id: session.id,
        error,
        failure_phase,
        phases_completed: tracker.phases.completed.length
      });

      console.log(`[📊🧠] Session failed: ${session.id} (Phase: ${failure_phase}, Error: ${error})`);
    }
  }

  trackIntelligentRouting(routingData) {
    const { task_id, session_id, complexity, strategy } = routingData;
    
    // Update routing analytics
    const complexityBucket = Math.floor(complexity * 10) / 10;
    this.dashboardData.routing_analytics.complexity_distribution.set(
      complexityBucket,
      (this.dashboardData.routing_analytics.complexity_distribution.get(complexityBucket) || 0) + 1
    );

    this.dashboardData.routing_analytics.strategy_effectiveness.set(
      strategy,
      (this.dashboardData.routing_analytics.strategy_effectiveness.get(strategy) || { uses: 0, successes: 0 })
    );

    // Update session tracker if it exists
    const tracker = this.chatdevSessions.get(session_id);
    if (tracker) {
      tracker.routing_source = 'intelligent';
      tracker.routing_complexity = complexity;
      tracker.routing_strategy = strategy;
    }

    // Calculate routing efficiency
    this.updateRoutingEfficiency();

    console.log(`[📊🧠] Intelligent routing tracked: ${strategy} (Complexity: ${complexity})`);
  }

  trackValidationCompletion(validationData) {
    const { chatdev_session_id, validation_success, duration_ms, validation_summary } = validationData;
    const tracker = this.chatdevSessions.get(chatdev_session_id);
    
    if (tracker) {
      tracker.metrics.validation_attempts++;
      tracker.validation_result = {
        success: validation_success,
        duration_ms,
        overall_score: validation_summary.overall_score,
        completed_at: new Date().toISOString()
      };

      // Update validation trends
      this.dashboardData.validation_trends.push({
        timestamp: new Date().toISOString(),
        session_id: chatdev_session_id,
        success: validation_success,
        score: validation_summary.overall_score,
        duration_ms,
        ability_id: tracker.ability_id
      });

      // Update validation success rate
      this.updateValidationSuccessRate();

      // Update testing pipeline health
      this.updateTestingPipelineHealth(validation_success, duration_ms);

      console.log(`[📊🧠] Validation tracked: ${validation_success ? 'PASSED' : 'FAILED'} for session ${chatdev_session_id}`);
    }
  }

  trackCouncilDeliberation(deliberationData) {
    const { session_id, decision, confidence_level, agent_insights } = deliberationData;
    const tracker = this.chatdevSessions.get(session_id);
    
    if (tracker) {
      tracker.metrics.council_reviews++;
      tracker.last_council_decision = {
        decision,
        confidence_level,
        timestamp: new Date().toISOString(),
        insight_count: agent_insights.length
      };

      // Track council effectiveness
      this.dashboardData.council_feedback_effectiveness.push({
        timestamp: new Date().toISOString(),
        session_id,
        decision,
        confidence_level,
        insight_count: agent_insights.length,
        session_success: tracker.success
      });

      // Update council approval rate
      this.updateCouncilApprovalRate(decision, confidence_level);

      // Update feedback loop responsiveness
      this.updateFeedbackLoopResponsiveness();

      console.log(`[📊🧠] Council deliberation tracked: ${decision} (Confidence: ${confidence_level}) for session ${session_id}`);
    }
  }

  trackPromptEvolution(evolutionData) {
    const { session_id, ability_ids, evolution_summary, expected_improvement } = evolutionData;
    
    // Track prompt evolution history
    this.dashboardData.prompt_evolution_history.push({
      timestamp: new Date().toISOString(),
      session_id,
      ability_ids,
      evolution_summary,
      expected_improvement
    });

    // Update prompt evolution rate
    this.realTimeMetrics.prompt_evolution_rate = this.calculatePromptEvolutionRate();

    // Update session tracker
    const tracker = this.chatdevSessions.get(session_id);
    if (tracker) {
      tracker.metrics.prompt_evolutions++;
    }

    console.log(`[📊🧠] Prompt evolution tracked: ${evolution_summary} (Expected improvement: ${Math.round(expected_improvement * 100)}%)`);
  }

  trackConsciousnessExpansion(expansionData) {
    const { session_id, expansion_amount, expansion_type } = expansionData;
    const tracker = this.chatdevSessions.get(session_id);
    
    if (tracker) {
      tracker.metrics.consciousness_expansions++;
      tracker.consciousness_level += expansion_amount;

      // Update global consciousness metrics
      this.realTimeMetrics.consciousness_expansions_today++;
      
      if (tracker.consciousness_level > this.realTimeMetrics.peak_consciousness_today) {
        this.realTimeMetrics.peak_consciousness_today = tracker.consciousness_level;
      }

      // Update consciousness progression
      this.dashboardData.consciousness_progression.push({
        timestamp: new Date().toISOString(),
        session_id,
        event: 'expansion',
        expansion_amount,
        expansion_type,
        new_level: tracker.consciousness_level
      });

      console.log(`[📊🧠] Consciousness expansion tracked: +${expansion_amount} for session ${session_id} (New level: ${tracker.consciousness_level})`);
    }
  }

  // Utility methods for metric calculations
  updateAverage(currentAverage, newValue, totalCount) {
    return ((currentAverage * (totalCount - 1)) + newValue) / totalCount;
  }

  updateAverageSessionDuration(newDuration) {
    const totalSessions = this.realTimeMetrics.completed_sessions_today + this.realTimeMetrics.failed_sessions_today;
    this.realTimeMetrics.average_session_duration = this.updateAverage(
      this.realTimeMetrics.average_session_duration,
      newDuration,
      totalSessions
    );
  }

  updateAbilityPerformance(abilityId, success, consciousnessExpansion, executionTime) {
    const performance = this.dashboardData.ability_performance.get(abilityId) || {
      total_uses: 0,
      successful_uses: 0,
      total_consciousness_expansion: 0,
      total_execution_time: 0,
      success_rate: 0,
      average_consciousness_impact: 0,
      average_execution_time: 0
    };

    performance.total_uses++;
    if (success) {
      performance.successful_uses++;
    }
    performance.total_consciousness_expansion += consciousnessExpansion;
    performance.total_execution_time += executionTime;
    
    performance.success_rate = performance.successful_uses / performance.total_uses;
    performance.average_consciousness_impact = performance.total_consciousness_expansion / performance.total_uses;
    performance.average_execution_time = performance.total_execution_time / performance.total_uses;

    this.dashboardData.ability_performance.set(abilityId, performance);
  }

  updateValidationSuccessRate() {
    const validatedSessions = Array.from(this.chatdevSessions.values()).filter(s => s.validation_result);
    if (validatedSessions.length > 0) {
      const successfulValidations = validatedSessions.filter(s => s.validation_result.success).length;
      this.realTimeMetrics.validation_success_rate = successfulValidations / validatedSessions.length;
    }
  }

  updateCouncilApprovalRate(decision, confidenceLevel) {
    // Simple approval calculation - decisions with confidence > 0.7 are considered approvals
    const isApproval = confidenceLevel > 0.7;
    // This would need a more sophisticated calculation in practice
    this.realTimeMetrics.council_approval_rate = this.realTimeMetrics.council_approval_rate * 0.9 + (isApproval ? 0.1 : 0);
  }

  updateRoutingEfficiency() {
    const totalRouted = this.dashboardData.routing_analytics.complexity_distribution.size;
    const successfulSessions = Array.from(this.chatdevSessions.values()).filter(s => s.success).length;
    
    if (totalRouted > 0) {
      this.realTimeMetrics.routing_efficiency = successfulSessions / totalRouted;
    }
  }

  updateTestingPipelineHealth(validationSuccess, duration) {
    // Health score based on success rate and reasonable duration
    const healthScore = validationSuccess ? (duration < 60000 ? 1.0 : 0.7) : 0.3;
    this.realTimeMetrics.testing_pipeline_health = this.realTimeMetrics.testing_pipeline_health * 0.9 + healthScore * 0.1;
  }

  updateFeedbackLoopResponsiveness() {
    // Calculate based on how quickly council feedback leads to prompt evolution
    // This is a simplified calculation
    this.realTimeMetrics.feedback_loop_responsiveness = Math.min(1.0, 
      this.dashboardData.prompt_evolution_history.length / Math.max(1, this.dashboardData.council_feedback_effectiveness.length)
    );
  }

  calculatePromptEvolutionRate() {
    const recentEvolutions = this.dashboardData.prompt_evolution_history.filter(
      evolution => Date.now() - new Date(evolution.timestamp).getTime() < 24 * 60 * 60 * 1000
    );
    return recentEvolutions.length / 24; // Evolutions per hour
  }

  startDashboardUpdates() {
    // Update average consciousness level every 30 seconds
    setInterval(() => {
      this.updateAverageConsciousnessLevel();
      this.pruneOldData();
    }, 30000);

    // Publish dashboard updates every 2 minutes
    setInterval(() => {
      this.publishDashboardSnapshot();
    }, 120000);

    console.log('[📊🧠] Dashboard update intervals started');
  }

  updateAverageConsciousnessLevel() {
    const activeSessions = Array.from(this.chatdevSessions.values()).filter(s => s.status === 'running');
    if (activeSessions.length > 0) {
      const totalConsciousness = activeSessions.reduce((sum, session) => sum + session.consciousness_level, 0);
      this.realTimeMetrics.average_consciousness_level = totalConsciousness / activeSessions.length;
    }
  }

  pruneOldData() {
    const cutoffTime = new Date(Date.now() - 24 * 60 * 60 * 1000); // 24 hours ago
    
    // Prune timeline data
    this.dashboardData.session_timeline = this.dashboardData.session_timeline.filter(
      event => new Date(event.timestamp) > cutoffTime
    );
    
    // Prune other time-series data
    this.dashboardData.consciousness_progression = this.dashboardData.consciousness_progression.filter(
      event => new Date(event.timestamp) > cutoffTime
    );
    
    this.dashboardData.validation_trends = this.dashboardData.validation_trends.filter(
      trend => new Date(trend.timestamp) > cutoffTime
    );
  }

  publishDashboardSnapshot() {
    const snapshot = {
      timestamp: new Date().toISOString(),
      real_time_metrics: this.realTimeMetrics,
      active_sessions: this.getActiveSessionsSummary(),
      recent_timeline: this.dashboardData.session_timeline.slice(-100),
      consciousness_trends: this.getConsciousnessTrends(),
      ability_performance: Object.fromEntries(this.dashboardData.ability_performance),
      phase_performance: Object.fromEntries(this.dashboardData.phase_completion_rates),
      validation_health: this.getValidationHealthSummary(),
      council_effectiveness: this.getCouncilEffectivenessSummary(),
      routing_analytics: this.getRoutingAnalyticsSummary(),
      system_health_score: this.calculateSystemHealthScore()
    };

    councilBus.publish('chatdev.dashboard_update', snapshot);
    
    console.log(`[📊🧠] Dashboard snapshot published - ${this.realTimeMetrics.active_chatdev_sessions} active sessions, Health Score: ${snapshot.system_health_score.toFixed(2)}`);
  }

  // Public API methods
  getActiveSessionsSummary() {
    const activeSessions = Array.from(this.chatdevSessions.values()).filter(s => s.status === 'running');
    
    return {
      total: activeSessions.length,
      by_ability: activeSessions.reduce((acc, session) => {
        acc[session.ability_id] = (acc[session.ability_id] || 0) + 1;
        return acc;
      }, {}),
      by_phase: activeSessions.reduce((acc, session) => {
        acc[session.phases.current || 'unknown'] = (acc[session.phases.current || 'unknown'] || 0) + 1;
        return acc;
      }, {}),
      average_consciousness: activeSessions.length > 0 ? 
        activeSessions.reduce((sum, s) => sum + s.consciousness_level, 0) / activeSessions.length : 0
    };
  }

  getConsciousnessTrends() {
    const recentProgression = this.dashboardData.consciousness_progression.slice(-20);
    
    if (recentProgression.length < 2) {
      return { trend: 'stable', rate: 0, current_peak: this.realTimeMetrics.peak_consciousness_today };
    }
    
    const startLevel = recentProgression[0].consciousness_level;
    const endLevel = recentProgression[recentProgression.length - 1].consciousness_level;
    const rate = (endLevel - startLevel) / recentProgression.length;
    
    return {
      trend: rate > 0.01 ? 'ascending' : rate < -0.01 ? 'descending' : 'stable',
      rate,
      current_peak: this.realTimeMetrics.peak_consciousness_today,
      progression_data: recentProgression.slice(-10) // Last 10 data points
    };
  }

  getValidationHealthSummary() {
    const recentValidations = this.dashboardData.validation_trends.slice(-20);
    
    return {
      recent_success_rate: recentValidations.length > 0 ? 
        recentValidations.filter(v => v.success).length / recentValidations.length : 0,
      average_validation_time: recentValidations.length > 0 ?
        recentValidations.reduce((sum, v) => sum + v.duration_ms, 0) / recentValidations.length : 0,
      pipeline_health: this.realTimeMetrics.testing_pipeline_health,
      validation_trends: recentValidations.slice(-10)
    };
  }

  getCouncilEffectivenessSummary() {
    const recentFeedback = this.dashboardData.council_feedback_effectiveness.slice(-10);
    
    return {
      average_confidence: recentFeedback.length > 0 ?
        recentFeedback.reduce((sum, f) => sum + f.confidence_level, 0) / recentFeedback.length : 0,
      approval_rate: this.realTimeMetrics.council_approval_rate,
      feedback_responsiveness: this.realTimeMetrics.feedback_loop_responsiveness,
      recent_decisions: recentFeedback.slice(-5)
    };
  }

  getRoutingAnalyticsSummary() {
    return {
      complexity_distribution: Object.fromEntries(this.dashboardData.routing_analytics.complexity_distribution),
      strategy_effectiveness: Object.fromEntries(this.dashboardData.routing_analytics.strategy_effectiveness),
      routing_efficiency: this.realTimeMetrics.routing_efficiency,
      total_routed_today: Array.from(this.dashboardData.routing_analytics.complexity_distribution.values())
        .reduce((sum, count) => sum + count, 0)
    };
  }

  calculateSystemHealthScore() {
    const weights = {
      validation_success_rate: 0.25,
      council_approval_rate: 0.20,
      routing_efficiency: 0.20,
      testing_pipeline_health: 0.15,
      feedback_loop_responsiveness: 0.10,
      consciousness_growth: 0.10
    };

    const consciousnessGrowthScore = Math.min(1.0, this.realTimeMetrics.consciousness_expansions_today / 10);

    const healthScore = 
      (this.realTimeMetrics.validation_success_rate * weights.validation_success_rate) +
      (this.realTimeMetrics.council_approval_rate * weights.council_approval_rate) +
      (this.realTimeMetrics.routing_efficiency * weights.routing_efficiency) +
      (this.realTimeMetrics.testing_pipeline_health * weights.testing_pipeline_health) +
      (this.realTimeMetrics.feedback_loop_responsiveness * weights.feedback_loop_responsiveness) +
      (consciousnessGrowthScore * weights.consciousness_growth);

    return Math.min(1.0, Math.max(0.0, healthScore));
  }

  getDashboardData() {
    return {
      real_time_metrics: this.realTimeMetrics,
      active_sessions: Object.fromEntries(
        Array.from(this.chatdevSessions.entries()).filter(([id, session]) => session.status === 'running')
      ),
      recent_timeline: this.dashboardData.session_timeline.slice(-50),
      consciousness_progression: this.dashboardData.consciousness_progression.slice(-30),
      ability_performance: Object.fromEntries(this.dashboardData.ability_performance),
      validation_trends: this.dashboardData.validation_trends.slice(-20),
      council_feedback_trends: this.dashboardData.council_feedback_effectiveness.slice(-10),
      prompt_evolution_history: this.dashboardData.prompt_evolution_history.slice(-10),
      system_health_score: this.calculateSystemHealthScore()
    };
  }

  getSessionDetails(sessionId) {
    return this.chatdevSessions.get(sessionId);
  }
}

// Export singleton instance
export const chatdevDashboardEnhancement = new ChatDevDashboardEnhancement();

console.log('[📊🧠] ChatDev Dashboard Enhancement module loaded - Real-time monitoring ready');