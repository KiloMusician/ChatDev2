import { Enemy, EnemyType, ResourceType } from "./schemas";
import { ResourceManager } from "./resources";
import { StructureManager } from "./structures";
import { receipt } from "./receipts";
import { nanoid } from "nanoid";

// Enemy templates
const ENEMY_TEMPLATES: Record<EnemyType, Omit<Enemy, "id" | "position" | "target" | "lastMove" | "path">> = {
  scout: {
    type: "scout",
    health: 25,
    maxHealth: 25,
    speed: 2.0,
    damage: 5,
    reward: { energy: 15, materials: 5 },
  },
  warrior: {
    type: "warrior",
    health: 60,
    maxHealth: 60,
    speed: 1.5,
    damage: 15,
    reward: { energy: 25, materials: 15, components: 2 },
  },
  tank: {
    type: "tank",
    health: 150,
    maxHealth: 150,
    speed: 0.8,
    damage: 30,
    reward: { energy: 40, materials: 30, components: 5 },
  },
  swarm: {
    type: "swarm",
    health: 15,
    maxHealth: 15,
    speed: 2.5,
    damage: 3,
    reward: { energy: 8, materials: 3 },
  },
  boss: {
    type: "boss",
    health: 500,
    maxHealth: 500,
    speed: 1.0,
    damage: 50,
    reward: { energy: 200, materials: 150, components: 50, research: 25 },
  },
};

export class EnemyManager {
  private enemies: Map<string, Enemy> = new Map();
  private spawnPoints: Array<{x: number, y: number}> = [
    { x: 0, y: 12 }, // Left side
    { x: 59, y: 12 }, // Right side
    { x: 30, y: 0 }, // Top
    { x: 30, y: 23 }, // Bottom
  ];
  private targetPoints: Array<{x: number, y: number}> = [
    { x: 30, y: 12 }, // Center of map
  ];

  constructor(
    private resourceManager: ResourceManager,
    private structureManager: StructureManager
  ) {}

  spawn(type: EnemyType, spawnIndex: number = 0): Enemy | null {
    const template = ENEMY_TEMPLATES[type];
    const spawnPoint = this.spawnPoints[spawnIndex % this.spawnPoints.length] ?? this.spawnPoints[0];
    if (!spawnPoint) {
      return null;
    }
    const target = this.targetPoints[0] ?? spawnPoint; // Simple targeting for now

    const id = nanoid();
    const enemy: Enemy = {
      ...template,
      id,
      position: { x: spawnPoint.x, y: spawnPoint.y },
      target: { x: target.x, y: target.y },
      lastMove: Date.now(),
      path: this.calculatePath(spawnPoint, target),
    };

    this.enemies.set(id, enemy);

    receipt("enemy:spawn", {
      id,
      type,
      spawnPoint,
      target,
      health: enemy.health,
      speed: enemy.speed,
    });

    return enemy;
  }

  private calculatePath(from: {x: number, y: number}, to: {x: number, y: number}): Array<{x: number, y: number}> {
    // Simple straight-line path for now
    const path: Array<{x: number, y: number}> = [];
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const steps = Math.max(Math.abs(dx), Math.abs(dy));
    
    if (steps === 0) return [to];

    for (let i = 1; i <= steps; i++) {
      const progress = i / steps;
      path.push({
        x: Math.round(from.x + dx * progress),
        y: Math.round(from.y + dy * progress),
      });
    }

    return path;
  }

  remove(id: string): boolean {
    const enemy = this.enemies.get(id);
    if (!enemy) return false;

    this.enemies.delete(id);

    receipt("enemy:remove", {
      id,
      type: enemy.type,
      position: enemy.position,
      health: enemy.health,
    });

    return true;
  }

