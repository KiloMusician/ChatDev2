// packages/studio/adapters/director-adapter.js
// Director Adapter - Connects existing Director agent to the universal protocol
// ENHANCES The Director without REPLACING it

import { councilBus } from '../../council/events/eventBus.js';
import { DEVELOPMENT_PROTOCOL } from '../serial-protocol.js';

class DirectorAdapter {
  constructor() {
    this.active = false;
    console.log('[🎭] Director Adapter initializing - Connecting existing Director to studio protocol');
  }

  start() {
    if (this.active) return;

    // Listen for planning requests via the universal protocol
    councilBus.subscribe('studio.planning', (event) => {
      this.handlePlanningRequest(event);
    });

    this.active = true;
    console.log('[🎭] Director Adapter online - Ready to orchestrate strategic planning');
    
    // Register capabilities with the protocol
    councilBus.publish('studio.agent.ready', {
      agent: 'director',
      capabilities: ['planning', 'strategy'],
      adapter: 'director-adapter',
      timestamp: new Date().toISOString()
    });
  }

  async handlePlanningRequest(event) {
    if (!DEVELOPMENT_PROTOCOL.validateEvent(event)) {
      console.warn('[🎭] Director Adapter received invalid event:', event);
      return;
    }

    const { taskId, directive, analysis } = event.payload;
    console.log(`[🎭] Director Adapter formulating plan for task: ${taskId}`);

    try {
      // Use The Director's EXISTING strategic planning capabilities
      const strategicPlan = await this.formulateStrategicPlan(directive, analysis);
      
      // Publish result using the universal protocol - next phase is COMPOSITION
      const nextPhase = DEVELOPMENT_PROTOCOL.getNextPhase('planning');
      if (nextPhase) {
        const nextEvent = DEVELOPMENT_PROTOCOL.createEvent(
          nextPhase,
          taskId,
          { 
            plan: strategicPlan,
            directive: directive,
            analysis: analysis,
            ready_for_composition: true
          },
          'director-adapter'
        );
        
        councilBus.publish(nextEvent.topic, nextEvent);
        console.log(`[🎭] Director planning complete → ${nextPhase} phase`);
      }

    } catch (error) {
      console.error('[🎭] Director Adapter planning error:', error);
      
      councilBus.publish('studio.error', {
        taskId,
        phase: 'planning',
        error: error.message,
        agent: 'director-adapter'
      });
    }
  }

  async formulateStrategicPlan(directive, analysis) {
    // This leverages The Director's EXISTING strategic capabilities
    console.log(`[🎭] Formulating strategic plan for: ${directive.name}`);

    const plan = {
      directive_name: directive.name,
      objective: directive.objective,
      strategy: directive.strategy,
      
      // Strategic breakdown based on analysis
      execution_phases: this.createExecutionPhases(directive, analysis),
      task_breakdown: this.createTaskBreakdown(directive, analysis),
      resource_allocation: this.planResourceAllocation(directive, analysis),
      risk_mitigation: this.planRiskMitigation(analysis),
      success_metrics: this.defineSuccessMetrics(directive),
      timeline: this.estimateTimeline(directive, analysis),
      
      // Integration with existing systems
      agent_coordination: this.planAgentCoordination(analysis),
      
      timestamp: new Date().toISOString(),
      plan_version: '1.0'
    };

    console.log(`[🎭] Strategic plan formulated:`, {
      phases: plan.execution_phases.length,
      tasks: plan.task_breakdown.length,
      agents_required: plan.agent_coordination.required_agents.length
    });

    return plan;
  }

  createExecutionPhases(directive, analysis) {
    const phases = [];
    
    // Phase 1: Preparation
    phases.push({
      name: 'preparation',
      description: 'Setup and initial analysis',
      duration_estimate: '10%',
      activities: ['environment_setup', 'baseline_assessment', 'agent_coordination']
    });

    // Phase 2: Core Execution  
    phases.push({
      name: 'core_execution',
      description: directive.strategy === 'audit-then-refactor' ? 'Audit and refactoring' : 'Primary development',
      duration_estimate: '70%',
      activities: this.getCoreActivities(directive.strategy)
    });

    // Phase 3: Integration & Validation
    phases.push({
      name: 'integration_validation',
      description: 'Testing and system integration',
      duration_estimate: '20%', 
      activities: ['testing', 'integration', 'validation', 'cleanup']
    });

    return phases;
  }

  getCoreActivities(strategy) {
    switch (strategy) {
      case 'audit-then-refactor':
        return ['structural_audit', 'pattern_analysis', 'incremental_refactoring', 'consolidation'];
      case 'generate-and-test':
        return ['iterative_development', 'continuous_testing', 'feedback_integration'];
      case 'debugging-spree':
        return ['issue_identification', 'systematic_debugging', 'pattern_correction'];
      default:
        return ['development', 'testing', 'refinement'];
    }
  }

