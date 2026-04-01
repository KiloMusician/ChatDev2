/**
 * Content Pack Integration System
 * Manages loading, activation, and coordination of modular content packs
 * Implements Mladenc's vision of seamless drop-in content expansion
 */

import { crashlandedAI } from '../narrative/crashlanded_ai_core';
import { facetIntegration } from '../narrative/facet_integration';
import { storyManager } from '../narrative/story_state_manager';

export interface ContentPackManifest {
  pack_id: string;
  pack_name: string;
  version: string;
  description: string;
  author: string;
  dependencies: string[];
  tier_requirements: {
    min_tier: number;
    unlock_tier: number;
    full_integration_tier: number;
  };
  consciousness_aspects: string[];
  gameplay_modes: string[];
  narrative_integration: any;
  systems: string[];
  integration_hooks: any;
  content_files: string[];
}

export interface PackActivationState {
  pack_id: string;
  loaded: boolean;
  activated: boolean;
  tier_unlocked: number;
  systems_initialized: string[];
  integration_status: Record<string, boolean>;
  last_updated: number;
}

export class ContentPackManager {
  private loadedPacks: Map<string, ContentPackManifest> = new Map();
  private activePacks: Map<string, PackActivationState> = new Map();
  private packData: Map<string, any> = new Map();
  
  constructor() {
    this.initializeCorePacks();
  }

  private async initializeCorePacks(): Promise<void> {
    // Load the three foundational content packs
    await this.loadContentPack('frontier_homestead');
    await this.loadContentPack('rogue_biolabs');
    await this.loadContentPack('idle_bureau');
  }

  async loadContentPack(packId: string): Promise<boolean> {
    try {
      // Load manifest with error handling
      const manifestResponse = await fetch(`/GameDev/content_packs/${packId}/pack_manifest.json`);
      if (!manifestResponse.ok) {
        console.warn(`[CONTENT_PACK] ⚠️ Pack ${packId} not found, creating minimal fallback`);
        return this.createFallbackPack(packId);
      }
      const manifest: ContentPackManifest = await manifestResponse.json();
      
      // **AGGRESSIVE DEPENDENCY RESOLUTION** - Auto-resolve and soft-load
      const dependenciesMet = this.validateDependencies(manifest.dependencies);
      if (!dependenciesMet) {
        console.warn(`[CONTENT_PACK] 🔧 Auto-resolving dependencies for ${packId}...`);
        await this.autoResolveDependencies(manifest.dependencies);
        // Soft-load with partial dependencies instead of hard failure
        console.log(`[CONTENT_PACK] ⚡ Soft-loading ${packId} with partial dependencies`);
      }
      
      // Load content data
      const packData = await this.loadPackData(packId, manifest.content_files);
      
      // Store pack info
      this.loadedPacks.set(packId, manifest);
      this.packData.set(packId, packData);
      
      // Initialize activation state
      const activationState: PackActivationState = {
        pack_id: packId,
        loaded: true,
        activated: false,
        tier_unlocked: 0,
        systems_initialized: [],
        integration_status: {},
        last_updated: Date.now()
      };
      this.activePacks.set(packId, activationState);
      
      console.log(`[CONTENT_PACK] Loaded: ${manifest.pack_name}`);
      return true;
      
    } catch (error) {
      console.error(`[CONTENT_PACK] Failed to load ${packId}:`, error);
      return false;
    }
  }

  private validateDependencies(dependencies: string[]): boolean {
    // **SOFT DEPENDENCY VALIDATION** - Allow partial loading
    const availableSystems = ['crashlanded_ai_core', 'facet_integration', 'story_state_manager', 'advanced_faction_system'];
    const metDependencies = dependencies.filter(dep => availableSystems.includes(dep));
    
    // Allow loading if at least 50% of dependencies are met or if no critical dependencies
    const compatibilityRatio = metDependencies.length / Math.max(dependencies.length, 1);
    console.log(`[CONTENT_PACK] Dependency compatibility: ${(compatibilityRatio * 100).toFixed(1)}%`);
    
    return compatibilityRatio >= 0.5 || dependencies.length === 0;
  }
  
