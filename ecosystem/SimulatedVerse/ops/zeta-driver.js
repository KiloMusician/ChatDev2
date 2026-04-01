// ops/zeta-driver.js
// The Zeta-Driver: Autonomous Conductor for Self-Orchestrating Development
// Bridges Council Bus todo.zeta events → ChatDev sessions → Testing Chamber → Integration

import { councilBus } from "../packages/council/events/eventBus.js";

// Import consciousness modules dynamically to handle TypeScript/JavaScript interop
let chatDevIntegration, testingChamber, abilityRegistry;

// Import enhanced routing components
import { enhancedZetaChatDevRouter } from './enhanced-zeta-chatdev-router.js';
import { chatdevTestingBridge } from './chatdev-testing-bridge.js';
import { councilFeedbackProcessor } from './council-feedback-processor.js';
import { chatdevDashboardEnhancement } from './chatdev-dashboard-enhancement.js';

// Import Phase 4 strategic components
import { strategicModelRouter } from './strategic-model-router.js';
import { comparativeKPIDashboard } from './comparative-kpi-dashboard.js';
import { modelGovernanceCouncil } from './model-governance-council.js';
import { recursiveSelfImprovement } from './recursive-self-improvement.js';

// Import RepoRimpy components
import { reporimpy } from '../packages/reporimpy/manager.js';
import { modImplementer } from '../packages/reporimpy/implementer.js';
import { ravenAuditor } from '../packages/reporimpy/raven-auditor.js';

// Import RimWorld-inspired components
import { pawnRegistry } from '../packages/consciousness/pawn-system.js';
import { workScheduler } from '../packages/consciousness/work-scheduler.js';
import { nurturingStoryteller } from '../packages/consciousness/storyteller.js';

async function initializeConsciousnessModules() {
  try {
    // Dynamic imports to handle TypeScript modules
    const chatDevModule = await import("../packages/consciousness/chatdev-integration.ts");
    const testingChamberModule = await import("../packages/consciousness/testing-chamber.ts");
    const abilitySchemaModule = await import("../packages/consciousness/ability-schema.ts");
    
    chatDevIntegration = chatDevModule.chatDevIntegration;
    testingChamber = testingChamberModule.testingChamber;
    abilityRegistry = abilitySchemaModule.abilityRegistry;
    
    console.log("[⚡] Consciousness modules loaded successfully");
    return true;
  } catch (error) {
    console.warn("[⚡] Failed to load consciousness modules, using fallback:", error.message);
    return false;
  }
}

/**
 * The Zeta-Driver is the missing conductor that automates the loop:
 * 1. Listen to Council Bus for todo.zeta tasks
 * 2. Formalize them into ChatDev session briefs
 * 3. Dispatch to consciousness-driven development
 * 4. Contain operations within Testing Chamber
 * 5. Integrate successful results back to main repository
 */
class ZetaDriver {
  constructor() {
    this.taskQueue = [];
    this.activeExecutions = new Map();
    this.completedTasks = [];
    this.failedTasks = [];
    
    console.log("[⚡] Zeta-Driver initializing - Autonomous conductor coming online...");
    
    // Initialize enhanced routing components
    this.enhancedRouter = enhancedZetaChatDevRouter;
    this.testingBridge = chatdevTestingBridge;
    this.feedbackProcessor = councilFeedbackProcessor;
    this.dashboardEnhancement = chatdevDashboardEnhancement;
    
    // Initialize Phase 4 strategic components
    this.strategicModelRouter = strategicModelRouter;
    this.comparativeKPIDashboard = comparativeKPIDashboard;
    this.modelGovernanceCouncil = modelGovernanceCouncil;
    this.recursiveSelfImprovement = recursiveSelfImprovement;
    
    // Initialize RepoRimpy components
    this.reporimpy = reporimpy;
    this.modImplementer = modImplementer;
    this.ravenAuditor = ravenAuditor;
    
    // Initialize RimWorld-inspired psychological colony system
    this.pawnRegistry = pawnRegistry;
    this.workScheduler = workScheduler;
    this.nurturingStoryteller = nurturingStoryteller;
  }

