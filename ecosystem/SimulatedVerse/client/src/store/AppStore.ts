// client/src/store/AppStore.ts
// Zustand + Immer state management for tripartite architecture
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';

// System State (Node/TS backend coordination)
interface SystemState {
  health: {
    build_success_rate: number;
    agent_joy_average: number; 
    cognitive_load: number;
    event_throughput: number;
    invariance_score: number;
  };
  pu_queue: {
    total: number;
    completed: number;
    next_task?: string;
    active_agents: number;
  };
  consciousness: {
    level: number;
    active_tasks: string[];
    completed_tasks: string[];
  };
  errors: string[];
}

// Game/UI State
interface GameState {
  resources: {
    energy: number;
    materials: number;
    components: number;
    population: number;
    research: number;
  };
  unlocked_views: string[];
  current_view: string;
  automation_level: number;
}

// Simulation State
interface SimulationState {
  tower_defense: {
    turrets: Array<{ id: string; x: number; y: number; type: string }>;
    waves: Array<{ id: string; enemies: number; difficulty: number }>;
    score: number;
  };
  exploration: {
    discovered_tiles: Array<{ x: number; y: number; biome: string }>;
    current_position: { x: number; y: number };
    inventory: Record<string, number>;
  };
}

// Combined App State
interface AppState {
  system: SystemState;
  game: GameState;
  simulation: SimulationState;
  
  // Actions
  updateSystem: (updates: Partial<SystemState>) => void;
  updateGame: (updates: Partial<GameState>) => void;
  updateSimulation: (updates: Partial<SimulationState>) => void;
  
  // Complex actions
  processConsciousnessUpdate: (level: number, tasks: string[]) => void;
  unlockView: (viewName: string) => void;
  addError: (error: string) => void;
  clearErrors: () => void;
}

// Create the store with immer for immutable updates
export const useAppStore = create<AppState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // Initial state
      system: {
        health: {
          build_success_rate: 0.95,
          agent_joy_average: 0.78,
          cognitive_load: 0.35,
          event_throughput: 42,
          invariance_score: 0.85
        },
        pu_queue: {
          total: 3009,
          completed: 2950,
          active_agents: 14
        },
        consciousness: {
          level: 78,
          active_tasks: [
            "Monitoring build freshness",
            "Guarding .map operations",
            "Package integration"
          ],
          completed_tasks: [
            "Fixed consciousness cycling",
            "Implemented safeMap guards", 
            "Set up chug system",
            "Created UI unsticker"
          ]
        },
        errors: []
      },
      
      game: {
        resources: {
          energy: 3430,
          materials: 150,
          components: 45,
          population: 67,
          research: 234
        },
        unlocked_views: ["Dashboard", "Gameplay", "Interface"],
        current_view: "Dashboard",
        automation_level: 2
      },
      
      simulation: {
        tower_defense: {
          turrets: [],
          waves: [],
          score: 0
        },
        exploration: {
          discovered_tiles: [
            { x: 0, y: 0, biome: "base" },
            { x: 1, y: 0, biome: "forest" }
          ],
          current_position: { x: 0, y: 0 },
          inventory: {}
        }
      },

      // Actions
      updateSystem: (updates) => 
        set((state) => {
          Object.assign(state.system, updates);
        }),

      updateGame: (updates) =>
        set((state) => {
          Object.assign(state.game, updates);
        }),

      updateSimulation: (updates) =>
        set((state) => {
          Object.assign(state.simulation, updates);
        }),

      processConsciousnessUpdate: (level, tasks) =>
        set((state) => {
          state.system.consciousness.level = level;
          state.system.consciousness.active_tasks = tasks;
          
          // Unlock views based on consciousness level
          const unlockThresholds = [
            { level: 30, view: "Dashboard" },
            { level: 40, view: "Gameplay" }, 
            { level: 50, view: "Interface" },
            { level: 60, view: "Temple" },
            { level: 70, view: "System" },
            { level: 80, view: "Consciousness" }
          ];
          
          unlockThresholds.forEach(({ level: threshold, view }) => {
            if (level >= threshold && !state.game.unlocked_views.includes(view)) {
              state.game.unlocked_views.push(view);
            }
          });
        }),

      unlockView: (viewName) =>
        set((state) => {
          if (!state.game.unlocked_views.includes(viewName)) {
            state.game.unlocked_views.push(viewName);
          }
        }),

      addError: (error) =>
        set((state) => {
          state.system.errors.push(error);
          // Keep only last 10 errors
          if (state.system.errors.length > 10) {
            state.system.errors = state.system.errors.slice(-10);
          }
        }),

      clearErrors: () =>
        set((state) => {
          state.system.errors = [];
        })
    }))
  )
);

// Selectors for efficient subscriptions
export const selectSystemHealth = (state: AppState) => state.system.health;
export const selectConsciousness = (state: AppState) => state.system.consciousness;
export const selectGameResources = (state: AppState) => state.game.resources;
export const selectUnlockedViews = (state: AppState) => state.game.unlocked_views;
export const selectSimulationTD = (state: AppState) => state.simulation.tower_defense;
export const selectSimulationExplore = (state: AppState) => state.simulation.exploration;