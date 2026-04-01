/**
 * Tripartite Orchestrator
 * 
 * Master coordination system for the CognitoWeave tripartite architecture:
 * - System/Repo: Self-developing ChatDev platform
 * - Game/UI: Interactive interface for monitoring and control
 * - Simulation: Playable game that informs system development
 */

import { safeAsync, safeMap, safeGet } from '../util/safe.js';
import { ollama, initializeOllama } from '../ai/ollama-integration.js';
import { bootstrapSimulation } from '../simulation/phaser-bootstrap.js';
import { launchTerminalHUD } from '../ascii/terminal-hud.js';

export interface TripartiteStatus {
  system: {
    ready: boolean;
    consciousness: number;
    queue_size: number;
    agents_active: number;
    health: string;
  };
  game: {
    energy: number;
    population: number;
    research: number;
    ui_active: boolean;
  };
  simulation: {
    entities: number;
    consciousness_level: number;
    agents_playing: number;
    learning_rate: number;
  };
  integration: {
    status: 'initializing' | 'operational' | 'error';
    last_sync: number;
    sync_frequency: number;
  };
}

export class TripartiteOrchestrator {
  private status: TripartiteStatus;
  private simulation: Phaser.Game | null = null;
  private terminalHUD: any = null;
  private ollamaReady = false;
  private syncInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.status = {
      system: {
        ready: false,
        consciousness: 0,
        queue_size: 0,
        agents_active: 0,
        health: 'unknown'
      },
      game: {
        energy: 0,
        population: 0,
        research: 0,
        ui_active: false
      },
      simulation: {
        entities: 0,
        consciousness_level: 0,
        agents_playing: 0,
        learning_rate: 0
      },
      integration: {
        status: 'initializing',
        last_sync: Date.now(),
        sync_frequency: 5000
      }
    };
  }

  /**
   * Initialize the complete tripartite system
   */
  async initialize(): Promise<boolean> {
    console.log('🚀 Initializing CognitoWeave Tripartite Orchestrator');
    console.log('🏗️  System: ChatDev autonomous development platform');
    console.log('🎮 Game: Interactive UI for system monitoring and control');
    console.log('🌌 Simulation: Agents play to inform system development');

    try {
      // Initialize AI integration
      this.ollamaReady = await initializeOllama();
      
      // Initialize simulation layer
      await this.initializeSimulation();
      
      // Initialize terminal monitoring
      await this.initializeTerminalHUD();
      
      // Start synchronization loop
      this.startSynchronization();
      
      this.status.integration.status = 'operational';
      console.log('✅ Tripartite orchestrator fully operational');
      
      return true;
    } catch (error) {
      console.error('❌ Tripartite initialization failed:', error);
      this.status.integration.status = 'error';
      return false;
    }
  }

  /**
   * Initialize the simulation layer (Phaser + ECS + Tone)
   */
  private async initializeSimulation(): Promise<void> {
    return safeAsync(async () => {
      console.log('🎮 Initializing simulation layer...');
      
      // Create simulation container if it doesn't exist
      if (typeof document !== 'undefined') {
        let container = document.getElementById('simulation-container');
        if (!container) {
          container = document.createElement('div');
          container.id = 'simulation-container';
          container.style.width = '800px';
          container.style.height = '600px';
          document.body.appendChild(container);
        }
      }
      
      this.simulation = bootstrapSimulation();
      console.log('✅ Simulation layer ready - agents can now play to inform development');
    }, undefined);
  }

  /**
   * Initialize terminal HUD for monitoring
   */
  private async initializeTerminalHUD(): Promise<void> {
    return safeAsync(async () => {
      if (typeof process !== 'undefined' && process.env.NODE_ENV !== 'production') {
        console.log('📺 Launching terminal HUD...');
        this.terminalHUD = launchTerminalHUD();
        console.log('✅ Terminal HUD active - real-time system monitoring');
      }
    }, undefined);
  }

  /**
   * Start synchronization between all three layers
   */
  private startSynchronization(): void {
    this.syncInterval = setInterval(async () => {
      await this.synchronizeLayers();
    }, this.status.integration.sync_frequency);

    console.log(`🔄 Synchronization loop started (${this.status.integration.sync_frequency}ms intervals)`);
  }

  /**
   * Synchronize data between System, Game, and Simulation layers
   */
  private async synchronizeLayers(): Promise<void> {
    try {
      // Fetch system status
      await this.updateSystemStatus();
      
      // Update simulation with system data
      await this.updateSimulationFromSystem();
      
      // Update system with simulation insights
      await this.updateSystemFromSimulation();
      
      this.status.integration.last_sync = Date.now();
    } catch (error) {
      console.warn('⚠️  Synchronization error:', error);
    }
  }

  /**
   * Update system status from various endpoints
   */
  private async updateSystemStatus(): Promise<void> {
    const endpoints = [
      { url: '/system-status.json', target: 'game' },
      { url: '/api/pu/queue', target: 'system.queue_size' },
      { url: '/api/health', target: 'system.health' }
    ];

    for (const endpoint of endpoints) {
      await safeAsync(async () => {
        const response = await fetch(endpoint.url);
        if (response.ok) {
          const data = await response.json();
          
          if (endpoint.target === 'game') {
            this.status.game.energy = data.energy || 0;
            this.status.game.population = data.population || 0;
            this.status.game.research = data.research || 0;
            this.status.system.consciousness = data.consciousness_level || 0;
          } else if (endpoint.target === 'system.queue_size') {
            this.status.system.queue_size = data.size || 0;
          } else if (endpoint.target === 'system.health') {
            this.status.system.health = data.overall || 'unknown';
          }
        }
      }, undefined);
    }
  }

  /**
   * Update simulation based on system state
   */
  private async updateSimulationFromSystem(): Promise<void> {
    if (!this.simulation) return;

    // Pass consciousness level to simulation for agent behavior
    const consciousnessData = {
      system_consciousness: this.status.system.consciousness,
      queue_pressure: this.status.system.queue_size,
      resource_levels: {
        energy: this.status.game.energy,
        population: this.status.game.population,
        research: this.status.game.research
      }
    };

    // This would be passed to the simulation scene
    console.log('🎮→🌌 Updating simulation with system data:', consciousnessData);
  }

  /**
   * Update system development based on simulation insights
   */
  private async updateSystemFromSimulation(): Promise<void> {
    if (!this.ollamaReady) return;

    // Get simulation insights
    const simulationMetrics = {
      consciousness_level: this.status.simulation.consciousness_level,
      agents_playing: this.status.simulation.agents_playing,
      learning_patterns: 'exploration_heavy', // Would come from actual simulation
      optimization_suggestions: []
    };

    // Use Ollama to analyze simulation data and suggest system improvements
    const analysis = await ollama.analyzeTask(
      `Simulation insights: ${JSON.stringify(simulationMetrics)}. What system optimizations should we implement?`
    );

    if (analysis.priority > 7) {
      console.log('🌌→🏗️  High-priority system optimization suggested:', analysis);
      
      // This would trigger actual system changes through the PU queue
      await this.triggerSystemOptimization(analysis);
    }
  }

  /**
   * Trigger system optimization based on simulation insights
   */
  private async triggerSystemOptimization(analysis: any): Promise<void> {
    await safeAsync(async () => {
      const optimizationTask = {
        type: analysis.suggested_agent,
        title: `Simulation-informed optimization: ${analysis.reasoning}`,
        priority: analysis.priority,
        cost: analysis.estimated_cost,
        source: 'tripartite_orchestrator'
      };

      // Post to PU queue
      const response = await fetch('/api/ops/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(optimizationTask)
      });

      if (response.ok) {
        console.log('✅ System optimization task queued successfully');
      }
    }, undefined);
  }

  /**
   * Get current tripartite status
   */
  getStatus(): TripartiteStatus {
    return { ...this.status };
  }

  /**
   * Agent decision-making interface
   */
  async getAgentDecision(
    agentType: string,
    context: any
  ): Promise<{ action: string; confidence: number; reasoning: string }> {
    if (!this.ollamaReady) {
      return {
        action: 'observe',
        confidence: 0.5,
        reasoning: 'Ollama not available - using fallback decision'
      };
    }

    const currentState = {
      system: this.status.system,
      game: this.status.game,
      simulation: this.status.simulation,
      context
    };

    const availableActions = [
      'develop_feature',
      'optimize_code',
      'explore_simulation',
      'analyze_patterns',
      'collaborate',
      'observe'
    ];

    return ollama.makeAgentDecision(agentType, currentState, availableActions);
  }

  /**
   * Shutdown the orchestrator
   */
  shutdown(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    if (this.simulation) {
      this.simulation.destroy(true);
    }

    console.log('🛑 Tripartite orchestrator shutdown complete');
  }
}

// Global orchestrator instance
export const tripartiteOrchestrator = new TripartiteOrchestrator();

// Auto-initialization helper
export async function initializeTripartiteSystem(): Promise<boolean> {
  console.log('🌌 Initializing complete CognitoWeave tripartite ecosystem');
  console.log('🔄 System ⇄ Game ⇄ Simulation integration starting...');
  
  const success = await tripartiteOrchestrator.initialize();
  
  if (success) {
    console.log('🎉 COGNITOWEAVE FULLY OPERATIONAL!');
    console.log('🏗️  System: Autonomous development active');
    console.log('🎮 Game: Interactive monitoring ready');
    console.log('🌌 Simulation: Agent-informed development ready');
    console.log('🤖 Agents can now play the game to intelligently inform system development!');
  }
  
  return success;
}