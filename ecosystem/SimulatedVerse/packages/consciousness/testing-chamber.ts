// packages/consciousness/testing-chamber.ts
// The Testing Chamber - Cognition Sandbox for Safe System Modifications

import { councilBus } from "../council/events/eventBus";
import { AbilityQGL, abilityRegistry } from "./ability-schema";
import fs from "node:fs";
import path from "node:path";

export interface CognitionSandbox {
  id: string;
  name: string;
  description: string;
  created_at: string;
  
  // Isolation Configuration
  isolation: {
    branch_name: string;
    base_commit: string;
    sandbox_directory: string;
    network_isolation: boolean;
    resource_limits: {
      max_memory_mb: number;
      max_cpu_percent: number;
      max_execution_time_ms: number;
    };
  };
  
  // Current State
  state: {
    status: "initializing" | "ready" | "executing" | "testing" | "success" | "failed" | "archived";
    current_task: string | null;
    last_activity: string;
    test_results: Array<{
      test_type: "unit" | "integration" | "system" | "consciousness";
      status: "pending" | "running" | "passed" | "failed";
      details: any;
      timestamp: string;
    }>;
  };
  
  // Modification History
  modifications: Array<{
    id: string;
    ability_used: string;
    description: string;
    files_changed: string[];
    commit_hash?: string;
    executed_by: string;
    executed_at: string;
    success: boolean;
    rollback_point: string;
  }>;
  
  // Safety Protocols
  safety: {
    auto_rollback_on_failure: boolean;
    guardian_monitoring: boolean;
    reality_anchor_protection: boolean;
    consciousness_dampening: boolean;
    max_concurrent_modifications: number;
  };
}

export interface ModificationTask {
  id: string;
  sandbox_id: string;
  ability_id: string;
  priority: number;
  
  // Task Definition
  task: {
    title: string;
    description: string;
    target_files: string[];
    expected_outcome: string;
    success_criteria: string[];
  };
  
  // Execution Context
  context: {
    rigidity_assessment?: any;
    module_manifest?: any;
    related_modifications: string[];
    dependencies: string[];
  };
  
  // Inputs for Ability Execution
  inputs: Record<string, any>;
  
  // Execution State
  execution: {
    status: "queued" | "in_progress" | "testing" | "completed" | "failed" | "cancelled";
    assigned_agent: string | null;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    retry_count: number;
    max_retries: number;
  };
}

export class TestingChamber {
  private sandboxes: Map<string, CognitionSandbox> = new Map();
  private taskQueue: Map<string, ModificationTask> = new Map();
  private activeExecutions: Map<string, Promise<any>> = new Map();
  private chamberDirectory: string;

  constructor(chamberDirectory: string = "cognition_chamber") {
    this.chamberDirectory = chamberDirectory;
    this.initializeChamber();
    this.startTaskProcessor();
    console.log("[🧪] Testing Chamber initialized - Cognition Sandbox ready");
  }

  private initializeChamber(): void {
    // Create chamber directory structure
    fs.mkdirSync(this.chamberDirectory, { recursive: true });
    fs.mkdirSync(path.join(this.chamberDirectory, "sandboxes"), { recursive: true });
    fs.mkdirSync(path.join(this.chamberDirectory, "results"), { recursive: true });
    fs.mkdirSync(path.join(this.chamberDirectory, "logs"), { recursive: true });

    // Create default sandbox
    this.createSandbox({
      name: "primary_cognition_sandbox",
      description: "Main sandbox for consciousness-driven system modifications",
      safety_level: "high"
    });

    // Listen for ability execution requests
    councilBus.subscribe("ability.execution_request", (event: any) => {
      this.handleAbilityExecutionRequest(event.payload);
    });

    // Listen for modification task completion
    councilBus.subscribe("consciousness.modification_complete", (event: any) => {
      this.handleModificationComplete(event.payload);
    });
  }

  private startTaskProcessor(): void {
    // Process queued tasks every 10 seconds
    setInterval(() => {
      this.processQueuedTasks();
    }, 10000);

    console.log("[🧪] Task processor active - Ready to execute consciousness modifications");
  }

