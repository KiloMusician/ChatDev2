import { ResourceType, Resource } from "./schemas";
import { receipt } from "./receipts";

export class ResourceManager {
  private resources: Map<ResourceType, Resource> = new Map();

  constructor() {
    this.initializeResources();
  }

  private initializeResources() {
    const initialResources: Array<[ResourceType, Partial<Resource>]> = [
      ["energy", { amount: 100, capacity: 1000, rate: 1, multiplier: 1 }],
      ["materials", { amount: 50, capacity: 500, rate: 0.5, multiplier: 1 }],
      ["components", { amount: 0, capacity: 100, rate: 0, multiplier: 1 }],
      ["research", { amount: 0, capacity: 100, rate: 0.1, multiplier: 1 }],
      ["population", { amount: 1, capacity: 10, rate: 0, multiplier: 1 }],
    ];

    for (const [type, partial] of initialResources) {
      this.resources.set(type, {
        id: `resource_${type}`,
        type,
        amount: partial.amount || 0,
        capacity: partial.capacity || 1000,
        rate: partial.rate || 0,
        multiplier: partial.multiplier || 1,
      });
    }
  }

  get(type: ResourceType): Resource | undefined {
    return this.resources.get(type);
  }

  getAmount(type: ResourceType): number {
    return this.resources.get(type)?.amount || 0;
  }

  getCapacity(type: ResourceType): number {
    return this.resources.get(type)?.capacity || 0;
  }

  getRate(type: ResourceType): number {
    const resource = this.resources.get(type);
    return resource ? resource.rate * resource.multiplier : 0;
  }

  add(type: ResourceType, amount: number): boolean {
    const resource = this.resources.get(type);
    if (!resource) return false;

    const oldAmount = resource.amount;
    const capacity = resource.capacity || Infinity;
    const newAmount = Math.min(capacity, resource.amount + amount);
    const actualAmount = newAmount - oldAmount;

    if (actualAmount > 0) {
      resource.amount = newAmount;
      receipt("resource:add", { 
        type, 
        amount: actualAmount, 
        total: newAmount,
        capacity,
        rate: this.getRate(type)
      });
      return true;
    }
    return false;
  }

  spend(type: ResourceType, amount: number): boolean {
    const resource = this.resources.get(type);
    if (!resource || resource.amount < amount) return false;

    const oldAmount = resource.amount;
    resource.amount -= amount;
    
    receipt("resource:spend", { 
      type, 
      amount, 
      remaining: resource.amount,
      total: oldAmount 
    });
    return true;
  }

  canAfford(costs: Record<ResourceType, number>): boolean {
    for (const [type, cost] of Object.entries(costs)) {
      if (this.getAmount(type as ResourceType) < cost) {
        return false;
      }
    }
    return true;
  }

  spendMultiple(costs: Record<ResourceType, number>): boolean {
    if (!this.canAfford(costs)) return false;

    for (const [type, cost] of Object.entries(costs)) {
      this.spend(type as ResourceType, cost);
    }
    return true;
  }

  tick(deltaTime: number) {
    const deltaSeconds = deltaTime / 1000;
    
    for (const [type, resource] of this.resources) {
      const rate = this.getRate(type);
      if (rate > 0) {
        const gain = rate * deltaSeconds;
        this.add(type, gain);
      }
    }
  }

  setMultiplier(type: ResourceType, multiplier: number) {
    const resource = this.resources.get(type);
    if (resource) {
      const oldMultiplier = resource.multiplier;
      resource.multiplier = multiplier;
      receipt("resource:multiplier", { 
        type, 
        from: oldMultiplier, 
        to: multiplier,
        newRate: this.getRate(type)
      });
    }
  }

  upgradeCapacity(type: ResourceType, increase: number) {
    const resource = this.resources.get(type);
    if (resource && resource.capacity) {
      const oldCapacity = resource.capacity;
      resource.capacity += increase;
      receipt("resource:upgrade_capacity", { 
        type, 
        from: oldCapacity, 
        to: resource.capacity,
        increase
      });
    }
  }

  getAll(): Record<ResourceType, Resource> {
    const result: Record<string, Resource> = {};
    for (const [type, resource] of this.resources) {
      result[type] = { ...resource };
    }
    return result as Record<ResourceType, Resource>;
  }

  loadState(resources: Record<ResourceType, Resource>) {
    this.resources.clear();
    for (const [type, resource] of Object.entries(resources)) {
      this.resources.set(type as ResourceType, { ...resource });
    }
    receipt("resource:load_state", { resourceCount: this.resources.size });
  }
}