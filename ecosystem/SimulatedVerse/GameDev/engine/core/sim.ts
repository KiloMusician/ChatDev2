// Core Simulation Orchestrator - Deterministic tick orchestration
// Bridges symbolic sim_breath to literal systems execution order

import { TickBus } from './time/TickBus.js';
import { Registry, type EntityId } from './entity/Registry.js';
import { EventHub, type GameEvent } from './events/EventHub.js';
import { SaveCodec } from './save/SaveCodec.js';
import { spatialGrid } from './spatial.js';
import { campaignRNG, initCampaignRNG } from './rng.js';

export interface InputFrame {
  timestamp: number;
  commands: Array<{
    type: string;
    data: any;
    entity_id?: EntityId;
  }>;
  mouse?: { x: number; y: number; click?: boolean };
  keyboard?: { keys: string[]; pressed: string[]; released: string[]; };
}

export interface SimState {
  tick: number;
  time: number;
  paused: boolean;
  speed: number;
  
  // Core systems
  registry: Registry;
  eventHub: EventHub;
  saveCodec: SaveCodec;
  
  // Current input
  inputBuffer: InputFrame[];
  
  // Render state
  renderState: RenderState;
  
  // Systems list (executed in order)
  systems: GameSystem[];
  
  // Session tracking
  campaign_id: string;
  planet_seed: number;
  session_id: string;
}

export interface RenderState {
  viewport: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  
  // ASCII rendering
  grid: Array<Array<{
    char: string;
    color?: string;
    bg?: string;
  }>>;
  
  // Pixel rendering
  sprites: Array<{
    key: string;
    x: number;
    y: number;
    layer: number;
    scale?: number;
    rotation?: number;
  }>;
  
  // UI overlays
  hud: {
    resources: Record<string, any>;
    messages: string[];
    tooltips: Array<{x: number, y: number, text: string}>;
  };
  
  // Metrics
  fps: number;
  frame: number;
}

export interface GameSystem {
  name: string;
  priority: number;
  enabled: boolean;
  run(state: SimState, deltaTime: number): void;
}

// Core simulation class
export class SimEngine {
  private state: SimState;
  private tickBus: TickBus;
  private lastTick: number = 0;
  private targetFPS: number = 60;
  private systems: GameSystem[] = [];
  
  constructor(campaignId: string = 'default', planetSeed: number = 1337) {
    // Initialize RNG first
    initCampaignRNG(campaignId, planetSeed);
    
    // Initialize core systems
    const registry = new Registry();
    const eventHub = new EventHub();
    const saveCodec = new SaveCodec();
    const tickBus = new TickBus();
    
    this.state = {
      tick: 0,
      time: 0,
      paused: false,
      speed: 1.0,
      
      registry,
      eventHub,
      saveCodec,
      
      inputBuffer: [],
      
      renderState: {
        viewport: { x: 0, y: 0, width: 80, height: 24 },
        grid: [],
        sprites: [],
        hud: { resources: {}, messages: [], tooltips: [] },
        fps: 60,
        frame: 0
      },
      
      systems: [],
      
      campaign_id: campaignId,
      planet_seed: planetSeed,
      session_id: `session_${Date.now()}`
    };
    
    this.tickBus = tickBus;
    this.initializeRenderGrid();
    
    console.log(`[SimEngine] Initialized campaign: ${campaignId}, seed: ${planetSeed}`);
  }

  private initializeRenderGrid(): void {
    const { width, height } = this.state.renderState.viewport;
    this.state.renderState.grid = [];
    
    for (let y = 0; y < height; y++) {
      const row = [];
      for (let x = 0; x < width; x++) {
        row.push({ char: ' ', color: '#ffffff', bg: '#000000' });
      }
      this.state.renderState.grid.push(row);
    }
  }

  // Register a game system
  addSystem(system: GameSystem): void {
    this.systems.push(system);
    this.systems.sort((a, b) => a.priority - b.priority);
    console.log(`[SimEngine] Added system: ${system.name} (priority: ${system.priority})`);
  }

  // Main simulation step - called by tick bus
  stepSim(deltaTime: number): void {
    if (this.state.paused) return;
    
    const frameStart = performance.now();
    
    // 1. Process buffered inputs
    this.processInputs();
    
    // 2. Run all systems in priority order
    const adjustedDelta = deltaTime * this.state.speed;
    for (const system of this.systems) {
      if (system.enabled) {
        try {
          system.run(this.state, adjustedDelta);
        } catch (error) {
          console.error(`[SimEngine] System ${system.name} failed:`, error);
          // Continue with other systems
        }
      }
    }
    
    // 3. Update render state
    this.updateRenderState();
    
    // 4. Emit tick event
    this.state.eventHub.publish('simulation_tick', {
      tick: this.state.tick,
      time: this.state.time,
      deltaTime: adjustedDelta
    }, 'sim_engine');
    
    // 5. Update counters
    this.state.tick++;
    this.state.time += adjustedDelta;
    
    // 6. Calculate performance
    const frameTime = performance.now() - frameStart;
    this.state.renderState.fps = 1000 / Math.max(frameTime, 1);
    this.state.renderState.frame++;
  }