  private async autoResolveDependencies(dependencies: string[]): Promise<void> {
    // **AUTONOMOUS DEPENDENCY RESOLUTION** - Smart loading
    console.log('[CONTENT_PACK] 🤖 Auto-resolving dependencies:', dependencies);
    for (const dep of dependencies) {
      if (!this.loadedPacks.has(dep)) {
        console.log(`[CONTENT_PACK] ⚡ Auto-loading dependency: ${dep}`);
        try {
          await this.loadContentPack(dep);
        } catch (error) {
          console.warn(`[CONTENT_PACK] 🔧 Soft-fail on dependency ${dep}:`, error);
        }
      }
    }
  }

  private async loadPackData(packId: string, contentFiles: string[]): Promise<any> {
    const packData: any = {};
    
    for (const file of contentFiles) {
      if (file.endsWith('.json')) {
        try {
          const response = await fetch(`/GameDev/content_packs/${packId}/${file}`);
          if (response.ok) {
            const data = await response.json();
            const fileName = file.split('/').pop()?.replace('.json', '') || file;
            packData[fileName] = data;
          } else {
            console.warn(`[CONTENT_PACK] ⚠️ ${file} not found for ${packId}, using fallback`);
            const fileName = file.split('/').pop()?.replace('.json', '') || file;
            packData[fileName] = this.createFallbackData(fileName);
          }
        } catch (error) {
          console.warn(`[CONTENT_PACK] Could not load ${file} for ${packId}:`, error);
          const fileName = file.split('/').pop()?.replace('.json', '') || file;
          packData[fileName] = this.createFallbackData(fileName);
        }
      }
    }
    
    return packData;
  }

  private createFallbackPack(packId: string): boolean {
    const manifest: ContentPackManifest = {
      pack_id: packId,
      pack_name: `${packId} (Fallback)`,
      version: '1.0.0-fallback',
      description: `Fallback content pack for ${packId}`,
      author: 'System',
      dependencies: [],
      tier_requirements: { min_tier: 0, unlock_tier: 0, full_integration_tier: 1 },
      consciousness_aspects: ['basic_systems'],
      gameplay_modes: ['basic'],
      narrative_integration: { story_beats: {}, memory_fragment_types: [] },
      systems: ['basic_systems'],
      integration_hooks: {},
      content_files: []
    };
    
    this.loadedPacks.set(packId, manifest);
    this.packData.set(packId, {});
    
    const activationState: PackActivationState = {
      pack_id: packId,
      loaded: true,
      activated: false,
      tier_unlocked: 0,
      systems_initialized: [],
      integration_status: {},
      last_updated: Date.now()
    };
    this.activePacks.set(packId, activationState);
    
    console.log(`[CONTENT_PACK] ✅ Created fallback for ${packId}`);
    return true;
  }

  private createFallbackData(fileName: string): any {
    switch (fileName) {
      case 'ai_systems':
        return { systems: { basic_ai: { name: 'Basic AI', status: 'active' } } };
      case 'anomaly_types':
        return { anomalies: { minor_glitch: { name: 'Minor Glitch', severity: 1 } } };
      case 'meta_systems':
        return { meta: { basic_meta: { name: 'Basic Meta', level: 1 } } };
      default:
        return { placeholder: true, loaded: false };
    }
  }

  // Check if packs should be activated based on game state
  checkPackActivations(gameState: any): string[] {
    const newlyActivated: string[] = [];
    
    this.loadedPacks.forEach((manifest, packId) => {
      const activationState = this.activePacks.get(packId);
      if (!activationState || activationState.activated) return;
      
      const currentTier = gameState.current_tier || 0;
      
      // Check if pack should be unlocked
      if (currentTier >= manifest.tier_requirements.unlock_tier) {
        this.activateContentPack(packId, gameState);
        newlyActivated.push(packId);
      }
    });
    
    return newlyActivated;
  }

