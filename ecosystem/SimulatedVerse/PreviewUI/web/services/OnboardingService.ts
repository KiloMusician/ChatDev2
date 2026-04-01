/**
 * Interactive Onboarding Service
 * Manages onboarding flows with Culture-Ship consciousness integration
 */

import { OnboardingFlow, OnboardingStep } from '../components/InteractiveTooltip';
import { PlayerState } from '../core/store';

export interface OnboardingState {
  active_flow: string | null;
  current_step: number;
  completed_flows: string[];
  skipped_steps: string[];
  user_preferences: {
    auto_skip_completed: boolean;
    show_action_hints: boolean;
    reduce_animations: boolean;
  };
}

export class OnboardingService {
  private flows = new Map<string, OnboardingFlow>();
  private state: OnboardingState;
  private listeners = new Set<(state: OnboardingState) => void>();
  
  constructor() {
    this.state = this.getDefaultState();
    this.initializeFlows();
    console.log('[Onboarding] Service initialized with', this.flows.size, 'flows');
  }

  private getDefaultState(): OnboardingState {
    const saved = localStorage.getItem('corelink_onboarding');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.warn('[Onboarding] Failed to load saved state, using defaults');
      }
    }
    
    return {
      active_flow: null,
      current_step: 0,
      completed_flows: [],
      skipped_steps: [],
      user_preferences: {
        auto_skip_completed: true,
        show_action_hints: true,
        reduce_animations: false
      }
    };
  }

  private saveState(): void {
    localStorage.setItem('corelink_onboarding', JSON.stringify(this.state));
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  private initializeFlows(): void {
    // Dev Menu Onboarding
    this.flows.set('dev_menu_basics', {
      id: 'dev_menu_basics',
      name: 'Culture-Ship Dev Interface',
      trigger_mode: 'DEV',
      steps: [
        {
          id: 'welcome_dev',
          title: 'Welcome to the Culture-Ship',
          content: 'This is your development interface. Here you can monitor systems, test features, and access advanced tools.',
          target: '[data-testid="dev-menu-container"], .dev-menu, .p-4', // Fallback selectors
          position: 'bottom',
          action: 'observe'
        },
        {
          id: 'play_mode_switch',
          title: 'Play Mode Toggle',
          content: 'Switch to Play Mode to experience the Culture-Ship interface as intended. You can return here anytime.',
          target: 'button:contains("Enter Play Mode"), [data-testid="enter-play-mode"]',
          position: 'bottom',
          action: 'click',
          highlight: true
        },
        {
          id: 'dev_tools_overview',
          title: 'Development Tools',
          content: 'The extended dev menu provides access to game state, testing tools, and system monitoring.',
          target: '[data-testid="dev-menu-extended"], .dev-extended',
          position: 'right',
          action: 'observe'
        }
      ],
      completion_flag: 'ONBOARDING_DEV_COMPLETE'
    });

    // Game Interface Onboarding
    this.flows.set('game_interface_intro', {
      id: 'game_interface_intro',
      name: 'Culture-Ship Navigation',
      trigger_mode: 'PLAY',
      steps: [
        {
          id: 'ship_systems_nav',
          title: 'Ship Systems Navigation',
          content: 'This sidebar provides access to all Culture-Ship systems. Each system unlocks as you progress.',
          target: '.w-64, [data-testid="ship-systems-nav"]',
          position: 'right',
          action: 'observe'
        },
        {
          id: 'game_engine_access',
          title: 'Multi-Renderer Game Engine',
          content: 'Access the game engine with support for ASCII, Pixel, and Vector rendering. Perfect for testing different game genres.',
          target: 'button:contains("Multi-Renderer Engine"), [data-testid="game-engine-button"]',
          position: 'right',
          action: 'click',
          highlight: true
        },
        {
          id: 'dev_mode_return',
          title: 'Return to Dev Mode',
          content: 'Click "Return to Dev" anytime to access development tools and system monitoring.',
          target: 'button:contains("Return to Dev"), [data-testid="return-dev-button"]',
          position: 'right',
          action: 'observe'
        }
      ],
      completion_flag: 'ONBOARDING_GAME_COMPLETE'
    });

    // Game Engine Onboarding
    this.flows.set('game_engine_tour', {
      id: 'game_engine_tour',
      name: 'Multi-Renderer Engine Tour',
      trigger_mode: 'PLAY',
      trigger_phase: ['GAME_ENGINE'],
      steps: [
        {
          id: 'renderer_selector',
          title: 'Renderer Selection',
          content: 'Switch between ASCII, Pixel, and Vector rendering modes. Each offers different visual experiences for the same game logic.',
          target: '[data-testid="renderer-selector"], .renderer-toggle',
          position: 'bottom',
          action: 'click',
          highlight: true
        },
        {
          id: 'game_mode_selector',
          title: 'Game Genre Selection',
          content: 'Choose between Roguelike dungeon crawling, Tower Defense, or Colony Simulation. Each uses the same engine core.',
          target: '[data-testid="game-mode-selector"], .game-mode-toggle',
          position: 'bottom',
          action: 'click',
          highlight: true
        },
        {
          id: 'seed_controls',
          title: 'Deterministic Seeds',
          content: 'Enter a seed for reproducible gameplay. The same seed always generates identical worlds and scenarios.',
          target: '[data-testid="seed-input"], input[placeholder*="seed"]',
          position: 'top',
          action: 'input'
        },
        {
          id: 'game_viewport',
          title: 'Game Viewport',
          content: 'The main game area renders your selected genre. Use WASD or arrow keys to interact in most games.',
          target: '[data-testid="game-viewport"], canvas, .game-area',
          position: 'left',
          action: 'observe'
        }
      ],
      completion_flag: 'ONBOARDING_ENGINE_COMPLETE'
    });
  }

  // Public API
  startFlow(flowId: string, playerState?: PlayerState): boolean {
    const flow = this.flows.get(flowId);
    if (!flow) {
      console.warn(`[Onboarding] Unknown flow: ${flowId}`);
      return false;
    }
    
    // Check if already completed and user prefers to skip
    if (this.state.user_preferences.auto_skip_completed && 
        this.state.completed_flows.includes(flowId)) {
      console.log(`[Onboarding] Skipping completed flow: ${flowId}`);
      return false;
    }
    
    // Check completion flag if available
    if (flow.completion_flag && playerState?.hasFlag) {
      const flagExists = playerState.flags[flow.completion_flag as keyof typeof playerState.flags];
      if (flagExists) {
        console.log(`[Onboarding] Flow already completed via flag: ${flow.completion_flag}`);
        return false;
      }
    }
    
    this.state.active_flow = flowId;
    this.state.current_step = 0;
    this.saveState();
    this.notifyListeners();
    
    console.log(`[Onboarding] Started flow: ${flow.name}`);
    return true;
  }

  nextStep(): boolean {
    if (!this.state.active_flow) return false;
    
    const flow = this.flows.get(this.state.active_flow);
    if (!flow) return false;
    
    if (this.state.current_step < flow.steps.length - 1) {
      this.state.current_step++;
      this.saveState();
      this.notifyListeners();
      return true;
    } else {
      // Complete the flow
      this.completeCurrentFlow();
      return false;
    }
  }

  previousStep(): boolean {
    if (!this.state.active_flow || this.state.current_step <= 0) return false;
    
    this.state.current_step--;
    this.saveState();
    this.notifyListeners();
    return true;
  }

  skipCurrentStep(): void {
    if (!this.state.active_flow) return;
    
    const flow = this.flows.get(this.state.active_flow);
    if (!flow) return;
    
    const currentStepId = flow.steps[this.state.current_step]?.id;
    if (currentStepId) {
      this.state.skipped_steps.push(currentStepId);
    }
    
    this.nextStep();
  }

  completeCurrentFlow(): void {
    if (!this.state.active_flow) return;
    
    const flowId = this.state.active_flow;
    this.state.completed_flows.push(flowId);
    this.state.active_flow = null;
    this.state.current_step = 0;
    this.saveState();
    this.notifyListeners();
    
    console.log(`[Onboarding] Completed flow: ${flowId}`);
  }

  closeFlow(): void {
    this.state.active_flow = null;
    this.state.current_step = 0;
    this.saveState();
    this.notifyListeners();
  }

  // Auto-trigger based on mode/phase changes
  checkAutoTrigger(mode: 'DEV' | 'PLAY', phase?: string): string | null {
    for (const [flowId, flow] of this.flows.entries()) {
      // Skip completed flows if user prefers
      if (this.state.user_preferences.auto_skip_completed && 
          this.state.completed_flows.includes(flowId)) {
        continue;
      }
      
      // Check mode match
      if (flow.trigger_mode !== 'BOTH' && flow.trigger_mode !== mode) {
        continue;
      }
      
      // Check phase match
      if (flow.trigger_phase && phase && !flow.trigger_phase.includes(phase)) {
        continue;
      }
      
      // This flow should trigger
      return flowId;
    }
    
    return null;
  }

  // State accessors
  getCurrentFlow(): OnboardingFlow | null {
    if (!this.state.active_flow) return null;
    return this.flows.get(this.state.active_flow) || null;
  }

  getCurrentStep(): OnboardingStep | null {
    const flow = this.getCurrentFlow();
    if (!flow) return null;
    return flow.steps[this.state.current_step] || null;
  }

  getState(): OnboardingState {
    return { ...this.state };
  }

  isActive(): boolean {
    return this.state.active_flow !== null;
  }

  // Subscribe to state changes
  subscribe(listener: (state: OnboardingState) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // Admin functions
  resetFlow(flowId: string): void {
    this.state.completed_flows = this.state.completed_flows.filter(f => f !== flowId);
    this.state.skipped_steps = this.state.skipped_steps.filter(s => !s.startsWith(flowId));
    this.saveState();
    this.notifyListeners();
  }

  resetAllOnboarding(): void {
    this.state = this.getDefaultState();
    this.saveState();
    this.notifyListeners();
    console.log('[Onboarding] All onboarding data reset');
  }

  // Add custom flow at runtime
  addCustomFlow(flow: OnboardingFlow): void {
    this.flows.set(flow.id, flow);
    console.log(`[Onboarding] Added custom flow: ${flow.name}`);
  }

  // Validation and health checks
  validateCurrentStep(): boolean {
    const step = this.getCurrentStep();
    if (!step) return true;
    
    // Check if target element exists
    const target = document.querySelector(step.target);
    if (!target) {
      console.warn(`[Onboarding] Step validation failed - target not found: ${step.target}`);
      return false;
    }
    
    // Run custom validation if provided
    if (step.validation) {
      return step.validation();
    }
    
    return true;
  }

  // Get available flows for current context
  getAvailableFlows(mode: 'DEV' | 'PLAY', phase?: string): OnboardingFlow[] {
    return Array.from(this.flows.values()).filter(flow => {
      // Check mode compatibility
      if (flow.trigger_mode !== 'BOTH' && flow.trigger_mode !== mode) {
        return false;
      }
      
      // Check phase compatibility
      if (flow.trigger_phase && phase && !flow.trigger_phase.includes(phase)) {
        return false;
      }
      
      return true;
    });
  }

  // Analytics and insights
  getCompletionStats(): {
    total_flows: number;
    completed: number;
    completion_rate: number;
    most_skipped_steps: string[];
  } {
    const totalFlows = this.flows.size;
    const completed = this.state.completed_flows.length;
    
    // Count skipped steps
    const skipCounts = new Map<string, number>();
    this.state.skipped_steps.forEach(stepId => {
      skipCounts.set(stepId, (skipCounts.get(stepId) || 0) + 1);
    });
    
    const mostSkipped = Array.from(skipCounts.entries())
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([stepId]) => stepId);
    
    return {
      total_flows: totalFlows,
      completed,
      completion_rate: totalFlows > 0 ? completed / totalFlows : 0,
      most_skipped_steps: mostSkipped
    };
  }
}

export const onboardingService = new OnboardingService();
