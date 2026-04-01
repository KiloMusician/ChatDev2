// Game State Storage - Simple in-memory store for autonomous evolution
export interface GameState {
  energy: number;
  materials: number;
  population: number;
  research: number;
  components?: number;
  buildings?: Record<string, number>;
  timestamp?: Date;
}

class MemoryGameState {
  private state: GameState = {
    energy: 1000,
    materials: 500,
    population: 10,
    research: 50,
    components: 20,
    buildings: {
      generators: 2,
      factories: 1,
      labs: 1,
      farms: 2,
      workshops: 1
    },
    timestamp: new Date()
  };

  getState(): GameState {
    return { ...this.state };
  }

  setState(newState: GameState): void {
    this.state = { ...newState, timestamp: new Date() };
  }

  updateResources(updates: Partial<GameState>): void {
    this.state = { 
      ...this.state, 
      ...updates, 
      timestamp: new Date() 
    };
  }
}

export const gameState = new MemoryGameState();