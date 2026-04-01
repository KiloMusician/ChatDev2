// ops/zeta-integration.js
// Integration layer for Zeta-Driver with the autonomous development ecosystem

import { councilBus } from "../packages/council/events/eventBus.js";
import ZetaProtocol, { ZetaTemplates } from "./zeta-protocol.js";

/**
 * Zeta Integration Layer
 * 
 * This module provides seamless integration between the autonomous system
 * and the Zeta-Driver orchestration engine. It automatically converts
 * system events into todo.zeta tasks and manages the development pipeline.
 */

export class ZetaIntegration {
  constructor() {
    this.isInitialized = false;
    this.taskHistory = [];
    this.activeIntegrations = new Set();
    
    console.log("[🔗] Zeta Integration Layer initializing...");
  }

  async initialize() {
    if (this.isInitialized) return true;

    try {
      // **SIMPLIFIED ZETA INTEGRATION** - Skip complex driver for now, focus on event coordination
      console.log("[🔗] Starting simplified Zeta workspace coordination...");
      
      // Set up integration event listeners without the full driver
      this.setupSystemIntegrations();
      
      this.isInitialized = true;
      console.log("[🔗] Zeta Integration Layer online - Workspace coordination active");
      
      // Publish readiness
      councilBus.publish('zeta_integration.ready', {
        status: 'operational',
        mode: 'simplified_coordination',
        timestamp: new Date().toISOString()
      });

      return true;
      
    } catch (error) {
      console.error("[🔗] Zeta Integration initialization failed:", error);
      return false;
    }
  }

  setupSystemIntegrations() {
    // 1. PU Queue Integration - Convert PU tasks to Zeta tasks
    councilBus.subscribe('pu.task_generated', (event) => {
      this.handlePUTask(event.payload);
    });

    // 2. AI Council Decisions - Convert decisions to development tasks
    councilBus.subscribe('ai_council.decision', (event) => {
      this.handleCouncilDecision(event.payload);
    });

    // 3. System Health Events - Generate improvement tasks
    councilBus.subscribe('system.health_warning', (event) => {
      this.handleHealthWarning(event.payload);
    });

    // 4. Performance Alerts - Generate optimization tasks  
    councilBus.subscribe('performance.alert', (event) => {
      this.handlePerformanceAlert(event.payload);
    });

    // 5. Code Quality Issues - Generate refactoring tasks
    councilBus.subscribe('code.quality_issue', (event) => {
      this.handleQualityIssue(event.payload);
    });

    // 6. Documentation Gaps - Generate documentation tasks
    councilBus.subscribe('docs.gap_detected', (event) => {
      this.handleDocumentationGap(event.payload);
    });

    // 7. Testing Coverage - Generate testing tasks
    councilBus.subscribe('testing.coverage_low', (event) => {
      this.handleTestingGap(event.payload);
    });

    console.log("[🔗] System integration listeners active");
  }

  handlePUTask(puTask) {
    // Convert PU (Processing Unit) tasks to Zeta tasks
    const taskType = this.inferTaskTypeFromPU(puTask);
    
    if (taskType && !this.activeIntegrations.has(`pu_${puTask.id}`)) {
      const zetaTask = ZetaProtocol.createTask({
        title: `PU Integration: ${puTask.title || puTask.type}`,
        description: `Autonomous processing unit task: ${puTask.description || puTask.summary}`,
        type: taskType,
        target_files: puTask.files || [],
        context: { 
          source: 'pu_queue',
          pu_task_id: puTask.id,
          pu_type: puTask.type 
        },
        priority: puTask.priority || 5,
        requester: 'pu_queue'
      });

      ZetaProtocol.publishTask(zetaTask);
      this.activeIntegrations.add(`pu_${puTask.id}`);
      
      console.log(`[🔗] PU task converted to Zeta: ${zetaTask.title}`);
    }
  }

  handleCouncilDecision(decision) {
    // Convert AI Council decisions into development tasks
    if (decision.action === 'optimize' && decision.confidence > 0.6) {
      const task = ZetaTemplates.optimizePerformance(['*']);
      task.context.council_decision = decision;
      task.priority = Math.ceil(decision.confidence * 10);
      
      ZetaProtocol.publishTask(task);
      console.log(`[🔗] Council optimization decision converted to Zeta task`);
    }
    
    if (decision.action === 'refactor' && decision.reasoning?.includes('modularity')) {
      const task = ZetaTemplates.improveModularity(decision.target_files || ['*']);
      task.context.council_decision = decision;
      
      ZetaProtocol.publishTask(task);
      console.log(`[🔗] Council refactor decision converted to Zeta task`);
    }
  }

