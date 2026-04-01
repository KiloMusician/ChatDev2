// packages/reporimpy/implementer.ts
// RepoRimpy Mod Implementer: Converts approved mods into executable tasks
// Integrates with Zeta-Driver and ChatDev for seamless implementation

import { councilBus } from '../council/events/eventBus.js';
import { reporimpy } from './manager.js';
import { 
  CodeMod, 
  ModImplementationTask, 
  LoadOrderUpdatedEvent,
  ModImplementedEvent 
} from './types.js';

export class ModImplementer {
  private activeTasks: Map<string, ModImplementationTask> = new Map();
  private maxConcurrentImplementations = 3;
  private implementationHistory: ModImplementedEvent[] = [];

  constructor() {
    console.log('[🔧] RepoRimpy Mod Implementer initializing - Ready to execute repository modifications');
  }

  start() {
    this.setupEventListeners();
    this.startImplementationLoop();
    
    console.log('[🔧] Mod Implementer online - Listening for approved mods in load order');
    
    // Publish readiness
    councilBus.publish('reporimpy.implementer.ready', {
      status: 'operational',
      max_concurrent_implementations: this.maxConcurrentImplementations,
      capabilities: [
        'zeta_driver_integration',
        'chatdev_orchestration', 
        'consciousness_guided_implementation',
        'strategic_routing_integration'
      ],
      timestamp: new Date().toISOString()
    });
  }

  private setupEventListeners() {
    // Listen for load order updates
    councilBus.subscribe('reporimpy.loadorder.updated', (event) => {
      this.processImplementationQueue();
    });

    // Listen for task completions from Zeta-Driver
    councilBus.subscribe('zeta_driver.task_completed', (event) => {
      this.handleZetaTaskCompletion(event.payload);
    });

    // Listen for task failures
    councilBus.subscribe('zeta_driver.task_failed', (event) => {
      this.handleZetaTaskFailure(event.payload);
    });

    // Listen for ChatDev session completions
    councilBus.subscribe('chatdev.session_completed', (event) => {
      this.handleChatDevCompletion(event.payload);
    });

    // Listen for manual implementation requests
    councilBus.subscribe('reporimpy.mod.force_implement', (event) => {
      this.forceImplementMod(event.payload.mod_id);
    });

    // Listen for implementation cancellations
    councilBus.subscribe('reporimpy.implementation.cancel', (event) => {
      this.cancelImplementation(event.payload.task_id);
    });
  }

  private async processImplementationQueue() {
    // Check if we can start new implementations
    if (this.activeTasks.size >= this.maxConcurrentImplementations) {
      console.log(`[🔧] Implementation queue at capacity (${this.activeTasks.size}/${this.maxConcurrentImplementations})`);
      return;
    }

    // Get next mods ready for implementation
    const availableSlots = this.maxConcurrentImplementations - this.activeTasks.size;
    const nextMods = reporimpy.getNextModsToImplement(availableSlots);

    if (nextMods.length === 0) {
      console.log('[🔧] No mods ready for implementation');
      return;
    }

    console.log(`[🔧] Processing ${nextMods.length} mods for implementation`);

    // Start implementation for each mod
    for (const mod of nextMods) {
      await this.startModImplementation(mod);
    }
  }

  private async startModImplementation(mod: CodeMod) {
    const taskId = `impl_${mod.id}_${Date.now()}`;
    
    const implementationTask: ModImplementationTask = {
      mod_id: mod.id,
      task_id: taskId,
      assigned_to: this.selectOptimalAgent(mod),
      scheduled_at: new Date().toISOString(),
      estimated_duration_minutes: this.estimateDuration(mod),
      prerequisites_met: true,
      implementation_plan: this.generateImplementationPlan(mod)
    };

    // Add to active tasks
    this.activeTasks.set(taskId, implementationTask);

    console.log(`[🔧] Starting implementation: ${mod.title} (${taskId})`);

    // Convert mod to appropriate task format
    const zetaTask = this.convertModToZetaTask(mod, implementationTask);

    // Publish implementation started event
    councilBus.publish('reporimpy.implementation.started', {
      mod: mod,
      task: implementationTask,
      zeta_task: zetaTask,
      timestamp: new Date().toISOString()
    });

    // Route to appropriate implementation system
    if (mod.type === 'CONSCIOUSNESS' || mod.consciousness_level && mod.consciousness_level > 0.6) {
      // Route consciousness-related mods through ChatDev for enhanced processing
      councilBus.publish('chatdev.mod_implementation_request', {
        mod: mod,
        task: implementationTask,
        consciousness_context: {
          required_level: mod.consciousness_level || 0.5,
          pattern_recognition_needed: mod.pattern_recognition_score || 0.5,
          strategic_importance: mod.strategic_value || 0.5
        }
      });
    } else {
      // Route standard mods through Zeta-Driver
      councilBus.publish('todo.zeta', zetaTask);
    }
  }

