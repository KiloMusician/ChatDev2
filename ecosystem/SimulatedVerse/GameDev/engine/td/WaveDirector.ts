// Tower Defense Wave Director - Literal wave spawning with escalation
// Bridges symbolic wave_breath to actual enemy spawning and difficulty curves

import { registry } from '../core/entity/Registry.js';
import { eventHub } from '../core/events/EventHub.js';
import { dataLoader } from '../core/data/DataLoader.js';

export interface WaveComposition {
  enemy_types: Array<{type: string, count: number}>;
  spawn_interval: number;
  total_enemies: number;
  estimated_difficulty: number;
}

export interface WaveDirectorState {
  current_wave: number;
  wave_active: boolean;
  enemies_spawned_this_wave: number;
  enemies_remaining: number;
  last_spawn_time: number;
  wave_start_time: number;
  total_enemies_killed: number;
}

export class WaveDirector {
  private state: WaveDirectorState;
  private enemyData: any = {};
  private waveTemplates: any = {};
  private spawnPaths: Array<Array<{x: number, y: number}>> = [];

  constructor() {
    this.state = {
      current_wave: 0,
      wave_active: false,
      enemies_spawned_this_wave: 0,
      enemies_remaining: 0,
      last_spawn_time: 0,
      wave_start_time: 0,
      total_enemies_killed: 0
    };

    this.loadEnemyData();
    this.initializeSpawnPaths();
    this.setupEventListeners();
    
    console.log('[WaveDirector] Tower Defense wave system initialized');
  }

  private loadEnemyData(): void {
    this.enemyData = dataLoader.getData('enemies')?.enemy_types || {};
    this.waveTemplates = dataLoader.getData('enemies')?.wave_templates || {};
    
    console.log(`[WaveDirector] Loaded ${Object.keys(this.enemyData).length} enemy types`);
  }

  private initializeSpawnPaths(): void {
    // Default 2-lane paths for Tower Defense
    this.spawnPaths = [
      // Lane 1 - Top
      [
        { x: -50, y: 100 },
        { x: 200, y: 100 },
        { x: 400, y: 100 },
        { x: 600, y: 100 },
        { x: 850, y: 100 }
      ],
      // Lane 2 - Bottom  
      [
        { x: -50, y: 200 },
        { x: 200, y: 200 },
        { x: 400, y: 200 },
        { x: 600, y: 200 },
        { x: 850, y: 200 }
      ]
    ];
  }

  private setupEventListeners(): void {
    // Listen for enemy deaths to track wave progress
    eventHub.subscribe('enemy_killed', (event) => {
      this.state.enemies_remaining--;
      this.state.total_enemies_killed++;
      
      // Check if wave is complete
      if (this.state.enemies_remaining <= 0 && 
          this.state.enemies_spawned_this_wave >= this.getCurrentWaveSize()) {
        this.completeWave();
      }
    }, 'wave_director');

    // Listen for enemies reaching the end
    eventHub.subscribe('enemy_reached_end', (event) => {
      this.state.enemies_remaining--;
      // Player loses life here in full implementation
    }, 'wave_director');
  }

  // Start next wave
  startWave(): boolean {
    if (this.state.wave_active) {
      console.warn('[WaveDirector] Wave already active');
      return false;
    }

    this.state.current_wave++;
    this.state.wave_active = true;
    this.state.enemies_spawned_this_wave = 0;
    this.state.wave_start_time = Date.now();
    
    const composition = this.getWaveComposition(this.state.current_wave);
    this.state.enemies_remaining = composition.total_enemies;

    eventHub.publish('wave_started', {
      wave_number: this.state.current_wave,
      composition,
      estimated_difficulty: composition.estimated_difficulty
    }, 'wave_director');

    console.log(`[WaveDirector] Wave ${this.state.current_wave} started: ${composition.total_enemies} enemies`);
    
    // Start spawning enemies
    this.scheduleEnemySpawns(composition);
    
    return true;
  }

  private scheduleEnemySpawns(composition: WaveComposition): void {
    let spawnDelay = 0;
    
    for (const enemyGroup of composition.enemy_types) {
      for (let i = 0; i < enemyGroup.count; i++) {
        setTimeout(() => {
          this.spawnEnemy(enemyGroup.type);
        }, spawnDelay * 1000);
        
        spawnDelay += composition.spawn_interval;
      }
    }
  }

  private spawnEnemy(enemyType: string): void {
    if (!this.state.wave_active) return;

    // Get enemy stats
    const enemyStats = this.enemyData[enemyType];
    if (!enemyStats) {
      console.error(`[WaveDirector] Unknown enemy type: ${enemyType}`);
      return;
    }

    // Choose random spawn path
    const pathIndex = Math.floor(Math.random() * this.spawnPaths.length);
    const spawnPath = this.spawnPaths[pathIndex];

    // Apply wave scaling
    const scaledStats = this.applyWaveScaling(enemyStats, this.state.current_wave);

    // Create enemy entity
    const enemyId = registry.createEntity('enemy', {
      'Position': spawnPath[0],
      'Health': { current: scaledStats.health, max: scaledStats.health },
      'Enemy': {
        path: spawnPath,
        path_index: 0,
        reward: scaledStats.reward,
        type: enemyType
      },
      'Movement': { speed: scaledStats.speed },
      'Renderable': { sprite: scaledStats.sprite || '👾' }
    });

    this.state.enemies_spawned_this_wave++;

    eventHub.publish('enemy_spawned', {
      enemy_id: enemyId,
      enemy_type: enemyType,
      wave: this.state.current_wave,
      path_index: pathIndex,
      stats: scaledStats
    }, 'wave_director');

    console.log(`[WaveDirector] Spawned ${enemyType} enemy (${this.state.enemies_spawned_this_wave}/${this.getCurrentWaveSize()})`);
  }