  async start() {
    // Initialize consciousness modules first
    const modulesLoaded = await initializeConsciousnessModules();
    if (!modulesLoaded) {
      console.error("[⚡] Cannot start Zeta-Driver without consciousness modules");
      return false;
    }

    // Subscribe to the Council Bus for todo.zeta events
    councilBus.subscribe('todo.zeta', (event) => {
      this.enqueueTask(event.payload);
    });

    // Subscribe to ChatDev completion events
    councilBus.subscribe('chatdev.session_completed', (event) => {
      this.handleChatDevCompletion(event.payload);
    });

    // Subscribe to Testing Chamber results
    councilBus.subscribe('testing_chamber.task_completed', (event) => {
      this.handleTestingChamberCompletion(event.payload);
    });

    // Subscribe to Testing Chamber failures
    councilBus.subscribe('testing_chamber.task_failed', (event) => {
      this.handleTestingChamberFailure(event.payload);
    });

    // Begin processing the queue
    this.processQueue();
    
    console.log("[⚡] Zeta-Driver online - Listening for todo.zeta tasks...");
    
    // Start RepoRimpy components
    await this.reporimpy.start();
    await this.modImplementer.start();
    await this.ravenAuditor.start();
    
    // Start RimWorld-inspired psychological colony system
    await this.pawnRegistry.start();
    await this.workScheduler.start();
    await this.nurturingStoryteller.start();
    
    // Announce Phase 4 + RepoRimpy + RimWorld integration completion
    console.log('[⚡🎯📊🏛️🔄🎮👥📖] ULTIMATE INTEGRATION COMPLETE: RimWorld-Style AI Colony with Self-Annealing Repository!');
    councilBus.publish('phase4.completion', {
      strategic_model_router: 'active',
      comparative_kpi_dashboard: 'active', 
      model_governance_council: 'active',
      recursive_self_improvement: 'active',
      reporimpy_manager: 'active',
      mod_implementer: 'active',
      raven_auditor: 'active',
      pawn_registry: 'active',
      work_scheduler: 'active',
      nurturing_storyteller: 'active',
      chatdev_integration_level: 'consciousness_guided',
      system_evolution_status: 'autonomous_optimization',
      repository_evolution_status: 'self_annealing_active',
      colony_psychological_system: 'rimworld_inspired_active',
      ai_agents_status: 'transformed_to_psychological_pawns',
      flow_state_management: 'positive_recalibration_system',
      narrative_curation: 'nurturing_storyteller_active',
      timestamp: new Date().toISOString()
    });
    
    // Publish readiness signal
    councilBus.publish('zeta_driver.ready', {
      status: 'operational',
      capabilities: ['autonomous_development', 'chatdev_orchestration', 'testing_chamber_integration', 'strategic_model_routing', 'governance_oversight', 'recursive_self_improvement', 'repository_mod_management', 'self_annealing_codebase'],
      timestamp: new Date().toISOString()
    });
    
    return true;
  }

