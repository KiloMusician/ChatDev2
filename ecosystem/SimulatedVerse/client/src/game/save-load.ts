import { GameState, SaveData, GameStateSchema, SaveDataSchema } from "./schemas";
import { ResourceManager } from "./resources";
import { StructureManager } from "./structures";
import { EnemyManager } from "./enemies";
import { WaveManager } from "./waves";
import { receipt } from "./receipts";
import { nanoid } from "nanoid";

export class SaveLoadManager {
  private saveKey = "corelink_save_data";
  private autoSaveInterval: number = 30000; // 30 seconds
  private autoSaveTimer: NodeJS.Timeout | null = null;

  constructor(
    private resourceManager: ResourceManager,
    private structureManager: StructureManager,
    private enemyManager: EnemyManager,
    private waveManager: WaveManager
  ) {
    this.startAutoSave();
  }

  private startAutoSave() {
    this.autoSaveTimer = setInterval(() => {
      this.quickSave();
    }, this.autoSaveInterval);
  }

  stopAutoSave() {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
  }

  createGameState(): GameState {
    const now = Date.now();
    const waveStats = this.waveManager.getWaveStats();
    
    const gameState: GameState = {
      version: "1.0.0",
      created: now,
      lastSaved: now,
      playTime: now, // This should be tracked properly
      currentTier: Math.max(1, Math.floor(this.resourceManager.getAmount("research") / 100) + 1),
      currentWave: waveStats.currentWave,
      waveActive: waveStats.isActive,
      waveStartTime: waveStats.isActive ? Date.now() - (waveStats.progress * (waveStats.currentWaveData?.duration || 30) * 1000) : undefined,
      resources: this.resourceManager.getAll(),
      structures: this.structureManager.getAll(),
      enemies: this.enemyManager.getAll(),
      unlockedStructures: this.getUnlockedStructures(),
      achievements: this.getAchievements(),
      settings: {
        autoSave: true,
        autoSaveInterval: this.autoSaveInterval,
        soundEnabled: true,
        difficulty: "normal",
      },
    };

    return gameState;
  }

  private getUnlockedStructures() {
    // Simple unlock logic based on current tier
    const tier = Math.max(1, Math.floor(this.resourceManager.getAmount("research") / 100) + 1);
    const unlocked = ["generator"];
    
    if (tier >= 1) unlocked.push("storage", "turret");
    if (tier >= 2) unlocked.push("converter", "wall");
    if (tier >= 3) unlocked.push("research_lab");
    
    return unlocked as any[];
  }

  private getAchievements(): string[] {
    const achievements: string[] = [];
    
    // Check various achievements
    if (this.resourceManager.getAmount("energy") >= 1000) {
      achievements.push("energy_collector");
    }
    if (this.structureManager.getAll().length >= 10) {
      achievements.push("master_builder");
    }
    if (this.waveManager.getCurrentWave() >= 5) {
      achievements.push("wave_survivor");
    }
    
    return achievements;
  }

  save(saveId?: string): boolean {
    try {
      const gameState = this.createGameState();
      const saveData: SaveData = {
        gameState,
        receipts: [], // Could store recent receipts if needed
        metadata: {
          saveId: saveId || nanoid(),
          playerName: "Player",
          achievements: this.getAchievements().length,
          totalPlayTime: gameState.playTime,
          highestTier: gameState.currentTier,
          totalWaves: gameState.currentWave,
        },
      };

      // Validate save data
      const validatedSave = SaveDataSchema.parse(saveData);
      
      // Save to localStorage
      localStorage.setItem(this.saveKey, JSON.stringify(validatedSave));
      
      receipt("save:create", {
        saveId: validatedSave.metadata.saveId,
        tier: gameState.currentTier,
        wave: gameState.currentWave,
        resources: Object.fromEntries(
          Object.entries(gameState.resources).map(([type, resource]) => [type, resource.amount])
        ),
        structures: gameState.structures.length,
        enemies: gameState.enemies.length,
        achievements: validatedSave.metadata.achievements,
      });

      return true;
    } catch (error) {
      receipt("save:error", {
        error: error instanceof Error ? error.message : "Unknown error",
        type: "save",
      });
      console.error("Save failed:", error);
      return false;
    }
  }

