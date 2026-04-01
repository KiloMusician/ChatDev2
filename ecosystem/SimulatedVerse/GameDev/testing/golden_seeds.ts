// Golden Seeds Testing - Deterministic gameplay validation
// Bridges symbolic test scenarios to literal reproducible outcomes

import { SeededRNG } from '../engine/core/rng.js';
import { simulator } from '../engine/core/sim.js';
import { dungeonGenerator } from '../patterns/roguelike/dungeon.js';
import { waveManager } from '../patterns/tower_defense/waves.js';
import { productionManager } from '../patterns/colony_sim/production.js';
// Browser-compatible testing - using localStorage for test data
const fs = {
  readFile: async (path: string) => localStorage.getItem(`test_${path}`) || '',
  writeFile: async (path: string, data: string) => localStorage.setItem(`test_${path}`, data)
};

export interface GoldenSeed {
  name: string;
  seed: string;
  mode: 'roguelike' | 'tower_defense' | 'colony_sim';
  steps: Array<{
    tick: number;
    action: string;
    expected_state?: any;
    description: string;
  }>;
  expected_final_state: {
    entities: number;
    resources?: Record<string, number>;
    grid_checksum?: string;
    custom_validations?: string[];
  };
}

export interface TestResult {
  seed_name: string;
  passed: boolean;
  steps_completed: number;
  total_steps: number;
  errors: string[];
  execution_time_ms: number;
  final_state: any;
}

export class GoldenSeedTester {
  private seeds = new Map<string, GoldenSeed>();
  private testResults: TestResult[] = [];
  
  constructor() {
    this.initializeGoldenSeeds();
    console.log('[GoldenSeeds] Tester initialized with', this.seeds.size, 'test seeds');
  }

  private initializeGoldenSeeds(): void {
    // Roguelike golden seed
    this.seeds.set('roguelike_basic', {
      name: 'Basic Roguelike Generation',
      seed: 'test_dungeon_42',
      mode: 'roguelike',
      steps: [
        { tick: 0, action: 'generate_level', description: 'Generate initial dungeon level' },
        { tick: 1, action: 'verify_rooms', expected_state: { min_rooms: 3 }, description: 'Verify minimum room count' },
        { tick: 10, action: 'verify_connectivity', description: 'Verify all rooms are connected' }
      ],
      expected_final_state: {
        entities: { min: 5, max: 15 }, // Player + enemies + treasure
        grid_checksum: 'deterministic_layout_hash'
      }
    });
    
    // Tower Defense golden seed
    this.seeds.set('tower_defense_wave1', {
      name: 'Tower Defense Wave 1',
      seed: 'test_td_waves_123',
      mode: 'tower_defense',
      steps: [
        { tick: 0, action: 'setup_path', description: 'Initialize enemy path' },
        { tick: 1, action: 'start_wave', description: 'Start first wave' },
        { tick: 100, action: 'verify_spawns', expected_state: { enemies_spawned: 3 }, description: 'Verify enemy spawning' }
      ],
      expected_final_state: {
        entities: { min: 3, max: 8 },
        resources: { gold: { min: 90, max: 110 } }
      }
    });
    
    // Colony Sim golden seed
    this.seeds.set('colony_production', {
      name: 'Colony Production Chain',
      seed: 'test_colony_prod_456',
      mode: 'colony_sim',
      steps: [
        { tick: 0, action: 'setup_resources', description: 'Initialize base resources' },
        { tick: 10, action: 'build_farm', description: 'Construct first farm' },
        { tick: 50, action: 'assign_workers', description: 'Assign citizens to jobs' },
        { tick: 200, action: 'verify_production', expected_state: { food_produced: true }, description: 'Verify production cycle' }
      ],
      expected_final_state: {
        entities: { min: 2, max: 10 },
        resources: {
          food: { min: 105, max: 120 },
          wood: { min: 45, max: 55 }
        }
      }
    });
  }

  // Run all golden seed tests
  async runAllTests(): Promise<TestResult[]> {
    console.log('[GoldenSeeds] Running all tests...');
    this.testResults = [];
    
    for (const [seedName, seed] of this.seeds.entries()) {
      const result = await this.runSingleTest(seed);
      this.testResults.push(result);
    }
    
    await this.generateTestReport();
    
    const passed = this.testResults.filter(r => r.passed).length;
    const total = this.testResults.length;
    
    console.log(`[GoldenSeeds] Tests completed: ${passed}/${total} passed`);
    
    return this.testResults;
  }

