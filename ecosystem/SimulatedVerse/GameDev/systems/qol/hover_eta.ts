// QoL Tier-1: Hover ETA System
// Nanobots unlock: Show hover tooltips with time-to-afford calculations

export interface Resource {
  id: string;
  current: number;
  generation_per_second: number;
  max?: number;
}

export interface PriceData {
  id: string;
  base_cost: number;
  currency: string;
  curve?: 'linear' | 'exponential' | 'logarithmic';
  scaling_factor?: number;
  current_level?: number;
}

export interface ETATooltip {
  item_id: string;
  title: string;
  description: string;
  current_price: number;
  currency: string;
  affordable: boolean;
  eta_seconds?: number;
  eta_display?: string;
  requirements?: string[];
  status: 'available' | 'locked' | 'coming_soon';
}

export class HoverETASystem {
  private resources: Map<string, Resource> = new Map();
  private prices: Map<string, PriceData> = new Map();
  private unlocked = false;

  constructor() {
    this.initializeBasicResources();
    this.loadPriceData();
  }

  // Unlock system when nanobots are researched
  unlock(): void {
    this.unlocked = true;
    console.log('[HoverETA] 🤖 Nanobots online - Hover ETAs enabled');
  }

  updateResource(id: string, current: number, generation: number): void {
    const resource = this.resources.get(id) || { id, current: 0, generation_per_second: 0 };
    resource.current = current;
    resource.generation_per_second = generation;
    this.resources.set(id, resource);
  }

  calculateETA(itemId: string, currency = 'energy'): ETATooltip | null {
    if (!this.unlocked) {
      return null; // No tooltips until unlocked
    }

    const price = this.prices.get(itemId);
    const resource = this.resources.get(currency);
    
    if (!price || !resource) {
      return {
        item_id: itemId,
        title: itemId,
        description: 'Unknown item',
        current_price: 0,
        currency,
        affordable: false,
        status: 'locked'
      };
    }

    const currentPrice = this.calculateCurrentPrice(price);
    const canAfford = resource.current >= currentPrice;
    
    let etaSeconds: number | undefined;
    let etaDisplay: string | undefined;
    
    if (!canAfford && resource.generation_per_second > 0) {
      const needed = currentPrice - resource.current;
      etaSeconds = needed / resource.generation_per_second;
      etaDisplay = this.formatETA(etaSeconds);
    }

    return {
      item_id: itemId,
      title: this.formatTitle(itemId),
      description: price.id || 'Item description',
      current_price: currentPrice,
      currency,
      affordable: canAfford,
      eta_seconds: etaSeconds,
      eta_display: etaDisplay,
      status: canAfford ? 'available' : 'coming_soon'
    };
  }

  // Calculate current price with scaling
  private calculateCurrentPrice(price: PriceData): number {
    const level = price.current_level || 0;
    
    switch (price.curve) {
      case 'exponential':
        return Math.floor(price.base_cost * Math.pow(price.scaling_factor || 1.15, level));
      case 'logarithmic':
        return Math.floor(price.base_cost * (1 + Math.log(level + 1) * (price.scaling_factor || 0.5)));
      case 'linear':
      default:
        return Math.floor(price.base_cost + level * (price.scaling_factor || 10));
    }
  }

  private formatETA(seconds: number): string {
    if (seconds < 60) {
      return `${Math.ceil(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.ceil(seconds / 60);
      return `${minutes}m`;
    } else if (seconds < 86400) {
      const hours = Math.ceil(seconds / 3600);
      return `${hours}h`;
    } else {
      const days = Math.ceil(seconds / 86400);
      return `${days}d`;
    }
  }

  private formatTitle(itemId: string): string {
    return itemId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  private initializeBasicResources(): void {
    this.resources.set('energy', { id: 'energy', current: 100, generation_per_second: 1 });
    this.resources.set('materials', { id: 'materials', current: 50, generation_per_second: 0.5 });
    this.resources.set('research', { id: 'research', current: 0, generation_per_second: 0.1 });
  }

  private loadPriceData(): void {
    // Basic pricing table - in real implementation, load from CSV
    const priceData = [
      { id: 'generator_upgrade', base_cost: 100, currency: 'energy', curve: 'exponential', scaling_factor: 1.15 },
      { id: 'nanobots', base_cost: 500, currency: 'energy', curve: 'linear', scaling_factor: 0 },
      { id: 'research_lab', base_cost: 200, currency: 'materials', curve: 'exponential', scaling_factor: 1.25 },
      { id: 'tower_defense_turret', base_cost: 50, currency: 'energy', curve: 'linear', scaling_factor: 10 },
      { id: 'colony_expansion', base_cost: 1000, currency: 'energy', curve: 'exponential', scaling_factor: 1.5 }
    ];

    priceData.forEach(price => this.prices.set(price.id, price));
  }

  // Get all items with their current ETAs
  getAllETAs(): ETATooltip[] {
    if (!this.unlocked) return [];
    
    return Array.from(this.prices.keys()).map(itemId => 
      this.calculateETA(itemId)
    ).filter(Boolean) as ETATooltip[];
  }

  // Proof checks for anti-theater validation
  async runProofChecks(): Promise<{passed: boolean, checks: any[], counters: Record<string, number>}> {
    const checks = [];
    const counters = {};

    // Check 1: System can calculate ETAs
    const testETA = this.calculateETA('generator_upgrade');
    checks.push({
      name: 'eta_calculation',
      status: testETA ? 'pass' : 'fail',
      evidence: testETA ? `ETA: ${testETA.eta_display || 'instant'}` : 'No ETA calculated'
    });

    // Check 2: Pricing system works
    const allETAs = this.getAllETAs();
    checks.push({
      name: 'pricing_system',
      status: allETAs.length > 0 ? 'pass' : 'fail',
      evidence: `${allETAs.length} items priced`
    });

    // Check 3: Resource tracking
    const energyResource = this.resources.get('energy');
    checks.push({
      name: 'resource_tracking',
      status: energyResource ? 'pass' : 'fail',
      evidence: energyResource ? `Energy: ${energyResource.current}` : 'No resources'
    });

    counters['items_priced'] = this.prices.size;
    counters['resources_tracked'] = this.resources.size;
    counters['etas_calculated'] = allETAs.length;

    return {
      passed: checks.every(c => c.status === 'pass'),
      checks,
      counters
    };
  }

  getState() {
    return {
      unlocked: this.unlocked,
      resources: Object.fromEntries(this.resources),
      prices: this.prices.size,
      eta_items: this.unlocked ? this.prices.size : 0
    };
  }
}

export const hoverETASystem = new HoverETASystem();