  private processInputs(): void {
    // Process all buffered inputs
    for (const inputFrame of this.state.inputBuffer) {
      for (const command of inputFrame.commands) {
        this.state.eventHub.publish('input_command', command, 'input_system');
      }
    }
    
    // Clear buffer
    this.state.inputBuffer = [];
  }

  private updateRenderState(): void {
    // Clear previous render data
    this.state.renderState.sprites = [];
    
    // Update viewport tiles for ASCII rendering
    const { viewport } = this.state.renderState;
    const tiles = spatialGrid.getViewportTiles(
      viewport.x + Math.floor(viewport.width / 2),
      viewport.y + Math.floor(viewport.height / 2),
      viewport.width,
      viewport.height
    );
    
    // Update grid for ASCII
    for (let i = 0; i < tiles.length; i++) {
      const tile = tiles[i];
      const gridX = i % viewport.width;
      const gridY = Math.floor(i / viewport.width);
      
      if (gridY < this.state.renderState.grid.length && gridX < this.state.renderState.grid[gridY].length) {
        this.state.renderState.grid[gridY][gridX] = {
          char: tile.char || (tile.visible ? (tile.type === 'wall' ? '#' : '.') : ' '),
          color: tile.visible ? '#ffffff' : '#444444',
          bg: '#000000'
        };
      }
    }
    
    // Add entities as sprites
    for (const [entityId, position] of spatialGrid.entityPositions) {
      const entity = this.state.registry.getEntity(entityId);
      if (entity) {
        const sprite = entity.components.get('sprite');
        if (sprite) {
          this.state.renderState.sprites.push({
            key: sprite.key || 'entity_default',
            x: position.x * 16, // Assuming 16x16 tiles
            y: position.y * 16,
            layer: sprite.layer || 0,
            scale: sprite.scale || 1,
            rotation: sprite.rotation || 0
          });
        }
      }
    }
    
    // Sort sprites by layer
    this.state.renderState.sprites.sort((a, b) => a.layer - b.layer);
  }

  // Public API
  addInput(inputFrame: InputFrame): void {
    this.state.inputBuffer.push(inputFrame);
  }

  pause(): void {
    this.state.paused = true;
    console.log('[SimEngine] Simulation paused');
  }

  resume(): void {
    this.state.paused = false;
    console.log('[SimEngine] Simulation resumed');
  }

  setSpeed(speed: number): void {
    this.state.speed = Math.max(0.1, Math.min(10, speed));
    console.log(`[SimEngine] Speed set to ${this.state.speed}x`);
  }

  getState(): SimState {
    return this.state;
  }

  getRenderState(): RenderState {
    return this.state.renderState;
  }

  // Start the simulation
  start(): void {
    console.log('[SimEngine] Starting simulation loop');
    
    this.tickBus.subscribe('simulation', (deltaTime) => {
      this.stepSim(deltaTime);
    });
    
    // Set appropriate tick rate
    this.tickBus.setRate('simulation', this.targetFPS);
  }

  // Stop the simulation
  stop(): void {
    console.log('[SimEngine] Stopping simulation');
    this.tickBus.destroy();
  }

  // Save current state
  async save(): Promise<void> {
    await this.state.saveCodec.saveDiff({
      timestamp: Date.now(),
      changes: {
        tick: this.state.tick,
        time: this.state.time,
        entities: this.state.registry.getAllEntities().length,
        campaign_progress: 'active'
      },
      change_type: 'progression'
    });
  }

  // Load from save
  async load(saveData: any): Promise<void> {
    // Implement save loading logic
    console.log('[SimEngine] Loading from save data');
  }

  // Create snapshot for testing
  snapshot(): any {
    return {
      tick: this.state.tick,
      time: this.state.time,
      entity_count: this.state.registry.getAllEntities().length,
      campaign_id: this.state.campaign_id,
      planet_seed: this.state.planet_seed,
      rng_state: campaignRNG.getState()
    };
  }

  // Restore from snapshot
  restore(snapshot: any): void {
    this.state.tick = snapshot.tick;
    this.state.time = snapshot.time;
    campaignRNG.setState(snapshot.rng_state);
    console.log(`[SimEngine] Restored to tick ${snapshot.tick}`);
  }
}

// Global simulation instance
export let simEngine: SimEngine;
export const simulator = simEngine; // Alias for GameEnginePanel compatibility

export function initSimEngine(campaignId: string = 'default', planetSeed: number = 1337): SimEngine {
  simEngine = new SimEngine(campaignId, planetSeed);
  return simEngine;
}
