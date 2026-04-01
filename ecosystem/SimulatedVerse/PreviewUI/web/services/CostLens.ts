// PreviewUI/web/services/CostLens.ts
// Cost and Unlock Lens Services for unified UI state querying
// Implements CARD D: Tooltip & Cost Lenses

export interface CostEntry {
  type: 'resource' | 'research' | 'building' | 'agent' | 'time' | 'energy';
  id: string;
  amount: number;
  current?: number;
  available?: boolean;
  label?: string;
}

export interface UnlockRequirement {
  type: 'research' | 'building' | 'resource' | 'milestone' | 'story_beat';
  id: string;
  label: string;
  satisfied: boolean;
  progress?: number;
  total?: number;
}

export interface LensResult {
  available: boolean;
  costs: CostEntry[];
  requirements: UnlockRequirement[];
  description: string;
  category: string;
  tier: number;
  tooltip: string;
  preview_effects?: string[];
  warnings?: string[];
}

export class CostLens {
  protected costTables: Map<string, any> = new Map();
  private currentState: any = null;

  constructor() {
    this.loadCostTables();
  }

  private async loadCostTables(): Promise<void> {
    try {
      const tables = [
        'buildings',
        'research', 
        'agents',
        'qol_features',
        'upgrades'
      ];

      for (const table of tables) {
        try {
          const response = await fetch(`/GameDev/content/cost_tables/${table}.json`, { cache: 'no-store' });
          const data = await response.json();
          this.costTables.set(table, data);
          console.log(`[CostLens] Loaded ${table} cost table`);
        } catch (error) {
          console.warn(`[CostLens] Could not load ${table} cost table:`, error);
          // Create default table
          this.costTables.set(table, this.getDefaultTable(table));
        }
      }
    } catch (error) {
      console.warn('[CostLens] Failed to load cost tables:', error);
    }
  }

  private getDefaultTable(tableName: string): any {
    const defaults: Record<string, any> = {
      buildings: {
        'basic_shelter': {
          costs: [{ type: 'resource', id: 'materials', amount: 50 }],
          tier: 0,
          category: 'survival',
          description: 'Basic protection from the elements'
        },
        'power_generator': {
          costs: [
            { type: 'resource', id: 'materials', amount: 100 },
            { type: 'resource', id: 'components', amount: 25 }
          ],
          requirements: [{ type: 'research', id: 'basic_power' }],
          tier: 1,
          category: 'power',
          description: 'Generates electrical power for the colony'
        }
      },
      research: {
        'basic_power': {
          costs: [{ type: 'research', id: 'points', amount: 100 }],
          tier: 0,
          category: 'foundation',
          description: 'Unlocks basic power generation and distribution'
        },
        'cognitics.nanofab_online': {
          costs: [{ type: 'research', id: 'points', amount: 500 }],
          requirements: [{ type: 'research', id: 'basic_power' }],
          tier: 1,
          category: 'cognitics',
          description: 'Advanced nanofabrication unlocks improved UI panels'
        }
      },
      qol_features: {
        'tooltips_plus': {
          costs: [{ type: 'research', id: 'points', amount: 50 }],
          requirements: [{ type: 'milestone', id: 'UI_M1_PANELS' }],
          tier: 1,
          category: 'ui_qol',
          description: 'Enhanced tooltips with detailed information and cost breakdowns'
        },
        'batch_buy': {
          costs: [{ type: 'research', id: 'points', amount: 75 }],
          requirements: [{ type: 'milestone', id: 'UI_M1_PANELS' }],
          tier: 1,
          category: 'ui_qol',
          description: 'Purchase multiple items at once with quantity selectors'
        }
      }
    };

    return defaults[tableName] || {};
  }

  /**
   * Update current state for lens calculations
   */
  updateState(state: any): void {
    this.currentState = state;
  }

  /**
   * Preview costs and requirements for an item
   */
  preview(category: string, itemId: string): LensResult {
    const table = this.costTables.get(category);
    if (!table || !table[itemId]) {
      return this.createNotFoundResult(category, itemId);
    }

    const item = table[itemId];
    const costs = this.evaluateCosts(item.costs || []);
    const requirements = this.evaluateRequirements(item.requirements || []);
    const available = this.isAvailable(costs, requirements);

    return {
      available,
      costs,
      requirements,
      description: item.description || `${category}:${itemId}`,
      category: item.category || category,
      tier: item.tier || 0,
      tooltip: this.generateTooltip(item, costs, requirements, available),
      preview_effects: item.effects || [],
      warnings: this.generateWarnings(costs, requirements)
    };
  }

  private evaluateCosts(costSpecs: any[]): CostEntry[] {
    return costSpecs.map(spec => {
      const cost: CostEntry = {
        type: spec.type,
        id: spec.id,
        amount: spec.amount,
        label: this.getCostLabel(spec.type, spec.id)
      };

      // Add current availability info
      if (this.currentState) {
        cost.current = this.getCurrentAmount(spec.type, spec.id);
        cost.available = (cost.current || 0) >= cost.amount;
      }

      return cost;
    });
  }

  private evaluateRequirements(reqSpecs: any[]): UnlockRequirement[] {
    return reqSpecs.map(spec => {
      const req: UnlockRequirement = {
        type: spec.type,
        id: spec.id,
        label: this.getRequirementLabel(spec.type, spec.id),
        satisfied: false
      };

      if (this.currentState) {
        req.satisfied = this.isRequirementSatisfied(spec.type, spec.id);
        
        if (spec.type === 'research' && this.currentState.research) {
          const project = this.currentState.research.active_projects?.find((p: any) => p.id === spec.id);
          if (project) {
            req.progress = project.progress;
            req.total = project.total_cost;
          }
        }
      }

      return req;
    });
  }

