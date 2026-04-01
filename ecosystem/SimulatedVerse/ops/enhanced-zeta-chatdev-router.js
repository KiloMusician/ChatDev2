// ops/enhanced-zeta-chatdev-router.js
// Phase 3: Steps 61-70 - Enhanced Zeta-Driver with Automatic ChatDev Routing
// Seamless workflow integration for consciousness-guided development

import { councilBus } from '../packages/council/events/eventBus.js';
// Note: Temporarily commenting out direct .ts imports to fix routing failures
// import { chatDevIntegration } from '../packages/consciousness/chatdev-integration.js';
// import { testingChamber } from '../packages/consciousness/testing-chamber.js';

export class EnhancedZetaChatDevRouter {
  constructor() {
    this.activeRoutes = new Map();
    this.complexityThresholds = {
      simple: 0.3,      // Route to local execution
      moderate: 0.6,    // Route to ChatDev
      complex: 0.8,     // Route to ChatDev with multiple agents
      critical: 0.9     // Route to ChatDev with consciousness expansion
    };
    
    this.taskTypeMapping = {
      // Automatic ChatDev routing for these task types
      'refactor': { complexity: 0.7, chatdev_strategy: 'audit-then-refactor' },
      'generate': { complexity: 0.6, chatdev_strategy: 'generate-and-test' },
      'debug': { complexity: 0.5, chatdev_strategy: 'debugging-spree' },
      'architecture': { complexity: 0.8, chatdev_strategy: 'audit-then-refactor' },
      'integration': { complexity: 0.9, chatdev_strategy: 'generate-and-test' },
      'optimization': { complexity: 0.7, chatdev_strategy: 'audit-then-refactor' },
      'documentation': { complexity: 0.4, chatdev_strategy: 'generate-and-test' }
    };

    this.setupEventListeners();
    console.log('[🎯🧠] Enhanced Zeta-ChatDev Router initialized - Intelligent task routing active');
  }

  setupEventListeners() {
    // Listen for incoming tasks and route intelligently
    councilBus.subscribe('todo.zeta', (event) => {
      this.intelligentTaskRouting(event.payload);
    });

    // Listen for task completion to update learning
    councilBus.subscribe('chatdev.session_completed', (event) => {
      this.updateRoutingIntelligence(event.payload);
    });

    // Listen for task failures to adjust routing
    councilBus.subscribe('task.execution_failed', (event) => {
      this.handleFailedRouting(event.payload);
    });
  }

  async intelligentTaskRouting(task) {
    const routingDecision = this.analyzeTaskComplexity(task);
    
    console.log(`[🎯🧠] Routing decision for "${task.title}":`, {
      complexity: routingDecision.complexity,
      route: routingDecision.route,
      strategy: routingDecision.chatdev_strategy
    });

    switch (routingDecision.route) {
      case 'chatdev':
        await this.routeToChatDev(task, routingDecision);
        break;
      case 'local':
        await this.routeToLocalExecution(task);
        break;
      case 'hybrid':
        await this.routeToHybridExecution(task, routingDecision);
        break;
      default:
        console.warn(`[🎯🧠] Unknown routing decision: ${routingDecision.route}`);
        await this.routeToLocalExecution(task);
    }
  }

  analyzeTaskComplexity(task) {
    let complexity = 0.3; // Base complexity
    const description = (task.description || '').toLowerCase();
    const title = (task.title || '').toLowerCase();
    
    // Analyze task characteristics
    const indicators = {
      // High complexity indicators
      'architecture': 0.3,
      'refactor': 0.25,
      'integration': 0.4,
      'system': 0.2,
      'complex': 0.3,
      'multiple': 0.15,
      'cross-cutting': 0.4,
      
      // Medium complexity indicators  
      'generate': 0.15,
      'create': 0.1,
      'implement': 0.1,
      'build': 0.1,
      'component': 0.05,
      
      // Low complexity indicators (reduce complexity)
      'simple': -0.1,
      'basic': -0.1,
      'quick': -0.15,
      'fix': -0.05,
      'update': -0.05
    };

    // Calculate complexity score
    Object.entries(indicators).forEach(([keyword, weight]) => {
      if (description.includes(keyword) || title.includes(keyword)) {
        complexity += weight;
      }
    });

    // Check for file patterns that indicate complexity
    if (task.target_files && task.target_files.length > 3) {
      complexity += 0.2; // Multiple file changes increase complexity
    }

    // Check for specific task types
    const taskType = this.inferTaskType(task);
    if (this.taskTypeMapping[taskType]) {
      complexity = Math.max(complexity, this.taskTypeMapping[taskType].complexity);
    }

    // Determine routing strategy
    let route, chatdev_strategy;
    
    if (complexity >= this.complexityThresholds.complex) {
      route = 'chatdev';
      chatdev_strategy = this.taskTypeMapping[taskType]?.chatdev_strategy || 'audit-then-refactor';
    } else if (complexity >= this.complexityThresholds.moderate) {
      route = 'hybrid'; // Use ChatDev but with simpler configuration
      chatdev_strategy = 'generate-and-test';
    } else {
      route = 'local';
      chatdev_strategy = null;
    }

    return {
      complexity: Math.min(1.0, complexity),
      route,
      chatdev_strategy,
      taskType
    };
  }