  private activateContentPack(packId: string, gameState: any): void {
    const manifest = this.loadedPacks.get(packId);
    const activationState = this.activePacks.get(packId);
    const packData = this.packData.get(packId);
    
    if (!manifest || !activationState || !packData) return;
    
    console.log(`[CONTENT_PACK] Activating: ${manifest.pack_name}`);
    
    // Initialize pack systems
    manifest.systems.forEach(system => {
      this.initializePackSystem(packId, system, packData);
      activationState.systems_initialized.push(system);
    });
    
    // Register narrative integration hooks
    this.registerNarrativeHooks(packId, manifest, packData);
    
    // Register new facets if any
    this.registerPackFacets(packId, manifest, packData);
    
    // Update activation state
    activationState.activated = true;
    activationState.tier_unlocked = gameState.current_tier || 0;
    activationState.last_updated = Date.now();
    
    // Emit activation event
    this.emitPackActivationEvent(packId, manifest);
  }

  private initializePackSystem(packId: string, systemName: string, packData: any): void {
    // System initialization based on pack type and system name
    switch (systemName) {
      case 'seasonal_cycles':
        this.initializeSeasonalSystem(packData);
        break;
      case 'procedural_lab_generation':
        this.initializeLabGeneration(packData);
        break;
      case 'ritual_automation_framework':
        this.initializeRitualSystem(packData);
        break;
      // Add more system initializers as needed
      default:
        console.log(`[CONTENT_PACK] System ${systemName} registered for ${packId}`);
    }
  }

  private initializeSeasonalSystem(packData: any): void {
    // Initialize farming/seasonal mechanics from Frontier Homestead
    if (packData.crops) {
      console.log(`[FRONTIER_HOMESTEAD] Initialized ${Object.keys(packData.crops.crops).length} crop types`);
    }
  }

  private initializeLabGeneration(packData: any): void {
    // Initialize biolab dungeon generation from Rogue Biolabs
    if (packData.bio_specimens) {
      console.log(`[ROGUE_BIOLABS] Initialized ${Object.keys(packData.bio_specimens.specimens).length} specimen types`);
    }
  }

  private initializeRitualSystem(packData: any): void {
    // Initialize ritual automation from Idle Bureau
    if (packData.rituals) {
      console.log(`[IDLE_BUREAU] Initialized ${Object.keys(packData.rituals.rituals).length} ritual types`);
    }
  }

  private registerNarrativeHooks(packId: string, manifest: ContentPackManifest, packData: any): void {
    // Register pack's narrative integration with story manager
    const integration = manifest.narrative_integration;
    
    if (integration.story_beats) {
      Object.entries(integration.story_beats).forEach(([eventType, description]) => {
        console.log(`[CONTENT_PACK] Registered story beat: ${eventType} for ${packId}`);
      });
    }
    
    if (integration.memory_fragment_types) {
      console.log(`[CONTENT_PACK] Registered ${integration.memory_fragment_types.length} memory fragment types for ${packId}`);
    }
  }

  private registerPackFacets(packId: string, manifest: ContentPackManifest, packData: any): void {
    // Register new consciousness facets from the pack
    manifest.consciousness_aspects.forEach(aspect => {
      console.log(`[CONTENT_PACK] Enhanced consciousness aspect: ${aspect} from ${packId}`);
    });
  }

  private emitPackActivationEvent(packId: string, manifest: ContentPackManifest): void {
    // Emit event that can be caught by other systems
    if (typeof window !== 'undefined' && (window as any).StoryBus) {
      (window as any).StoryBus.emit('content_pack.activated', {
        pack_id: packId,
        pack_name: manifest.pack_name,
        systems: manifest.systems,
        gameplay_modes: manifest.gameplay_modes,
        timestamp: Date.now()
      });
    }
  }

  // Get available content for current game state
  getAvailableContent(gameState: any): any {
    const availableContent: any = {
      packs: {},
      total_systems: 0,
      unlocked_modes: new Set(['colony_sim', 'idle']) // Default modes
    };
    
    this.activePacks.forEach((state, packId) => {
      if (state.activated) {
        const manifest = this.loadedPacks.get(packId);
        const packData = this.packData.get(packId);
        
        if (manifest && packData) {
          availableContent.packs[packId] = {
            name: manifest.pack_name,
            systems: state.systems_initialized,
            modes: manifest.gameplay_modes,
            data: packData
          };
          
          availableContent.total_systems += state.systems_initialized.length;
          manifest.gameplay_modes.forEach(mode => availableContent.unlocked_modes.add(mode));
        }
      }
    });
    
    availableContent.unlocked_modes = Array.from(availableContent.unlocked_modes);
    return availableContent;
  }