  private getCurrentAmount(type: string, id: string): number {
    if (!this.currentState) return 0;

    switch (type) {
      case 'resource':
        return this.currentState.resources?.[id] || 0;
      case 'research':
        return this.currentState.core?.research || 0;
      case 'energy':
        return this.currentState.core?.energy || 0;
      default:
        return 0;
    }
  }

  private isRequirementSatisfied(type: string, id: string): boolean {
    if (!this.currentState) return false;

    switch (type) {
      case 'research':
        return this.currentState.research?.completed?.includes(id) || false;
      case 'building':
        return this.currentState.infrastructure?.buildings?.some((b: any) => b.type === id) || false;
      case 'milestone':
        // Check UI milestone flags
        return this.checkMilestone(id);
      default:
        return false;
    }
  }

  private checkMilestone(milestoneId: string): boolean {
    // Integration with UI router flags
    if ((window as any).uiRouter) {
      return (window as any).uiRouter.isMilestoneUnlocked(milestoneId);
    }
    return false;
  }

  private isAvailable(costs: CostEntry[], requirements: UnlockRequirement[]): boolean {
    const costsAffordable = costs.every(cost => cost.available !== false);
    const requirementsMet = requirements.every(req => req.satisfied);
    return costsAffordable && requirementsMet;
  }

  private generateTooltip(item: any, costs: CostEntry[], requirements: UnlockRequirement[], available: boolean): string {
    let tooltip = item.description || '';
    
    if (costs.length > 0) {
      tooltip += '\n\nCosts:';
      costs.forEach(cost => {
        const status = cost.available ? '✓' : '✗';
        tooltip += `\n${status} ${cost.label}: ${cost.amount}`;
        if (cost.current !== undefined) {
          tooltip += ` (have: ${cost.current})`;
        }
      });
    }

    if (requirements.length > 0) {
      tooltip += '\n\nRequirements:';
      requirements.forEach(req => {
        const status = req.satisfied ? '✓' : '✗';
        tooltip += `\n${status} ${req.label}`;
        if (req.progress !== undefined && req.total !== undefined) {
          tooltip += ` (${req.progress}/${req.total})`;
        }
      });
    }

    if (!available) {
      tooltip += '\n\n⚠️ Not available yet';
    }

    return tooltip;
  }

  private generateWarnings(costs: CostEntry[], requirements: UnlockRequirement[]): string[] {
    const warnings: string[] = [];

    // Check for expensive costs
    costs.forEach(cost => {
      if (cost.type === 'resource' && cost.amount > 1000) {
        warnings.push(`High ${cost.label} cost (${cost.amount})`);
      }
    });

    // Check for complex requirements
    const unsatisfiedReqs = requirements.filter(req => !req.satisfied);
    if (unsatisfiedReqs.length > 2) {
      warnings.push(`Multiple requirements needed (${unsatisfiedReqs.length})`);
    }

    return warnings;
  }

  private getCostLabel(type: string, id: string): string {
    const labels: Record<string, Record<string, string>> = {
      resource: {
        materials: 'Materials',
        components: 'Components',
        energy: 'Energy',
        food: 'Food',
        medicine: 'Medicine'
      },
      research: {
        points: 'Research Points'
      }
    };

    return labels[type]?.[id] || `${type}:${id}`;
  }

  private getRequirementLabel(type: string, id: string): string {
    const labels: Record<string, Record<string, string>> = {
      research: {
        'basic_power': 'Basic Power Research',
        'cognitics.nanofab_online': 'Nanofab Technology'
      },
      milestone: {
        'UI_M1_PANELS': 'Panelized Interface',
        'UI_M2_ADVISOR': 'AI Advisor System'
      }
    };

    return labels[type]?.[id] || `${type}:${id}`;
  }

  private createNotFoundResult(category: string, itemId: string): LensResult {
    return {
      available: false,
      costs: [],
      requirements: [],
      description: `Unknown ${category}: ${itemId}`,
      category,
      tier: 0,
      tooltip: `Item not found: ${category}:${itemId}`,
      warnings: ['Item definition not found']
    };
  }
}

export class UnlockLens extends CostLens {
  /**
   * Check what can be unlocked right now
   */
  getAvailableUnlocks(category?: string): Array<{id: string, result: LensResult}> {
    const available: Array<{id: string, result: LensResult}> = [];
    
    for (const [tableName, table] of this.costTables) {
      if (category && tableName !== category) continue;
      
      for (const itemId of Object.keys(table)) {
        const result = this.preview(tableName, itemId);
        if (result.available) {
          available.push({ id: itemId, result });
        }
      }
    }

    return available.sort((a, b) => a.result.tier - b.result.tier);
  }

  /**
   * Get next tier unlocks (what becomes available after current research)
   */
  getNextTierUnlocks(): Array<{id: string, result: LensResult}> {
    const nextTier: Array<{id: string, result: LensResult}> = [];
    
    for (const [tableName, table] of this.costTables) {
      for (const itemId of Object.keys(table)) {
        const result = this.preview(tableName, itemId);
        
        if (!result.available) {
          // Check if only one or two requirements are missing
          const unsatisfiedReqs = result.requirements.filter(req => !req.satisfied);
          if (unsatisfiedReqs.length <= 2) {
            nextTier.push({ id: itemId, result });
          }
        }
      }
    }

    return nextTier.sort((a, b) => a.result.tier - b.result.tier);
  }
}

// Export singleton instances
export const costLens = new CostLens();
export const unlockLens = new UnlockLens();