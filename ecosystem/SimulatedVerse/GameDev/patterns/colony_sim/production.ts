// Colony Simulation Genre Module - Production chains and citizen AI
// Bridges economic simulation to literal resource generation

import { campaignRNG } from '../../engine/core/rng.js';
import { registry } from '../../engine/core/entity/Registry.js';
import type { Coord } from '../../engine/core/spatial.js';

export interface ProductionBuilding {
  type: string;
  inputs: Record<string, number>;
  outputs: Record<string, number>;
  production_time: number;
  efficiency: number;
  worker_slots: number;
  current_workers: number;
}

export interface ColonyResource {
  name: string;
  amount: number;
  max_storage: number;
  production_rate: number;
  consumption_rate: number;
}

export interface CitizenJob {
  type: string;
  building_id?: string;
  skill_requirement: number;
  efficiency_bonus: number;
  happiness_modifier: number;
}

export class ProductionManager {
  private buildings = new Map<string, ProductionBuilding>();
  private resources = new Map<string, ColonyResource>();
  private jobs = new Map<string, CitizenJob>();
  private productionCycles: Map<string, number> = new Map();
  
  constructor() {
    this.initializeResources();
    this.initializeBuildings();
    this.initializeJobs();
    
    console.log('[Production] Manager initialized with', this.buildings.size, 'building types');
  }

  private initializeResources(): void {
    const baseResources = [
      { name: 'food', amount: 100, max_storage: 1000, production_rate: 0, consumption_rate: 0.1 },
      { name: 'wood', amount: 50, max_storage: 500, production_rate: 0, consumption_rate: 0 },
      { name: 'stone', amount: 30, max_storage: 300, production_rate: 0, consumption_rate: 0 },
      { name: 'metal', amount: 10, max_storage: 200, production_rate: 0, consumption_rate: 0 },
      { name: 'energy', amount: 0, max_storage: 100, production_rate: 1, consumption_rate: 0.5 },
      { name: 'research', amount: 0, max_storage: Infinity, production_rate: 0, consumption_rate: 0 }
    ];
    
    for (const resource of baseResources) {
      this.resources.set(resource.name, resource);
    }
  }

  private initializeBuildings(): void {
    const buildingTypes = [
      {
        type: 'farm',
        inputs: {},
        outputs: { food: 5 },
        production_time: 10000,
        efficiency: 1.0,
        worker_slots: 2,
        current_workers: 0
      },
      {
        type: 'lumber_mill',
        inputs: {},
        outputs: { wood: 3 },
        production_time: 15000,
        efficiency: 1.0,
        worker_slots: 1,
        current_workers: 0
      },
      {
        type: 'quarry',
        inputs: {},
        outputs: { stone: 2 },
        production_time: 20000,
        efficiency: 1.0,
        worker_slots: 2,
        current_workers: 0
      },
      {
        type: 'workshop',
        inputs: { wood: 2, stone: 1 },
        outputs: { metal: 1 },
        production_time: 30000,
        efficiency: 1.0,
        worker_slots: 1,
        current_workers: 0
      },
      {
        type: 'generator',
        inputs: { metal: 1 },
        outputs: { energy: 10 },
        production_time: 5000,
        efficiency: 1.0,
        worker_slots: 0,
        current_workers: 0
      },
      {
        type: 'lab',
        inputs: { energy: 5 },
        outputs: { research: 3 },
        production_time: 25000,
        efficiency: 1.0,
        worker_slots: 3,
        current_workers: 0
      }
    ];
    
    for (const building of buildingTypes) {
      this.buildings.set(building.type, building);
    }
  }

  private initializeJobs(): void {
    const jobTypes = [
      { type: 'farmer', skill_requirement: 1, efficiency_bonus: 0.2, happiness_modifier: 0.1 },
      { type: 'lumberjack', skill_requirement: 2, efficiency_bonus: 0.15, happiness_modifier: 0.05 },
      { type: 'miner', skill_requirement: 3, efficiency_bonus: 0.25, happiness_modifier: -0.05 },
      { type: 'craftsman', skill_requirement: 4, efficiency_bonus: 0.3, happiness_modifier: 0.15 },
      { type: 'researcher', skill_requirement: 5, efficiency_bonus: 0.4, happiness_modifier: 0.2 },
      { type: 'unemployed', skill_requirement: 0, efficiency_bonus: 0, happiness_modifier: -0.1 }
    ];
    
    for (const job of jobTypes) {
      this.jobs.set(job.type, job);
    }
  }

