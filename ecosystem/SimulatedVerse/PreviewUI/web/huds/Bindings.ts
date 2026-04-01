// UI Bindings - Narrow interfaces for PreviewUI to read game state
// Bridges literal game engines to React components

export interface ResourceSnapshot {
  id: string;
  amount: number;
  generation_per_second: number;
  max_amount?: number;
  visible: boolean;
}

export interface BuildQueueItem {
  id: string;
  name: string;
  cost: Record<string, number>;
  progress: number; // 0-1
  eta_seconds?: number;
  can_afford: boolean;
}

export interface WaveInfo {
  current_wave: number;
  wave_active: boolean;
  enemies_remaining: number;
  next_wave_eta?: number;
  preview: {
    enemy_count: number;
    estimated_difficulty: number;
  };
}

export interface ResearchInfo {
  active_research?: {
    id: string;
    name: string;
    progress: number;
    eta_seconds: number;
  };
  available_techs: Array<{
    id: string;
    name: string;
    cost: Record<string, number>;
    can_afford: boolean;
    prerequisites_met: boolean;
  }>;
  completed_count: number;
}

export interface TooltipData {
  title: string;
  description: string;
  cost?: Record<string, number>;
  eta_display?: string;
  status: 'available' | 'locked' | 'coming_soon' | 'error';
  breakdown?: Array<{
    label: string;
    value: string;
    positive: boolean;
  }>;
}

class GameBindings {
  private initialized = false;
  private cache = new Map<string, { data: any, timestamp: number }>();
  private cacheTimeout = 100; // 100ms cache

  constructor() {
    this.initialize();
  }

  private async initialize() {
    if (this.initialized) return;
    
    try {
      // Initialize connections to game engines
      console.log('[Bindings] Initializing UI bindings to game engines');
      this.initialized = true;
    } catch (error) {
      console.error('[Bindings] Failed to initialize:', error);
    }
  }

  // Get current resource state
  getResources(): ResourceSnapshot[] {
    return this.getCached('resources', () => {
      // In full implementation, this would read from ResourceLedger
      return [
        {
          id: 'energy',
          amount: 150,
          generation_per_second: 2.5,
          visible: true
        },
        {
          id: 'materials', 
          amount: 25,
          generation_per_second: 0.8,
          visible: true
        },
        {
          id: 'research',
          amount: 5,
          generation_per_second: 0.2,
          visible: false // Locked until research lab built
        },
        {
          id: 'nanobots',
          amount: 0,
          generation_per_second: 0,
          visible: false // Locked until nanofab tech
        }
      ];
    });
  }

  // Get build queue status
  getBuildQueue(): BuildQueueItem[] {
    return this.getCached('build_queue', () => {
      return [
        {
          id: 'solar_panel',
          name: 'Solar Panel',
          cost: { energy: 50, materials: 10 },
          progress: 0.7,
          eta_seconds: 15,
          can_afford: true
        },
        {
          id: 'research_lab',
          name: 'Research Lab', 
          cost: { energy: 200, materials: 50 },
          progress: 0.0,
          eta_seconds: 120,
          can_afford: false
        }
      ];
    });
  }

  // Get tower defense wave info
  getWaveInfo(): WaveInfo {
    return this.getCached('wave_info', () => {
      return {
        current_wave: 3,
        wave_active: false,
        enemies_remaining: 0,
        next_wave_eta: 30,
        preview: {
          enemy_count: 8,
          estimated_difficulty: 2.1
        }
      };
    });
  }

  // Get research tree state
  getResearchInfo(): ResearchInfo {
    return this.getCached('research_info', () => {
      return {
        active_research: {
          id: 'nanobots',
          name: 'Nanobot Fabrication',
          progress: 0.65,
          eta_seconds: 45
        },
        available_techs: [
          {
            id: 'automation',
            name: 'Basic Automation',
            cost: { research: 10 },
            can_afford: false,
            prerequisites_met: true
          },
          {
            id: 'advanced_materials',
            name: 'Advanced Materials',
            cost: { research: 25 },
            can_afford: false,
            prerequisites_met: false
          }
        ],
        completed_count: 2
      };
    });
  }

  // Generate tooltip data for any game element
  getTooltip(elementType: string, elementId: string): TooltipData {
    const cacheKey = `tooltip_${elementType}_${elementId}`;
    
    return this.getCached(cacheKey, () => {
      // Default tooltip generation based on type
      switch (elementType) {
        case 'resource':
          return this.generateResourceTooltip(elementId);
        case 'building':
          return this.generateBuildingTooltip(elementId);
        case 'tech':
          return this.generateTechTooltip(elementId);
        case 'tower':
          return this.generateTowerTooltip(elementId);
        default:
          return {
            title: elementId,
            description: 'No information available',
            status: 'error' as const
          };
      }
    });
  }

