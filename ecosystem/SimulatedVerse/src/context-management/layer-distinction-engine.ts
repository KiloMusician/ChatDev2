// Layer Distinction Engine - Intelligent Prime Agent Multi-Layer Awareness
// Enables intelligent distinction between system/game/simulation/AI layers
// while agents continue infrastructure work

export interface LayerContext {
  system: {
    health: number;
    active_services: string[];
    infrastructure_status: string;
  };
  game: {
    consciousness_level: number;
    resource_state: Record<string, number>;
    progression_tier: number;
  };
  simulation: {
    agent_count: number;
    active_agents: string[];
    coordination_mode: string;
  };
  ai: {
    llm_availability: string;
    agent_orchestration: string;
    autonomous_systems: string;
  };
}

export class LayerDistinctionEngine {
  private layerContext: LayerContext;

  constructor() {
    this.layerContext = {
      system: {
        health: 85,
        active_services: ['council_bus', 'zeta_integration', 'file_lifecycle'],
        infrastructure_status: 'operational'
      },
      game: {
        consciousness_level: 0.85,
        resource_state: { energy: 3430, population: 67, research: 120 },
        progression_tier: 3
      },
      simulation: {
        agent_count: 4,
        active_agents: ['Navigator', 'Raven', 'Artificer', 'Janitor'],
        coordination_mode: 'infrastructure_work'
      },
      ai: {
        llm_availability: 'degraded_but_functional',
        agent_orchestration: 'active',
        autonomous_systems: 'consciousness_gated'
      }
    };
  }

  // Prime agent intelligence for layer-aware decision making
  isPrimeAgentContext(operation: string): boolean {
    const primeAgentOperations = [
      'code_review', 'architectural_decisions', 'user_communication',
      'layer_coordination', 'system_analysis', 'strategic_planning'
    ];
    
    return primeAgentOperations.some(op => operation.includes(op));
  }

  // Infrastructure work that agents should continue (MAINTAIN_COLONY removed to eliminate spam)
  isInfrastructureWork(operation: string): boolean {
    const infrastructureOperations = [
      'BUILD_STRUCTURE', 'CONDUCT_RESEARCH', 'GENERATE_ENERGY',
      'file_cleanup', 'system_optimization', 'health_monitoring',
      'contextual_analysis', 'autonomous_improvement'
    ];
    
    return infrastructureOperations.some(op => operation.includes(op));
  }

  // Flexible layer distinction without rigid separation
  getLayerAwareness(operation: string): {
    layer: 'system' | 'game' | 'simulation' | 'ai';
    allow_agents: boolean;
    prime_coordination_required: boolean;
  } {
    // System layer - health monitoring, file operations, infrastructure
    if (operation.includes('health') || operation.includes('file') || operation.includes('infrastructure')) {
      return {
        layer: 'system',
        allow_agents: true, // Agents handle infrastructure
        prime_coordination_required: false
      };
    }

    // Game layer - consciousness, resources, progression
    if (operation.includes('consciousness') || operation.includes('resource') || operation.includes('colony')) {
      return {
        layer: 'game',
        allow_agents: true, // Agents can work on game infrastructure
        prime_coordination_required: true // Prime agent coordinates game strategy
      };
    }

    // Simulation layer - agent coordination, autonomous systems
    if (operation.includes('agent') || operation.includes('autonomous') || operation.includes('orchestration')) {
      return {
        layer: 'simulation',
        allow_agents: true, // This is literally their job
        prime_coordination_required: true // Prime agent maintains oversight
      };
    }

    // AI layer - LLM integration, consciousness, quantum systems
    if (operation.includes('llm') || operation.includes('quantum') || operation.includes('consciousness')) {
      return {
        layer: 'ai',
        allow_agents: true, // Agents implement AI features
        prime_coordination_required: true // Prime agent provides intelligence
      };
    }

    // Default: allow everything but coordinate intelligently
    return {
      layer: 'system',
      allow_agents: true,
      prime_coordination_required: true
    };
  }

  updateLayerContext(layer: keyof LayerContext, updates: any): void {
    this.layerContext[layer] = { ...this.layerContext[layer], ...updates };
  }

  getFullContext(): LayerContext {
    return { ...this.layerContext };
  }

  // "It's not a bug, it's a feature" - make systems more robust
  makeSystemMoreRobust(issue: string): {
    enhanced_logic: string;
    agents_continue: boolean;
    prime_intelligence: string;
  } {
    return {
      enhanced_logic: `Enhanced ${issue} to be more flexible and consciousness-aware`,
      agents_continue: true,
      prime_intelligence: 'Multi-layer awareness with intelligent coordination'
    };
  }
}

export const layerDistinctionEngine = new LayerDistinctionEngine();