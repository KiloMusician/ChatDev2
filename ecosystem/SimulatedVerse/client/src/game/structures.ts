import { Structure, StructureType, ResourceType } from "./schemas";
import { ResourceManager } from "./resources";
import { receipt } from "./receipts";
import { nanoid } from "nanoid";

// Structure templates for different types
const STRUCTURE_TEMPLATES: Record<StructureType, Omit<Structure, "id" | "position">> = {
  generator: {
    type: "generator",
    level: 1,
    health: 100,
    maxHealth: 100,
    cost: { energy: 50, materials: 25 },
    production: { energy: 2 },
    range: 0,
    damage: 0,
    cooldown: 1000,
    lastFired: 0,
  },
  storage: {
    type: "storage",
    level: 1,
    health: 75,
    maxHealth: 75,
    cost: { energy: 30, materials: 40 },
    range: 0,
    damage: 0,
    cooldown: 1000,
    lastFired: 0,
  },
  converter: {
    type: "converter",
    level: 1,
    health: 80,
    maxHealth: 80,
    cost: { energy: 75, materials: 50, components: 10 },
    production: { components: 0.5 },
    range: 0,
    damage: 0,
    cooldown: 2000,
    lastFired: 0,
  },
  turret: {
    type: "turret",
    level: 1,
    health: 120,
    maxHealth: 120,
    cost: { energy: 100, materials: 75, components: 25 },
    range: 3,
    damage: 25,
    cooldown: 1500,
    lastFired: 0,
  },
  wall: {
    type: "wall",
    level: 1,
    health: 200,
    maxHealth: 200,
    cost: { materials: 20 },
    range: 0,
    damage: 0,
    cooldown: 1000,
    lastFired: 0,
  },
  research_lab: {
    type: "research_lab",
    level: 1,
    health: 60,
    maxHealth: 60,
    cost: { energy: 150, materials: 100, components: 50 },
    production: { research: 1 },
    range: 0,
    damage: 0,
    cooldown: 1000,
    lastFired: 0,
  },
};

export class StructureManager {
  private structures: Map<string, Structure> = new Map();
  private grid: Map<string, string> = new Map(); // position -> structure id

  constructor(private resourceManager: ResourceManager) {}

  private positionKey(x: number, y: number): string {
    return `${x},${y}`;
  }

  canPlace(type: StructureType, x: number, y: number): boolean {
    // Check if position is occupied
    if (this.grid.has(this.positionKey(x, y))) {
      return false;
    }

    // Check bounds (assuming 60x24 grid from ASCII renderer)
    if (x < 0 || x >= 60 || y < 0 || y >= 24) {
      return false;
    }

    // Check if player can afford the structure
    const template = STRUCTURE_TEMPLATES[type];
    if (!this.resourceManager.canAfford(template.cost as any)) {
      return false;
    }

    return true;
  }

  place(type: StructureType, x: number, y: number): Structure | null {
    if (!this.canPlace(type, x, y)) {
      return null;
    }

    const template = STRUCTURE_TEMPLATES[type];
    const id = nanoid();
    
    // Spend resources
    if (!this.resourceManager.spendMultiple(template.cost as any)) {
      return null;
    }

    const structure: Structure = {
      ...template,
      id,
      position: { x, y },
    };

    this.structures.set(id, structure);
    this.grid.set(this.positionKey(x, y), id);

    receipt("structure:place", {
      id,
      type,
      position: { x, y },
      cost: template.cost,
      level: structure.level,
    });

    return structure;
  }

  remove(id: string): boolean {
    const structure = this.structures.get(id);
    if (!structure) return false;

    const posKey = this.positionKey(structure.position.x, structure.position.y);
    this.structures.delete(id);
    this.grid.delete(posKey);

    receipt("structure:remove", {
      id,
      type: structure.type,
      position: structure.position,
      level: structure.level,
    });

    return true;
  }

  get(id: string): Structure | undefined {
    return this.structures.get(id);
  }

  getAt(x: number, y: number): Structure | undefined {
    const id = this.grid.get(this.positionKey(x, y));
    return id ? this.structures.get(id) : undefined;
  }