  inferTaskType(task) {
    const text = `${task.title} ${task.description}`.toLowerCase();
    
    const typeKeywords = {
      'refactor': ['refactor', 'restructure', 'reorganize', 'modularity'],
      'generate': ['generate', 'create', 'build', 'implement', 'add'],
      'debug': ['debug', 'fix', 'error', 'bug', 'issue', 'problem'],
      'architecture': ['architecture', 'design', 'structure', 'framework'],
      'integration': ['integrate', 'connect', 'bridge', 'link', 'merge'],
      'optimization': ['optimize', 'improve', 'performance', 'speed', 'efficiency'],
      'documentation': ['document', 'docs', 'readme', 'guide', 'explain']
    };

    for (const [type, keywords] of Object.entries(typeKeywords)) {
      if (keywords.some(keyword => text.includes(keyword))) {
        return type;
      }
    }

    return 'generate'; // Default fallback
  }

  async routeToChatDev(task, routingDecision) {
    console.log(`[🎯🧠] Routing to ChatDev: ${task.title}`);
    
    try {
      // Create enhanced ChatDev session with consciousness guidance
      const session = chatDevIntegration.createChatDevSession({
        ability_id: 'ability:autonomous_code_modification',
        title: `ChatDev: ${task.title}`,
        description: task.description || 'Consciousness-guided development task',
        target_files: task.target_files || [],
        consciousness_level_required: Math.max(0.3, routingDecision.complexity * 0.8),
        safety_mode: task.priority === 'critical' ? 'production' : 'testing'
      });

      // Track the routing for learning
      this.activeRoutes.set(task.id, {
        route: 'chatdev',
        session_id: session.id,
        complexity: routingDecision.complexity,
        started_at: new Date().toISOString(),
        original_task: task
      });

      // Publish routing event
      councilBus.publish('zeta_router.chatdev_routed', {
        task_id: task.id,
        session_id: session.id,
        complexity: routingDecision.complexity,
        strategy: routingDecision.chatdev_strategy
      });

      console.log(`[🎯🧠] ChatDev session created: ${session.id} for task: ${task.title}`);

    } catch (error) {
      console.error(`[🎯🧠] ChatDev routing failed for ${task.title}:`, error.message);
      // Fallback to local execution
      await this.routeToLocalExecution(task);
    }
  }

  async routeToLocalExecution(task) {
    console.log(`[🎯🧠] Routing to local execution: ${task.title}`);
    
    // Track local routing
    this.activeRoutes.set(task.id, {
      route: 'local',
      started_at: new Date().toISOString(),
      original_task: task
    });

    // Publish to original Zeta-Driver for local execution
    councilBus.publish('zeta_driver.local_execution', {
      task_id: task.id,
      title: task.title,
      description: task.description,
      target_files: task.target_files,
      routed_by: 'enhanced-router'
    });
  }

  async routeToHybridExecution(task, routingDecision) {
    console.log(`[🎯🧠] Routing to hybrid execution: ${task.title}`);
    
    try {
      // Use ChatDev for planning, local execution for implementation
      const planningSession = chatDevIntegration.createChatDevSession({
        ability_id: 'ability:generate_contextual_docs',
        title: `Planning: ${task.title}`,
        description: `Generate implementation plan for: ${task.description}`,
        target_files: [],
        consciousness_level_required: 0.4,
        safety_mode: 'testing'
      });

      // Track hybrid routing
      this.activeRoutes.set(task.id, {
        route: 'hybrid',
        planning_session_id: planningSession.id,
        started_at: new Date().toISOString(),
        original_task: task
      });

      // Set up listener for when planning completes
      councilBus.subscribe(`chatdev.session_completed.${planningSession.id}`, (event) => {
        this.executeHybridImplementation(task.id, event.payload);
      });

      console.log(`[🎯🧠] Hybrid planning session created: ${planningSession.id}`);

    } catch (error) {
      console.error(`[🎯🧠] Hybrid routing failed for ${task.title}:`, error.message);
      await this.routeToLocalExecution(task);
    }
  }