  private generateResourceTooltip(resourceId: string): TooltipData {
    const resources = this.getResources();
    const resource = resources.find(r => r.id === resourceId);
    
    if (!resource) {
      return {
        title: resourceId,
        description: 'Resource not found',
        status: 'error'
      };
    }

    return {
      title: resource.id.charAt(0).toUpperCase() + resource.id.slice(1),
      description: `Current: ${resource.amount.toFixed(1)} (${resource.generation_per_second > 0 ? '+' : ''}${resource.generation_per_second.toFixed(2)}/s)`,
      status: resource.visible ? 'available' : 'locked',
      breakdown: [
        { label: 'Current Amount', value: resource.amount.toFixed(1), positive: true },
        { label: 'Generation Rate', value: `${resource.generation_per_second.toFixed(2)}/s`, positive: resource.generation_per_second > 0 },
        { label: 'Visible', value: resource.visible ? 'Yes' : 'Locked', positive: resource.visible }
      ]
    };
  }

  private generateBuildingTooltip(buildingId: string): TooltipData {
    // Mock building data - in full implementation, read from Buildings system
    const buildingData = {
      'solar_panel': {
        name: 'Solar Panel',
        cost: { energy: 50, materials: 10 },
        effect: '+1.5 energy/s',
        can_afford: true
      },
      'research_lab': {
        name: 'Research Lab',
        cost: { energy: 200, materials: 50 },
        effect: 'Enables research projects',
        can_afford: false
      }
    };

    const building = buildingData[buildingId];
    if (!building) {
      return {
        title: buildingId,
        description: 'Building not found',
        status: 'error'
      };
    }

    const costEntries = Object.entries(building.cost) as [string, number][];
    const totalCost = costEntries.reduce((sum, [_, amount]) => sum + amount, 0);

    return {
      title: building.name,
      description: building.effect,
      cost: building.cost,
      status: building.can_afford ? 'available' : 'coming_soon',
      breakdown: [
        { label: 'Effect', value: building.effect, positive: true },
        ...costEntries.map(([resource, amount]) => ({
          label: `${resource} cost`,
          value: (amount as number).toString(),
          positive: false
        }))
      ]
    };
  }

  private generateTechTooltip(techId: string): TooltipData {
    const research = this.getResearchInfo();
    const tech = research.available_techs.find(t => t.id === techId);
    
    if (!tech) {
      return {
        title: techId,
        description: 'Technology not found',
        status: 'error'
      };
    }

    return {
      title: tech.name,
      description: `Research project: ${tech.name}`,
      cost: tech.cost,
      status: tech.can_afford && tech.prerequisites_met ? 'available' : 'locked'
    };
  }

  private generateTowerTooltip(towerId: string): TooltipData {
    // Mock tower data - in full implementation, read from Tower registry
    const towerTypes = {
      'basic_tower': { name: 'Basic Tower', damage: 25, range: 100, cost: 50 },
      'rapid_tower': { name: 'Rapid Tower', damage: 15, range: 80, cost: 75 },
      'heavy_tower': { name: 'Heavy Tower', damage: 50, range: 120, cost: 100 }
    };

    const tower = towerTypes[towerId];
    if (!tower) {
      return {
        title: towerId,
        description: 'Tower type not found',
        status: 'error'
      };
    }

    return {
      title: tower.name,
      description: `Damage: ${tower.damage}, Range: ${tower.range}`,
      cost: { energy: tower.cost },
      status: 'available',
      breakdown: [
        { label: 'Damage per Shot', value: tower.damage.toString(), positive: true },
        { label: 'Range', value: tower.range.toString(), positive: true },
        { label: 'Cost', value: `${tower.cost} energy`, positive: false }
      ]
    };
  }

  // Generic caching system
  private getCached<T>(key: string, generator: () => T): T {
    const cached = this.cache.get(key);
    const now = Date.now();
    
    if (cached && (now - cached.timestamp) < this.cacheTimeout) {
      return cached.data;
    }

    const data = generator();
    this.cache.set(key, { data, timestamp: now });
    return data;
  }

  // Clear cache for specific key or all
  invalidateCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  // Get binding statistics
  getStats(): any {
    return {
      initialized: this.initialized,
      cache_entries: this.cache.size,
      last_cache_clear: 'never',
      cache_timeout_ms: this.cacheTimeout
    };
  }

  // Msg⛛ command interface for symbolic integration
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Bindings:Refresh' && parts.length === 2) {
      this.invalidateCache(parts[1]);
      return true;
    } else if (parts[0] === 'Bindings:ClearCache') {
      this.invalidateCache();
      return true;
    }
    
    return false;
  }
}

export const gameBindings = new GameBindings();