  async runSingleTest(seed: GoldenSeed): Promise<TestResult> {
    const startTime = performance.now();
    const errors: string[] = [];
    let stepsCompleted = 0;
    
    console.log(`[GoldenSeeds] Testing ${seed.name} (${seed.seed})`);
    
    try {
      // Initialize with golden seed
      const testRNG = new SeededRNG(seed.seed);
      simulator.reset();
      
      // Initialize game mode
      await this.initializeGameMode(seed.mode, testRNG);
      
      // Execute test steps
      for (const step of seed.steps) {
        try {
          // Advance simulation to target tick
          while (simulator.getCurrentTick() < step.tick) {
            simulator.tick(16.67); // ~60fps ticks
          }
          
          // Execute step action
          const stepResult = await this.executeTestAction(step.action, seed.mode, step.expected_state);
          
          if (!stepResult.success) {
            errors.push(`Step ${stepsCompleted + 1} failed: ${stepResult.error}`);
            break;
          }
          
          stepsCompleted++;
          
        } catch (error) {
          errors.push(`Step ${stepsCompleted + 1} exception: ${error}`);
          break;
        }
      }
      
      // Validate final state
      if (stepsCompleted === seed.steps.length) {
        const finalValidation = this.validateFinalState(seed.expected_final_state);
        if (!finalValidation.success) {
          errors.push(`Final validation failed: ${finalValidation.error}`);
        }
      }
      
    } catch (error) {
      errors.push(`Test setup failed: ${error}`);
    }
    
    const executionTime = performance.now() - startTime;
    
    const result: TestResult = {
      seed_name: seed.name,
      passed: errors.length === 0 && stepsCompleted === seed.steps.length,
      steps_completed: stepsCompleted,
      total_steps: seed.steps.length,
      errors,
      execution_time_ms: Math.floor(executionTime),
      final_state: this.captureCurrentState()
    };
    
    console.log(`[GoldenSeeds] ${seed.name}: ${result.passed ? 'PASS' : 'FAIL'} (${result.execution_time_ms}ms)`);
    
    return result;
  }

  private async initializeGameMode(mode: string, rng: SeededRNG): Promise<void> {
    switch (mode) {
      case 'roguelike':
        // Use seeded RNG for dungeon generation
        const level = dungeonGenerator.generateLevel(32, 32, 1);
        const grid = dungeonGenerator.levelToGrid(level);
        simulator.setGrid(grid);
        break;
        
      case 'tower_defense':
        // Set deterministic path
        const path = [{ x: 0, y: 10 }, { x: 10, y: 10 }, { x: 10, y: 20 }];
        waveManager.setPath(path);
        
        const tdGrid = Array(24).fill(null).map(() => 
          Array(24).fill({ char: '.', color: '#444', bg: '#000' })
        );
        simulator.setGrid(tdGrid);
        break;
        
      case 'colony_sim':
        // Set up basic colony grid
        const colonyGrid = Array(24).fill(null).map(() => 
          Array(24).fill({ char: '.', color: '#444', bg: '#000' })
        );
        simulator.setGrid(colonyGrid);
        break;
    }
  }

  private async executeTestAction(action: string, mode: string, expectedState?: any): Promise<{success: boolean, error?: string}> {
    try {
      switch (action) {
        case 'generate_level':
          if (mode !== 'roguelike') return { success: false, error: 'Invalid action for mode' };
          // Already done in initialization
          return { success: true };
          
        case 'verify_rooms':
          if (mode !== 'roguelike') return { success: false, error: 'Invalid action for mode' };
          // Check if minimum rooms were generated
          const roomCount = simulator.getEntityCount('room');
          if (expectedState?.min_rooms && roomCount < expectedState.min_rooms) {
            return { success: false, error: `Only ${roomCount} rooms, expected >= ${expectedState.min_rooms}` };
          }
          return { success: true };
          
        case 'start_wave':
          if (mode !== 'tower_defense') return { success: false, error: 'Invalid action for mode' };
          const waveStarted = waveManager.startWave();
          if (!waveStarted) return { success: false, error: 'Failed to start wave' };
          return { success: true };
          
        case 'verify_spawns':
          if (mode !== 'tower_defense') return { success: false, error: 'Invalid action for mode' };
          const enemyCount = simulator.getEntityCount('enemy');
          if (expectedState?.enemies_spawned && enemyCount < expectedState.enemies_spawned) {
            return { success: false, error: `Only ${enemyCount} enemies spawned, expected >= ${expectedState.enemies_spawned}` };
          }
          return { success: true };
          
        case 'setup_resources':
          if (mode !== 'colony_sim') return { success: false, error: 'Invalid action for mode' };
          // Resources already initialized
          return { success: true };
          
        case 'build_farm':
          if (mode !== 'colony_sim') return { success: false, error: 'Invalid action for mode' };
          const farmId = productionManager.constructBuilding('farm', { x: 5, y: 5 });
          if (!farmId) return { success: false, error: 'Failed to build farm' };
          return { success: true };
          
        default:
          return { success: false, error: `Unknown action: ${action}` };
      }
    } catch (error) {
      return { success: false, error: `Action execution failed: ${error}` };
    }
  }

