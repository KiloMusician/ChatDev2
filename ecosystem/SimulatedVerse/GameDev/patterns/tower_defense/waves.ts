// Tower Defense Genre Module - Wave management and enemy AI
// Bridges strategic gameplay to literal combat simulation

import { campaignRNG } from '../../engine/core/rng.js';
import { spatialGrid } from '../../engine/core/spatial.js';
import { registry } from '../../engine/core/entity/Registry.js';
import type { Coord } from '../../engine/core/spatial.js';

export interface EnemyType {
  name: string;
  health: number;
  speed: number;
  reward: number;
  armor?: number;
  special?: string;
}

export interface Wave {
  number: number;
  enemies: Array<{
    type: string;
    count: number;
    delay: number;
    spawn_interval: number;
  }>;
  total_enemies: number;
  difficulty_modifier: number;
}

export interface TowerDefenseState {
  current_wave: number;
  wave_active: boolean;
  enemies_remaining: number;
  lives: number;
  gold: number;
  next_wave_countdown: number;
}

export class WaveManager {
  private enemyTypes: Map<string, EnemyType> = new Map();
  private path: Coord[] = [];
  private state: TowerDefenseState;
  private spawnQueue: Array<{ type: string; spawn_time: number }> = [];
  private currentTime = 0;
  
  constructor() {
    this.initializeEnemyTypes();
    this.state = {
      current_wave: 0,
      wave_active: false,
      enemies_remaining: 0,
      lives: 20,
      gold: 100,
      next_wave_countdown: 0
    };
    
    console.log('[WaveManager] Initialized with', this.enemyTypes.size, 'enemy types');
  }

  private initializeEnemyTypes(): void {
    this.enemyTypes.set('basic', {
      name: 'Scout',
      health: 50,
      speed: 1.0,
      reward: 10
    });
    
    this.enemyTypes.set('fast', {
      name: 'Runner',
      health: 25,
      speed: 2.0,
      reward: 15
    });
    
    this.enemyTypes.set('tank', {
      name: 'Bruiser',
      health: 150,
      speed: 0.5,
      reward: 30,
      armor: 2
    });
    
    this.enemyTypes.set('swarm', {
      name: 'Swarmling',
      health: 15,
      speed: 1.5,
      reward: 5
    });
    
    this.enemyTypes.set('boss', {
      name: 'Commander',
      health: 500,
      speed: 0.8,
      reward: 100,
      armor: 5,
      special: 'spawn_minions'
    });
  }

  // Set path for enemies to follow
  setPath(path: Coord[]): void {
    this.path = [...path];
    console.log(`[WaveManager] Path set with ${path.length} waypoints`);
  }

  // Generate wave configuration
  generateWave(waveNumber: number): Wave {
    const difficulty = 1 + (waveNumber * 0.2);
    const baseEnemies = 5 + Math.floor(waveNumber * 1.5);
    
    const wave: Wave = {
      number: waveNumber,
      enemies: [],
      total_enemies: 0,
      difficulty_modifier: difficulty
    };
    
    // Basic enemies every wave
    wave.enemies.push({
      type: 'basic',
      count: Math.floor(baseEnemies * 0.6),
      delay: 0,
      spawn_interval: 2000
    });
    
    // Fast enemies after wave 2
    if (waveNumber >= 2) {
      wave.enemies.push({
        type: 'fast',
        count: Math.floor(baseEnemies * 0.3),
        delay: 5000,
        spawn_interval: 1500
      });
    }
    
    // Tank enemies after wave 5
    if (waveNumber >= 5) {
      wave.enemies.push({
        type: 'tank',
        count: Math.floor(baseEnemies * 0.2),
        delay: 10000,
        spawn_interval: 3000
      });
    }
    
    // Boss every 10 waves
    if (waveNumber % 10 === 0) {
      wave.enemies.push({
        type: 'boss',
        count: 1,
        delay: 15000,
        spawn_interval: 0
      });
    }
    
    wave.total_enemies = wave.enemies.reduce((sum, group) => sum + group.count, 0);
    
    return wave;
  }