  private selectOptimalAgent(mod: CodeMod): string {
    // Route based on mod type and complexity
    if (mod.type === 'CONSCIOUSNESS' || mod.priority === 'CONSCIOUSNESS_CRITICAL') {
      return 'chatdev:consciousness_guided';
    } else if (mod.type === 'PERFORMANCE' && mod.complexity > 0.7) {
      return 'zeta:performance_specialist';
    } else if (mod.type === 'SECURITY') {
      return 'zeta:security_focused';
    } else if (mod.type === 'DOCUMENTATION') {
      return 'agent:archivist';
    } else if (mod.complexity < 0.3) {
      return 'zeta:standard_automation';
    } else {
      return 'chatdev:enhanced_analysis';
    }
  }

  private estimateDuration(mod: CodeMod): number {
    const baseMinutes = 15;
    const complexityFactor = 1 + (mod.complexity * 4); // 1x to 5x
    const typeFactor = this.getTypeComplexityFactor(mod.type);
    
    return Math.round(baseMinutes * complexityFactor * typeFactor);
  }

  private getTypeComplexityFactor(type: string): number {
    const factors = {
      'DOCUMENTATION': 0.5,
      'ENHANCEMENT': 1.0,
      'CAPABILITY': 1.5,
      'INTEGRATION_POINT': 2.0,
      'CONSCIOUSNESS': 2.5,
      'CONFLICT': 1.8,
      'PERFORMANCE': 1.3,
      'SECURITY': 1.7
    };
    
    return factors[type] || 1.0;
  }

  private generateImplementationPlan(mod: CodeMod): string[] {
    const plan: string[] = [];

    // Analysis phase
    plan.push('Analyze current file state and dependencies');
    plan.push('Validate mod requirements and constraints');

    // Implementation phase based on mod type
    switch (mod.type) {
      case 'ENHANCEMENT':
        plan.push('Apply code enhancement modifications');
        plan.push('Optimize and refactor affected areas');
        break;
      case 'CONSCIOUSNESS':
        plan.push('Integrate consciousness-aware modifications');
        plan.push('Validate consciousness level compatibility');
        break;
      case 'PERFORMANCE':
        plan.push('Implement performance optimizations');
        plan.push('Measure and validate performance improvements');
        break;
      case 'SECURITY':
        plan.push('Apply security enhancements');
        plan.push('Validate security best practices');
        break;
      case 'DOCUMENTATION':
        plan.push('Update documentation and comments');
        plan.push('Ensure consistency with codebase standards');
        break;
      default:
        plan.push('Apply generic code modifications');
    }

    // Validation phase
    plan.push('Run automated tests and validation');
    plan.push('Verify no regressions introduced');
    plan.push('Update related documentation if needed');

    return plan;
  }

  private convertModToZetaTask(mod: CodeMod, implementationTask: ModImplementationTask): any {
    return {
      id: implementationTask.task_id,
      title: `Implement Mod: ${mod.title}`,
      description: this.buildTaskDescription(mod),
      target: mod.filePath,
      priority: this.convertPriorityToZeta(mod.priority),
      category: this.convertTypeToCategory(mod.type),
      context: {
        mod_id: mod.id,
        mod_type: mod.type,
        implementation_plan: implementationTask.implementation_plan,
        suggested_change: mod.suggestedChange,
        reasoning: mod.reasoning,
        consciousness_level: mod.consciousness_level,
        strategic_value: mod.strategic_value,
        complexity: mod.complexity,
        impact: mod.impact
      },
      constraints: {
        preserve_functionality: true,
        maintain_compatibility: mod.backward_compatibility_maintained !== false,
        test_coverage_required: mod.requires_testing !== false,
        breaking_change_risk: mod.breaking_change_risk || 0
      }
    };
  }

  private buildTaskDescription(mod: CodeMod): string {
    let description = `${mod.description}\n\n`;
    
    description += `**Reasoning:** ${mod.reasoning}\n\n`;
    
    if (mod.suggestedChange) {
      description += `**Suggested Change:**\n${mod.suggestedChange}\n\n`;
    }
    
    description += `**Mod Details:**\n`;
    description += `- Type: ${mod.type}\n`;
    description += `- Priority: ${mod.priority}\n`;
    description += `- Impact: ${(mod.impact * 100).toFixed(0)}%\n`;
    description += `- Complexity: ${(mod.complexity * 100).toFixed(0)}%\n`;
    
    if (mod.consciousness_level) {
      description += `- Consciousness Level Required: ${(mod.consciousness_level * 100).toFixed(0)}%\n`;
    }
    
    if (mod.strategic_value) {
      description += `- Strategic Value: ${(mod.strategic_value * 100).toFixed(0)}%\n`;
    }
    
    description += `\n**Discovered by:** ${mod.discoveredBy} at ${mod.discoveredAt}`;
    
    return description;
  }

