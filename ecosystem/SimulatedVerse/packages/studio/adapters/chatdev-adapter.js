// packages/studio/adapters/chatdev-adapter.js  
// ChatDev Adapter - Connects existing ChatDev integration to the universal protocol
// LEVERAGES existing ChatDev without REPLACING it

import { councilBus } from '../../council/events/eventBus.js';
import { DEVELOPMENT_PROTOCOL } from '../serial-protocol.js';

class ChatDevAdapter {
  constructor() {
    this.active = false;
    this.activeSessions = new Map();
    console.log('[🧠] ChatDev Adapter initializing - Connecting existing ChatDev to studio protocol');
  }

  start() {
    if (this.active) return;

    // Listen for composition requests via the universal protocol
    councilBus.subscribe('studio.composition', (event) => {
      this.handleCompositionRequest(event);
    });

    this.active = true;
    console.log('[🧠] ChatDev Adapter online - Ready to orchestrate AI-driven development');
    
    // Register capabilities with the protocol
    councilBus.publish('studio.agent.ready', {
      agent: 'chatdev',
      capabilities: ['composition', 'development', 'ai_orchestration'],
      adapter: 'chatdev-adapter',
      timestamp: new Date().toISOString()
    });
  }

  async handleCompositionRequest(event) {
    if (!DEVELOPMENT_PROTOCOL.validateEvent(event)) {
      console.warn('[🧠] ChatDev Adapter received invalid event:', event);
      return;
    }

    const { taskId, directive, analysis, plan } = event.payload;
    console.log(`[🧠] ChatDev Adapter starting composition for task: ${taskId}`);

    try {
      // Use existing ChatDev integration capabilities
      const compositionResult = await this.orchestrateComposition(directive, analysis, plan, taskId);
      
      // Publish result using the universal protocol - next phase is REVIEW
      const nextPhase = DEVELOPMENT_PROTOCOL.getNextPhase('composition');
      if (nextPhase) {
        const nextEvent = DEVELOPMENT_PROTOCOL.createEvent(
          nextPhase,
          taskId,
          { 
            composition: compositionResult,
            directive: directive,
            analysis: analysis,
            plan: plan,
            ready_for_review: true
          },
          'chatdev-adapter'
        );
        
        councilBus.publish(nextEvent.topic, nextEvent);
        console.log(`[🧠] ChatDev composition complete → ${nextPhase} phase`);
      }

    } catch (error) {
      console.error('[🧠] ChatDev Adapter composition error:', error);
      
      councilBus.publish('studio.error', {
        taskId,
        phase: 'composition',
        error: error.message,
        agent: 'chatdev-adapter'
      });
    }
  }

  async orchestrateComposition(directive, analysis, plan, taskId) {
    console.log(`[🧠] Orchestrating AI composition for: ${directive.name}`);

    // Create a comprehensive prompt based on the analysis and plan
    const compositionPrompt = this.createCompositionPrompt(directive, analysis, plan);
    
    // Track this session
    this.activeSessions.set(taskId, {
      directive,
      analysis,
      plan,
      startTime: new Date().toISOString(),
      status: 'composing'
    });

    // Generate the composition using existing ChatDev-style approach
    const composition = await this.generateComposition(compositionPrompt, directive, plan);

    // Update session status
    const session = this.activeSessions.get(taskId);
    if (session) {
      session.status = 'completed';
      session.endTime = new Date().toISOString();
      session.result = composition;
    }

    console.log(`[🧠] Composition orchestrated:`, {
      components: composition.components.length,
      files_modified: composition.files_modified.length,
      strategy: composition.strategy
    });

    return composition;
  }

  createCompositionPrompt(directive, analysis, plan) {
    return {
      context: {
        objective: directive.objective,
        strategy: directive.strategy,
        scope: directive.scope,
        complexity: analysis?.complexity_assessment || 'medium',
        approach: analysis?.recommended_approach || 'standard'
      },
      requirements: {
        execution_phases: plan?.execution_phases || [],
        task_breakdown: plan?.task_breakdown || [],
        success_metrics: plan?.success_metrics || {},
        agent_coordination: plan?.agent_coordination || {}
      },
      constraints: {
        safety_level: directive.parameters?.safetyLevel || 'testing',
        autonomous_authority: directive.parameters?.autonomous_authority || false,
        target_task_count: directive.parameters?.targetTaskCount || 10
      },
      instructions: this.generateInstructions(directive, analysis, plan)
    };
  }

  generateInstructions(directive, analysis, plan) {
    const instructions = [];

    // Strategy-specific instructions
    switch (directive.strategy) {
      case 'audit-then-refactor':
        instructions.push('Perform systematic code analysis and incremental refactoring');
        instructions.push('Prioritize consolidation of duplicate functionality');
        instructions.push('Maintain backwards compatibility during refactoring');
        break;
      
      case 'generate-and-test':
        instructions.push('Implement iterative development with continuous validation');
        instructions.push('Generate comprehensive test coverage for new code');
        instructions.push('Use test-driven development principles');
        break;
        
      case 'debugging-spree':
        instructions.push('Focus on identifying and fixing existing issues');
        // Comprehensive TODO/FIXME to actionable task conversion
        instructions.push('Scan codebase for TODO/FIXME comments and categorize by priority');
        instructions.push('Generate specific implementation tasks for each TODO with context');
        instructions.push('Create task dependencies map for complex TODO clusters');
        instructions.push('Estimate effort and assign appropriate agent for each actionable task');
        instructions.push('Eliminate hardcoded values and magic numbers');
        break;
        
      default:
        instructions.push('Follow standard development workflow with quality gates');
    }

    // Complexity-specific guidance
    const complexity = analysis?.complexity_assessment;
    if (complexity === 'high') {
      instructions.push('Break down complex tasks into smaller, manageable components');
      instructions.push('Implement progressive rollout with checkpoints');
    }

    // Add integration requirements
    instructions.push('Ensure all modifications integrate with existing Council Bus event system');
    instructions.push('Maintain compatibility with current agent ecosystem');

    return instructions;
  }