  // Start next wave
  startWave(): boolean {
    if (this.state.wave_active) return false;
    
    this.state.current_wave++;
    const wave = this.generateWave(this.state.current_wave);
    
    console.log(`[WaveManager] Starting wave ${wave.number} with ${wave.total_enemies} enemies`);
    
    // Queue up enemy spawns
    this.spawnQueue = [];
    this.currentTime = 0;
    
    for (const enemyGroup of wave.enemies) {
      for (let i = 0; i < enemyGroup.count; i++) {
        this.spawnQueue.push({
          type: enemyGroup.type,
          spawn_time: enemyGroup.delay + (i * enemyGroup.spawn_interval)
        });
      }
    }
    
    this.state.wave_active = true;
    this.state.enemies_remaining = wave.total_enemies;
    this.state.next_wave_countdown = 0;
    
    return true;
  }

  // Update wave state (called each game tick)
  update(deltaTime: number): void {
    this.currentTime += deltaTime;
    
    // Process spawn queue
    while (this.spawnQueue.length > 0 && 
           this.spawnQueue[0].spawn_time <= this.currentTime) {
      const spawn = this.spawnQueue.shift()!;
      this.spawnEnemy(spawn.type);
    }
    
    // Check wave completion
    if (this.state.wave_active && this.spawnQueue.length === 0 && 
        this.state.enemies_remaining <= 0) {
      this.completeWave();
    }
    
    // Countdown to next wave
    if (!this.state.wave_active && this.state.next_wave_countdown > 0) {
      this.state.next_wave_countdown = Math.max(0, this.state.next_wave_countdown - deltaTime);
    }
  }

  private spawnEnemy(enemyType: string): void {
    const type = this.enemyTypes.get(enemyType);
    if (!type || this.path.length === 0) return;
    
    const startPos = this.path[0];
    const entityId = registry.createEntity('enemy', {
      'Position': { x: startPos.x * 16, y: startPos.y * 16 },
      'Health': { current: type.health, max: type.health },
      'Enemy': {
        path: this.path.map(p => ({ x: p.x * 16, y: p.y * 16 })),
        path_index: 0,
        reward: type.reward
      },
      'AIState': { state: 'following_path', data: { speed: type.speed, armor: type.armor || 0 } }
    });
    
    console.log(`[WaveManager] Spawned ${type.name} (${entityId})`);
  }

  private completeWave(): void {
    this.state.wave_active = false;
    this.state.next_wave_countdown = 15000; // 15 second break
    
    // Bonus gold for wave completion
    this.state.gold += Math.floor(10 * Math.sqrt(this.state.current_wave));
    
    console.log(`[WaveManager] Wave ${this.state.current_wave} completed!`);
  }

  // Called when enemy dies
  onEnemyKilled(reward: number): void {
    this.state.enemies_remaining--;
    this.state.gold += reward;
  }

  // Called when enemy reaches end
  onEnemyReachedEnd(): void {
    this.state.enemies_remaining--;
    this.state.lives--;
    
    if (this.state.lives <= 0) {
      console.log('[WaveManager] Game Over! No lives remaining');
    }
  }

  // Public getters
  getState(): TowerDefenseState {
    return { ...this.state };
  }

  getCurrentWave(): number {
    return this.state.current_wave;
  }

  isWaveActive(): boolean {
    return this.state.wave_active;
  }

  canStartWave(): boolean {
    return !this.state.wave_active && this.state.next_wave_countdown <= 0 && this.state.lives > 0;
  }

  // Tower placement validation
  canPlaceTowerAt(x: number, y: number, towerType: string): boolean {
    // Check if position is on path
    if (this.path.some(p => p.x === x && p.y === y)) {
      return false;
    }
    
    // Check if position is blocked
    const entities = spatialGrid.getEntitiesAt({ x, y });
    if (entities.length > 0) {
      return false;
    }
    
    // Check gold cost
    const cost = this.getTowerCost(towerType);
    return this.state.gold >= cost;
  }

  private getTowerCost(towerType: string): number {
    const costs = {
      'basic': 50,
      'rapid': 75,
      'heavy': 125
    };
    return costs[towerType as keyof typeof costs] || 50;
  }
}

export const waveManager = new WaveManager();
