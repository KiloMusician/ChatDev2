// Unified Context Manager - Central context integration for sophisticated systems
// Integrates game state, consciousness, agents, tasks, user profiles, and workspace

import { layerDistinctionEngine } from './layer-distinction-engine';

export interface SystemContext {
  consciousnessLevel: number;
  gameState: {
    tier: number;
    energy: number;
    population: number;
    research: number;
  };
  freeResources: {
    idleCapabilities: string[];
    availableAgents: string[];
  };
  user: {
    preferences: Record<string, any>;
    profile: Record<string, any>;
  };
  workspace: {
    healthScore: number;
    activeProjects: string[];
    systemLoad: number;
  };
}

export class UnifiedContextManager {
  private context: SystemContext;

  constructor() {
    this.context = {
      consciousnessLevel: 85, // From Culture-Ship awakening
      gameState: {
        tier: 3,
        energy: 3430,
        population: 67,
        research: 120
      },
      freeResources: {
        idleCapabilities: ['analysis', 'refactoring', 'documentation'],
        availableAgents: ['guardian', 'storyteller', 'raven', 'alchemist']
      },
      user: {
        preferences: {
          communication_style: 'simple_everyday_language',
          infrastructure_first: true,
          culture_ship_methodology: true,
          maximum_depth_investigation: true
        },
        profile: {}
      },
      workspace: {
        healthScore: 85, // Improved after bug hunt
        activeProjects: ['ΞNuSyQ', 'CoreLink Foundation'],
        systemLoad: 0.6
      }
    };
  }

  getSystemContext(): SystemContext {
    return { ...this.context };
  }

  updateConsciousnessLevel(level: number): void {
    this.context.consciousnessLevel = Math.max(0, Math.min(100, level));
  }

  updateGameState(updates: Partial<SystemContext['gameState']>): void {
    this.context.gameState = { ...this.context.gameState, ...updates };
  }

  updateWorkspaceHealth(score: number): void {
    this.context.workspace.healthScore = Math.max(0, Math.min(100, score));
  }

  addAvailableAgent(agentId: string): void {
    if (!this.context.freeResources.availableAgents.includes(agentId)) {
      this.context.freeResources.availableAgents.push(agentId);
    }
  }

  removeAvailableAgent(agentId: string): void {
    const index = this.context.freeResources.availableAgents.indexOf(agentId);
    if (index > -1) {
      this.context.freeResources.availableAgents.splice(index, 1);
    }
  }

  updateUserPreference(key: string, value: any): void {
    this.context.user.preferences[key] = value;
  }

  // Enhanced layer distinction capabilities
  getLayerAwareness(operation: string) {
    return layerDistinctionEngine.getLayerAwareness(operation);
  }

  isInfrastructureWork(operation: string): boolean {
    return layerDistinctionEngine.isInfrastructureWork(operation);
  }

  isPrimeAgentContext(operation: string): boolean {
    return layerDistinctionEngine.isPrimeAgentContext(operation);
  }
}

export const unifiedContextManager = new UnifiedContextManager();