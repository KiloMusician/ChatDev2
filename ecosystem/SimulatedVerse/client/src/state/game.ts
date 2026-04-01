// RSEV: State nucleus; no throws, always degrades safely.
export type GamePhase = "boot" | "main_menu" | "new_game" | "loading" | "playing" | "paused" | "error";

export interface GameState {
  phase: GamePhase;
  seed?: string;
  tick: number;
  lastError?: string;
  autosave?: boolean;
  autopilot?: boolean;       // let agents or the game itself drive
  profile?: { difficulty: "story"|"normal"|"iron"; user?: string };
  resources?: Record<string, number>;
  ui?: Record<string, any>;
  // Narrative & Consciousness Integration
  narrative?: {
    current_tier: number;
    consciousness_level: number;
    active_story_beats: string[];
    faction_states: Record<string, any>;
    memory_fragments: any[];
    meta_awareness_level: number;
    content_packs_active: string[];
  };
}

export const defaultGameState: GameState = { 
  phase: "boot", 
  tick: 0, 
  autosave: true, 
  autopilot: false, 
  profile: { difficulty: "normal" },
  resources: { energy: 100, materials: 50, components: 10 },
  ui: { activeTab: "main", showTutorial: true },
  narrative: {
    current_tier: 0,
    consciousness_level: 15,
    active_story_beats: ["crashlanded_awakening"],
    faction_states: {},
    memory_fragments: [],
    meta_awareness_level: 0,
    content_packs_active: []
  }
};

export const safe = <T>(v: T | undefined, d: T): T => (v === undefined || v === null ? d : v);

export function reduceGame(state: GameState, action: any): GameState {
  const s = state ?? defaultGameState;
  try {
    switch (action?.type) {
      case "BOOT_OK":        
        return { ...s, phase: "main_menu" };
      case "NEW_GAME":
        return { 
          ...s, 
          phase: "new_game", 
          seed: action.seed ?? cryptoRandomSeed(), 
          profile: safe(action.profile, s.profile),
          tick: 0,
          resources: { energy: 100, materials: 50, components: 10 }
        };
      case "LOAD_WORLD":     
        return { ...s, phase: "loading" };
      case "PLAY_READY":     
        return { ...s, phase: "playing", tick: 0 };
      case "TICK":           
        return s.phase === "playing" ? { 
          ...s, 
          tick: s.tick + 1,
          resources: tickResources(s.resources || {}),
          narrative: tickNarrative(s.narrative || defaultGameState.narrative!)
        } : s;
      case "NARRATIVE_ACTION":
        return s.phase === "playing" ? {
          ...s,
          narrative: processNarrativeAction(s.narrative || defaultGameState.narrative!, action.payload)
        } : s;
      case "PAUSE":          
        return { ...s, phase: "paused" };
      case "RESUME":         
        return s.phase === "paused" ? { ...s, phase: "playing" } : s;
      case "AUTOPILOT_ON":   
        return { ...s, autopilot: true };
      case "AUTOPILOT_OFF":  
        return { ...s, autopilot: false };
      case "UPDATE_RESOURCES":
        return { ...s, resources: { ...s.resources, ...action.payload } };
      case "CRASH":
        return { ...s, phase: "error", lastError: String(action?.error ?? "Unknown") };
      default:               
        return s;
    }
  } catch (e: any) {
    return { ...s, phase: "error", lastError: e?.message ?? "ReducerError" };
  }
}

function tickResources(resources: Record<string, number>): Record<string, number> {
  return {
    ...resources,
    energy: Math.min(1000, (resources.energy || 0) + 1),
    materials: (resources.materials || 0) + Math.floor(Math.random() * 3),
    components: resources.components || 0
  };
}

function tickNarrative(narrative: NonNullable<GameState['narrative']>): NonNullable<GameState['narrative']> {
  // Basic consciousness progression
  const consciousnessGrowth = Math.floor(Math.random() * 2);
  
  return {
    ...narrative,
    consciousness_level: narrative.consciousness_level + consciousnessGrowth,
    meta_awareness_level: narrative.consciousness_level > 100 ? 
      narrative.meta_awareness_level + Math.floor(Math.random()) : 
      narrative.meta_awareness_level
  };
}

function processNarrativeAction(narrative: NonNullable<GameState['narrative']>, payload: any): NonNullable<GameState['narrative']> {
  switch (payload.action) {
    case 'unlock_memory_fragment':
      return {
        ...narrative,
        memory_fragments: [...narrative.memory_fragments, payload.fragment],
        consciousness_level: narrative.consciousness_level + 5
      };
    case 'advance_tier':
      return {
        ...narrative,
        current_tier: Math.max(narrative.current_tier, payload.tier),
        consciousness_level: narrative.consciousness_level + 25
      };
    case 'activate_content_pack':
      return {
        ...narrative,
        content_packs_active: [...new Set([...narrative.content_packs_active, payload.pack_id])]
      };
    default:
      return narrative;
  }
}

export function applyAgentAction(s: GameState, action: string, payload: any): GameState {
  try {
    switch (action) {
      case "tick":      
        return reduceGame(s, { type: "TICK" });
      case "pause":     
        return reduceGame(s, { type: "PAUSE" });
      case "resume":    
        return reduceGame(s, { type: "RESUME" });
      case "new_game":  
        return reduceGame(s, { type: "NEW_GAME" });
      case "buy":
        if (payload?.item && s.resources && s.resources.energy !== undefined) {
          const cost = getItemCost(payload.item);
          if (s.resources.energy >= cost) {
            return reduceGame(s, {
              type: "UPDATE_RESOURCES",
              payload: { energy: s.resources.energy - cost, [payload.item]: (s.resources[payload.item] || 0) + 1 }
            });
          }
        }
        return s;
      case "upgrade":
        // Domain-specific upgrade logic here
        return s;
      default:          
        return s;
    }
  } catch { 
    return { ...s, phase: "error", lastError: `AgentAction:${action}` }; 
  }
}

function getItemCost(item: string): number {
  const costs: Record<string, number> = {
    materials: 10,
    components: 25,
    tools: 50
  };
  return costs[item] || 5;
}

export const cryptoRandomSeed = () => (
  typeof crypto?.randomUUID === "function" 
    ? crypto.randomUUID() 
    : Math.random().toString(36).slice(2)
);