  handleHealthWarning(warning) {
    // Generate tasks to address system health issues
    const task = ZetaProtocol.createTask({
      title: `Address System Health Warning: ${warning.type}`,
      description: `System health monitoring detected: ${warning.message}. Implement fixes to improve system stability.`,
      type: 'bugfix',
      target_files: warning.affected_files || ['*'],
      priority: warning.severity === 'critical' ? 9 : 7,
      context: { 
        source: 'health_monitoring',
        warning_type: warning.type,
        severity: warning.severity
      },
      success_criteria: [
        'Health warning resolved',
        'Monitoring metrics improved',
        'System stability enhanced'
      ]
    });

    ZetaProtocol.publishTask(task);
    console.log(`[🔗] Health warning converted to Zeta task: ${warning.type}`);
  }

  handlePerformanceAlert(alert) {
    // Generate performance optimization tasks
    const task = ZetaTemplates.optimizePerformance(alert.files || ['*']);
    task.title = `Performance Alert: ${alert.metric}`;
    task.description = `Performance monitoring detected degradation in ${alert.metric}: ${alert.message}`;
    task.priority = alert.severity === 'critical' ? 9 : 6;
    task.context.performance_alert = alert;

    ZetaProtocol.publishTask(task);
    console.log(`[🔗] Performance alert converted to Zeta task: ${alert.metric}`);
  }

  handleQualityIssue(issue) {
    // Generate code quality improvement tasks
    const task = ZetaTemplates.improveModularity(issue.files || ['*']);
    task.title = `Code Quality Issue: ${issue.type}`;
    task.description = `Code quality analysis detected: ${issue.message}. Refactor to improve maintainability.`;
    task.context.quality_issue = issue;

    ZetaProtocol.publishTask(task);
    console.log(`[🔗] Quality issue converted to Zeta task: ${issue.type}`);
  }

  handleDocumentationGap(gap) {
    // Generate documentation tasks
    const task = ZetaTemplates.enhanceDocumentation(gap.files || ['*']);
    task.title = `Documentation Gap: ${gap.area}`;
    task.description = `Documentation analysis detected missing or outdated docs in ${gap.area}: ${gap.message}`;
    task.context.docs_gap = gap;

    ZetaProtocol.publishTask(task);
    console.log(`[🔗] Documentation gap converted to Zeta task: ${gap.area}`);
  }

  handleTestingGap(gap) {
    // Generate testing improvement tasks
    const task = ZetaTemplates.addTesting(gap.files || ['*']);
    task.title = `Testing Coverage Gap: ${gap.area}`;
    task.description = `Testing analysis detected low coverage in ${gap.area}: ${gap.message}`;
    task.context.testing_gap = gap;

    ZetaProtocol.publishTask(task);
    console.log(`[🔗] Testing gap converted to Zeta task: ${gap.area}`);
  }

  // Helper Methods

  inferTaskTypeFromPU(puTask) {
    const type = puTask.type?.toLowerCase() || '';
    const description = puTask.description?.toLowerCase() || '';

    if (type.includes('refactor') || description.includes('refactor')) return 'refactor';
    if (type.includes('doc') || description.includes('document')) return 'documentation';
    if (type.includes('perf') || description.includes('performance')) return 'optimization';
    if (type.includes('test') || description.includes('testing')) return 'testing';
    if (type.includes('ui') || type.includes('ux')) return 'enhancement';
    if (type.includes('bug') || description.includes('fix')) return 'bugfix';
    if (type.includes('ml') || description.includes('machine learning')) return 'enhancement';
    
    return 'enhancement'; // Default
  }

  // Public Interface

  getStatus() {
    return {
      initialized: this.isInitialized,
      active_integrations: this.activeIntegrations.size,
      task_history_count: this.taskHistory.length,
      driver_status: this.zetaDriver?.getStatus() || null
    };
  }

  // Manual task creation helpers for testing/debugging
  createTestTask(type = 'enhancement') {
    const task = ZetaProtocol.createTask({
      title: `Test Zeta Task: ${type}`,
      description: `This is a test task to validate the Zeta-Driver pipeline for ${type} tasks`,
      type,
      target_files: ['ops/zeta-driver.js'],
      priority: 3,
      requester: 'manual_test',
      success_criteria: [
        'Task executed successfully',
        'ChatDev session completed',
        'Testing chamber validation passed'
      ]
    });

    ZetaProtocol.publishTask(task);
    console.log(`[🔗] Test task created: ${task.title}`);
    return task;
  }

  createDemoRefactorTask() {
    return this.createTestTask('refactor');
  }

  createDemoDocumentationTask() {
    return this.createTestTask('documentation');
  }

  createDemoOptimizationTask() {
    return this.createTestTask('optimization');
  }
}

// Export singleton instance
export const zetaIntegration = new ZetaIntegration();

// Auto-initialize if running as module
console.log("[🔗] Zeta Integration module loaded");

export default zetaIntegration;