  async generateComposition(prompt, directive, plan) {
    // This is where we would call the EXISTING ChatDev integration
    // For now, we'll simulate the composition generation process

    const composition = {
      strategy: directive.strategy,
      approach: prompt.context.approach,
      
      // Generated components based on the plan
      components: this.generateComponents(plan, directive),
      
      // Files that would be modified
      files_modified: this.identifyFilesToModify(directive, plan),
      
      // Task breakdown for execution
      execution_tasks: this.generateExecutionTasks(plan, directive),
      
      // Integration points
      integration_points: this.identifyIntegrationPoints(directive),
      
      // Quality gates
      quality_gates: this.defineQualityGates(directive),
      
      // Metadata
      generated_at: new Date().toISOString(),
      composition_id: `comp_${Date.now()}`,
      confidence: this.assessConfidence(directive, plan)
    };

    return composition;
  }

  generateComponents(plan, directive) {
    const components = [];
    
    // Generate components based on execution phases
    if (plan?.execution_phases) {
      for (const phase of plan.execution_phases) {
        for (const activity of phase.activities) {
          components.push({
            name: `${activity}_component`,
            type: this.mapActivityToComponentType(activity),
            phase: phase.name,
            description: `Component handling ${activity.replace(/_/g, ' ')}`,
            dependencies: [],
            estimated_complexity: 'medium'
          });
        }
      }
    }

    return components;
  }

  mapActivityToComponentType(activity) {
    const mapping = {
      'structural_audit': 'analyzer',
      'pattern_analysis': 'analyzer', 
      'incremental_refactoring': 'refactor',
      'consolidation': 'refactor',
      'iterative_development': 'generator',
      'continuous_testing': 'tester',
      'issue_identification': 'analyzer',
      'systematic_debugging': 'fixer'
    };
    
    return mapping[activity] || 'utility';
  }

  identifyFilesToModify(directive, plan) {
    const files = [];
    
    // Based on scope and strategy, identify likely file modifications
    if (directive.scope === 'repository') {
      files.push(
        'packages/studio/integration-enhancement.js',
        'ops/enhanced-orchestration.js',
        'packages/council/enhanced-coordination.js'
      );
    }

    if (directive.strategy === 'audit-then-refactor') {
      files.push(
        'ops/consolidation-processor.js',
        'packages/studio/refactoring-engine.js'
      );
    }

    return files;
  }

  generateExecutionTasks(plan, directive) {
    const tasks = [];
    
    if (plan?.task_breakdown) {
      for (const task of plan.task_breakdown.slice(0, 10)) { // Limit to first 10
        tasks.push({
          id: `exec_${task.id}`,
          type: task.type,
          priority: task.priority,
          description: `Execute ${task.type} task for ${directive.name}`,
          estimated_effort: task.estimated_effort,
          dependencies: task.dependencies,
          agent_assignment: this.suggestAgentForTask(task.type)
        });
      }
    }

    return tasks;
  }

  suggestAgentForTask(taskType) {
    const assignments = {
      'analysis': 'raven',
      'development': 'chatdev',
      'testing': 'testing-chamber',
      'integration': 'zeta-driver',
      'fix': 'enhanced-local-execution'
    };
    
    return assignments[taskType] || 'chatdev';
  }

  identifyIntegrationPoints(directive) {
    return [
      {
        system: 'council_bus',
        integration_type: 'event_publishing',
        required: true
      },
      {
        system: 'pu_queue',
        integration_type: 'task_submission',
        required: true
      },
      {
        system: 'zeta_driver',
        integration_type: 'execution_coordination',
        required: directive.parameters?.autonomous_authority || false
      }
    ];
  }

  defineQualityGates(directive) {
    return [
      {
        gate: 'syntax_validation',
        description: 'All generated code must pass syntax validation',
        required: true
      },
      {
        gate: 'integration_test',
        description: 'Components must integrate without breaking existing functionality',
        required: true
      },
      {
        gate: 'performance_check',
        description: 'No significant performance degradation',
        required: directive.parameters?.safetyLevel !== 'experimental'
      }
    ];
  }

  assessConfidence(directive, plan) {
    let confidence = 0.7; // Base confidence
    
    // Adjust based on complexity
    const taskCount = directive.parameters?.targetTaskCount || 10;
    if (taskCount > 50) confidence -= 0.1;
    if (taskCount < 20) confidence += 0.1;
    
    // Adjust based on strategy familiarity
    if (directive.strategy === 'audit-then-refactor') confidence += 0.1;
    if (directive.strategy === 'debugging-spree') confidence += 0.1;
    
    return Math.min(0.95, Math.max(0.5, confidence));
  }

  getActiveSession(taskId) {
    return this.activeSessions.get(taskId);
  }

  getStatus() {
    return {
      active: this.active,
      agent: 'chatdev',
      capabilities: ['composition', 'development', 'ai_orchestration'],
      active_sessions: this.activeSessions.size,
      adapter_version: '1.0'
    };
  }
}

// Export singleton instance
export const chatdevAdapter = new ChatDevAdapter();

console.log('[🧠] ChatDev Adapter module loaded - Ready to orchestrate AI-driven composition');

export default chatdevAdapter;