  damage(id: string, amount: number): boolean {
    const enemy = this.enemies.get(id);
    if (!enemy) return false;

    enemy.health = Math.max(0, enemy.health - amount);

    receipt("enemy:damage", {
      id,
      type: enemy.type,
      damage: amount,
      health: enemy.health,
      killed: enemy.health === 0,
    });

    if (enemy.health === 0) {
      // Give rewards
      for (const [resourceType, amount] of Object.entries(enemy.reward)) {
        this.resourceManager.add(resourceType as ResourceType, amount);
      }

      receipt("enemy:kill_reward", {
        id,
        type: enemy.type,
        rewards: enemy.reward,
      });

      this.remove(id);
      return true; // Enemy killed
    }

    return false;
  }

  get(id: string): Enemy | undefined {
    return this.enemies.get(id);
  }

  getAll(): Enemy[] {
    return Array.from(this.enemies.values());
  }

  getInRange(x: number, y: number, range: number): Enemy[] {
    return this.getAll().filter(enemy => {
      const dx = enemy.position.x - x;
      const dy = enemy.position.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return distance <= range;
    });
  }

  tick(deltaTime: number) {
    const now = Date.now();
    const deltaSeconds = deltaTime / 1000;

    for (const enemy of this.enemies.values()) {
      // Move enemy along path
      if (enemy.path.length > 0 && now - enemy.lastMove > (1000 / enemy.speed)) {
        const nextStep = enemy.path.shift();
        if (nextStep) {
          enemy.position = nextStep;
          enemy.lastMove = now;

          // Check if enemy reached target
          if (enemy.path.length === 0) {
            // Enemy reached base - deal damage to structures or resources
            this.handleEnemyReachTarget(enemy);
          }
        }
      }

      // Attack nearby structures
      const nearbyStructures = this.structureManager.getInRange(
        enemy.position.x, 
        enemy.position.y, 
        1.5
      );

      if (nearbyStructures.length > 0 && now - enemy.lastMove > 2000) {
        const target = nearbyStructures[0];
        if (target) {
          this.structureManager.damage(target.id, enemy.damage);
          enemy.lastMove = now;

          receipt("enemy:attack_structure", {
            enemyId: enemy.id,
            structureId: target.id,
            damage: enemy.damage,
            enemyType: enemy.type,
            structureType: target.type,
          });
        }
      }
    }
  }

  private handleEnemyReachTarget(enemy: Enemy) {
    // Enemy reached the base - cause damage
    const baseDamage = enemy.damage * 2; // Double damage for reaching base
    
    // Damage resources or population
    if (this.resourceManager.getAmount("population") > 0) {
      this.resourceManager.spend("population", 1);
    } else {
      // Damage energy as fallback
      this.resourceManager.spend("energy", baseDamage);
    }

    receipt("enemy:reach_target", {
      enemyId: enemy.id,
      enemyType: enemy.type,
      damage: baseDamage,
      populationLoss: 1,
    });

    this.remove(enemy.id);
  }

  clearAll() {
    const enemyCount = this.enemies.size;
    this.enemies.clear();
    
    receipt("enemy:clear_all", { 
      count: enemyCount 
    });
  }

  loadState(enemies: Enemy[]) {
    this.enemies.clear();

    for (const enemy of enemies) {
      this.enemies.set(enemy.id, { ...enemy });
    }

    receipt("enemy:load_state", { 
      enemyCount: this.enemies.size,
      types: Object.fromEntries(
        Object.entries(ENEMY_TEMPLATES).map(([type]) => [
          type, 
          this.getAll().filter(e => e.type === type).length
        ])
      )
    });
  }

  // Wave spawning utilities
  spawnWave(enemySpecs: Array<{type: EnemyType, count: number, spawn_delay: number}>) {
    let totalDelay = 0;
    
    for (const spec of enemySpecs) {
      for (let i = 0; i < spec.count; i++) {
        setTimeout(() => {
          const spawnIndex = Math.floor(Math.random() * this.spawnPoints.length);
          this.spawn(spec.type, spawnIndex);
        }, totalDelay);
        
        totalDelay += spec.spawn_delay * 1000;
      }
    }

    receipt("enemy:spawn_wave", {
      specs: enemySpecs,
      totalEnemies: enemySpecs.reduce((sum, spec) => sum + spec.count, 0),
      duration: totalDelay / 1000,
    });
  }
}