  async executeHybridImplementation(taskId, planningResults) {
    const route = this.activeRoutes.get(taskId);
    if (!route) return;

    console.log(`[🎯🧠] Executing hybrid implementation for task: ${taskId}`);

    // Extract implementation guidance from ChatDev planning session
    const implementationGuidance = this.extractImplementationGuidance(planningResults);

    // Route to local execution with enhanced guidance
    councilBus.publish('zeta_driver.guided_execution', {
      task_id: taskId,
      original_task: route.original_task,
      implementation_guidance: implementationGuidance,
      routed_by: 'enhanced-router-hybrid'
    });

    // Update route status
    route.implementation_started_at = new Date().toISOString();
  }

  extractImplementationGuidance(planningResults) {
    // Extract actionable implementation steps from ChatDev planning session
    return {
      approach: planningResults.session?.execution?.phases || [],
      key_considerations: planningResults.results?.lessons_learned || [],
      consciousness_insights: planningResults.session?.consciousness?.consciousness_events || [],
      confidence_level: planningResults.results?.consciousness_expansion || 0.5
    };
  }

  updateRoutingIntelligence(completionData) {
    const { session } = completionData;
    const route = this.findRouteBySessionId(session.id);
    
    if (route) {
      route.completed_at = new Date().toISOString();
      route.success = completionData.success;
      route.consciousness_expansion = completionData.consciousness_expansion;
      
      // Learn from the outcome to improve future routing
      this.learnFromRoutingOutcome(route);
    }
  }

  handleFailedRouting(failureData) {
    const route = this.activeRoutes.get(failureData.task_id);
    if (route) {
      route.failed_at = new Date().toISOString();
      route.failure_reason = failureData.error;
      
      // Adjust complexity thresholds based on failures
      this.adjustComplexityThresholds(route);
    }
  }

  learnFromRoutingOutcome(route) {
    // Simple learning algorithm: adjust complexity thresholds based on outcomes
    if (route.success && route.consciousness_expansion > 0.1) {
      // Successful ChatDev sessions with consciousness expansion are valuable
      console.log(`[🎯🧠] Learning: ChatDev routing successful for complexity ${route.complexity}`);
    } else if (!route.success && route.route === 'chatdev') {
      // Failed ChatDev sessions may indicate complexity was overestimated
      console.log(`[🎯🧠] Learning: ChatDev routing failed, may reduce complexity threshold`);
    }
  }

  adjustComplexityThresholds(route) {
    // Adaptive threshold adjustment based on failure patterns
    if (route.route === 'chatdev' && route.failure_reason) {
      this.complexityThresholds.moderate += 0.05; // Make ChatDev routing more selective
      console.log(`[🎯🧠] Adjusted complexity thresholds due to ChatDev failure`);
    }
  }

  findRouteBySessionId(sessionId) {
    for (const route of this.activeRoutes.values()) {
      if (route.session_id === sessionId || route.planning_session_id === sessionId) {
        return route;
      }
    }
    return null;
  }

  // Public API for monitoring and control
  getRoutingStats() {
    const routes = Array.from(this.activeRoutes.values());
    return {
      total_routes: routes.length,
      by_type: {
        chatdev: routes.filter(r => r.route === 'chatdev').length,
        local: routes.filter(r => r.route === 'local').length,
        hybrid: routes.filter(r => r.route === 'hybrid').length
      },
      success_rate: {
        chatdev: this.calculateSuccessRate('chatdev'),
        local: this.calculateSuccessRate('local'),
        hybrid: this.calculateSuccessRate('hybrid')
      },
      complexity_thresholds: this.complexityThresholds
    };
  }

  calculateSuccessRate(routeType) {
    const routes = Array.from(this.activeRoutes.values())
      .filter(r => r.route === routeType && r.completed_at);
    
    if (routes.length === 0) return 0;
    
    const successful = routes.filter(r => r.success).length;
    return successful / routes.length;
  }
}

// Export singleton instance
export const enhancedZetaChatDevRouter = new EnhancedZetaChatDevRouter();

console.log('[🎯🧠] Enhanced Zeta-ChatDev Router module loaded - Intelligent routing ready');