  createTaskBreakdown(directive, analysis) {
    const targetCount = directive.parameters?.targetTaskCount || 10;
    const complexity = analysis?.complexity_assessment || 'medium';
    
    const tasks = [];
    const baseTaskCount = Math.min(targetCount, 20); // Cap for initial breakdown
    
    for (let i = 1; i <= baseTaskCount; i++) {
      tasks.push({
        id: `task_${i}`,
        type: this.determineTaskType(i, baseTaskCount, directive.strategy),
        priority: this.determineTaskPriority(i, baseTaskCount),
        estimated_effort: complexity === 'high' ? 'large' : complexity === 'low' ? 'small' : 'medium',
        dependencies: i > 1 ? [`task_${i-1}`] : []
      });
    }

    return tasks;
  }

  determineTaskType(index, total, strategy) {
    const ratio = index / total;
    
    if (ratio <= 0.3) return 'analysis';
    if (ratio <= 0.7) return strategy === 'debugging-spree' ? 'fix' : 'development';
    return 'integration';
  }

  determineTaskPriority(index, total) {
    if (index <= 2) return 'critical';
    if (index <= total * 0.7) return 'high';
    return 'medium';
  }

  planResourceAllocation(directive, analysis) {
    return {
      primary_agents: analysis?.agent_requirements || ['chatdev'],
      effort_distribution: {
        analysis: '20%',
        development: '60%', 
        testing: '15%',
        integration: '5%'
      },
      estimated_duration: this.estimateDuration(directive, analysis)
    };
  }

  planRiskMitigation(analysis) {
    const risks = analysis?.risk_factors || [];
    return risks.map(risk => ({
      risk,
      mitigation: this.getMitigationStrategy(risk),
      monitoring: this.getMonitoringStrategy(risk)
    }));
  }

  getMitigationStrategy(risk) {
    const strategies = {
      'large_task_volume_may_cause_overwhelm': 'Implement task batching and progress checkpoints',
      'repository_wide_changes_require_careful_coordination': 'Use incremental changes with rollback points',
      'autonomous_execution_needs_monitoring': 'Set up monitoring alerts and manual checkpoints'
    };
    return strategies[risk] || 'Monitor closely and adjust as needed';
  }

  getMonitoringStrategy(risk) {
    return 'Real-time progress tracking with automated alerts on deviations';
  }

  defineSuccessMetrics(directive) {
    return {
      completion_rate: '100% of planned tasks completed',
      quality_metrics: 'Zero critical errors, minimal technical debt',
      performance_impact: 'No degradation in system performance',
      integration_success: 'All modified components properly integrated'
    };
  }

  estimateTimeline(directive, analysis) {
    const taskCount = directive.parameters?.targetTaskCount || 10;
    const complexity = analysis?.complexity_assessment || 'medium';
    
    const baseMinutes = {
      'low': 2,
      'medium': 5,
      'high': 10
    }[complexity];

    return {
      estimated_total_minutes: taskCount * baseMinutes,
      estimated_completion: new Date(Date.now() + taskCount * baseMinutes * 60000).toISOString(),
      confidence: complexity === 'high' ? 'low' : 'medium'
    };
  }

  estimateDuration(directive, analysis) {
    const complexity = analysis?.complexity_assessment || 'medium';
    const taskCount = directive.parameters?.targetTaskCount || 10;
    
    if (complexity === 'high' || taskCount > 50) return 'extended';
    if (complexity === 'low' && taskCount < 20) return 'short';
    return 'medium';
  }

  planAgentCoordination(analysis) {
    const requiredAgents = analysis?.agent_requirements || ['chatdev'];
    
    return {
      required_agents: requiredAgents,
      coordination_strategy: 'serial_with_parallel_opportunities',
      communication_protocol: 'studio_serial_v1',
      handoff_points: this.defineHandoffPoints(requiredAgents)
    };
  }

  defineHandoffPoints(agents) {
    const handoffs = [];
    
    for (let i = 0; i < agents.length - 1; i++) {
      handoffs.push({
        from: agents[i],
        to: agents[i + 1],
        trigger: 'phase_completion',
        data_required: ['phase_results', 'context', 'next_phase_requirements']
      });
    }
    
    return handoffs;
  }

  getStatus() {
    return {
      active: this.active,
      agent: 'director',
      capabilities: ['planning', 'strategy'],
      adapter_version: '1.0'
    };
  }
}

// Export singleton instance
export const directorAdapter = new DirectorAdapter();

console.log('[🎭] Director Adapter module loaded - Ready to enhance strategic planning capabilities');

export default directorAdapter;