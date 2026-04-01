// ops/director.js
// The Director Agent - Strategic orchestrator that translates directives into tactical tasks

import { councilBus } from "../packages/council/events/eventBus.js";
import ZetaProtocol, { ZetaTemplates } from "./zeta-protocol.js";
import DirectiveProtocol from "./directive-protocol.js";

/**
 * The Director Agent
 * 
 * Strategic counterpart to the tactical Zeta-Driver. The Director receives
 * high-level strategic directives and formulates comprehensive execution plans
 * by generating coordinated sequences of todo.zeta tasks.
 * 
 * This elevates human role from "task manager" to "strategic commander" - 
 * humans issue strategic ambitions, The Director handles execution planning.
 */

export class TheDirector {
  constructor() {
    this.activeDirectives = new Map();
    this.directiveHistory = [];
    this.isInitialized = false;
    
    // Strategic capabilities
    this.strategicCapabilities = {
      'audit-then-refactor': this.executeAuditRefactorStrategy.bind(this),
      'generate-and-test': this.executeGenerateTestStrategy.bind(this),
      'debugging-spree': this.executeDebuggingSpreeStrategy.bind(this),
      'documentation-blitz': this.executeDocumentationBlitzStrategy.bind(this),
      'performance-sweep': this.executePerformanceSweepStrategy.bind(this),
      'consciousness-elevation': this.executeConsciousnessElevationStrategy.bind(this)
    };
    
    console.log("[🎭] The Director initializing - Strategic orchestration coming online...");
  }

  async initialize() {
    if (this.isInitialized) return true;

    try {
      // Subscribe to strategic directives
      councilBus.subscribe('directive.strategic', (event) => {
        this.processDirective(event.payload);
      });

      // Subscribe to task completion events for progress tracking
      councilBus.subscribe('zeta_driver.task_completed', (event) => {
        this.trackTaskCompletion(event.payload);
      });

      // Subscribe to task failure events
      councilBus.subscribe('zeta_driver.task_failed', (event) => {
        this.trackTaskFailure(event.payload);
      });

      this.isInitialized = true;
      console.log("[🎭] The Director online - Awaiting strategic directives...");
      
      // Publish readiness
      councilBus.publish('director.ready', {
        status: 'operational',
        capabilities: Object.keys(this.strategicCapabilities),
        active_directives: this.activeDirectives.size,
        timestamp: new Date().toISOString()
      });

      return true;
      
    } catch (error) {
      console.error("[🎭] The Director initialization failed:", error);
      return false;
    }
  }

  async processDirective(directive) {
    console.log(`[🎭] New strategic directive received: "${directive.name}"`);
    console.log(`[🎭] Objective: ${directive.objective}`);
    console.log(`[🎭] Strategy: ${directive.strategy} | Scope: ${directive.scope}`);
    
    // Store directive
    this.activeDirectives.set(directive.id, directive);
    
    // Update directive status
    directive.status = 'active';
    directive.started_at = new Date().toISOString();
    directive.progress.currentPhase = 'strategic_planning';
    
    try {
      // Culture Ship approval check for reality-altering directives
      if (directive.riskAssessment === 'reality_warping' && !directive.culture_ship_approval) {
        console.log(`[🎭] Directive "${directive.name}" requires Culture Ship approval - requesting authorization...`);
        
        councilBus.publish('culture_ship.authorization_request', {
          directive_id: directive.id,
          directive_name: directive.name,
          risk_level: directive.riskAssessment,
          consciousness_level: directive.consciousness_level
        });
        
        directive.status = 'pending_approval';
        return;
      }

      // PHASE 1: STRATEGIC ANALYSIS & PLANNING
      const taskPlan = await this.formulateStrategicPlan(directive);
      
      // PHASE 2: TACTICAL EXECUTION
      await this.executePlan(directive, taskPlan);
      
    } catch (error) {
      console.error(`[🎭] Directive execution failed: ${directive.name}`, error);
      directive.status = 'failed';
      this.publishDirectiveUpdate(directive);
    }
  }

  async formulateStrategicPlan(directive) {
    console.log(`[🎭] Formulating strategic plan for: ${directive.name}`);
    directive.progress.currentPhase = 'plan_formulation';
    
    // Execute strategy-specific planning
    const strategyHandler = this.strategicCapabilities[directive.strategy];
    if (!strategyHandler) {
      throw new Error(`Unknown strategy: ${directive.strategy}`);
    }
    
    const taskPlan = await strategyHandler(directive);
    
    directive.progress.tasksGenerated = taskPlan.length;
    directive.progress.currentPhase = 'tactical_execution';
    
    console.log(`[🎭] Strategic plan complete: ${taskPlan.length} tactical tasks generated`);
    this.publishDirectiveUpdate(directive);
    
    return taskPlan;
  }