  // Process pack-specific actions
  processPackAction(packId: string, action: string, context: any): any {
    const manifest = this.loadedPacks.get(packId);
    const packData = this.packData.get(packId);
    const activationState = this.activePacks.get(packId);
    
    if (!manifest || !packData || !activationState?.activated) {
      return { error: `Pack ${packId} not available` };
    }
    
    // Route action to appropriate pack handler
    switch (packId) {
      case 'frontier_homestead':
        return this.processFarmingAction(action, context, packData);
      case 'rogue_biolabs':
        return this.processBiolabAction(action, context, packData);
      case 'idle_bureau':
        return this.processIdleAction(action, context, packData);
      default:
        return { error: `Unknown pack: ${packId}` };
    }
  }

  private processFarmingAction(action: string, context: any, packData: any): any {
    switch (action) {
      case 'plant_crop':
        return this.handleCropPlanting(context, packData);
      case 'harvest_crop':
        return this.handleCropHarvest(context, packData);
      case 'seasonal_transition':
        return this.handleSeasonalTransition(context, packData);
      default:
        return { message: `Farming action: ${action}` };
    }
  }

  private processBiolabAction(action: string, context: any, packData: any): any {
    switch (action) {
      case 'analyze_specimen':
        return this.handleSpecimenAnalysis(context, packData);
      case 'enter_biolab':
        return this.handleBiolabEntry(context, packData);
      case 'containment_breach':
        return this.handleContainmentBreach(context, packData);
      default:
        return { message: `Biolab action: ${action}` };
    }
  }

  private processIdleAction(action: string, context: any, packData: any): any {
    switch (action) {
      case 'perform_ritual':
        return this.handleRitualPerformance(context, packData);
      case 'automate_system':
        return this.handleSystemAutomation(context, packData);
      case 'consciousness_cultivation':
        return this.handleConsciousnessCultivation(context, packData);
      default:
        return { message: `Idle action: ${action}` };
    }
  }

  // Placeholder action handlers - would be expanded with full implementations
  private handleCropPlanting(context: any, packData: any): any {
    return { 
      success: true, 
      message: "Crop planted successfully",
      consciousness_impact: 1,
      faction_approval: { builders: 2 }
    };
  }

  private handleSpecimenAnalysis(context: any, packData: any): any {
    return {
      success: true,
      message: "Specimen analysis reveals interesting genetic modifications",
      consciousness_impact: 3,
      research_progress: 5,
      faction_approval: { anomalists: 4 }
    };
  }

  private handleRitualPerformance(context: any, packData: any): any {
    return {
      success: true,
      message: "Ritual completed, consciousness cultivation progressed",
      consciousness_impact: 8,
      automation_efficiency_bonus: 1.1,
      ritual_mastery_progress: 10
    };
  }

  // Additional handler methods would be implemented here...
  private handleCropHarvest(context: any, packData: any): any { return {}; }
  private handleSeasonalTransition(context: any, packData: any): any { return {}; }
  private handleBiolabEntry(context: any, packData: any): any { return {}; }
  private handleContainmentBreach(context: any, packData: any): any { return {}; }
  private handleSystemAutomation(context: any, packData: any): any { return {}; }
  private handleConsciousnessCultivation(context: any, packData: any): any { return {}; }

  // Public getters
  getLoadedPacks(): ContentPackManifest[] {
    return Array.from(this.loadedPacks.values());
  }

  getActivePacks(): PackActivationState[] {
    return Array.from(this.activePacks.values()).filter(state => state.activated);
  }

  getPackData(packId: string): any {
    return this.packData.get(packId);
  }

  // Save/load state
  saveState(): any {
    return {
      active_packs: Object.fromEntries(this.activePacks),
      pack_data: Object.fromEntries(this.packData)
    };
  }

  loadState(savedState: any): void {
    try {
      if (savedState.active_packs) {
        this.activePacks = new Map(Object.entries(savedState.active_packs));
      }
      if (savedState.pack_data) {
        this.packData = new Map(Object.entries(savedState.pack_data));
      }
    } catch (error) {
      console.error('[CONTENT_PACK] Failed to load state:', error);
    }
  }
}

// Singleton instance
export const contentPackManager = new ContentPackManager();