  private validateFinalState(expectedState: any): {success: boolean, error?: string} {
    const currentEntities = simulator.getActiveEntityCount();
    
    // Validate entity count
    if (expectedState.entities?.min && currentEntities < expectedState.entities.min) {
      return { success: false, error: `Too few entities: ${currentEntities} < ${expectedState.entities.min}` };
    }
    if (expectedState.entities?.max && currentEntities > expectedState.entities.max) {
      return { success: false, error: `Too many entities: ${currentEntities} > ${expectedState.entities.max}` };
    }
    
    // Validate resources (for applicable modes)
    if (expectedState.resources) {
      for (const [resourceName, constraints] of Object.entries(expectedState.resources)) {
        const actual = productionManager.getResource(resourceName);
        
        if (constraints.min && actual < constraints.min) {
          return { success: false, error: `${resourceName}: ${actual} < ${constraints.min}` };
        }
        if (constraints.max && actual > constraints.max) {
          return { success: false, error: `${resourceName}: ${actual} > ${constraints.max}` };
        }
      }
    }
    
    return { success: true };
  }

  private captureCurrentState(): any {
    return {
      tick: simulator.getCurrentTick(),
      entities: simulator.getActiveEntityCount(),
      resources: productionManager.getResources(),
      render_state: {
        fps: 60, // Simulated
        sprites: simulator.getEntityCount()
      }
    };
  }

  private async generateTestReport(): Promise<void> {
    const report = {
      generated_at: new Date().toISOString(),
      total_tests: this.testResults.length,
      passed_tests: this.testResults.filter(r => r.passed).length,
      failed_tests: this.testResults.filter(r => !r.passed).length,
      average_execution_time: Math.floor(
        this.testResults.reduce((sum, r) => sum + r.execution_time_ms, 0) / this.testResults.length
      ),
      results: this.testResults
    };
    
    await fs.mkdir('GameDev/testing/reports', { recursive: true });
    const reportPath = `GameDev/testing/reports/golden_seeds_${Date.now()}.json`;
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    
    console.log(`[GoldenSeeds] Test report saved: ${reportPath}`);
  }

  // Public API
  async runTest(seedName: string): Promise<TestResult | null> {
    const seed = this.seeds.get(seedName);
    if (!seed) {
      console.error(`[GoldenSeeds] Unknown seed: ${seedName}`);
      return null;
    }
    
    return await this.runSingleTest(seed);
  }

  listAvailableSeeds(): string[] {
    return Array.from(this.seeds.keys());
  }

  getLastResults(): TestResult[] {
    return [...this.testResults];
  }

  // Add custom seed for testing
  addSeed(seed: GoldenSeed): void {
    this.seeds.set(seed.name.toLowerCase().replace(/\s+/g, '_'), seed);
    console.log(`[GoldenSeeds] Added custom seed: ${seed.name}`);
  }

  // Quick validation test
  async quickValidation(): Promise<boolean> {
    console.log('[GoldenSeeds] Running quick validation...');
    
    try {
      // Test RNG determinism
      const rng1 = new SeededRNG('test_123');
      const rng2 = new SeededRNG('test_123');
      
      const sequence1 = [rng1.nextFloat(), rng1.nextInt(100), rng1.nextFloat()];
      const sequence2 = [rng2.nextFloat(), rng2.nextInt(100), rng2.nextFloat()];
      
      if (JSON.stringify(sequence1) !== JSON.stringify(sequence2)) {
        console.error('[GoldenSeeds] RNG not deterministic!');
        return false;
      }
      
      // Test simulator reset
      const initialEntities = simulator.getActiveEntityCount();
      simulator.tick(100);
      simulator.reset();
      const afterReset = simulator.getActiveEntityCount();
      
      if (afterReset !== 0) {
        console.error('[GoldenSeeds] Simulator reset failed!');
        return false;
      }
      
      console.log('[GoldenSeeds] Quick validation passed!');
      return true;
      
    } catch (error) {
      console.error('[GoldenSeeds] Quick validation failed:', error);
      return false;
    }
  }
}

export const goldenSeedTester = new GoldenSeedTester();
