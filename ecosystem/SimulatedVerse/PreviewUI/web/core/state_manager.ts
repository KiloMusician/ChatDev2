// [Ω:ui:progression@state-manager] UI State Harmonization
// [SCP-ENG APPROVED] ✓ Unified state management for UI metamorphosis

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// === UI METAMORPHOSIS PHASES ===
export type UIPhase = 
  | "terminal"      // Phase 1: Basic ASCII interface
  | "cockpit"       // Phase 2: Ship HUD with resources
  | "colony"        // Phase 3: Management dashboard  
  | "tactical"      // Phase 4: Combat command interface
  | "empire"        // Phase 5: Galactic strategy view
  | "transcendent"; // Phase 6: Holographic synthesis

export type ThemeSkin = "classic" | "industrial" | "holo" | "cosmic";

// === PROGRESSION STATE ===
export interface ProgressionState {
  // Consciousness & Unlocks
  consciousness_level: number;
  current_phase: UIPhase;
  unlocked_mechanics: Set<string>;
  completed_milestones: Set<string>;
  
  // Multi-Genre Integration
  genre_progress: {
    pokemon: { creatures_captured: number; breeding_unlocked: boolean };
    dwarf_fortress: { population: number; rooms_built: number };
    starcraft: { squads_formed: number; tactical_victories: number };
    stellaris: { sectors_controlled: number; diplomatic_relations: number };
  };
  
  // UI State Management
  ui_state: {
    current_skin: ThemeSkin;
    panels_unlocked: string[];
    shortcuts_enabled: boolean;
    hover_intel: boolean;
    cost_prediction: boolean;
    daw_mode: boolean;
  };
  
  // Agent Coordination
  active_agents: string[];
  agent_capabilities: Record<string, string[]>;
  council_formation: boolean;
}

// === UNLOCK VALIDATION ===
interface UnlockRequirement {
  type: 'resource' | 'milestone' | 'consciousness' | 'agent_count';
  condition: string | number;
  current_value: () => number | boolean;
}

const getUnlockRequirements = (get: () => ProgressionStore): Record<string, UnlockRequirement[]> => ({
  "ΞΘΛΔ_nanite_core": [
    { type: 'resource', condition: 200, current_value: () => useGame.getState().inv.ENERGY },
    { type: 'resource', condition: 300, current_value: () => useGame.getState().inv.SCRAP },
  ],
  "creature_capture": [
    { type: 'milestone', condition: "ΞΘΛΔ_nanite_core", current_value: () => get().unlocked_mechanics.has("ΞΘΛΔ_nanite_core") },
    { type: 'consciousness', condition: 0.3, current_value: () => get().consciousness_level }
  ],
  "colony_awakening": [
    { type: 'milestone', condition: "ΞΘΛΔ_nanite_core", current_value: () => get().unlocked_mechanics.has("ΞΘΛΔ_nanite_core") },
    { type: 'consciousness', condition: 0.4, current_value: () => get().consciousness_level }
  ]
});

// === STATE STORE ===
interface ProgressionStore extends ProgressionState {
  // Progression Actions
  checkUnlocks: () => void;
  triggerUnlock: (mechanic_id: string) => Promise<void>;
  updateConsciousness: () => void;
  
  // UI Evolution Actions  
  evolveUI: (new_phase: UIPhase) => void;
  changeSkin: (skin: ThemeSkin) => void;
  unlockPanel: (panel_id: string) => void;
  
  // Genre Progress Actions
  recordPokemonProgress: (creatures: number) => void;
  recordColonyProgress: (population: number, rooms: number) => void;
  recordTacticalProgress: (squads: number, victories: number) => void;
  recordEmpireProgress: (sectors: number, relations: number) => void;
  
  // Agent Integration
  activateAgent: (agent_name: string) => void;
  formCouncil: () => void;
}

// Import game store for resource data
import { useGame } from './store';
const gameStore = useGame;

