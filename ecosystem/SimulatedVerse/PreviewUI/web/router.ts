// PreviewUI/web/router.ts
// UI Router with milestone-based feature flags and seamless legacy fallback
// Implements CARD A: Entrypoint Arbitration

interface UIFlags {
  active_ui: 'legacy' | 'main';
  milestones: Record<string, boolean>;
  research_gates: Record<string, string>;
  debug: {
    force_ui: string | null;
    bypass_research: boolean;
    log_routing: boolean;
  };
}

interface RouteContext {
  ui: string | null;
  demo: string | null;
  debug: string | null;
  milestone: string | null;
}

class UIRouter {
  private flags: UIFlags | null = null;
  private context: RouteContext;

  constructor() {
    this.context = this.parseURLParams();
    this.loadFlags();
  }

  private parseURLParams(): RouteContext {
    const params = new URLSearchParams(window.location.search);
    return {
      ui: params.get('ui'),
      demo: params.get('demo'),
      debug: params.get('debug'),
      milestone: params.get('milestone')
    };
  }

  private async loadFlags(): Promise<void> {
    try {
      const response = await fetch('/SystemDev/guards/flags.json', { cache: 'no-store' });
      this.flags = await response.json();
      if (this.flags?.debug?.log_routing) {
        console.log('[UI Router] Flags loaded:', this.flags);
      }
    } catch (error) {
      console.warn('[UI Router] Could not load flags, using defaults:', error);
      this.flags = {
        active_ui: 'legacy',
        milestones: { UI_M0_BOOT: true },
        research_gates: {},
        debug: { force_ui: null, bypass_research: false, log_routing: true }
      };
    }
  }

  /**
   * Determine which UI to show based on URL params and feature flags
   */
  public resolveUI(): 'legacy' | 'main' | 'demo' {
    if (!this.flags) {
      console.warn('[UI Router] Flags not loaded, defaulting to legacy');
      return 'legacy';
    }

    // Debug override
    if (this.flags.debug.force_ui) {
      if (this.flags.debug.log_routing) {
        console.log(`[UI Router] Debug force override: ${this.flags.debug.force_ui}`);
      }
      return this.flags.debug.force_ui as 'legacy' | 'main' | 'demo';
    }

    // URL parameter override
    if (this.context.ui) {
      if (this.flags.debug.log_routing) {
        console.log(`[UI Router] URL override: ${this.context.ui}`);
      }
      
      if (this.context.demo === '1') {
        return 'demo';
      }
      
      return this.context.ui as 'legacy' | 'main';
    }

    // Milestone-based routing
    if (this.context.milestone && this.flags.milestones[this.context.milestone]) {
      if (this.flags.debug.log_routing) {
        console.log(`[UI Router] Milestone unlock: ${this.context.milestone}`);
      }
      return 'main';
    }

    // Default from flags
    const resolved = this.flags.active_ui;
    if (this.flags.debug.log_routing) {
      console.log(`[UI Router] Default resolution: ${resolved}`);
    }
    
    return resolved;
  }

  /**
   * Check if a UI milestone is unlocked
   */
  public isMilestoneUnlocked(milestone: string): boolean {
    return this.flags?.milestones[milestone] || false;
  }

  /**
   * Get the highest unlocked milestone
   */
  public getHighestMilestone(): string | null {
    if (!this.flags) return null;

    const milestones = ['UI_M0_BOOT', 'UI_M1_PANELS', 'UI_M2_ADVISOR', 'UI_M3_HOLO', 'UI_M4_CHATDEV', 'UI_M5_COMPOSER'];
    
    for (let i = milestones.length - 1; i >= 0; i--) {
      if (this.flags.milestones[milestones[i]]) {
        return milestones[i];
      }
    }
    
    return null;
  }

  /**
   * Navigate to a specific UI mode
   */
  public navigate(ui: 'legacy' | 'main' | 'demo', options: {
    demo?: boolean;
    milestone?: string;
    preserveState?: boolean;
  } = {}): void {
    const params = new URLSearchParams();
    
    params.set('ui', ui);
    
    if (options.demo) {
      params.set('demo', '1');
    }
    
    if (options.milestone) {
      params.set('milestone', options.milestone);
    }

    // Preserve simulation state if requested
    if (options.preserveState) {
      const currentState = this.getSimulationSnapshot();
      if (currentState) {
        localStorage.setItem('simSnapshot', JSON.stringify(currentState));
      }
    }

    const newURL = `${window.location.pathname}?${params.toString()}`;
    
    if (this.flags?.debug?.log_routing) {
      console.log(`[UI Router] Navigating to: ${newURL}`);
    }
    
    window.location.href = newURL;
  }

  /**
   * Get current simulation state for preservation
   */
  private getSimulationSnapshot(): any {
    // Try to extract current game state from various possible sources
    const sources = [
      () => (window as any).__GAME_STATE,
      () => (window as any).gameState,
      () => JSON.parse(localStorage.getItem('gameState') || '{}'),
      () => (window as any).colony?.getState?.()
    ];

    for (const source of sources) {
      try {
        const state = source();
        if (state && typeof state === 'object') {
          return {
            ...state,
            timestamp: Date.now(),
            ui_context: this.context
          };
        }
      } catch (error) {
        // Continue to next source
      }
    }

    return null;
  }

  /**
   * Restore simulation state from snapshot
   */
  public restoreSimulationState(): any {
    try {
      const snapshot = localStorage.getItem('simSnapshot');
      if (snapshot) {
        const state = JSON.parse(snapshot);
        console.log('[UI Router] Restored simulation state:', state);
        return state;
      }
    } catch (error) {
      console.warn('[UI Router] Could not restore simulation state:', error);
    }
    return null;
  }

  /**
   * Create a "Return to Dev Menu" button
   */
  public createReturnButton(parent: HTMLElement): void {
    const button = document.createElement('button');
    button.textContent = '← Return to Dev Menu';
    button.className = 'ui-router-return-btn';
    button.style.cssText = `
      position: fixed;
      top: 10px;
      left: 10px;
      z-index: 9999;
      padding: 8px 16px;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      border: 1px solid #333;
      border-radius: 4px;
      cursor: pointer;
      font-family: monospace;
      font-size: 12px;
    `;

    button.addEventListener('click', () => {
      this.navigate('legacy', { preserveState: true });
    });

    parent.appendChild(button);
  }

  /**
   * Emit routing receipt for agent tracking
   */
  public emitReceipt(ui: string, milestone?: string): void {
    const receipt = {
      timestamp: Date.now(),
      action: 'ui_route',
      from: this.flags?.active_ui || 'unknown',
      to: ui,
      milestone: milestone || this.getHighestMilestone(),
      context: this.context,
      flags_state: this.flags
    };

    // Emit to Council Bus if available
    if ((window as any).councilBus) {
      (window as any).councilBus.publish('ui.route.change', receipt);
    }

    // Store receipt
    try {
      fetch('/api/council-bus/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: 'ui.router.receipt',
          payload: receipt
        })
      }).catch(console.warn);
    } catch (error) {
      console.warn('[UI Router] Could not emit receipt:', error);
    }

    console.log('[UI Router] Receipt emitted:', receipt);
  }
}

// Export singleton instance
export const uiRouter = new UIRouter();

// Global access for legacy compatibility
(window as any).uiRouter = uiRouter;