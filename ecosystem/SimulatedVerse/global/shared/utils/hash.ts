/**
 * Utility functions for state hashing and integrity checking
 */

import type { KPulseState } from '../types/core';

/**
 * Generate a hash of the game state for integrity checking
 */
export function hashState(state: KPulseState): string {
  // Create a stable representation of the state for hashing
  const stableState = {
    tier: state.tier,
    timestamp: state.timestamp,
    resources: state.resources,
    buildingCount: Object.keys(state.buildings).length,
    colonistCount: Object.keys(state.colonists).length,
    researchActive: state.research.active,
    researchProgress: state.research.progress,
    researchCompleted: Array.from(state.research.completed).sort(),
    narrativeIntensity: state.narrative.intensity,
    activeArcs: state.narrative.activeArcs.length
  };

  // Simple hash function - in production you might want to use a proper crypto hash
  const stateStr = JSON.stringify(stableState);
  let hash = 0;
  for (let i = 0; i < stateStr.length; i++) {
    const char = stateStr.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  return Math.abs(hash).toString(16).padStart(8, '0');
}

/**
 * Verify if a state hash is valid
 */
export function verifyStateHash(state: KPulseState): boolean {
  const currentHash = state.hash;
  const calculatedHash = hashState(state);
  return currentHash === calculatedHash;
}

/**
 * Create a deep clone of state (useful for checkpoints)
 */
export function cloneState(state: KPulseState): KPulseState {
  return {
    ...state,
    resources: { ...state.resources },
    buildings: Object.fromEntries(
      Object.entries(state.buildings).map(([k, v]) => [k, { ...v }])
    ),
    colonists: Object.fromEntries(
      Object.entries(state.colonists).map(([k, v]) => [k, { 
        ...v, 
        memoryBank: [...v.memoryBank],
        relationships: { ...v.relationships },
        skills: { ...v.skills },
        voiceProfile: { ...v.voiceProfile, quirks: [...v.voiceProfile.quirks] }
      }])
    ),
    research: {
      ...state.research,
      completed: new Set(state.research.completed),
      available: new Set(state.research.available),
      tree: [...state.research.tree]
    },
    narrative: {
      ...state.narrative,
      activeArcs: [...state.narrative.activeArcs],
      recentEvents: [...state.narrative.recentEvents],
      dialogueHistory: [...state.narrative.dialogueHistory]
    },
    checkpoints: [...state.checkpoints]
  };
}