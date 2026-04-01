// Save/Load System - Core Game Persistence
// Handles chunked diffs, autosave, and version migration

// Browser-compatible storage (using localStorage/IndexedDB instead of fs)
const fs = {
  writeFile: async (path: string, data: string) => {
    localStorage.setItem(`save_${path}`, data);
  },
  readFile: async (path: string) => {
    return localStorage.getItem(`save_${path}`) || '';
  }
};
import { registry } from '../entity/Registry.js';

export interface SaveDiff {
  timestamp: number;
  changes: Record<string, any>;
  change_type: 'resource' | 'building' | 'research' | 'progression' | 'settings';
}

export interface SaveData {
  version: string;
  timestamp: number;
  player_id: string;
  game_session_id: string;
  
  // Core game state
  resources: Record<string, any>;
  research_progress: Record<string, any>;
  buildings: Array<any>;
  citizens: Array<any>;
  
  // Progression state
  unlocked_features: string[];
  completed_quests: string[];
  prestige_data: any;
  
  // Settings and preferences
  ui_phase: number;
  game_speed: number;
  audio_settings: any;
  
  // Metrics for analytics
  session_stats: any;
  playtime_seconds: number;
}

export interface SaveDiff {
  timestamp: number;
  changes: Record<string, any>;
  change_type: 'resource' | 'building' | 'research' | 'progression' | 'settings';
}

export class SaveCodec {
  private currentSave: SaveData | null = null;
  private autoSaveInterval: NodeJS.Timeout | null = null;
  private autoSaveEnabled = true;
  private autoSaveIntervalMs = 30000; // 30 seconds
  private sessionStartTime = Date.now();
  private lastSaveTime = 0;

  constructor() {
    this.initializeAutoSave();
    console.log('[SaveCodec] Save system initialized');
  }

  async createNewSave(playerId: string = 'player_1'): Promise<SaveData> {
    const newSave: SaveData = {
      version: '1.0.0',
      timestamp: Date.now(),
      player_id: playerId,
      game_session_id: `session_${Date.now()}`,
      
      resources: {
        energy: { amount: 100, generation: 0 },
        materials: { amount: 0, generation: 0 },
        research: { amount: 0, generation: 0 }
      },
      
      research_progress: {},
      buildings: [],
      citizens: [],
      
      unlocked_features: ['basic_ui'],
      completed_quests: [],
      prestige_data: { level: 0, currency: 0 },
      
      ui_phase: 0,
      game_speed: 1.0,
      audio_settings: { master: 0.8, effects: 0.7, music: 0.5 },
      
      session_stats: {
        clicks: 0,
        buildings_built: 0,
        enemies_killed: 0,
        waves_completed: 0
      },
      
      playtime_seconds: 0
    };

    this.currentSave = newSave;
    await this.saveToDisk();
    
    console.log(`[SaveCodec] Created new save for ${playerId}`);
    return newSave;
  }

  async loadSave(filename: string = 'game_save.json'): Promise<SaveData | null> {
    try {
      const content = await fs.readFile(`saves/${filename}`, 'utf8');
      const saveData: SaveData = JSON.parse(content);
      
      // Calculate offline time
      const offlineSeconds = (Date.now() - saveData.timestamp) / 1000;
      
      // Migrate save version if needed
      const migratedSave = await this.migrateSave(saveData);
      
      this.currentSave = migratedSave;
      this.lastSaveTime = saveData.timestamp;
      
      console.log(`[SaveCodec] Loaded save: ${filename} (${offlineSeconds.toFixed(1)}s offline)`);
      
      // Process offline time if game systems are available
      if (offlineSeconds > 60) { // Only process if offline for more than 1 minute
        await this.processOfflineTime(offlineSeconds);
      }
      
      return this.currentSave;
      
    } catch (error) {
      console.warn(`[SaveCodec] Failed to load save ${filename}:`, error);
      return null;
    }
  }

  async saveToDisk(filename: string = 'game_save.json'): Promise<boolean> {
    if (!this.currentSave) {
      console.warn('[SaveCodec] No save data to write');
      return false;
    }

    try {
      // Update playtime
      this.currentSave.playtime_seconds += (Date.now() - this.sessionStartTime) / 1000;
      this.currentSave.timestamp = Date.now();
      
      // Ensure saves directory exists
      await fs.mkdir('saves', { recursive: true });
      
      // Create backup of previous save
      const savePath = `saves/${filename}`;
      const backupPath = `saves/${filename}.backup`;
      
      try {
        await fs.copyFile(savePath, backupPath);
      } catch {
        // Backup failed, but continue with save
      }
      
      // Write new save
      await fs.writeFile(savePath, JSON.stringify(this.currentSave, null, 2));
      
      this.lastSaveTime = Date.now();
      console.log(`[SaveCodec] Saved game: ${filename}`);
      
      // Emit save receipt
      await this.emitSaveReceipt('manual_save', filename);
      
      return true;
      
    } catch (error) {
      console.error('[SaveCodec] Save failed:', error);
      return false;
    }
  }

  // Update specific parts of save data
  updateSave(updates: Partial<SaveData>): void {
    if (!this.currentSave) return;

    // Deep merge updates
    this.currentSave = { ...this.currentSave, ...updates };
    
    // Track what changed for differential saves
    this.trackChanges(updates);
  }

