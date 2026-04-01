// Data Loader - Hot-reload game data files with versioned receipts
// Bridges symbolic data_breath to literal YAML/JSON loading with validation

// Browser-compatible data loading - using fetch for static files
import * as yaml from 'yaml';
const fs = {
  readFile: async (path: string) => {
    const response = await fetch(`/${path}`);
    return response.text();
  }
};
const watch = () => {}; // Browser - no file watching

export interface DataFile {
  path: string;
  type: 'yaml' | 'json';
  last_loaded: number;
  version: string;
  content: any;
  valid: boolean;
  errors: string[];
}

export interface DataManifest {
  tech_tree: string;
  buildings: string;
  enemies: string;
  recipes: string;
  upgrades: string;
  encounters: string;
  meta_layers: string;
}

export class DataLoader {
  private dataFiles = new Map<string, DataFile>();
  private watchers = new Map<string, any>();
  private devMode = process.env.NODE_ENV === 'development';

  private manifest: DataManifest = {
    tech_tree: 'GameDev/content/data/tech_tree.yml',
    buildings: 'GameDev/content/data/buildings.yml', 
    enemies: 'GameDev/content/data/enemies.yml',
    recipes: 'GameDev/content/data/recipes.yml',
    upgrades: 'GameDev/content/data/upgrades.yml',
    encounters: 'GameDev/content/data/encounters.yml',
    meta_layers: 'GameDev/content/data/meta_layers.yml'
  };

  constructor() {
    this.loadAllData();
    
    if (this.devMode) {
      this.setupHotReload();
    }
    
    console.log('[DataLoader] Data loading system initialized');
  }

  async loadAllData(): Promise<void> {
    console.log('[DataLoader] Loading all game data files...');
    
    const loadPromises = Object.entries(this.manifest).map(async ([key, path]) => {
      try {
        await this.loadDataFile(key, path);
      } catch (error) {
        console.warn(`[DataLoader] Failed to load ${key}:`, error);
        // Create placeholder data file to continue development
        await this.createPlaceholderData(key, path);
      }
    });

    await Promise.all(loadPromises);
    
    await this.emitLoadReceipt();
    console.log(`[DataLoader] Loaded ${this.dataFiles.size} data files`);
  }

  private async loadDataFile(key: string, path: string): Promise<void> {
    try {
      const content = await fs.readFile(path, 'utf8');
      const isYaml = path.endsWith('.yml') || path.endsWith('.yaml');
      
      let parsedContent: any;
      let errors: string[] = [];
      
      try {
        parsedContent = isYaml ? yaml.parse(content) : JSON.parse(content);
      } catch (parseError) {
        errors.push(`Parse error: ${parseError.message}`);
        parsedContent = {};
      }

      // Validate content structure
      const validationErrors = this.validateDataStructure(key, parsedContent);
      errors.push(...validationErrors);

      const dataFile: DataFile = {
        path,
        type: isYaml ? 'yaml' : 'json',
        last_loaded: Date.now(),
        version: this.calculateVersion(content),
        content: parsedContent,
        valid: errors.length === 0,
        errors
      };

      this.dataFiles.set(key, dataFile);
      
      if (dataFile.valid) {
        console.log(`[DataLoader] ✅ Loaded ${key}: ${path}`);
      } else {
        console.warn(`[DataLoader] ⚠️ Loaded ${key} with ${errors.length} errors`);
      }
      
    } catch (error) {
      console.error(`[DataLoader] Failed to load ${key}:`, error);
      throw error;
    }
  }

  private validateDataStructure(key: string, content: any): string[] {
    const errors: string[] = [];

    switch (key) {
      case 'tech_tree':
        if (!content.techs) errors.push('Missing techs section');
        if (!content.ui_phases) errors.push('Missing ui_phases section');
        break;
        
      case 'buildings':
        if (!content.buildings) errors.push('Missing buildings section');
        if (!content.categories) errors.push('Missing categories section');
        break;
        
      case 'enemies':
        if (!content.enemy_types) errors.push('Missing enemy_types section');
        if (!content.wave_templates) errors.push('Missing wave_templates section');
        break;
    }

    return errors;
  }

  private calculateVersion(content: string): string {
    // Simple content hash for versioning
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }

  private setupHotReload(): void {
    console.log('[DataLoader] Setting up hot-reload for development');
    
    for (const [key, path] of Object.entries(this.manifest)) {
      try {
        const watcher = watch(path, (eventType) => {
          if (eventType === 'change') {
            console.log(`[DataLoader] Hot-reloading ${key}: ${path}`);
            this.loadDataFile(key, path).catch(console.error);
          }
        });
        
        this.watchers.set(key, watcher);
      } catch (error) {
        console.warn(`[DataLoader] Could not watch ${path}:`, error);
      }
    }
  }