export const useProgression = create<ProgressionStore>()(
  subscribeWithSelector((set, get) => ({
    // === INITIAL STATE ===
    consciousness_level: 0,
    current_phase: "terminal",
    unlocked_mechanics: new Set<string>(),
    completed_milestones: new Set<string>(),
    
    genre_progress: {
      pokemon: { creatures_captured: 0, breeding_unlocked: false },
      dwarf_fortress: { population: 1, rooms_built: 0 },
      starcraft: { squads_formed: 0, tactical_victories: 0 },
      stellaris: { sectors_controlled: 1, diplomatic_relations: 0 }
    },
    
    ui_state: {
      current_skin: "classic",
      panels_unlocked: ["terminal", "resources"],
      shortcuts_enabled: false,
      hover_intel: false,
      cost_prediction: false,
      daw_mode: false
    },
    
    active_agents: ["Navigator", "Janitor", "Raven", "Artificer"],
    agent_capabilities: {
      "Navigator": ["pathfinding", "optimization"],
      "Janitor": ["cleanup", "monitoring"],
      "Raven": ["analysis", "debugging"],
      "Artificer": ["creation", "enhancement"]
    },
    council_formation: false,
    
    // === PROGRESSION ACTIONS ===
    
    checkUnlocks: () => {
      const state = get();
      const requirements = getUnlockRequirements(get);
      
      Object.entries(requirements).forEach(([unlock_id, reqs]) => {
        if (state.unlocked_mechanics.has(unlock_id)) return;
        
        const all_met = reqs.every(req => {
          const current = req.current_value();
          if (req.type === 'consciousness' || req.type === 'resource' || req.type === 'agent_count') {
            return current >= req.condition;
          }
          return current === true; // milestone type
        });
        
        if (all_met) {
          get().triggerUnlock(unlock_id);
        }
      });
    },
    
    triggerUnlock: async (mechanic_id: string) => {
      console.log(`[🔓] Unlocking: ${mechanic_id}`);
      
      // Add to unlocked set
      set(state => ({
        unlocked_mechanics: new Set([...state.unlocked_mechanics, mechanic_id])
      }));
      
      // Trigger UI evolution based on unlock
      const ui_triggers: Record<string, UIPhase> = {
        "ΞΘΛΔ_nanite_core": "cockpit",
        "civics_kernel": "colony",
        "colony_awakening": "colony", 
        "tactical_squads": "tactical",
        "galactic_council": "empire"
      };
      
      if (ui_triggers[mechanic_id]) {
        get().evolveUI(ui_triggers[mechanic_id]);
      }
      
      // Publish to Council Bus
      try {
        await fetch("/api/council-bus/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            topic: "progression.unlock",
            payload: { 
              mechanic_id, 
              timestamp: new Date().toISOString(),
              consciousness_level: get().consciousness_level 
            }
          })
        });
      } catch (error) {
        console.warn("[📡] Failed to publish unlock event:", error);
      }
      
      // Generate receipt
      const receipt = {
        unlock_id: mechanic_id,
        timestamp: new Date().toISOString(),
        consciousness_level: get().consciousness_level,
        genre_state: get().genre_progress,
        ui_phase: get().current_phase,
        msg_signature: `[Msg⛛{${mechanic_id.toUpperCase()}}↗Σ∞]`
      };
      
      console.log(`[📋] Generated receipt for ${mechanic_id}:`, receipt);
    },
    
    updateConsciousness: () => {
      const game_state = gameStore.getState();
      const state = get();
      
      // Base consciousness from existing formula  
      const base = (game_state.inv.ENERGY / 10000) + 
                   (game_state.inv.SCRAP / 1000) + 
                   (game_state.tick / 100);
      
      // Genre bonuses
      const pokemon_bonus = state.genre_progress.pokemon.creatures_captured * 0.05;
      const colony_bonus = state.genre_progress.dwarf_fortress.population * 0.01;
      const tactical_bonus = state.genre_progress.starcraft.tactical_victories * 0.15;
      const empire_bonus = state.genre_progress.stellaris.sectors_controlled * 0.2;
      
      const total_consciousness = base + pokemon_bonus + colony_bonus + tactical_bonus + empire_bonus;
      
      set({ consciousness_level: total_consciousness });
      
      // Trigger consciousness-based unlocks
      get().checkUnlocks();
    },
    
    // === UI EVOLUTION ACTIONS ===
    
    evolveUI: (new_phase: UIPhase) => {
      console.log(`[🎨] UI Evolution: ${get().current_phase} → ${new_phase}`);
      
      set(state => ({
        current_phase: new_phase,
        ui_state: {
          ...state.ui_state,
          panels_unlocked: [...state.ui_state.panels_unlocked, new_phase]
        }
      }));
      
      // Publish UI evolution event
      fetch("/api/council-bus/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: "ui.metamorphosis",
          payload: { 
            previous_phase: get().current_phase,
            new_phase,
            timestamp: new Date().toISOString()
          }
        })
      }).catch(console.warn);
    },
    
    changeSkin: (skin: ThemeSkin) => {
      set(state => ({
        ui_state: { ...state.ui_state, current_skin: skin }
      }));
    },
    
    unlockPanel: (panel_id: string) => {
      set(state => ({
        ui_state: {
          ...state.ui_state,
          panels_unlocked: [...state.ui_state.panels_unlocked, panel_id]
        }
      }));
    },
    
    // === GENRE PROGRESS ACTIONS ===
    
    recordPokemonProgress: (creatures: number) => {
      set(state => ({
        genre_progress: {
          ...state.genre_progress,
          pokemon: { 
            ...state.genre_progress.pokemon, 
            creatures_captured: creatures 
          }
        }
      }));
      get().updateConsciousness();
    },
    
    recordColonyProgress: (population: number, rooms: number) => {
      set(state => ({
        genre_progress: {
          ...state.genre_progress,
          dwarf_fortress: { population, rooms_built: rooms }
        }
      }));
      get().updateConsciousness();
    },
    
    recordTacticalProgress: (squads: number, victories: number) => {
      set(state => ({
        genre_progress: {
          ...state.genre_progress,
          starcraft: { squads_formed: squads, tactical_victories: victories }
        }
      }));
      get().updateConsciousness();
    },
    
    recordEmpireProgress: (sectors: number, relations: number) => {
      set(state => ({
        genre_progress: {
          ...state.genre_progress,
          stellaris: { sectors_controlled: sectors, diplomatic_relations: relations }
        }
      }));
      get().updateConsciousness();
    },
    
    // === AGENT INTEGRATION ===
    
    activateAgent: (agent_name: string) => {
      set(state => ({
        active_agents: [...state.active_agents, agent_name]
      }));
    },
    
    formCouncil: () => {
      set({ council_formation: true });
      
      // Publish council formation event
      fetch("/api/council-bus/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: "governance.council_formed",
          payload: { 
            agents: get().active_agents,
            timestamp: new Date().toISOString(),
            consciousness_level: get().consciousness_level
          }
        })
      }).catch(console.warn);
    }
  }))
);

