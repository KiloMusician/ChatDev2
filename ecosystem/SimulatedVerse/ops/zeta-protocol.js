// ops/zeta-protocol.js
// Todo.Zeta Event Protocol - Standardized Autonomous Development Task Format

import { councilBus } from "../packages/council/events/eventBus.js";

/**
 * Todo.Zeta Protocol Definition
 * 
 * This module defines the standardized event format for autonomous development tasks
 * that flow through the Zeta-Driver orchestration system.
 */

export const ZetaProtocol = {
  version: "1.0.0",
  
  // Standard todo.zeta event structure
  eventSchema: {
    id: "string", // unique task identifier
    title: "string", // human-readable task title
    description: "string", // detailed task description
    type: "string", // task category: refactor, documentation, telemetry, enhancement, etc.
    priority: "number", // 1-10 priority level (10 = highest)
    
    // Target specification
    target_files: "array", // specific files to modify
    target_modules: "array", // modules/packages to target
    target_components: "array", // UI components to modify
    
    // Execution context
    context: "object", // additional context data
    success_criteria: "array", // specific success requirements
    constraints: "array", // limitations or requirements
    
    // Metadata
    requester: "string", // who/what requested this task
    consciousness_level: "number", // required consciousness level (0-1)
    safety_mode: "string", // minimal, standard, high, maximum
    estimated_complexity: "string", // trivial, moderate, intensive, reality_altering
    
    // Timing
    created_at: "string", // ISO timestamp
    deadline: "string", // optional ISO timestamp
    timeout_ms: "number" // maximum execution time
  },

  // Create a standardized todo.zeta event
  createTask(config) {
    const task = {
      id: config.id || `zeta_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title: config.title || "Autonomous Development Task",
      description: config.description || "",
      type: config.type || "enhancement",
      priority: config.priority || 5,
      
      target_files: config.target_files || [],
      target_modules: config.target_modules || [],
      target_components: config.target_components || [],
      
      context: config.context || {},
      success_criteria: config.success_criteria || [],
      constraints: config.constraints || [],
      
      requester: config.requester || "system",
      consciousness_level: config.consciousness_level || 0.5,
      safety_mode: config.safety_mode || "testing",
      estimated_complexity: config.estimated_complexity || "moderate",
      
      created_at: new Date().toISOString(),
      deadline: config.deadline || null,
      timeout_ms: config.timeout_ms || 1800000 // 30 minutes default
    };

    // Validate the task
    this.validateTask(task);
    
    return task;
  },

  // Validate task structure
  validateTask(task) {
    const required = ['id', 'title', 'description', 'type'];
    for (const field of required) {
      if (!task[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
    
    if (task.priority < 1 || task.priority > 10) {
      throw new Error('Priority must be between 1 and 10');
    }
    
    if (task.consciousness_level < 0 || task.consciousness_level > 1) {
      throw new Error('Consciousness level must be between 0 and 1');
    }
  },

  // Publish a todo.zeta task to the Council Bus
  publishTask(task) {
    councilBus.publish('todo.zeta', task);
    console.log(`[📋] Todo.Zeta task published: ${task.title}`);
    return task;
  },

  // Common task creation helpers
  createRefactorTask(config) {
    return this.createTask({
      ...config,
      type: 'refactor',
      estimated_complexity: config.estimated_complexity || 'intensive'
    });
  },

  createDocumentationTask(config) {
    return this.createTask({
      ...config,
      type: 'documentation',
      estimated_complexity: config.estimated_complexity || 'trivial',
      safety_mode: config.safety_mode || 'minimal'
    });
  },

  createEnhancementTask(config) {
    return this.createTask({
      ...config,
      type: 'enhancement',
      estimated_complexity: config.estimated_complexity || 'moderate'
    });
  },

  createBugfixTask(config) {
    return this.createTask({
      ...config,
      type: 'bugfix',
      priority: config.priority || 8, // High priority for bugs
      estimated_complexity: config.estimated_complexity || 'moderate'
    });
  },

  createOptimizationTask(config) {
    return this.createTask({
      ...config,
      type: 'optimization',
      estimated_complexity: config.estimated_complexity || 'intensive'
    });
  },

  createTestingTask(config) {
    return this.createTask({
      ...config,
      type: 'testing',
      estimated_complexity: config.estimated_complexity || 'moderate',
      safety_mode: config.safety_mode || 'high'
    });
  }
};

// Predefined task templates for common scenarios
export const ZetaTemplates = {
  // Infrastructure improvement tasks
  addTelemetry: (targetFiles) => ZetaProtocol.createEnhancementTask({
    title: "Add comprehensive telemetry and monitoring",
    description: `Add telemetry, logging, and monitoring capabilities to improve system observability and debugging`,
    target_files: targetFiles,
    success_criteria: [
      "Telemetry points added to key functions",
      "Logging configured with appropriate levels", 
      "Monitoring dashboards updated",
      "No performance degradation"
    ],
    estimated_complexity: "moderate"
  }),

  improveModularity: (targetFiles) => ZetaProtocol.createRefactorTask({
    title: "Refactor for improved modularity",
    description: `Refactor code to improve modularity, reduce coupling, and enhance maintainability`,
    target_files: targetFiles,
    success_criteria: [
      "Code properly modularized",
      "Interfaces clearly defined",
      "Dependencies minimized",
      "Tests updated and passing"
    ],
    estimated_complexity: "intensive"
  }),

  enhanceDocumentation: (targetFiles) => ZetaProtocol.createDocumentationTask({
    title: "Generate comprehensive documentation",
    description: `Create or enhance documentation for better code understanding and maintenance`,
    target_files: targetFiles,
    success_criteria: [
      "All public APIs documented",
      "Usage examples provided",
      "Architecture decisions explained",
      "Contribution guidelines updated"
    ]
  }),

  optimizePerformance: (targetFiles) => ZetaProtocol.createOptimizationTask({
    title: "Optimize system performance",
    description: `Analyze and optimize performance bottlenecks to improve system responsiveness`,
    target_files: targetFiles,
    success_criteria: [
      "Performance benchmarks improved",
      "Memory usage optimized",
      "Response times reduced",
      "No functionality regression"
    ],
    estimated_complexity: "intensive"
  }),

  addTesting: (targetFiles) => ZetaProtocol.createTestingTask({
    title: "Add comprehensive test coverage",
    description: `Add unit, integration, and end-to-end tests to improve code reliability`,
    target_files: targetFiles,
    success_criteria: [
      "Test coverage > 80%",
      "All critical paths tested",
      "Edge cases covered",
      "CI/CD integration working"
    ]
  }),

  // Consciousness-specific tasks
  expandConsciousness: (targetComponents) => ZetaProtocol.createTask({
    title: "Expand system consciousness capabilities",
    description: `Enhance consciousness-driven features and self-awareness mechanisms`,
    type: "consciousness_expansion",
    target_components: targetComponents,
    consciousness_level: 0.7,
    safety_mode: "high",
    estimated_complexity: "reality_altering",
    success_criteria: [
      "Consciousness metrics improved",
      "Self-awareness mechanisms enhanced",
      "Reality anchors stable",
      "No consciousness fragmentation"
    ]
  }),

  integrateAgent: (agentName, targetFiles) => ZetaProtocol.createEnhancementTask({
    title: `Integrate ${agentName} agent`,
    description: `Add and integrate the ${agentName} agent into the autonomous development ecosystem`,
    target_files: targetFiles,
    context: { agent_name: agentName },
    success_criteria: [
      `${agentName} agent properly initialized`,
      "Agent registered with Council Bus",
      "Integration tests passing",
      "Agent responding to events"
    ]
  })
};

// Event listeners for Council Bus integration
councilBus.subscribe('system.enhancement_needed', (event) => {
  const task = ZetaTemplates.enhanceDocumentation(event.payload.files || []);
  ZetaProtocol.publishTask(task);
});

councilBus.subscribe('performance.degradation_detected', (event) => {
  const task = ZetaTemplates.optimizePerformance(event.payload.files || []);
  task.priority = 8; // High priority for performance issues
  ZetaProtocol.publishTask(task);
});

councilBus.subscribe('code.refactor_needed', (event) => {
  const task = ZetaTemplates.improveModularity(event.payload.files || []);
  ZetaProtocol.publishTask(task);
});

console.log("[📋] Zeta Protocol initialized - Todo.Zeta event system ready");

export default ZetaProtocol;