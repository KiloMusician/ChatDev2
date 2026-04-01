// Minimal database setup for testing
// Will integrate with full Drizzle setup once tsx issues are resolved

export function createDatabase() {
  // For now, return mock database operations
  return {
    async saveGameState(state) {
      console.log('Mock: Saving game state', state.playerId);
      return state;
    },
    
    async loadGameState(playerId) {
      console.log('Mock: Loading game state for', playerId);
      return null; // Use in-memory state for now
    },
    
    async getAchievements(playerId) {
      return [];
    }
  };
}