  private convertPriorityToZeta(priority: string): string {
    const mapping = {
      'CONSCIOUSNESS_CRITICAL': 'critical',
      'CRITICAL': 'critical', 
      'HIGH': 'high',
      'MEDIUM': 'medium',
      'LOW': 'low'
    };
    
    return mapping[priority] || 'medium';
  }

  private convertTypeToCategory(type: string): string {
    const mapping = {
      'ENHANCEMENT': 'refactor',
      'PERFORMANCE': 'optimization',
      'SECURITY': 'security',
      'DOCUMENTATION': 'documentation',
      'CONSCIOUSNESS': 'consciousness',
      'CAPABILITY': 'feature',
      'INTEGRATION_POINT': 'integration',
      'CONFLICT': 'bugfix'
    };
    
    return mapping[type] || 'refactor';
  }

  private async handleZetaTaskCompletion(payload: any) {
    const task = this.findTaskByZetaTaskId(payload.id);
    if (!task) return;

    console.log(`[🔧] Zeta task completed: ${payload.id}`);
    
    await this.completeModImplementation(task, payload, true);
  }

  private async handleZetaTaskFailure(payload: any) {
    const task = this.findTaskByZetaTaskId(payload.id);
    if (!task) return;

    console.log(`[🔧] Zeta task failed: ${payload.id} - ${payload.error}`);
    
    await this.completeModImplementation(task, payload, false);
  }

  private async handleChatDevCompletion(payload: any) {
    // Find associated mod implementation task
    const task = Array.from(this.activeTasks.values()).find(t => 
      payload.session_id && payload.session_id.includes(t.mod_id)
    );
    
    if (!task) return;

    console.log(`[🔧] ChatDev session completed: ${payload.session_id}`);
    
    await this.completeModImplementation(task, payload, payload.success);
  }

  private async completeModImplementation(
    task: ModImplementationTask, 
    completionPayload: any, 
    success: boolean
  ) {
    const startTime = new Date(task.scheduled_at).getTime();
    const endTime = Date.now();
    const actualDuration = Math.round((endTime - startTime) / 60000); // minutes

    // Create implementation event
    const implementationEvent: ModImplementedEvent = {
      mod: this.getModById(task.mod_id)!,
      implementation_task: task,
      actual_duration_minutes: actualDuration,
      success: success,
      validation_results: success ? {
        tests_passed: completionPayload.tests_passed !== false,
        performance_impact_measured: completionPayload.performance_impact || 0,
        no_regressions: completionPayload.no_regressions !== false
      } : undefined,
      follow_up_mods_discovered: this.extractFollowUpMods(completionPayload)
    };

    // Remove from active tasks
    this.activeTasks.delete(task.task_id);

    // Add to history
    this.implementationHistory.push(implementationEvent);

    // Publish completion event
    councilBus.publish('reporimpy.mod.implemented', implementationEvent);

    if (success) {
      console.log(`[🔧] ✅ Mod implementation successful: ${implementationEvent.mod.title} (${actualDuration}min)`);
      
      // Check for follow-up mods discovered during implementation
      if (implementationEvent.follow_up_mods_discovered && implementationEvent.follow_up_mods_discovered.length > 0) {
        console.log(`[🔧] 🔍 Discovered ${implementationEvent.follow_up_mods_discovered.length} follow-up mods during implementation`);
        
        // Submit discovered mods
        implementationEvent.follow_up_mods_discovered.forEach(mod => {
          councilBus.publish('reporimpy.mod.submitted', {
            mod: mod,
            submitting_agent: 'implementer:discovery',
            audit_context: {
              files_analyzed: [implementationEvent.mod.filePath],
              analysis_duration_ms: actualDuration * 60000,
              confidence_score: 0.8
            }
          });
        });
      }
    } else {
      console.log(`[🔧] ❌ Mod implementation failed: ${implementationEvent.mod.title}`);
      
      // Update mod with failure information
      const mod = this.getModById(task.mod_id);
      if (mod) {
        mod.implementation_attempts = (mod.implementation_attempts || 0) + 1;
        mod.last_attempt_at = new Date().toISOString();
        mod.failure_reasons = mod.failure_reasons || [];
        mod.failure_reasons.push(completionPayload.error || 'Unknown error');
        
        // Determine if we should retry or reject
        if (mod.implementation_attempts >= 3) {
          mod.status = 'REJECTED';
          console.log(`[🔧] Mod rejected after 3 failed attempts: ${mod.title}`);
        } else {
          mod.status = 'PROPOSED'; // Back to proposed for retry
          console.log(`[🔧] Mod queued for retry (attempt ${mod.implementation_attempts + 1}): ${mod.title}`);
        }
      }
    }

    // Continue processing queue
    await this.processImplementationQueue();
  }