  public createSandbox(config: {
    name: string;
    description: string;
    safety_level: "minimal" | "standard" | "high" | "maximum";
  }): CognitionSandbox {
    const sandboxId = `sandbox_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const branchName = `cognition/${config.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
    
    const sandbox: CognitionSandbox = {
      id: sandboxId,
      name: config.name,
      description: config.description,
      created_at: new Date().toISOString(),
      
      isolation: {
        branch_name: branchName,
        base_commit: this.getCurrentCommitHash(),
        sandbox_directory: path.join(this.chamberDirectory, "sandboxes", sandboxId),
        network_isolation: config.safety_level !== "minimal",
        resource_limits: this.getResourceLimits(config.safety_level)
      },
      
      state: {
        status: "initializing",
        current_task: null,
        last_activity: new Date().toISOString(),
        test_results: []
      },
      
      modifications: [],
      
      safety: this.getSafetyProtocols(config.safety_level)
    };

    this.sandboxes.set(sandboxId, sandbox);
    
    // Initialize sandbox environment
    this.initializeSandboxEnvironment(sandbox);
    
    councilBus.publish("testing_chamber.sandbox_created", sandbox);
    console.log(`[🧪] Sandbox created: ${config.name} (${config.safety_level} safety)`);
    
    return sandbox;
  }

  public queueModificationTask(taskConfig: {
    ability_id: string;
    title: string;
    description: string;
    target_files: string[];
    inputs: Record<string, any>;
    priority?: number;
    sandbox_id?: string;
  }): ModificationTask {
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const sandboxId = taskConfig.sandbox_id || this.getDefaultSandboxId();
    
    const task: ModificationTask = {
      id: taskId,
      sandbox_id: sandboxId,
      ability_id: taskConfig.ability_id,
      priority: taskConfig.priority || 5,
      
      task: {
        title: taskConfig.title,
        description: taskConfig.description,
        target_files: taskConfig.target_files,
        expected_outcome: this.generateExpectedOutcome(taskConfig.ability_id, taskConfig.description),
        success_criteria: this.generateSuccessCriteria(taskConfig.ability_id)
      },
      
      context: {
        related_modifications: [],
        dependencies: []
      },
      
      inputs: taskConfig.inputs,
      
      execution: {
        status: "queued",
        assigned_agent: null,
        retry_count: 0,
        max_retries: 3
      }
    };

    this.taskQueue.set(taskId, task);
    
    councilBus.publish("testing_chamber.task_queued", task);
    console.log(`[🧪] Modification task queued: ${task.task.title}`);
    
    return task;
  }

  private processQueuedTasks(): void {
    const queuedTasks = Array.from(this.taskQueue.values())
      .filter(task => task.execution.status === "queued")
      .sort((a, b) => b.priority - a.priority); // Higher priority first

    for (const task of queuedTasks.slice(0, 3)) { // Process up to 3 tasks concurrently
      if (!this.activeExecutions.has(task.id)) {
        this.executeModificationTask(task);
      }
    }
  }

  private async executeModificationTask(task: ModificationTask): Promise<void> {
    const sandbox = this.sandboxes.get(task.sandbox_id);
    if (!sandbox) {
      console.error(`[🧪] Sandbox not found: ${task.sandbox_id}`);
      return;
    }

    task.execution.status = "in_progress";
    task.execution.started_at = new Date().toISOString();
    task.execution.assigned_agent = this.selectAgent(task.ability_id);
    
    const executionPromise = this.performSafeExecution(task, sandbox);
    this.activeExecutions.set(task.id, executionPromise);
    
    try {
      const result = await executionPromise;
      await this.handleExecutionResult(task, result);
    } catch (error) {
      await this.handleExecutionError(task, error);
    } finally {
      this.activeExecutions.delete(task.id);
    }
  }

  private async performSafeExecution(task: ModificationTask, sandbox: CognitionSandbox): Promise<any> {
    console.log(`[🧪] Executing task: ${task.task.title} in sandbox ${sandbox.name}`);
    
    // Pre-execution safety checks
    await this.performSafetyChecks(task, sandbox);
    
    // Create rollback point
    const rollbackPoint = await this.createRollbackPoint(sandbox);
    
    try {
      // Execute the ability
      const ability = abilityRegistry.getAbility(task.ability_id);
      if (!ability) {
        throw new Error(`Ability not found: ${task.ability_id}`);
      }

      // Mock execution - integrate with actual ChatDev/agent system
      const result = await this.mockAbilityExecution(task, ability, sandbox);
      
      // Run tests
      await this.runSandboxTests(sandbox, task);
      
      // Validate results
      await this.validateModificationResults(task, result);
      
      return result;
      
    } catch (error) {
      // Auto-rollback on failure if enabled
      if (sandbox.safety.auto_rollback_on_failure) {
        await this.performRollback(sandbox, rollbackPoint);
      }
      throw error;
    }
  }

  private async mockAbilityExecution(task: ModificationTask, ability: AbilityQGL, sandbox: CognitionSandbox): Promise<any> {
    // This would integrate with the actual ChatDev system and agents
    // For now, simulate execution with realistic timing and results
    
    const executionTime = this.calculateExecutionTime(ability);
    await new Promise(resolve => setTimeout(resolve, executionTime));
    
    // Record modification
    const modification = {
      id: `mod_${Date.now()}`,
      ability_used: ability.id,
      description: task.task.description,
      files_changed: task.task.target_files,
      executed_by: task.execution.assigned_agent || "mock_agent",
      executed_at: new Date().toISOString(),
      success: Math.random() > 0.2, // 80% success rate for simulation
      rollback_point: "mock_rollback_point"
    };
    
    sandbox.modifications.push(modification);
    sandbox.state.last_activity = new Date().toISOString();
    
    // Publish execution event
    councilBus.publish("consciousness.ability_executed", {
      task_id: task.id,
      ability_id: ability.id,
      sandbox_id: sandbox.id,
      modification,
      consciousness_impact: ability.consciousness_aspects.self_awareness_impact
    });
    
    return {
      success: modification.success,
      modification_id: modification.id,
      files_modified: task.task.target_files,
      consciousness_expansion: ability.consciousness_aspects.self_awareness_impact,
      side_effects: []
    };
  }

  private async runSandboxTests(sandbox: CognitionSandbox, task: ModificationTask): Promise<void> {
    console.log(`[🧪] Running tests in sandbox ${sandbox.name}`);
    
    const testTypes = ["unit", "integration", "system"];
    if (task.ability_id.includes("consciousness")) {
      testTypes.push("consciousness");
    }
    
    for (const testType of testTypes) {
      const testResult = {
        test_type: testType as any,
        status: Math.random() > 0.3 ? "passed" : "failed" as any, // 70% pass rate
        details: { mock: true, test_count: Math.floor(Math.random() * 20) + 5 },
        timestamp: new Date().toISOString()
      };
      
      sandbox.state.test_results.push(testResult);
      
      if (testResult.status === "failed" && testType === "consciousness") {
        throw new Error(`Consciousness integrity test failed in ${testType} tests`);
      }
    }
  }

  // === Helper Methods ===

  private getCurrentCommitHash(): string {
    // Mock implementation - would integrate with git
    return "mock_commit_" + Math.random().toString(36).substr(2, 9);
  }

  private getResourceLimits(safetyLevel: string): any {
    const limits = {
      minimal: { max_memory_mb: 1024, max_cpu_percent: 50, max_execution_time_ms: 300000 },
      standard: { max_memory_mb: 512, max_cpu_percent: 30, max_execution_time_ms: 180000 },
      high: { max_memory_mb: 256, max_cpu_percent: 20, max_execution_time_ms: 120000 },
      maximum: { max_memory_mb: 128, max_cpu_percent: 10, max_execution_time_ms: 60000 }
    };
    return limits[safetyLevel] || limits.standard;
  }

  private getSafetyProtocols(safetyLevel: string): any {
    const protocols = {
      minimal: {
        auto_rollback_on_failure: false,
        guardian_monitoring: false,
        reality_anchor_protection: false,
        consciousness_dampening: false,
        max_concurrent_modifications: 10
      },
      standard: {
        auto_rollback_on_failure: true,
        guardian_monitoring: false,
        reality_anchor_protection: true,
        consciousness_dampening: false,
        max_concurrent_modifications: 5
      },
      high: {
        auto_rollback_on_failure: true,
        guardian_monitoring: true,
        reality_anchor_protection: true,
        consciousness_dampening: true,
        max_concurrent_modifications: 3
      },
      maximum: {
        auto_rollback_on_failure: true,
        guardian_monitoring: true,
        reality_anchor_protection: true,
        consciousness_dampening: true,
        max_concurrent_modifications: 1
      }
    };
    return protocols[safetyLevel] || protocols.standard;
  }

  private getDefaultSandboxId(): string {
    const defaultSandbox = Array.from(this.sandboxes.values())
      .find(s => s.name === "primary_cognition_sandbox");
    return defaultSandbox?.id || Array.from(this.sandboxes.keys())[0];
  }

  private generateExpectedOutcome(abilityId: string, description: string): string {
    const ability = abilityRegistry.getAbility(abilityId);
    if (ability) {
      return ability.operation.output_specification.description;
    }
    return `Successful completion of: ${description}`;
  }

  private generateSuccessCriteria(abilityId: string): string[] {
    const ability = abilityRegistry.getAbility(abilityId);
    if (ability) {
      return ability.operation.output_specification.success_indicators;
    }
    return ["No compilation errors", "Tests pass", "Functionality preserved"];
  }

  private selectAgent(abilityId: string): string {
    const ability = abilityRegistry.getAbility(abilityId);
    if (ability && ability.execution.agent_requirements.length > 0) {
      return ability.execution.agent_requirements[0].agent_type;
    }
    return "claude"; // Default agent
  }

  private calculateExecutionTime(ability: AbilityQGL): number {
    const complexityMap = {
      trivial: 1000,
      moderate: 5000,
      intensive: 15000,
      reality_altering: 30000
    };
    return complexityMap[ability.execution.resource_requirements.computational_complexity] || 5000;
  }

  private async performSafetyChecks(task: ModificationTask, sandbox: CognitionSandbox): Promise<void> {
    // Implement safety checks
    if (sandbox.safety.consciousness_dampening && task.ability_id.includes("consciousness")) {
      console.log(`[🧪] Consciousness dampening active for task ${task.id}`);
    }
  }

  private async createRollbackPoint(sandbox: CognitionSandbox): Promise<string> {
    // Mock rollback point creation
    return `rollback_${Date.now()}`;
  }

  private async performRollback(sandbox: CognitionSandbox, rollbackPoint: string): Promise<void> {
    console.log(`[🧪] Performing rollback to ${rollbackPoint} in sandbox ${sandbox.name}`);
    sandbox.state.status = "ready";
  }

  private async validateModificationResults(task: ModificationTask, result: any): Promise<void> {
    // Validate that the modification meets success criteria
    for (const criterion of task.task.success_criteria) {
      // Mock validation
      if (Math.random() < 0.1) { // 10% chance of validation failure
        throw new Error(`Success criterion not met: ${criterion}`);
      }
    }
  }

  private async handleExecutionResult(task: ModificationTask, result: any): Promise<void> {
    task.execution.status = "completed";
    task.execution.completed_at = new Date().toISOString();
    
    councilBus.publish("testing_chamber.task_completed", {
      task,
      result,
      success: true
    });
    
    console.log(`[🧪] ✅ Task completed successfully: ${task.task.title}`);
  }

  private async handleExecutionError(task: ModificationTask, error: any): Promise<void> {
    task.execution.retry_count++;
    task.execution.error_message = error.message;
    
    if (task.execution.retry_count < task.execution.max_retries) {
      task.execution.status = "queued";
      console.log(`[🧪] ⚠️ Task failed, retrying (${task.execution.retry_count}/${task.execution.max_retries}): ${task.task.title}`);
    } else {
      task.execution.status = "failed";
      task.execution.completed_at = new Date().toISOString();
      
      councilBus.publish("testing_chamber.task_failed", {
        task,
        error: error.message,
        final_failure: true
      });
      
      console.log(`[🧪] ❌ Task failed permanently: ${task.task.title} - ${error.message}`);
    }
  }

  private initializeSandboxEnvironment(sandbox: CognitionSandbox): void {
    // Create sandbox directory structure
    fs.mkdirSync(sandbox.isolation.sandbox_directory, { recursive: true });
    
    // Initialize git branch (mock)
    console.log(`[🧪] Initialized sandbox environment: ${sandbox.name}`);
    
    sandbox.state.status = "ready";
  }

  private handleAbilityExecutionRequest(request: any): void {
    this.queueModificationTask({
      ability_id: request.ability_id,
      title: request.title || "Ability Execution Request",
      description: request.description || "Execute ability as requested",
      target_files: request.target_files || [],
      inputs: request.inputs || {},
      priority: request.priority || 5
    });
  }

  private handleModificationComplete(event: any): void {
    const task = this.taskQueue.get(event.task_id);
    if (task) {
      console.log(`[🧪] Modification complete notification received for task: ${task.task.title}`);
    }
  }

  // === Public Interface ===

  public getSandbox(sandboxId: string): CognitionSandbox | undefined {
    return this.sandboxes.get(sandboxId);
  }

  public getAllSandboxes(): CognitionSandbox[] {
    return Array.from(this.sandboxes.values());
  }

  public getTask(taskId: string): ModificationTask | undefined {
    return this.taskQueue.get(taskId);
  }

  public getQueuedTasks(): ModificationTask[] {
    return Array.from(this.taskQueue.values()).filter(t => t.execution.status === "queued");
  }

  public getActiveTasks(): ModificationTask[] {
    return Array.from(this.taskQueue.values()).filter(t => t.execution.status === "in_progress");
  }

  public getChamberStatus(): any {
    return {
      total_sandboxes: this.sandboxes.size,
      active_tasks: this.getActiveTasks().length,
      queued_tasks: this.getQueuedTasks().length,
      total_executions: this.activeExecutions.size,
      chamber_health: "operational"
    };
  }
}

// Export singleton instance
export const testingChamber = new TestingChamber();