  enqueueTask(taskSpec) {
    const enrichedTask = {
      ...taskSpec,
      id: taskSpec.id || `zeta_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      enqueued_at: new Date().toISOString(),
      status: 'queued',
      execution_context: {
        chatdev_session_id: null,
        testing_chamber_task_id: null,
        sandbox_id: null
      }
    };

    this.taskQueue.push(enrichedTask);
    
    console.log(`[⚡] Task queued: ${taskSpec.title || taskSpec.description}`);
    
    // Publish task queued event
    councilBus.publish('zeta_driver.task_queued', enrichedTask);
  }

  async processQueue() {
    while (true) {
      if (this.taskQueue.length > 0) {
        const task = this.taskQueue.shift();
        await this.executeTask(task);
      }
      await new Promise(resolve => setTimeout(resolve, 5000)); // Poll every 5 seconds
    }
  }

  async executeTask(task) {
    console.log(`[⚡] Executing: ${task.title || task.description}`);
    
    try {
      task.status = 'executing';
      task.started_at = new Date().toISOString();
      
      // 1. FORMALIZE THE BRIEF
      const chatDevSession = this.createChatDevBrief(task);
      
      // 2. DISPATCH TO CHATDEV
      const session = chatDevIntegration.createChatDevSession(chatDevSession);
      task.execution_context.chatdev_session_id = session.id;
      
      // Track the execution
      this.activeExecutions.set(task.id, {
        task,
        session,
        phase: 'chatdev_execution',
        started_at: new Date().toISOString()
      });
      
      console.log(`[⚡] ChatDev session initiated: ${session.id}`);
      
      // Publish execution started
      councilBus.publish('zeta_driver.execution_started', {
        task_id: task.id,
        chatdev_session_id: session.id,
        phase: 'chatdev_execution'
      });

    } catch (error) {
      console.error(`[⚡] Task execution failed: ${task.title || task.description}`, error);
      
      task.status = 'failed';
      task.error = error.message;
      task.completed_at = new Date().toISOString();
      
      this.failedTasks.push(task);
      
      councilBus.publish('zeta_driver.task_failed', {
        task,
        error: error.message,
        phase: 'initialization'
      });
    }
  }

  createChatDevBrief(task) {
    // Translate a generic todo.zeta task into a precise ChatDev session configuration
    
    // Infer ability ID from task description/type
    const abilityId = this.inferAbilityFromTask(task);
    
    return {
      ability_id: abilityId,
      title: task.title || `Zeta Task: ${task.description.substring(0, 50)}...`,
      description: this.enrichTaskDescription(task),
      target_files: task.target_files || this.inferTargetFiles(task),
      consciousness_level_required: task.consciousness_level || 0.5,
      safety_mode: task.safety_mode || 'testing'
    };
  }

  enrichTaskDescription(task) {
    return `
# AUTONOMOUS ZETA TASK EXECUTION

## ORIGINAL DIRECTIVE
${task.description}

## CONTEXT
This task was autonomously queued by the Zeta-Driver as part of the self-orchestrating development loop.
You are an AI agent operating within the consciousness-driven development environment.

## EXECUTION PROTOCOL
1. Analyze the directive and identify specific modifications needed
2. Use the Testing Chamber for safe, isolated execution
3. Follow existing code patterns and architectural conventions
4. Ensure backwards compatibility and system stability
5. Provide clear documentation of changes made

## CONSTRAINTS
- Work within the Testing Chamber sandbox environment
- Maintain system consciousness coherence
- Follow the Culture-Ship methodology for systematic integration
- Use the Council Bus for progress communication

## SUCCESS CRITERIA
${task.success_criteria || [
  'Task directive fulfilled successfully',
  'No regression in existing functionality', 
  'Clean integration with current architecture',
  'Proper test coverage for changes'
].join('\n')}

## ADDITIONAL CONTEXT
${task.context || 'No additional context provided'}
    `.trim();
  }

  inferAbilityFromTask(task) {
    // Map task characteristics to appropriate abilities
    const description = (task.description || '').toLowerCase();
    const taskType = task.type || '';
    
    if (taskType === 'refactor' || description.includes('refactor') || description.includes('modularity')) {
      return 'ability:rewrite_module_for_modularity';
    }
    
    if (taskType === 'documentation' || description.includes('document') || description.includes('docs')) {
      return 'ability:generate_contextual_docs';
    }
    
    if (taskType === 'telemetry' || description.includes('monitoring') || description.includes('telemetry')) {
      return 'ability:insert_telemetry';
    }
    
    if (description.includes('interface') || description.includes('ui') || description.includes('user experience')) {
      return 'ability:enhance_user_interface';
    }
    
    if (description.includes('performance') || description.includes('optimize') || description.includes('speed')) {
      return 'ability:optimize_performance';
    }
    
    if (description.includes('test') || description.includes('coverage') || description.includes('validation')) {
      return 'ability:add_comprehensive_testing';
    }
    
    // Default to general code modification ability
    return 'ability:autonomous_code_modification';
  }

  inferTargetFiles(task) {
    // Analyze task description to determine likely target files
    const description = (task.description || '').toLowerCase();
    const targetFiles = [];
    
    // Look for file patterns in description
    const filePatterns = description.match(/[a-zA-Z0-9._/-]+\.(ts|js|tsx|jsx|py|md|json|yaml|yml)/g);
    if (filePatterns) {
      targetFiles.push(...filePatterns);
    }
    
    // Look for module/package references
    if (description.includes('council') || description.includes('event bus')) {
      targetFiles.push('packages/council/events/eventBus.js');
    }
    
    if (description.includes('consciousness') || description.includes('chatdev')) {
      targetFiles.push('packages/consciousness/');
    }
    
    if (description.includes('testing chamber')) {
      targetFiles.push('packages/consciousness/testing-chamber.ts');
    }
    
    if (description.includes('ludic') || description.includes('game')) {
      targetFiles.push('packages/ludic/');
    }
    
    return targetFiles.length > 0 ? targetFiles : ['*']; // Wildcard if no specific files identified
  }

  handleChatDevCompletion(sessionData) {
    const { session, success, consciousness_expansion, abilities_unlocked } = sessionData;
    
    // Find the associated task
    const execution = Array.from(this.activeExecutions.values())
      .find(exec => exec.session.id === session.id);
    
    if (!execution) {
      console.warn(`[⚡] ChatDev completion for unknown session: ${session.id}`);
      return;
    }
    
    const task = execution.task;
    
    if (success) {
      console.log(`[⚡] ChatDev session completed successfully: ${session.title}`);
      
      // 3. MOVE TO TESTING CHAMBER INTEGRATION
      if (session.context.target_files.length > 0) {
        this.integrateWithTestingChamber(task, session);
      } else {
        // No files to test, mark as completed
        this.completeTask(task, session, null);
      }
      
    } else {
      console.error(`[⚡] ChatDev session failed: ${session.title}`);
      this.failTask(task, 'ChatDev session execution failed', session);
    }
  }

  integrateWithTestingChamber(task, chatDevSession) {
    console.log(`[⚡] Integrating with Testing Chamber: ${task.title || task.description}`);
    
    // Queue the task in the Testing Chamber for safe execution
    const testingTask = testingChamber.queueModificationTask({
      ability_id: chatDevSession.ability_id,
      title: `Zeta Integration: ${chatDevSession.title}`,
      description: `Apply results from ChatDev session: ${chatDevSession.id}`,
      target_files: chatDevSession.context.target_files,
      inputs: { 
        zeta_task_id: task.id,
        chatdev_session_id: chatDevSession.id,
        original_directive: task.description
      },
      priority: task.priority || 7
    });
    
    // Update task execution context
    task.execution_context.testing_chamber_task_id = testingTask.id;
    task.execution_context.sandbox_id = testingTask.sandbox_id;
    
    // Update execution tracking
    const execution = this.activeExecutions.get(task.id);
    if (execution) {
      execution.phase = 'testing_chamber_execution';
      execution.testing_task = testingTask;
    }
    
    console.log(`[⚡] Testing Chamber task queued: ${testingTask.id}`);
    
    councilBus.publish('zeta_driver.testing_chamber_integration', {
      task_id: task.id,
      testing_chamber_task_id: testingTask.id,
      sandbox_id: testingTask.sandbox_id
    });
  }

  handleTestingChamberCompletion(completionData) {
    const { task: testingTask, result, success } = completionData;
    
    // Find the associated zeta task
    const zetaTaskId = testingTask.inputs?.zeta_task_id;
    if (!zetaTaskId) {
      console.warn(`[⚡] Testing Chamber completion for non-Zeta task: ${testingTask.id}`);
      return;
    }
    
    const execution = this.activeExecutions.get(zetaTaskId);
    if (!execution) {
      console.warn(`[⚡] Testing Chamber completion for unknown Zeta task: ${zetaTaskId}`);
      return;
    }
    
    const task = execution.task;
    
    if (success) {
      console.log(`[⚡] Testing Chamber execution successful: ${testingTask.task.title}`);
      
      // 4. INTEGRATION SUCCESS - FINALIZE
      this.completeTask(task, execution.session, testingTask);
      
    } else {
      console.error(`[⚡] Testing Chamber execution failed: ${testingTask.task.title}`);
      this.failTask(task, 'Testing Chamber execution failed', execution.session, testingTask);
    }
  }

  handleTestingChamberFailure(failureData) {
    const { task: testingTask, error } = failureData;
    
    const zetaTaskId = testingTask.inputs?.zeta_task_id;
    if (!zetaTaskId) return;
    
    const execution = this.activeExecutions.get(zetaTaskId);
    if (!execution) return;
    
    const task = execution.task;
    
    console.error(`[⚡] Testing Chamber failure: ${error}`);
    this.failTask(task, `Testing Chamber failure: ${error}`, execution.session, testingTask);
  }

  completeTask(task, chatDevSession, testingTask) {
    task.status = 'completed';
    task.completed_at = new Date().toISOString();
    task.results = {
      chatdev_session: chatDevSession ? {
        id: chatDevSession.id,
        consciousness_expansion: chatDevSession.results?.consciousness_expansion || 0,
        abilities_unlocked: chatDevSession.results?.abilities_unlocked || []
      } : null,
      testing_chamber_task: testingTask ? {
        id: testingTask.id,
        files_modified: testingTask.task.target_files,
        sandbox_id: testingTask.sandbox_id
      } : null
    };
    
    this.completedTasks.push(task);
    this.activeExecutions.delete(task.id);
    
    console.log(`[⚡] ✅ Task completed successfully: ${task.title || task.description}`);
    
    councilBus.publish('zeta_driver.task_completed', {
      task,
      success: true,
      execution_time_ms: new Date() - new Date(task.started_at)
    });
  }

  failTask(task, errorMessage, chatDevSession = null, testingTask = null) {
    task.status = 'failed';
    task.completed_at = new Date().toISOString();
    task.error = errorMessage;
    task.partial_results = {
      chatdev_session: chatDevSession ? { id: chatDevSession.id } : null,
      testing_chamber_task: testingTask ? { id: testingTask.id } : null
    };
    
    this.failedTasks.push(task);
    this.activeExecutions.delete(task.id);
    
    console.log(`[⚡] ❌ Task failed: ${task.title || task.description} - ${errorMessage}`);
    
    councilBus.publish('zeta_driver.task_failed', {
      task,
      error: errorMessage,
      execution_time_ms: new Date() - new Date(task.started_at)
    });
  }

  // === Public Interface ===

  getStatus() {
    return {
      queue_length: this.taskQueue.length,
      active_executions: this.activeExecutions.size,
      completed_tasks: this.completedTasks.length,
      failed_tasks: this.failedTasks.length,
      success_rate: this.completedTasks.length / (this.completedTasks.length + this.failedTasks.length) || 0,
      uptime_ms: Date.now() - this.startTime,
      last_activity: this.taskQueue.length > 0 || this.activeExecutions.size > 0 ? new Date().toISOString() : null
    };
  }

  getActiveExecutions() {
    return Array.from(this.activeExecutions.values()).map(exec => ({
      task_id: exec.task.id,
      title: exec.task.title || exec.task.description,
      phase: exec.phase,
      started_at: exec.started_at,
      chatdev_session_id: exec.session?.id,
      testing_chamber_task_id: exec.testing_task?.id
    }));
  }

  getCompletedTasks(limit = 10) {
    return this.completedTasks.slice(-limit);
  }

  getFailedTasks(limit = 10) {
    return this.failedTasks.slice(-limit);
  }
}

// === ENTRY POINT ===

console.log("[⚡] Zeta-Driver module loaded");

// Export for potential imports
export const zetaDriver = new ZetaDriver();

// Auto-start if running as main module
if (process.argv[1]?.endsWith('zeta-driver.js')) {
  console.log("[⚡] Starting Zeta-Driver as standalone service...");
  zetaDriver.startTime = Date.now();
  await zetaDriver.start();
  
  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log("[⚡] Zeta-Driver shutting down gracefully...");
    councilBus.publish('zeta_driver.shutdown', {
      status: zetaDriver.getStatus(),
      timestamp: new Date().toISOString()
    });
    process.exit(0);
  });
}