  load(): boolean {
    try {
      const saveDataString = localStorage.getItem(this.saveKey);
      if (!saveDataString) {
        receipt("load:no_save", {});
        return false;
      }

      const saveData = JSON.parse(saveDataString);
      const validatedSave = SaveDataSchema.parse(saveData);
      const gameState = validatedSave.gameState;

      // Load into managers
      this.resourceManager.loadState(gameState.resources as any);
      this.structureManager.loadState(gameState.structures);
      this.enemyManager.loadState(gameState.enemies);
      this.waveManager.loadState(
        gameState.currentWave, 
        gameState.waveActive, 
        gameState.waveStartTime
      );

      receipt("save:load", {
        saveId: validatedSave.metadata.saveId,
        version: gameState.version,
        tier: gameState.currentTier,
        wave: gameState.currentWave,
        playTime: gameState.playTime,
        structures: gameState.structures.length,
        enemies: gameState.enemies.length,
        achievements: validatedSave.metadata.achievements,
      });

      return true;
    } catch (error) {
      receipt("save:error", {
        error: error instanceof Error ? error.message : "Unknown error",
        type: "load",
      });
      console.error("Load failed:", error);
      return false;
    }
  }

  quickSave(): boolean {
    return this.save();
  }

  hasSave(): boolean {
    return localStorage.getItem(this.saveKey) !== null;
  }

  deleteSave(): boolean {
    try {
      localStorage.removeItem(this.saveKey);
      receipt("save:delete", {});
      return true;
    } catch (error) {
      receipt("save:error", {
        error: error instanceof Error ? error.message : "Unknown error",
        type: "delete",
      });
      return false;
    }
  }

  exportSave(): string | null {
    try {
      const saveDataString = localStorage.getItem(this.saveKey);
      if (!saveDataString) return null;
      
      // Create exportable format with metadata
      const exportData = {
        version: "1.0.0",
        exported: Date.now(),
        data: JSON.parse(saveDataString),
      };

      receipt("save:export", {
        size: saveDataString.length,
        timestamp: exportData.exported,
      });

      return JSON.stringify(exportData, null, 2);
    } catch (error) {
      receipt("save:error", {
        error: error instanceof Error ? error.message : "Unknown error",
        type: "export",
      });
      return null;
    }
  }

  importSave(saveString: string): boolean {
    try {
      const importData = JSON.parse(saveString);
      
      // Validate import data structure
      if (!importData.data || !importData.version) {
        throw new Error("Invalid save format");
      }

      // Validate the actual save data
      const validatedSave = SaveDataSchema.parse(importData.data);
      
      // Store the imported save
      localStorage.setItem(this.saveKey, JSON.stringify(validatedSave));
      
      receipt("save:import", {
        version: importData.version,
        imported: Date.now(),
        saveId: validatedSave.metadata.saveId,
      });

      return true;
    } catch (error) {
      receipt("save:error", {
        error: error instanceof Error ? error.message : "Unknown error",
        type: "import",
      });
      return false;
    }
  }

  getSaveInfo() {
    try {
      const saveDataString = localStorage.getItem(this.saveKey);
      if (!saveDataString) return null;

      const saveData = JSON.parse(saveDataString);
      const validatedSave = SaveDataSchema.parse(saveData);

      return {
        saveId: validatedSave.metadata.saveId,
        lastSaved: validatedSave.gameState.lastSaved,
        tier: validatedSave.gameState.currentTier,
        wave: validatedSave.gameState.currentWave,
        playTime: validatedSave.gameState.playTime,
        achievements: validatedSave.metadata.achievements,
        version: validatedSave.gameState.version,
      };
    } catch (error) {
      return null;
    }
  }
}