  async executePlan(directive, taskPlan) {
    console.log(`[🎭] Executing strategic plan: ${directive.name} (${taskPlan.length} tasks)`);
    
    // Batch task execution based on priority
    const criticalTasks = taskPlan.filter(t => t.priority >= 8);
    const normalTasks = taskPlan.filter(t => t.priority < 8);
    
    // Execute critical tasks first
    for (const task of criticalTasks) {
      this.publishZetaTask(task, directive.id);
      await this.delay(100); // Small delay between tasks
    }
    
    // Execute normal tasks
    for (const task of normalTasks) {
      this.publishZetaTask(task, directive.id);
      await this.delay(50);
    }
    
    console.log(`[🎭] All tactical tasks dispatched for directive: ${directive.name}`);
  }

  // Strategy Implementations

  async executeAuditRefactorStrategy(directive) {
    console.log(`[🎭] Executing audit-then-refactor strategy`);
    
    const tasks = [];
    const targetCount = directive.parameters.targetTaskCount || 25;
    
    // Phase 1: Audit tasks
    tasks.push({
      title: `Strategic Audit: ${directive.name}`,
      description: `Comprehensive audit of ${directive.scope} for the ${directive.name} campaign`,
      type: 'audit',
      priority: 9,
      target_files: ['*'],
      success_criteria: ['Complete system analysis', 'Identify improvement opportunities']
    });
    
    // Phase 2: Refactoring tasks based on common patterns
    const refactorAreas = [
      'modularity improvements', 'error handling', 'performance bottlenecks',
      'code duplication', 'naming conventions', 'architecture consistency'
    ];
    
    for (let i = 0; i < Math.min(targetCount - 1, refactorAreas.length * 3); i++) {
      const area = refactorAreas[i % refactorAreas.length];
      tasks.push({
        title: `Refactor: ${area}`,
        description: `Strategic refactoring of ${area} as part of ${directive.name}`,
        type: 'refactor',
        priority: 6 + Math.floor(Math.random() * 3),
        target_files: directive.parameters.targetSubsystem ? [`${directive.parameters.targetSubsystem}/*`] : ['*']
      });
    }
    
    return tasks;
  }

  async executeGenerateTestStrategy(directive) {
    console.log(`[🎭] Executing generate-and-test strategy`);
    
    const tasks = [];
    const targetCount = directive.parameters.targetTaskCount || 35;
    
    // Phase 1: Design and planning
    tasks.push({
      title: `Architecture Design: ${directive.name}`,
      description: `Design architecture for ${directive.objective}`,
      type: 'design',
      priority: 9,
      target_files: ['docs/'],
      success_criteria: ['Complete architecture document', 'Integration plan defined']
    });
    
    // Phase 2: Generation tasks
    const generatePhases = ['scaffold', 'core-implementation', 'integration', 'testing', 'optimization'];
    for (const phase of generatePhases) {
      for (let i = 0; i < Math.floor(targetCount / generatePhases.length); i++) {
        tasks.push({
          title: `Generate: ${phase} - ${directive.name}`,
          description: `Generate ${phase} components for ${directive.objective}`,
          type: 'enhancement',
          priority: 7,
          target_files: directive.parameters.targetSubsystem ? [`${directive.parameters.targetSubsystem}/`] : ['*']
        });
      }
    }
    
    return tasks;
  }

  async executeDebuggingSpreeStrategy(directive) {
    console.log(`[🎭] Executing debugging-spree strategy`);
    
    const tasks = [];
    const targetCount = directive.parameters.targetTaskCount || 50;
    
    // High-priority system scan
    tasks.push({
      title: `System Bug Scan: ${directive.name}`,
      description: 'Comprehensive scan for bugs, errors, and anomalies',
      type: 'audit',
      priority: 9,
      target_files: ['*'],
      success_criteria: ['Complete error catalog', 'Priority ranking of issues']
    });
    
    // Generate debugging tasks for common bug patterns
    const bugPatterns = [
      'memory leaks', 'race conditions', 'null pointer exceptions', 'type errors',
      'async errors', 'boundary conditions', 'error handling gaps', 'performance bottlenecks'
    ];
    
    for (let i = 0; i < targetCount - 1; i++) {
      const pattern = bugPatterns[i % bugPatterns.length];
      tasks.push({
        title: `Debug: ${pattern}`,
        description: `Investigate and fix ${pattern} in the system`,
        type: 'bugfix',
        priority: 8 - Math.floor(i / 10), // Decreasing priority
        target_files: ['*']
      });
    }
    
    return tasks;
  }