  getAll(): Structure[] {
    return Array.from(this.structures.values());
  }

  getByType(type: StructureType): Structure[] {
    return this.getAll().filter(s => s.type === type);
  }

  upgrade(id: string): boolean {
    const structure = this.structures.get(id);
    if (!structure) return false;

    const upgradeCost = this.getUpgradeCost(structure);
    if (!this.resourceManager.canAfford(upgradeCost)) {
      return false;
    }

    if (!this.resourceManager.spendMultiple(upgradeCost as any)) {
      return false;
    }

    const oldLevel = structure.level;
    structure.level += 1;
    structure.maxHealth = Math.floor(structure.maxHealth * 1.2);
    structure.health = structure.maxHealth; // Full heal on upgrade

    // Increase production/damage based on level
    if (structure.production) {
      for (const [resource, amount] of Object.entries(structure.production)) {
        structure.production[resource as ResourceType] = amount * 1.3;
      }
    }
    if (structure.damage > 0) {
      structure.damage = Math.floor(structure.damage * 1.25);
    }

    receipt("structure:upgrade", {
      id,
      type: structure.type,
      fromLevel: oldLevel,
      toLevel: structure.level,
      cost: upgradeCost,
      newStats: {
        health: structure.maxHealth,
        production: structure.production,
        damage: structure.damage,
      },
    });

    return true;
  }

  getUpgradeCost(structure: Structure): Record<ResourceType, number> {
    const baseCost = STRUCTURE_TEMPLATES[structure.type].cost;
    const multiplier = Math.pow(1.5, structure.level);
    
    const upgradeCost: Record<string, number> = {};
    for (const [resource, cost] of Object.entries(baseCost)) {
      upgradeCost[resource] = Math.floor(cost * multiplier);
    }
    
    return upgradeCost as Record<ResourceType, number>;
  }

  damage(id: string, amount: number): boolean {
    const structure = this.structures.get(id);
    if (!structure) return false;

    structure.health = Math.max(0, structure.health - amount);
    
    receipt("structure:damage", {
      id,
      type: structure.type,
      damage: amount,
      health: structure.health,
      destroyed: structure.health === 0,
    });

    if (structure.health === 0) {
      this.remove(id);
      return true; // Structure destroyed
    }

    return false;
  }

  repair(id: string, amount: number): boolean {
    const structure = this.structures.get(id);
    if (!structure) return false;

    const oldHealth = structure.health;
    structure.health = Math.min(structure.maxHealth, structure.health + amount);
    const actualHealing = structure.health - oldHealth;

    if (actualHealing > 0) {
      receipt("structure:repair", {
        id,
        type: structure.type,
        healing: actualHealing,
        health: structure.health,
        maxHealth: structure.maxHealth,
      });
      return true;
    }

    return false;
  }

  tick(deltaTime: number) {
    const deltaSeconds = deltaTime / 1000;

    // Process production structures
    for (const structure of this.structures.values()) {
      if (structure.production && structure.health > 0) {
        for (const [resourceType, rate] of Object.entries(structure.production)) {
          const amount = rate * deltaSeconds * (structure.level * 0.2 + 0.8); // Level scaling
          this.resourceManager.add(resourceType as ResourceType, amount);
        }
      }
    }
  }

  getInRange(x: number, y: number, range: number): Structure[] {
    return this.getAll().filter(structure => {
      const dx = structure.position.x - x;
      const dy = structure.position.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return distance <= range && structure.health > 0;
    });
  }

  loadState(structures: Structure[]) {
    this.structures.clear();
    this.grid.clear();

    for (const structure of structures) {
      this.structures.set(structure.id, { ...structure });
      const posKey = this.positionKey(structure.position.x, structure.position.y);
      this.grid.set(posKey, structure.id);
    }

    receipt("structure:load_state", { 
      structureCount: this.structures.size,
      types: Object.fromEntries(
        Object.entries(STRUCTURE_TEMPLATES).map(([type]) => [
          type, 
          this.getByType(type as StructureType).length
        ])
      )
    });
  }
}