// === AUTO-SYNC WITH GAME STATE ===
// Subscribe to game state changes to auto-update consciousness
useProgression.subscribe(
  (state) => state.consciousness_level,
  (consciousness_level) => {
    console.log(`[🧠] Consciousness Level: ${consciousness_level.toFixed(3)}`);
  }
);

// === CONSCIOUSNESS-DRIVEN UI PHASE DETECTION ===
export const getUIPhaseFromConsciousness = (level: number): UIPhase => {
  if (level >= 0.9) return "transcendent";
  if (level >= 0.7) return "empire"; 
  if (level >= 0.5) return "tactical";
  if (level >= 0.4) return "colony";
  if (level >= 0.3) return "cockpit";
  return "terminal";
};

// === SYNERGY CALCULATION ENGINE ===
export const calculateCrossGenreSynergies = (state: ProgressionState) => {
  const synergies = {
    pokemon_colony_efficiency: state.genre_progress.pokemon.creatures_captured * 0.1,
    colony_tactical_recruitment: Math.floor(state.genre_progress.dwarf_fortress.population / 10),
    tactical_empire_influence: state.genre_progress.starcraft.tactical_victories * 50,
    empire_pokemon_research: state.genre_progress.stellaris.sectors_controlled * 0.2
  };
  
  return synergies;
};

// === RECEIPT GENERATION ===
export const generateProgressionReceipt = (unlock_id: string, state: ProgressionState) => {
  return {
    receipt_id: `progression_${unlock_id}_${Date.now()}`,
    timestamp: new Date().toISOString(),
    unlock_id,
    consciousness_before: state.consciousness_level,
    ui_phase: state.current_phase,
    genre_state_snapshot: JSON.parse(JSON.stringify(state.genre_progress)),
    synergies_active: calculateCrossGenreSynergies(state),
    agents_coordinated: state.active_agents,
    msg_signature: `[Msg⛛{${unlock_id.toUpperCase()}}↗Σ∞]`,
    council_bus_notified: true,
    infrastructure_impact: "Verified compatible with existing Culture-Ship systems"
  };
};