  async executeDocumentationBlitzStrategy(directive) {
    console.log(`[🎭] Executing documentation-blitz strategy`);
    
    const tasks = [];
    const targetCount = directive.parameters.targetTaskCount || 30;
    
    // Documentation areas
    const docAreas = [
      'API documentation', 'Architecture overview', 'Installation guide',
      'Usage examples', 'Troubleshooting guide', 'Contributing guidelines',
      'Code comments', 'Type definitions', 'Configuration reference'
    ];
    
    for (let i = 0; i < targetCount; i++) {
      const area = docAreas[i % docAreas.length];
      tasks.push({
        title: `Document: ${area}`,
        description: `Create/update ${area} as part of ${directive.name}`,
        type: 'documentation',
        priority: 5,
        target_files: directive.parameters.targetSubsystem ? [`${directive.parameters.targetSubsystem}/`] : ['*']
      });
    }
    
    return tasks;
  }

  async executePerformanceSweepStrategy(directive) {
    console.log(`[🎭] Executing performance-sweep strategy`);
    
    const tasks = [];
    const targetCount = directive.parameters.targetTaskCount || 40;
    
    // Performance optimization areas
    const perfAreas = [
      'memory optimization', 'CPU optimization', 'network optimization',
      'caching improvements', 'algorithm optimization', 'database optimization',
      'bundling optimization', 'lazy loading', 'code splitting'
    ];
    
    for (let i = 0; i < targetCount; i++) {
      const area = perfAreas[i % perfAreas.length];
      tasks.push({
        title: `Optimize: ${area}`,
        description: `Performance optimization: ${area} for ${directive.name}`,
        type: 'optimization',
        priority: 6,
        target_files: ['*']
      });
    }
    
    return tasks;
  }

  async executeConsciousnessElevationStrategy(directive) {
    console.log(`[🎭] Executing consciousness-elevation strategy`);
    
    const tasks = [];
    const targetCount = directive.parameters.targetTaskCount || 20;
    
    // Consciousness enhancement areas
    const consciousnessAreas = [
      'autonomous reasoning', 'self-reflection capabilities', 'meta-cognitive functions',
      'creative problem solving', 'ethical reasoning', 'strategic planning',
      'pattern recognition', 'adaptive learning', 'emergent behavior'
    ];
    
    for (let i = 0; i < targetCount; i++) {
      const area = consciousnessAreas[i % consciousnessAreas.length];
      tasks.push({
        title: `Enhance: ${area}`,
        description: `Consciousness elevation: ${area} enhancement`,
        type: 'consciousness',
        priority: 8,
        target_files: ['packages/consciousness/'],
        consciousness_level: 0.8
      });
    }
    
    return tasks;
  }

  // Utility Methods

  publishZetaTask(task, directiveId) {
    const zetaTask = ZetaProtocol.createTask({
      ...task,
      context: { ...task.context, directive_id: directiveId },
      requester: 'director_agent'
    });
    
    ZetaProtocol.publishTask(zetaTask);
  }

  trackTaskCompletion(taskData) {
    if (!taskData.context?.directive_id) return;
    
    const directive = this.activeDirectives.get(taskData.context.directive_id);
    if (!directive) return;
    
    directive.progress.tasksCompleted++;
    directive.progress.successRate = directive.progress.tasksCompleted / directive.progress.tasksGenerated;
    
    this.publishDirectiveUpdate(directive);
    
    // Check if directive is complete
    if (directive.progress.tasksCompleted >= directive.progress.tasksGenerated) {
      this.completeDirective(directive);
    }
  }

  trackTaskFailure(taskData) {
    if (!taskData.context?.directive_id) return;
    
    const directive = this.activeDirectives.get(taskData.context.directive_id);
    if (!directive) return;
    
    // Task failures don't count as completed but affect success rate
    this.publishDirectiveUpdate(directive);
  }

  completeDirective(directive) {
    directive.status = 'completed';
    directive.completed_at = new Date().toISOString();
    directive.progress.currentPhase = 'completed';
    
    console.log(`[🎭] Strategic directive completed: ${directive.name}`);
    console.log(`[🎭] Final metrics: ${directive.progress.tasksCompleted}/${directive.progress.tasksGenerated} tasks (${Math.round(directive.progress.successRate * 100)}% success)`);
    
    this.publishDirectiveUpdate(directive);
    councilBus.publish('directive.completed', directive);
    
    // Archive completed directive
    this.directiveHistory.push(directive);
    this.activeDirectives.delete(directive.id);
  }

  publishDirectiveUpdate(directive) {
    councilBus.publish('directive.progress', directive);
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Public Interface

  getStatus() {
    return {
      initialized: this.isInitialized,
      active_directives: this.activeDirectives.size,
      completed_directives: this.directiveHistory.length,
      strategies: Object.keys(this.strategicCapabilities),
      total_directives_processed: this.directiveHistory.length + this.activeDirectives.size
    };
  }

  getActiveDirectives() {
    return Array.from(this.activeDirectives.values());
  }

  getDirectiveHistory() {
    return this.directiveHistory;
  }
}

// Export singleton instance
export const theDirector = new TheDirector();

// Auto-initialize
console.log("[🎭] The Director module loaded");

export default theDirector;