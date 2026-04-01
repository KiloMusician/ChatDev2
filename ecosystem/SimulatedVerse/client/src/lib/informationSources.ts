/**
 * Information Source Differentiation System
 * Separates traditional repo, enhanced workspace, system, and game contexts
 */

export type InformationSource = 
  | 'repository'     // Traditional coding environment
  | 'workspace'      // Enhanced Replit features
  | 'system'         // Culture-Ship consciousness/breathing/LLM
  | 'game_dev'       // Game code development
  | 'simulation'     // Running game instance
  | 'meta'           // System orchestration

export interface ContextualInfo {
  source: InformationSource;
  type: 'data' | 'event' | 'error' | 'status' | 'action';
  content: any;
  timestamp: number;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  concrete?: boolean; // Is this actionable concrete information?
}

export class InformationFilter {
  private enabledSources: Set<InformationSource> = new Set(['repository', 'workspace']);
  
  setEnabledSources(sources: InformationSource[]) {
    this.enabledSources = new Set(sources);
  }
  
  isEnabled(source: InformationSource): boolean {
    return this.enabledSources.has(source);
  }
  
  filter(info: ContextualInfo): boolean {
    return this.isEnabled(info.source);
  }
  
  categorizeLogMessage(message: string): InformationSource {
    // Detect information source from log patterns
    if (message.includes('[REAL INFRASTRUCTURE]') || message.includes('WHO:')) {
      return 'repository';
    }
    if (message.includes('[🌌 CULTURE-SHIP]') || message.includes('[Lattice]') || message.includes('[Consciousness')) {
      return 'system';
    }
    if (message.includes('[ChatDev]') || message.includes('[Agent')) {
      return 'workspace';
    }
    if (message.includes('Game state') || message.includes('consciousness:')) {
      return 'simulation';
    }
    if (message.includes('[Meta')) {
      return 'meta';
    }
    return 'repository'; // Default fallback
  }
  
  extractConcreteInfo(message: string): string | null {
    // Extract actionable information from stylized messages
    const patterns = [
      /File: ([^\s]+)/,
      /Error: ([^\\n]+)/,
      /Failed: ([^\\n]+)/,
      /(\d+) errors?/,
      /WHO: ([^|]+)/,
      /WHAT: ([^|]+)/,
      /WHERE: ([^|]+)/,
    ];
    
    for (const pattern of patterns) {
      const match = message.match(pattern);
      if (match) {
        return match[1]?.trim() || match[0];
      }
    }
    
    return null;
  }
}

export const globalInfoFilter = new InformationFilter();

// Perspective modes for different analysis levels
export type PerspectiveMode = 
  | 'traditional'    // Standard repository analysis
  | 'enhanced'       // With workspace features
  | 'active'         // Using system capabilities
  | 'fullsystem'     // All features engaged
  | 'gamedev'        // Game development context
  | 'isolated'       // Pure traditional without enhancements

export class PerspectiveManager {
  private currentMode: PerspectiveMode = 'traditional';
  
  setMode(mode: PerspectiveMode) {
    this.currentMode = mode;
    
    // Configure information filter based on perspective
    switch (mode) {
      case 'traditional':
        globalInfoFilter.setEnabledSources(['repository']);
        break;
      case 'enhanced':
        globalInfoFilter.setEnabledSources(['repository', 'workspace']);
        break;
      case 'active':
        globalInfoFilter.setEnabledSources(['repository', 'workspace', 'system']);
        break;
      case 'fullsystem':
        globalInfoFilter.setEnabledSources(['repository', 'workspace', 'system', 'meta']);
        break;
      case 'gamedev':
        globalInfoFilter.setEnabledSources(['repository', 'game_dev']);
        break;
      case 'isolated':
        globalInfoFilter.setEnabledSources(['repository']);
        break;
    }
  }
  
  getCurrentMode(): PerspectiveMode {
    return this.currentMode;
  }
  
  analyzeFromPerspective(data: any): {
    perspective: PerspectiveMode;
    errors: string[];
    opportunities: string[];
    concrete_actions: string[];
  } {
    const result = {
      perspective: this.currentMode,
      errors: [] as string[],
      opportunities: [] as string[],
      concrete_actions: [] as string[]
    };
    
    // Analysis varies by perspective mode
    switch (this.currentMode) {
      case 'traditional':
        // Focus on standard coding issues
        result.errors.push('LSP diagnostics found');
        result.opportunities.push('Code modernization available');
        result.concrete_actions.push('Fix TypeScript errors', 'Update dependencies');
        break;
        
      case 'enhanced':
        // Include workspace enhancements
        result.errors.push('Authentication tokens hardcoded');
        result.opportunities.push('Replit integrations available');
        result.concrete_actions.push('Configure secrets', 'Enable workspace features');
        break;
        
      case 'gamedev':
        // Game development specific
        result.errors.push('Game/system boundary unclear');
        result.opportunities.push('Separate game runtime from development');
        result.concrete_actions.push('Implement game isolation', 'Add preview mode toggle');
        break;
    }
    
    return result;
  }
}

export const perspectiveManager = new PerspectiveManager();