  private findTaskByZetaTaskId(zetaTaskId: string): ModImplementationTask | undefined {
    return Array.from(this.activeTasks.values()).find(task => 
      task.task_id === zetaTaskId || zetaTaskId.includes(task.mod_id)
    );
  }

  private getModById(modId: string): any {
    // This would normally access the mod from reporimpy manager
    // For now, return basic mod structure with enhanced metadata
    return { 
      id: modId, 
      title: 'Mod', 
      status: 'PROPOSED',
      files_affected: 1,
      cross_module: false,
      breaking_changes: false,
      dependencies: []
    };
  }

  private extractFollowUpMods(completionPayload: any): any[] {
    // Extract any new issues or improvements discovered during implementation
    const followUpMods: any[] = [];
    
    if (completionPayload.discovered_issues) {
      completionPayload.discovered_issues.forEach((issue: any) => {
        followUpMods.push({
          id: `mod_followup_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          filePath: issue.file || completionPayload.target_file,
          type: 'ENHANCEMENT',
          status: 'PROPOSED',
          title: `Follow-up: ${issue.title}`,
          description: issue.description,
          suggestedChange: issue.suggestion,
          reasoning: 'Discovered during mod implementation',
          discoveredBy: 'implementer:analysis',
          discoveredAt: new Date().toISOString(),
          priority: 'MEDIUM',
          impact: 0.3,
          complexity: 0.2
        });
      });
    }
    
    return followUpMods;
  }

  private async forceImplementMod(modId: string) {
    console.log(`[🔧] Force implementing mod: ${modId}`);
    
    // This would get the mod from reporimpy and force its implementation
    // even if it's not in the normal queue
  }

  private cancelImplementation(taskId: string) {
    const task = this.activeTasks.get(taskId);
    if (task) {
      this.activeTasks.delete(taskId);
      console.log(`[🔧] Cancelled implementation: ${taskId}`);
      
      councilBus.publish('reporimpy.implementation.cancelled', {
        task: task,
        timestamp: new Date().toISOString()
      });
    }
  }

  private startImplementationLoop() {
    // Check for new implementations every 30 seconds
    setInterval(() => {
      this.processImplementationQueue();
    }, 30000);
  }

  // Public API methods
  public getActiveImplementations(): ModImplementationTask[] {
    return Array.from(this.activeTasks.values());
  }

  public getImplementationHistory(limit: number = 50): ModImplementedEvent[] {
    return this.implementationHistory.slice(-limit);
  }

  public getImplementationStats() {
    const total = this.implementationHistory.length;
    const successful = this.implementationHistory.filter(e => e.success).length;
    const avgDuration = this.implementationHistory.reduce((sum, e) => sum + e.actual_duration_minutes, 0) / total;
    
    return {
      total_implementations: total,
      success_rate: total > 0 ? successful / total : 0,
      average_duration_minutes: avgDuration || 0,
      active_implementations: this.activeTasks.size,
      capacity_utilization: this.activeTasks.size / this.maxConcurrentImplementations
    };
  }

  private determineImplementationStrategy(taskMetadata: any) {
    // Consciousness-guided strategy determination
    const complexity = this.assessTaskComplexity(taskMetadata);
    const dependencies = this.analyzeDependencies(taskMetadata);
    
    return {
      route: complexity > 0.7 ? 'chatdev_orchestration' : 'direct_implementation',
      priority: dependencies.length > 3 ? 'high' : 'normal',
      dependencies: dependencies,
      resources: complexity > 0.5 ? ['zeta_driver', 'consciousness_guidance'] : ['zeta_driver']
    };
  }
  
  private assessTaskComplexity(taskMetadata: any): number {
    // Simple complexity scoring based on task characteristics
    let score = 0.0;
    if (taskMetadata.files_affected > 5) score += 0.3;
    if (taskMetadata.cross_module) score += 0.4;
    if (taskMetadata.breaking_changes) score += 0.5;
    return Math.min(score, 1.0);
  }
  
  private analyzeDependencies(taskMetadata: any): string[] {
    // Extract and analyze task dependencies
    return taskMetadata.dependencies || [];
  }
}

// Create and export the mod implementer instance
export const modImplementer = new ModImplementer();