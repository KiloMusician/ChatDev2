// Resource Ledger - Core resource management with forecasting
// Bridges symbolic resource_breath to literal accounting and generation

import { eventHub } from '../../core/events/EventHub.js';

export interface ResourceType {
  id: string;
  name: string;
  max_amount?: number;
  decay_rate?: number; // Some resources decay over time
  storage_cost?: number; // Cost to increase storage
}

export interface ResourceState {
  amount: number;
  generation_per_second: number;
  consumption_per_second: number;
  visible: boolean;
  storage_limit?: number;
}

export interface ResourceBundle {
  [resourceId: string]: number;
}

export interface ResourceForecast {
  resource_id: string;
  current_amount: number;
  projected_in_60s: number;
  time_to_full?: number;
  time_to_empty?: number;
  bottlenecks: string[];
}

export class ResourceLedger {
  private resources = new Map<string, ResourceState>();
  private resourceTypes = new Map<string, ResourceType>();
  private generationSources = new Map<string, Array<{source: string, amount: number}>>();
  private consumptionSinks = new Map<string, Array<{sink: string, amount: number}>>();

  constructor() {
    this.initializeBaseResources();
    this.startResourceTick();
    console.log('[ResourceLedger] Resource management system initialized');
  }

  private initializeBaseResources() {
    // Define resource types
    const baseTypes: ResourceType[] = [
      { id: 'energy', name: 'Energy', max_amount: 10000 },
      { id: 'materials', name: 'Materials', max_amount: 5000 },
      { id: 'research', name: 'Research Points', max_amount: 1000 },
      { id: 'food', name: 'Food', max_amount: 2000, decay_rate: 0.01 },
      { id: 'nanobots', name: 'Nanobots', max_amount: 500 },
      { id: 'quantum_cores', name: 'Quantum Cores', max_amount: 50 },
      { id: 'data', name: 'Data', max_amount: 10000 },
      { id: 'water', name: 'Water', max_amount: 3000, decay_rate: 0.005 }
    ];

    for (const type of baseTypes) {
      this.resourceTypes.set(type.id, type);
      this.resources.set(type.id, {
        amount: type.id === 'energy' ? 100 : 0, // Start with some energy
        generation_per_second: 0,
        consumption_per_second: 0,
        visible: ['energy', 'materials'].includes(type.id), // Basic resources visible
        storage_limit: type.max_amount
      });

      this.generationSources.set(type.id, []);
      this.consumptionSinks.set(type.id, []);
    }
  }

  // Core resource operations
  add(resourceId: string, amount: number, source = 'unknown'): boolean {
    const resource = this.resources.get(resourceId);
    if (!resource) return false;

    const oldAmount = resource.amount;
    resource.amount += amount;

    // Apply storage limits
    if (resource.storage_limit && resource.amount > resource.storage_limit) {
      const overflow = resource.amount - resource.storage_limit;
      resource.amount = resource.storage_limit;
      
      if (overflow > 0.1) { // Only warn about significant overflow
        eventHub.publish('resource_overflow', { 
          resource: resourceId, 
          overflow, 
          source 
        }, 'resource_ledger');
      }
    }

    // Emit generation event for significant amounts
    if (amount > 0.1) {
      eventHub.publish('resource_generated', {
        resource: resourceId,
        amount,
        source,
        new_total: resource.amount
      }, 'resource_ledger');
    }

    return true;
  }

  // Check if we can afford a cost bundle
  costCheck(costs: ResourceBundle): boolean {
    for (const [resourceId, amount] of Object.entries(costs)) {
      const resource = this.resources.get(resourceId);
      if (!resource || resource.amount < amount) {
        return false;
      }
    }
    return true;
  }

  // Spend resources (atomic - all or nothing)
  spend(costs: ResourceBundle, reason = 'unknown'): boolean {
    if (!this.costCheck(costs)) {
      return false;
    }

    for (const [resourceId, amount] of Object.entries(costs)) {
      const resource = this.resources.get(resourceId)!;
      resource.amount -= amount;
      
      eventHub.publish('resource_spent', {
        resource: resourceId,
        amount,
        reason,
        remaining: resource.amount
      }, 'resource_ledger');

      // Check for depletion
      if (resource.amount <= 0.1) {
        eventHub.publish('resource_depleted', {
          resource: resourceId,
          reason
        }, 'resource_ledger');
      }
    }

    return true;
  }

  // Register resource generation source
  registerGeneration(resourceId: string, sourceId: string, amountPerSecond: number): void {
    const sources = this.generationSources.get(resourceId);
    if (!sources) return;

    // Remove existing source with same ID
    const existingIndex = sources.findIndex(s => s.source === sourceId);
    if (existingIndex >= 0) {
      sources.splice(existingIndex, 1);
    }

    // Add new source
    if (amountPerSecond > 0) {
      sources.push({ source: sourceId, amount: amountPerSecond });
    }

    // Recalculate total generation
    this.recalculateGeneration(resourceId);
  }

  // Register resource consumption sink  
  registerConsumption(resourceId: string, sinkId: string, amountPerSecond: number): void {
    const sinks = this.consumptionSinks.get(resourceId);
    if (!sinks) return;

    // Remove existing sink
    const existingIndex = sinks.findIndex(s => s.sink === sinkId);
    if (existingIndex >= 0) {
      sinks.splice(existingIndex, 1);
    }

    // Add new sink
    if (amountPerSecond > 0) {
      sinks.push({ sink: sinkId, amount: amountPerSecond });
    }

    // Recalculate consumption
    this.recalculateConsumption(resourceId);
  }

