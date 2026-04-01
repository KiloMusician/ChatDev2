// **GAME STATE STORE** - Server-side state management with rich game integration
import { GameState as SimpleGameState, defaultGameState as simpleDefaultState, reduceGame, applyAgentAction } from "../../client/src/state/game.js";
import { GameState as RichGameState, initialGameState, GameEngine } from "../../client/src/game/index.js";

// Unified game state that bridges both systems
interface UnifiedGameState extends SimpleGameState {
  richState?: RichGameState;
}

const defaultUnifiedState: UnifiedGameState = {
  ...simpleDefaultState,
  richState: initialGameState
};

class GameStore {
  private state: UnifiedGameState = { ...defaultUnifiedState };
  private gameEngine: GameEngine = new GameEngine();
  private history: UnifiedGameState[] = [];
  
  readGameSnapshot(): UnifiedGameState {
    // Sync the rich game engine state before returning
    this.state.richState = this.gameEngine.getState();
    return { ...this.state };
  }
  
  applyAction(actor: string, action: string, payload: any = {}): any {
    const prevState = { ...this.state };
    
    try {
      // Log the action for ML training
      this.logAction(actor, action, payload, prevState);
      
      // Handle rich game actions (buildings, research, etc.)
      let richActionHandled = false;
      if (this.handleRichGameAction(action, payload)) {
        richActionHandled = true;
        // Sync simple state with rich state
        this.syncSimpleStateFromRich();
      }
      
      // Apply simple game actions if not already handled
      if (!richActionHandled) {
        if (actor.startsWith("agent:") || actor.startsWith("system:")) {
          this.state = applyAgentAction(this.state, action, payload);
        } else {
          this.state = reduceGame(this.state, { type: action.toUpperCase(), ...payload });
        }
      }
      
      // Keep history for ML training (last 100 states)
      this.history.push(prevState);
      if (this.history.length > 100) {
        this.history.shift();
      }
      
      return {
        success: true,
        prevState: prevState,
        newState: this.state,
        actor,
        action,
        tick: this.state.tick
      };
    } catch (error) {
      console.error(`[STORE] Action failed:`, { actor, action, payload, error });
      this.state = { ...prevState, phase: "error", lastError: String(error) };
      return { success: false, error: String(error) };
    }
  }

  private handleRichGameAction(action: string, payload: any): boolean {
    switch (action) {
      case "buy_building":
      case "build":
        if (payload.building || payload.type) {
          const buildingType = payload.building || payload.type;
          return this.gameEngine.buyBuilding(buildingType);
        }
        break;
      
      case "start_research":
      case "research":
        if (payload.research || payload.type) {
          const researchType = payload.research || payload.type;
          return this.gameEngine.startResearch(researchType);
        }
        break;
      
      case "manual_action":
      case "activate":
        if (payload.action || payload.type) {
          const actionType = payload.action || payload.type;
          return this.gameEngine.activateAction(actionType);
        }
        break;
      
      case "tick":
        this.gameEngine.tick();
        return true;
        
      default:
        return false;
    }
    return false;
  }

  private syncSimpleStateFromRich(): void {
    const richState = this.gameEngine.getState();
    // Update simple state to reflect rich state changes
    this.state.resources = {
      energy: richState.resources.energy,
      materials: richState.resources.materials,
      components: richState.resources.components
    };
    this.state.richState = richState;
  }
  
  computeReward(): number {
    // Enhanced reward function using rich game state
    const s = this.state;
    if (s.phase === "error") return -10;
    if (s.phase === "playing") {
      const richState = s.richState;
      
      // Basic resource score
      const resourceScore = Object.values(s.resources || {}).reduce((a: number, b: number) => a + b, 0);
      
      // Building and progression bonuses
      let bonusScore = 0;
      if (richState) {
        bonusScore += Object.values(richState.buildings).reduce((sum, count) => sum + count, 0) * 10; // 10 points per building
        bonusScore += richState.research.completed.length * 50; // 50 points per research completed
        bonusScore += Object.values(richState.unlocks).filter(Boolean).length * 100; // 100 points per unlock
        bonusScore += richState.effects.achievements.length * 25; // 25 points per achievement
      }
      
      const tickBonus = Math.floor(s.tick / 10);
      return resourceScore + bonusScore + tickBonus;
    }
    return 0;
  }
  
  getHistory(): UnifiedGameState[] {
    return [...this.history];
  }
  
  reset(): void {
    this.state = { ...defaultUnifiedState };
    this.gameEngine = new GameEngine();
    this.history = [];
  }
  
  private logAction(actor: string, action: string, payload: any, prevState: UnifiedGameState): void {
    // This will be used by ML nursery for training data
    const event = {
      timestamp: Date.now(),
      actor,
      action,
      payload,
      prevState: {
        phase: prevState.phase,
        tick: prevState.tick,
        resources: prevState.resources
      },
      gameContext: {
        phase: prevState.phase,
        autopilot: prevState.autopilot
      }
    };
    
    // Store for ML training (implement actual storage later)
    if (typeof process !== 'undefined' && process.env.ML_LOGGING === 'true') {
      console.log(`[ML-LOG]`, JSON.stringify(event));
    }
  }
}

let store: GameStore | null = null;

export function getStore(): GameStore {
  if (!store) {
    store = new GameStore();
  }
  return store;
}