  // Update resources specifically
  updateResources(resourceUpdates: Record<string, any>): void {
    if (!this.currentSave) return;

    this.currentSave.resources = { ...this.currentSave.resources, ...resourceUpdates };
  }

  // Save incremental diff
  async saveDiff(diff: SaveDiff): Promise<void> {
    if (!this.currentSave) return;
    
    // Apply diff to current save
    Object.assign(this.currentSave, diff.changes);
    
    // Write receipt
    const receipt = {
      diff_applied: {
        timestamp: diff.timestamp,
        change_type: diff.change_type,
        changes_count: Object.keys(diff.changes).length
      }
    };
    
    await fs.mkdir('SystemDev/receipts/saves', { recursive: true });
    await fs.writeFile(`SystemDev/receipts/saves/diff_${Date.now()}.json`, JSON.stringify(receipt, null, 2));
  }

  // Add unlocked feature
  unlockFeature(featureId: string): boolean {
    if (!this.currentSave) return false;

    if (!this.currentSave.unlocked_features.includes(featureId)) {
      this.currentSave.unlocked_features.push(featureId);
      console.log(`[SaveCodec] Unlocked feature: ${featureId}`);
      return true;
    }
    return false;
  }

  // Check if feature is unlocked
  isFeatureUnlocked(featureId: string): boolean {
    return this.currentSave?.unlocked_features.includes(featureId) || false;
  }

  // Auto-save system
  private initializeAutoSave(): void {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
    }

    this.autoSaveInterval = setInterval(() => {
      if (this.autoSaveEnabled && this.currentSave) {
        this.saveToDisk('autosave.json').then(success => {
          if (success) {
            this.emitSaveReceipt('auto_save', 'autosave.json');
          }
        });
      }
    }, this.autoSaveIntervalMs);
  }

  setAutoSave(enabled: boolean, intervalMs = 30000): void {
    this.autoSaveEnabled = enabled;
    this.autoSaveIntervalMs = intervalMs;
    
    if (enabled) {
      this.initializeAutoSave();
    } else if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }
    
    console.log(`[SaveCodec] Auto-save ${enabled ? 'enabled' : 'disabled'} (${intervalMs}ms)`);
  }

  private async processOfflineTime(offlineSeconds: number): Promise<void> {
    console.log(`[SaveCodec] Processing ${offlineSeconds.toFixed(1)}s of offline time`);
    
    // Cap offline progression to prevent exploits
    const maxOfflineHours = 24;
    const cappedSeconds = Math.min(offlineSeconds, maxOfflineHours * 3600);
    
    // Calculate offline resource generation
    if (this.currentSave) {
      for (const [resourceId, resourceData] of Object.entries(this.currentSave.resources)) {
        if (resourceData.generation > 0) {
          const generated = resourceData.generation * cappedSeconds;
          resourceData.amount = (resourceData.amount || 0) + generated;
          
          console.log(`[SaveCodec] Offline generation: ${resourceId} +${generated.toFixed(1)}`);
        }
      }
      
      // Update playtime to include offline time
      this.currentSave.playtime_seconds += cappedSeconds;
    }
  }

  private async migrateSave(saveData: SaveData): Promise<SaveData> {
    // Handle save version migrations
    if (saveData.version === '1.0.0') {
      return saveData; // Current version, no migration needed
    }

    // Example migration from hypothetical older version
    if (saveData.version === '0.9.0') {
      console.log('[SaveCodec] Migrating save from v0.9.0 to v1.0.0');
      
      // Add new fields with defaults
      saveData.ui_phase = saveData.ui_phase || 0;
      saveData.session_stats = saveData.session_stats || { clicks: 0, buildings_built: 0, enemies_killed: 0, waves_completed: 0 };
      saveData.version = '1.0.0';
    }

    return saveData;
  }

  private trackChanges(updates: Partial<SaveData>): void {
    // Track changes for differential saves (future optimization)
    const diff: SaveDiff = {
      timestamp: Date.now(),
      changes: updates,
      change_type: this.inferChangeType(updates)
    };

    // For now, just log significant changes
    if (diff.change_type !== 'settings') {
      console.log(`[SaveCodec] Tracked change: ${diff.change_type}`);
    }
  }

  private inferChangeType(updates: Partial<SaveData>): SaveDiff['change_type'] {
    if (updates.resources) return 'resource';
    if (updates.buildings) return 'building';
    if (updates.research_progress) return 'research';
    if (updates.unlocked_features || updates.completed_quests) return 'progression';
    return 'settings';
  }

  private async emitSaveReceipt(saveType: string, filename: string): Promise<void> {
    const receipt = {
      action: 'game_save',
      save_type: saveType,
      filename,
      timestamp: Date.now(),
      save_size_entities: this.currentSave ? Object.keys(this.currentSave).length : 0,
      session_playtime: this.currentSave?.playtime_seconds || 0,
      ui_phase: this.currentSave?.ui_phase || 0
    };

    try {
      await fs.mkdir('SystemDev/receipts/saves', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/saves/${saveType}_${Date.now()}.json`,
        JSON.stringify(receipt, null, 2)
      );
    } catch {
      // Fail silently
    }
  }

  getCurrentSave(): SaveData | null {
    return this.currentSave;
  }

  destroy(): void {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }
    console.log('[SaveCodec] Destroyed');
  }
}

export const saveCodec = new SaveCodec();