  // Process production cycles
  update(deltaTime: number): void {
    // Update each building's production
    const buildings = registry.query(['Position', 'Buildable']);
    
    for (const buildingId of buildings) {
      this.updateBuildingProduction(buildingId, deltaTime);
    }
    
    // Natural resource consumption
    this.updateResourceConsumption(deltaTime);
    
    // Check resource caps
    this.enforceStorageLimits();
  }

  private updateBuildingProduction(buildingId: string, deltaTime: number): void {
    const position = registry.getComponent(buildingId, 'Position');
    const buildable = registry.getComponent(buildingId, 'Buildable');
    
    if (!position || !buildable || buildable.progress < buildable.build_time) return;
    
    // Extract building type from entity ID
    const buildingType = buildingId.split('_')[0];
    const buildingData = this.buildings.get(buildingType);
    
    if (!buildingData) return;
    
    // Check production cycle
    const lastProduction = this.productionCycles.get(buildingId) || 0;
    const timeSinceProduction = Date.now() - lastProduction;
    
    if (timeSinceProduction >= buildingData.production_time) {
      // Check if we have required inputs
      if (this.canAfford(buildingData.inputs)) {
        // Consume inputs
        this.consumeResources(buildingData.inputs);
        
        // Calculate worker efficiency
        const workerEfficiency = this.calculateWorkerEfficiency(buildingId, buildingData);
        
        // Produce outputs
        for (const [resourceName, amount] of Object.entries(buildingData.outputs)) {
          const finalAmount = Math.floor(amount * buildingData.efficiency * workerEfficiency);
          this.addResource(resourceName, finalAmount);
        }
        
        // Record production cycle
        this.productionCycles.set(buildingId, Date.now());
        
        console.log(`[Production] ${buildingType} produced`, Object.entries(buildingData.outputs));
      }
    }
  }

  private calculateWorkerEfficiency(buildingId: string, buildingData: ProductionBuilding): number {
    if (buildingData.worker_slots === 0) return 1.0;
    
    const workers = registry.query(['Position', 'Citizen'])
      .map(cId => ({ id: cId, citizen: registry.getComponent(cId, 'Citizen') }))
      .filter(c => c.citizen?.job === buildingId);
    
    const actualWorkers = workers.length;
    const optimalWorkers = buildingData.worker_slots;
    
    // Efficiency scales with worker ratio and skill
    const workerRatio = Math.min(actualWorkers / optimalWorkers, 1.2); // 120% max with overflow
    
    let skillBonus = 0;
    for (const worker of workers) {
      skillBonus += (worker.citizen.skill_level - 1) * 0.1;
    }
    
    return workerRatio + skillBonus;
  }

  private updateResourceConsumption(deltaTime: number): void {
    const citizens = registry.query(['Citizen']);
    const populationCount = citizens.length;
    
    // Food consumption
    const foodConsumption = populationCount * 0.1 * (deltaTime / 1000);
    this.consumeResource('food', foodConsumption);
    
    // Energy consumption (base systems)
    this.consumeResource('energy', 0.5 * (deltaTime / 1000));
  }

  private enforceStorageLimits(): void {
    for (const [name, resource] of this.resources.entries()) {
      if (resource.amount > resource.max_storage) {
        resource.amount = resource.max_storage;
      }
      if (resource.amount < 0) {
        resource.amount = 0;
      }
    }
  }

  // Resource management
  addResource(name: string, amount: number): boolean {
    const resource = this.resources.get(name);
    if (!resource) return false;
    
    const oldAmount = resource.amount;
    resource.amount = Math.min(resource.amount + amount, resource.max_storage);
    
    const actualAdded = resource.amount - oldAmount;
    if (actualAdded > 0) {
      console.log(`[Production] +${actualAdded} ${name} (${resource.amount}/${resource.max_storage})`);
    }
    
    return actualAdded > 0;
  }

  consumeResource(name: string, amount: number): boolean {
    const resource = this.resources.get(name);
    if (!resource || resource.amount < amount) return false;
    
    resource.amount -= amount;
    return true;
  }

  consumeResources(costs: Record<string, number>): boolean {
    // Check if we can afford all
    if (!this.canAfford(costs)) return false;
    
    // Consume all
    for (const [name, amount] of Object.entries(costs)) {
      this.consumeResource(name, amount);
    }
    
    return true;
  }

