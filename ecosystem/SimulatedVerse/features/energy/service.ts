// [Ω:energy:service@engine] Resource generation and allocation
import type { ResourceState } from '../../core/types';

export class ResourceEngine {
  private state: ResourceState = {
    energy: 0,
    materials: 0,
    bio: 0,
    circuits: 0
  };

  /**
   * Pure function: calculate resource deltas
   * Emits Δ not absolutes for easier testing
   */
  calculateDeltas(timeElapsed: number): ResourceState {
    const deltas: ResourceState = {
      energy: timeElapsed * 0.5,     // Base energy generation
      materials: timeElapsed * 0.2,   // Material gathering
      bio: timeElapsed * 0.1,         // Biological systems
      circuits: timeElapsed * 0.05    // Circuit manufacturing
    };

    return deltas;
  }

  /**
   * Apply resource changes and return new state
   */
  applyDeltas(deltas: ResourceState): ResourceState {
    for (const [resource, delta] of Object.entries(deltas)) {
      if (typeof delta === 'number') {
        this.state[resource] = (this.state[resource] || 0) + delta;
      }
    }

    return { ...this.state };
  }

  getState(): ResourceState {
    return { ...this.state };
  }

  // [Ω:energy:test-missing] Add property-based tests for edge cases
  allocate(requirements: ResourceState): boolean {
    // Check if we have enough resources
    for (const [resource, required] of Object.entries(requirements)) {
      if (typeof required === 'number' && (this.state[resource] || 0) < required) {
        return false;
      }
    }

    // Deduct resources
    for (const [resource, required] of Object.entries(requirements)) {
      if (typeof required === 'number') {
        this.state[resource] = (this.state[resource] || 0) - required;
      }
    }

    return true;
  }
}