  private applyWaveScaling(baseStats: any, waveNumber: number): any {
    const enemyScaling = dataLoader.getData('enemies')?.scaling || {};
    
    const healthMultiplier = Math.pow(enemyScaling.health_per_wave || 1.15, waveNumber - 1);
    const speedMultiplier = Math.pow(enemyScaling.speed_per_wave || 1.05, waveNumber - 1);
    const rewardMultiplier = Math.pow(enemyScaling.reward_per_wave || 1.10, waveNumber - 1);

    return {
      health: Math.floor(baseStats.health * healthMultiplier),
      speed: Math.floor(baseStats.speed * speedMultiplier),
      reward: Math.floor(baseStats.reward * rewardMultiplier),
      armor: baseStats.armor + Math.floor(waveNumber / 3), // Armor increases every 3 waves
      sprite: baseStats.sprite
    };
  }

  private getWaveComposition(waveNumber: number): WaveComposition {
    // Get composition from templates
    let waveTemplate;
    
    if (waveNumber <= 3) {
      waveTemplate = this.waveTemplates.early_game?.[`wave_${waveNumber}`];
    } else if (waveNumber <= 6) {
      waveTemplate = this.waveTemplates.mid_game?.[`wave_${waveNumber}`];
    } else {
      waveTemplate = this.waveTemplates.late_game?.[`wave_${waveNumber}`] || 
                    this.waveTemplates.late_game?.['wave_10']; // Default to final wave
    }

    if (!waveTemplate) {
      // Generate procedural wave if no template
      waveTemplate = this.generateProceduralWave(waveNumber);
    }

    // Count enemy types and calculate difficulty
    const enemyTypeCounts = new Map<string, number>();
    for (const enemyType of waveTemplate) {
      enemyTypeCounts.set(enemyType, (enemyTypeCounts.get(enemyType) || 0) + 1);
    }

    const composition: WaveComposition = {
      enemy_types: Array.from(enemyTypeCounts.entries()).map(([type, count]) => ({type, count})),
      spawn_interval: Math.max(0.5, 3 - (waveNumber * 0.1)), // Faster spawning as waves progress
      total_enemies: waveTemplate.length,
      estimated_difficulty: this.calculateWaveDifficulty(waveTemplate, waveNumber)
    };

    return composition;
  }

  private generateProceduralWave(waveNumber: number): string[] {
    // Simple procedural generation for higher waves
    const baseSize = 5 + waveNumber;
    const enemyTypes = Object.keys(this.enemyData);
    
    if (enemyTypes.length === 0) {
      // Fallback enemies if no data loaded
      return Array(baseSize).fill('assault_unit');
    }

    const wave: string[] = [];
    for (let i = 0; i < baseSize; i++) {
      const randomType = enemyTypes[Math.floor(Math.random() * enemyTypes.length)];
      wave.push(randomType);
    }

    return wave;
  }

  private calculateWaveDifficulty(enemyTypes: string[], waveNumber: number): number {
    let difficulty = 0;
    
    for (const enemyType of enemyTypes) {
      const enemyStats = this.enemyData[enemyType];
      if (enemyStats) {
        // Simple difficulty calculation: (health + armor * 10 + speed/2) / 100
        const baseDifficulty = (enemyStats.health + (enemyStats.armor || 0) * 10 + enemyStats.speed / 2) / 100;
        difficulty += baseDifficulty;
      }
    }

    // Apply wave scaling
    return difficulty * Math.pow(1.1, waveNumber - 1);
  }

  private getCurrentWaveSize(): number {
    const composition = this.getWaveComposition(this.state.current_wave);
    return composition.total_enemies;
  }

  private completeWave(): void {
    this.state.wave_active = false;
    const duration = (Date.now() - this.state.wave_start_time) / 1000;

    eventHub.publish('wave_completed', {
      wave_number: this.state.current_wave,
      duration_seconds: duration,
      enemies_killed: this.state.enemies_spawned_this_wave,
      total_killed: this.state.total_enemies_killed
    }, 'wave_director');

    console.log(`[WaveDirector] Wave ${this.state.current_wave} completed in ${duration.toFixed(1)}s`);
  }

  // Preview next wave for UI
  previewNextWave(): WaveComposition {
    return this.getWaveComposition(this.state.current_wave + 1);
  }

  // Get current wave state for UI
  getWaveState(): any {
    const nextWave = this.previewNextWave();
    
    return {
      current_wave: this.state.current_wave,
      wave_active: this.state.wave_active,
      enemies_spawned: this.state.enemies_spawned_this_wave,
      enemies_remaining: this.state.enemies_remaining,
      total_enemies_killed: this.state.total_enemies_killed,
      next_wave_preview: {
        enemy_count: nextWave.total_enemies,
        estimated_difficulty: nextWave.estimated_difficulty,
        new_enemy_types: nextWave.enemy_types.map(et => et.type)
      }
    };
  }

  // Manual controls for testing
  forceSpawnEnemy(enemyType = 'assault_unit'): boolean {
    if (Object.keys(this.enemyData).length === 0) {
      // Create minimal enemy data if none loaded
      this.enemyData[enemyType] = {
        health: 100,
        speed: 50,
        reward: 10,
        sprite: '👾'
      };
    }
    
    this.spawnEnemy(enemyType);
    return true;
  }

  // Msg⛛ command interface
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Wave:Start') {
      return this.startWave();
    } else if (parts[0] === 'Wave:Spawn' && parts.length === 2) {
      return this.forceSpawnEnemy(parts[1]);
    }
    
    return false;
  }
}

export const waveDirector = new WaveDirector();