  canAfford(costs: Record<string, number>): boolean {
    for (const [name, amount] of Object.entries(costs)) {
      const resource = this.resources.get(name);
      if (!resource || resource.amount < amount) {
        return false;
      }
    }
    return true;
  }

  // Citizen management
  assignJob(citizenId: string, jobType: string, buildingId?: string): boolean {
    const citizen = registry.getComponent(citizenId, 'Citizen');
    if (!citizen) return false;
    
    const job = this.jobs.get(jobType);
    if (!job) return false;
    
    // Check skill requirement
    if (citizen.skill_level < job.skill_requirement) {
      return false;
    }
    
    // Assign job
    citizen.job = buildingId || jobType;
    
    console.log(`[Production] Assigned ${citizenId} to ${jobType}`);
    return true;
  }

  // Building construction
  constructBuilding(type: string, position: Coord): string | null {
    const buildingData = this.buildings.get(type);
    if (!buildingData) return null;
    
    // Check construction costs
    const costs = { wood: 10, stone: 5 }; // Base costs
    if (!this.canAfford(costs)) return null;
    
    // Create building entity
    const buildingId = registry.createEntity('building', {
      'Position': { x: position.x * 16, y: position.y * 16 },
      'Buildable': {
        cost: costs,
        build_time: 15000,
        progress: 0
      },
      'Health': { current: 100, max: 100 }
    });
    
    // Consume resources
    this.consumeResources(costs);
    
    console.log(`[Production] Started construction of ${type} at (${position.x}, ${position.y})`);
    return buildingId;
  }

  // Get resource amounts
  getResource(name: string): number {
    return this.resources.get(name)?.amount || 0;
  }

  getResources(): Record<string, ColonyResource> {
    const result: Record<string, ColonyResource> = {};
    for (const [name, resource] of this.resources.entries()) {
      result[name] = { ...resource };
    }
    return result;
  }

  // Get production stats for UI
  getProductionStats(): Array<{ building: string; efficiency: number; workers: string; status: string }> {
    const stats: Array<{ building: string; efficiency: number; workers: string; status: string }> = [];
    
    const buildings = registry.query(['Position', 'Buildable']);
    
    for (const buildingId of buildings) {
      const buildingType = buildingId.split('_')[0];
      const buildingData = this.buildings.get(buildingType);
      
      if (buildingData) {
        const efficiency = this.calculateWorkerEfficiency(buildingId, buildingData);
        
        stats.push({
          building: buildingType,
          efficiency: Math.floor(efficiency * 100),
          workers: `${buildingData.current_workers}/${buildingData.worker_slots}`,
          status: efficiency > 0.8 ? 'optimal' : efficiency > 0.5 ? 'adequate' : 'understaffed'
        });
      }
    }
    
    return stats;
  }

  // Emergency resource injection (for testing)
  cheatResources(multiplier: number = 10): void {
    for (const resource of this.resources.values()) {
      resource.amount = Math.min(resource.amount * multiplier, resource.max_storage);
    }
    
    console.log('[Production] Resource cheat applied (x' + multiplier + ')');
  }

  // Smart citizen assignment
  autoAssignCitizens(): number {
    const unemployedCitizens = registry.query(['Citizen'])
      .map(id => ({ id, citizen: registry.getComponent(id, 'Citizen') }))
      .filter(c => c.citizen?.job === 'unemployed');
    
    const buildings = registry.query(['Position', 'Buildable'])
      .map(id => ({ id, type: id.split('_')[0] }))
      .filter(b => this.buildings.has(b.type));
    
    let assigned = 0;
    
    for (const building of buildings) {
      const buildingData = this.buildings.get(building.type)!;
      const needed = buildingData.worker_slots - buildingData.current_workers;
      
      if (needed > 0 && unemployedCitizens.length > 0) {
        // Find most skilled available citizen
        const available = unemployedCitizens
          .filter(c => c.citizen.skill_level >= this.jobs.get(building.type)?.skill_requirement || 1)
          .sort((a, b) => b.citizen.skill_level - a.citizen.skill_level);
        
        if (available.length > 0) {
          const citizen = available.shift()!;
          this.assignJob(citizen.id, building.type, building.id);
          buildingData.current_workers++;
          assigned++;
          
          // Remove from unemployed list
          const index = unemployedCitizens.indexOf(citizen);
          unemployedCitizens.splice(index, 1);
        }
      }
    }
    
    if (assigned > 0) {
      console.log(`[Production] Auto-assigned ${assigned} citizens to jobs`);
    }
    
    return assigned;
  }
}

export const productionManager = new ProductionManager();