  // Forecasting system for ETA calculations
  forecast(resourceId: string, timeHorizonSeconds = 60): ResourceForecast {
    const resource = this.resources.get(resourceId);
    if (!resource) {
      return {
        resource_id: resourceId,
        current_amount: 0,
        projected_in_60s: 0,
        bottlenecks: ['Resource not found']
      };
    }

    const netRate = resource.generation_per_second - resource.consumption_per_second;
    const projectedAmount = resource.amount + (netRate * timeHorizonSeconds);
    
    const forecast: ResourceForecast = {
      resource_id: resourceId,
      current_amount: resource.amount,
      projected_in_60s: Math.max(0, projectedAmount),
      bottlenecks: []
    };

    // Calculate time to full/empty
    if (resource.storage_limit && netRate > 0) {
      const timeToFull = (resource.storage_limit - resource.amount) / netRate;
      forecast.time_to_full = timeToFull > 0 ? timeToFull : undefined;
    }

    if (netRate < 0) {
      const timeToEmpty = resource.amount / Math.abs(netRate);
      forecast.time_to_empty = timeToEmpty;
    }

    // Identify bottlenecks
    if (netRate < 0) {
      forecast.bottlenecks.push('Net consumption exceeds generation');
    }
    if (resource.consumption_per_second > resource.generation_per_second * 0.9) {
      forecast.bottlenecks.push('High consumption relative to generation');
    }

    return forecast;
  }

  // Get current state for UI bindings
  getResourceSnapshot(): Array<{id: string, amount: number, generation: number, visible: boolean, max?: number}> {
    const snapshot = [];
    
    for (const [id, state] of this.resources.entries()) {
      snapshot.push({
        id,
        amount: Math.floor(state.amount * 100) / 100, // Round to 2 decimal places
        generation: Math.floor(state.generation_per_second * 100) / 100,
        visible: state.visible,
        max: state.storage_limit
      });
    }

    return snapshot.filter(r => r.visible); // Only return visible resources
  }

  // Unlock resource visibility
  unlockResource(resourceId: string): boolean {
    const resource = this.resources.get(resourceId);
    if (!resource) return false;

    if (!resource.visible) {
      resource.visible = true;
      console.log(`[ResourceLedger] Unlocked resource: ${resourceId}`);
      
      eventHub.publish('resource_unlocked', {
        resource: resourceId
      }, 'resource_ledger');
      
      return true;
    }
    return false;
  }

  private recalculateGeneration(resourceId: string): void {
    const sources = this.generationSources.get(resourceId);
    const resource = this.resources.get(resourceId);
    
    if (!sources || !resource) return;

    resource.generation_per_second = sources.reduce((total, source) => total + source.amount, 0);
  }

  private recalculateConsumption(resourceId: string): void {
    const sinks = this.consumptionSinks.get(resourceId);
    const resource = this.resources.get(resourceId);
    
    if (!sinks || !resource) return;

    resource.consumption_per_second = sinks.reduce((total, sink) => total + sink.amount, 0);
  }

  private startResourceTick(): void {
    // Import TickBus dynamically to avoid circular dependencies
    import('../../core/time/TickBus.js').then(({ tickBus }) => {
      tickBus.subscribe('idle', (deltaTime) => {
        this.tickResources(deltaTime);
      });
    }).catch(() => {
      // Fall back to manual timer if TickBus not available
      setInterval(() => {
        this.tickResources(1.0);
      }, 1000);
    });
  }

  private tickResources(deltaTime: number): void {
    for (const [resourceId, resource] of this.resources.entries()) {
      const oldAmount = resource.amount;
      
      // Apply generation
      if (resource.generation_per_second > 0) {
        this.add(resourceId, resource.generation_per_second * deltaTime, 'automatic_generation');
      }

      // Apply consumption
      if (resource.consumption_per_second > 0) {
        resource.amount = Math.max(0, resource.amount - (resource.consumption_per_second * deltaTime));
        
        if (resource.amount === 0 && oldAmount > 0) {
          eventHub.publish('resource_depleted', {
            resource: resourceId,
            consumption_rate: resource.consumption_per_second
          }, 'resource_ledger');
        }
      }

      // Apply decay for perishable resources
      const resourceType = this.resourceTypes.get(resourceId);
      if (resourceType?.decay_rate && resource.amount > 0) {
        const decay = resource.amount * resourceType.decay_rate * deltaTime;
        resource.amount = Math.max(0, resource.amount - decay);
      }
    }
  }

  // Debug and analysis functions
  getGenerationBreakdown(resourceId: string): Array<{source: string, amount: number}> {
    return this.generationSources.get(resourceId) || [];
  }

  getConsumptionBreakdown(resourceId: string): Array<{sink: string, amount: number}> {
    return this.consumptionSinks.get(resourceId) || [];
  }

  getResourceStats(): any {
    const stats = {
      total_resources: this.resources.size,
      visible_resources: Array.from(this.resources.values()).filter(r => r.visible).length,
      total_generation: 0,
      total_consumption: 0,
      resource_breakdown: {}
    };

    for (const [id, resource] of this.resources.entries()) {
      stats.total_generation += resource.generation_per_second;
      stats.total_consumption += resource.consumption_per_second;
      
      if (resource.visible) {
        stats.resource_breakdown[id] = {
          amount: resource.amount,
          net_rate: resource.generation_per_second - resource.consumption_per_second,
          sources: this.generationSources.get(id)?.length || 0,
          sinks: this.consumptionSinks.get(id)?.length || 0
        };
      }
    }

    return stats;
  }

  // Msg⛛ command interface for symbolic integration
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Resource:Add' && parts.length === 4) {
      const [_, resourceId, amount, source] = parts;
      return this.add(resourceId, parseFloat(amount), source || 'command');
    } else if (parts[0] === 'Resource:Unlock' && parts.length === 2) {
      return this.unlockResource(parts[1]);
    }
    
    return false;
  }
}

export const resourceLedger = new ResourceLedger();