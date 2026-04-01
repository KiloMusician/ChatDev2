import { Wave, EnemyType } from "./schemas";
import { EnemyManager } from "./enemies";
import { ResourceManager } from "./resources";
import { receipt } from "./receipts";

// Wave progression data - gets more challenging over time
const WAVE_DATA: Wave[] = [
  {
    wave: 1,
    tier: 1,
    enemies: [
      { type: "scout", count: 3, spawn_delay: 2 }
    ],
    duration: 15,
    rewards: { energy: 50, materials: 20 }
  },
  {
    wave: 2,
    tier: 1,
    enemies: [
      { type: "scout", count: 2, spawn_delay: 1.5 },
      { type: "warrior", count: 1, spawn_delay: 3 }
    ],
    duration: 20,
    rewards: { energy: 75, materials: 30, components: 5 }
  },
  {
    wave: 3,
    tier: 1,
    enemies: [
      { type: "swarm", count: 5, spawn_delay: 1 },
      { type: "warrior", count: 2, spawn_delay: 2 }
    ],
    duration: 25,
    rewards: { energy: 100, materials: 50, components: 10 }
  },
  {
    wave: 4,
    tier: 1,
    enemies: [
      { type: "scout", count: 3, spawn_delay: 1 },
      { type: "tank", count: 1, spawn_delay: 5 }
    ],
    duration: 30,
    rewards: { energy: 125, materials: 75, components: 15 }
  },
  {
    wave: 5,
    tier: 1,
    enemies: [
      { type: "swarm", count: 8, spawn_delay: 0.5 },
      { type: "warrior", count: 3, spawn_delay: 2 },
      { type: "boss", count: 1, spawn_delay: 10 }
    ],
    duration: 45,
    rewards: { energy: 200, materials: 150, components: 50, research: 25 }
  },
  // Tier 2 waves
  {
    wave: 6,
    tier: 2,
    enemies: [
      { type: "warrior", count: 4, spawn_delay: 1.5 },
      { type: "tank", count: 2, spawn_delay: 3 }
    ],
    duration: 35,
    rewards: { energy: 175, materials: 100, components: 25, research: 10 }
  },
  {
    wave: 7,
    tier: 2,
    enemies: [
      { type: "swarm", count: 10, spawn_delay: 0.8 },
      { type: "scout", count: 5, spawn_delay: 1 },
      { type: "tank", count: 1, spawn_delay: 5 }
    ],
    duration: 40,
    rewards: { energy: 225, materials: 125, components: 35, research: 15 }
  },
  {
    wave: 8,
    tier: 2,
    enemies: [
      { type: "warrior", count: 6, spawn_delay: 1 },
      { type: "tank", count: 3, spawn_delay: 3 },
      { type: "boss", count: 1, spawn_delay: 15 }
    ],
    duration: 50,
    rewards: { energy: 300, materials: 200, components: 75, research: 40 }
  }
];

export class WaveManager {
  private currentWave: number = 0;
  private waveActive: boolean = false;
  private waveStartTime: number = 0;
  private waveEndTime: number = 0;
  private waveData: Wave[] = WAVE_DATA;
  
  constructor(
    private enemyManager: EnemyManager,
    private resourceManager: ResourceManager
  ) {}

  getCurrentWave(): number {
    return this.currentWave;
  }

  isWaveActive(): boolean {
    return this.waveActive;
  }

  getWaveProgress(): number {
    if (!this.waveActive) return 0;
    
    const now = Date.now();
    const elapsed = (now - this.waveStartTime) / 1000;
    const duration = this.getCurrentWaveData()?.duration || 30;
    
    return Math.min(1, elapsed / duration);
  }

  getTimeUntilNextWave(): number {
    if (this.waveActive) return 0;
    
    const now = Date.now();
    if (this.waveEndTime === 0) return 0;
    
    const timeUntilNext = Math.max(0, (this.waveEndTime + 30000 - now) / 1000); // 30 second break
    return timeUntilNext;
  }

  getCurrentWaveData(): Wave | null {
    if (this.currentWave === 0) return null;
    return this.waveData.find(w => w.wave === this.currentWave) || null;
  }

  getNextWaveData(): Wave | null {
    return this.waveData.find(w => w.wave === this.currentWave + 1) || null;
  }

