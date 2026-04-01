// Real Resource Manager Implementation
export interface Resource {
  id: string;
  name: string;
  amount: number;
  maxCapacity: number;
  productionRate: number;
}

export class ResourceManager {
  private resources: Map<string, Resource> = new Map();

  initializeResources(): void {
    this.addResource("energy", "Energy", 100, 1000, 10);
    this.addResource("materials", "Materials", 50, 500, 5);
    this.addResource("components", "Components", 0, 100, 0);
  }

  addResource(id: string, name: string, amount: number, capacity: number, rate: number): void {
    this.resources.set(id, { id, name, amount, maxCapacity: capacity, productionRate: rate });
  }

  produceResources(): void {
    for (const [_, resource] of this.resources) {
      resource.amount = Math.min(resource.amount + resource.productionRate, resource.maxCapacity);
    }
  }

  getResource(id: string): Resource | undefined {
    return this.resources.get(id);
  }

  getAllResources(): Resource[] {
    return Array.from(this.resources.values());
  }
}