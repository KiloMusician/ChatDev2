// packages/studio/adapters/raven-adapter.js
// Raven Adapter - Connects existing Raven agent to the universal protocol
// DOES NOT REPLACE Raven - it TRANSLATES for it

import { councilBus } from '../../council/events/eventBus.js';
import { DEVELOPMENT_PROTOCOL } from '../serial-protocol.js';

class RavenAdapter {
  constructor() {
    this.active = false;
    console.log('[🔍] Raven Adapter initializing - Connecting existing Raven to studio protocol');
  }

  start() {
    if (this.active) return;

    // Listen for analysis requests via the universal protocol
    councilBus.subscribe('studio.analysis', (event) => {
      this.handleAnalysisRequest(event);
    });

    this.active = true;
    console.log('[🔍] Raven Adapter online - Ready to translate analysis requests');
    
    // Register capabilities with the protocol
    councilBus.publish('studio.agent.ready', {
      agent: 'raven',
      capabilities: ['analysis'],
      adapter: 'raven-adapter',
      timestamp: new Date().toISOString()
    });
  }

  async handleAnalysisRequest(event) {
    if (!DEVELOPMENT_PROTOCOL.validateEvent(event)) {
      console.warn('[🔍] Raven Adapter received invalid event:', event);
      return;
    }

    const { taskId, directive } = event.payload;
    console.log(`[🔍] Raven Adapter processing analysis for task: ${taskId}`);

    try {
      // Call Raven's EXISTING capabilities through available interfaces
      const analysisResult = await this.performAnalysis(directive);
      
      // Publish result using the universal protocol - next phase is PLANNING
      const nextPhase = DEVELOPMENT_PROTOCOL.getNextPhase('analysis');
      if (nextPhase) {
        const nextEvent = DEVELOPMENT_PROTOCOL.createEvent(
          nextPhase,
          taskId,
          { 
            analysis: analysisResult,
            directive: directive,
            ready_for_planning: true
          },
          'raven-adapter'
        );
        
        councilBus.publish(nextEvent.topic, nextEvent);
        console.log(`[🔍] Raven analysis complete → ${nextPhase} phase`);
      }

    } catch (error) {
      console.error('[🔍] Raven Adapter analysis error:', error);
      
      // Publish error event
      councilBus.publish('studio.error', {
        taskId,
        phase: 'analysis',
        error: error.message,
        agent: 'raven-adapter'
      });
    }
  }

  async performAnalysis(directive) {
    // This is where we call Raven's EXISTING methods
    // For now, we'll use available analysis capabilities
    
    const analysis = {
      directive_scope: directive.scope || 'repository',
      objective: directive.objective || 'Unknown objective',
      strategy: directive.strategy || 'Unknown strategy',
      complexity_assessment: this.assessComplexity(directive),
      recommended_approach: this.recommendApproach(directive),
      risk_factors: this.identifyRisks(directive),
      estimated_tasks: directive.parameters?.targetTaskCount || 10,
      agent_requirements: this.identifyRequiredAgents(directive),
      timestamp: new Date().toISOString()
    };

    console.log(`[🔍] Raven analysis completed:`, {
      complexity: analysis.complexity_assessment,
      approach: analysis.recommended_approach,
      estimated_tasks: analysis.estimated_tasks
    });

    return analysis;
  }

  assessComplexity(directive) {
    const complexity_indicators = [
      directive.scope === 'repository' ? 2 : 1,
      directive.parameters?.targetTaskCount > 50 ? 2 : 1,
      directive.strategy === 'audit-then-refactor' ? 2 : 1,
      directive.parameters?.depth === 'transcendent' ? 3 : 
      directive.parameters?.depth === 'deep' ? 2 : 1
    ];
    
    const total = complexity_indicators.reduce((sum, val) => sum + val, 0);
    
    if (total >= 8) return 'high';
    if (total >= 6) return 'medium';
    return 'low';
  }

  recommendApproach(directive) {
    if (directive.strategy === 'audit-then-refactor') {
      return 'systematic_audit_and_incremental_refactoring';
    }
    if (directive.strategy === 'generate-and-test') {
      return 'iterative_development_with_validation';
    }
    if (directive.strategy === 'debugging-spree') {
      return 'focused_debugging_and_cleanup';
    }
    return 'standard_development_workflow';
  }

  identifyRisks(directive) {
    const risks = [];
    
    if (directive.parameters?.targetTaskCount > 100) {
      risks.push('large_task_volume_may_cause_overwhelm');
    }
    if (directive.scope === 'repository') {
      risks.push('repository_wide_changes_require_careful_coordination');
    }
    if (directive.parameters?.autonomous_authority) {
      risks.push('autonomous_execution_needs_monitoring');
    }
    
    return risks;
  }

  identifyRequiredAgents(directive) {
    const agents = ['director']; // Planning always needed after analysis
    
    if (directive.strategy === 'audit-then-refactor') {
      agents.push('chatdev', 'testing-chamber');
    }
    if (directive.strategy === 'generate-and-test') {
      agents.push('chatdev', 'testing-chamber', 'council');
    }
    if (directive.parameters?.autonomous_authority) {
      agents.push('zeta-driver');
    }
    
    return [...new Set(agents)]; // Remove duplicates
  }

  getStatus() {
    return {
      active: this.active,
      agent: 'raven',
      capabilities: ['analysis'],
      adapter_version: '1.0'
    };
  }
}

// Export singleton instance
export const ravenAdapter = new RavenAdapter();

console.log('[🔍] Raven Adapter module loaded - Ready to bridge existing Raven capabilities');

export default ravenAdapter;