  private async createPlaceholderData(key: string, path: string): Promise<void> {
    const placeholders = {
      recipes: {
        recipes: {
          basic_energy_cell: {
            name: "Basic Energy Cell",
            inputs: { materials: 10 },
            outputs: { energy: 50 },
            craft_time: 15
          }
        }
      },
      upgrades: {
        upgrades: {
          efficient_panels: {
            name: "Efficient Solar Panels",
            cost: { energy: 500 },
            effect: { type: 'generation_multiplier', target: 'solar_panel', value: 1.5 }
          }
        }
      },
      encounters: {
        encounters: {
          merchant_visit: {
            name: "Traveling Merchant",
            description: "A merchant offers to trade supplies",
            choices: [
              { id: 'trade', text: 'Trade energy for materials', cost: { energy: 100 }, reward: { materials: 150 } },
              { id: 'decline', text: 'Send them away', reward: {} }
            ]
          }
        }
      },
      meta_layers: {
        prestige_levels: {
          1: { name: "First Transcendence", bonus: { generation_multiplier: 1.1 } },
          5: { name: "Quantum Mastery", bonus: { ui_unlock: "quantum_interface" } }
        }
      }
    };

    const placeholder = placeholders[key] || { [key]: {} };
    
    await fs.mkdir(path.substring(0, path.lastIndexOf('/')), { recursive: true });
    const content = path.endsWith('.yml') ? yaml.stringify(placeholder) : JSON.stringify(placeholder, null, 2);
    await fs.writeFile(path, content);
    
    console.log(`[DataLoader] Created placeholder: ${path}`);
    
    // Load the placeholder
    await this.loadDataFile(key, path);
  }

  // Get loaded data
  getData(key: string): any {
    const dataFile = this.dataFiles.get(key);
    return dataFile?.content || null;
  }

  // Check if data is valid
  isDataValid(key: string): boolean {
    const dataFile = this.dataFiles.get(key);
    return dataFile?.valid || false;
  }

  // Get data loading statistics
  getLoadStats(): any {
    const stats = {
      files_loaded: this.dataFiles.size,
      valid_files: Array.from(this.dataFiles.values()).filter(f => f.valid).length,
      hot_reload_enabled: this.devMode,
      watchers_active: this.watchers.size,
      last_load_time: Math.max(...Array.from(this.dataFiles.values()).map(f => f.last_loaded))
    };

    // Error summary
    const allErrors = Array.from(this.dataFiles.values()).flatMap(f => f.errors);
    stats['total_errors'] = allErrors.length;
    stats['error_breakdown'] = {};
    for (const error of allErrors) {
      const errorType = error.split(':')[0] || 'unknown';
      stats.error_breakdown[errorType] = (stats.error_breakdown[errorType] || 0) + 1;
    }

    return stats;
  }

  private async emitLoadReceipt(): Promise<void> {
    const receipt = {
      action: 'data_load',
      timestamp: Date.now(),
      files_loaded: Array.from(this.dataFiles.keys()),
      valid_files: Array.from(this.dataFiles.values()).filter(f => f.valid).length,
      total_errors: Array.from(this.dataFiles.values()).flatMap(f => f.errors).length,
      hot_reload: this.devMode,
      data_versions: Object.fromEntries(
        Array.from(this.dataFiles.entries()).map(([key, file]) => [key, file.version])
      )
    };

    try {
      await fs.mkdir('SystemDev/receipts/data', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/data/load_${Date.now()}.json`,
        JSON.stringify(receipt, null, 2)
      );
    } catch (error) {
      // Fail silently
    }
  }

  // Force reload specific data file
  async reloadData(key: string): Promise<boolean> {
    const path = this.manifest[key];
    if (!path) return false;

    try {
      await this.loadDataFile(key, path);
      console.log(`[DataLoader] Reloaded ${key}`);
      return true;
    } catch (error) {
      console.error(`[DataLoader] Reload failed for ${key}:`, error);
      return false;
    }
  }

  // Msg⛛ command interface
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Data:Reload' && parts.length === 2) {
      this.reloadData(parts[1]);
      return true;
    } else if (parts[0] === 'Data:ReloadAll') {
      this.loadAllData();
      return true;
    }
    
    return false;
  }

  destroy(): void {
    // Close all file watchers
    for (const watcher of this.watchers.values()) {
      watcher.close();
    }
    this.watchers.clear();
    console.log('[DataLoader] Destroyed');
  }
}

export const dataLoader = new DataLoader();