  canStartNextWave(): boolean {
    if (this.waveActive) return false;
    if (this.getTimeUntilNextWave() > 0) return false;
    
    const nextWave = this.getNextWaveData();
    return nextWave !== null;
  }

  startNextWave(): boolean {
    if (!this.canStartNextWave()) return false;
    
    this.currentWave += 1;
    const waveData = this.getCurrentWaveData();
    
    if (!waveData) return false;
    
    this.waveActive = true;
    this.waveStartTime = Date.now();
    this.waveEndTime = 0;
    
    // Clear any existing enemies
    this.enemyManager.clearAll();
    
    // Spawn wave enemies
    this.enemyManager.spawnWave(waveData.enemies);
    
    receipt("wave:start", {
      wave: this.currentWave,
      tier: waveData.tier,
      duration: waveData.duration,
      enemyTypes: waveData.enemies.map(e => e.type),
      totalEnemies: waveData.enemies.reduce((sum, e) => sum + e.count, 0),
      rewards: waveData.rewards,
    });
    
    // Set wave end timer
    setTimeout(() => {
      this.endWave();
    }, waveData.duration * 1000);
    
    return true;
  }

  endWave(): void {
    if (!this.waveActive) return;
    
    const waveData = this.getCurrentWaveData();
    if (!waveData) return;
    
    this.waveActive = false;
    this.waveEndTime = Date.now();
    
    // Clear remaining enemies
    const remainingEnemies = this.enemyManager.getAll().length;
    this.enemyManager.clearAll();
    
    // Give wave completion rewards
    for (const [resourceType, amount] of Object.entries(waveData.rewards)) {
      this.resourceManager.add(resourceType as any, amount);
    }
    
    receipt("wave:end", {
      wave: this.currentWave,
      tier: waveData.tier,
      remainingEnemies,
      rewards: waveData.rewards,
      nextWaveAvailable: this.getNextWaveData() !== null,
    });
  }

  forceEndWave(): void {
    if (this.waveActive) {
      this.endWave();
    }
  }

  tick(deltaTime: number): void {
    if (!this.waveActive) return;
    
    const now = Date.now();
    const waveData = this.getCurrentWaveData();
    
    if (waveData && (now - this.waveStartTime) / 1000 >= waveData.duration) {
      this.endWave();
    }
    
    // Check if all enemies are defeated early
    if (this.enemyManager.getAll().length === 0 && this.waveActive) {
      // Wave completed early - bonus rewards
      const waveData = this.getCurrentWaveData();
      if (waveData) {
        const timeBonus = Math.max(0, waveData.duration - (now - this.waveStartTime) / 1000);
        const bonusMultiplier = 1 + (timeBonus / waveData.duration) * 0.5; // Up to 50% bonus
        
        receipt("wave:early_completion", {
          wave: this.currentWave,
          timeBonus,
          bonusMultiplier,
        });
        
        // Add bonus resources
        for (const [resourceType, amount] of Object.entries(waveData.rewards)) {
          const bonusAmount = Math.floor(amount * (bonusMultiplier - 1));
          if (bonusAmount > 0) {
            this.resourceManager.add(resourceType as any, bonusAmount);
          }
        }
      }
      
      this.endWave();
    }
  }

  // Get wave statistics
  getWaveStats() {
    const current = this.getCurrentWaveData();
    const next = this.getNextWaveData();
    
    return {
      currentWave: this.currentWave,
      isActive: this.waveActive,
      progress: this.getWaveProgress(),
      timeUntilNext: this.getTimeUntilNextWave(),
      currentWaveData: current,
      nextWaveData: next,
      canStart: this.canStartNextWave(),
      totalWaves: this.waveData.length,
    };
  }

  loadState(waveNumber: number, isActive: boolean, startTime?: number) {
    this.currentWave = waveNumber;
    this.waveActive = isActive;
    this.waveStartTime = startTime || 0;
    
    if (isActive && startTime) {
      const waveData = this.getCurrentWaveData();
      if (waveData) {
        const elapsed = (Date.now() - startTime) / 1000;
        if (elapsed >= waveData.duration) {
          this.endWave();
        } else {
          // Continue the wave
          setTimeout(() => {
            this.endWave();
          }, (waveData.duration - elapsed) * 1000);
        }
      }
    }

    receipt("wave:load_state", {
      wave: this.currentWave,
      isActive: this.waveActive,
      startTime: this.waveStartTime,
    });
  }
}