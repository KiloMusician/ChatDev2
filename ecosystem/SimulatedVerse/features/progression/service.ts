// [Ω:progression:service@tiers] Tier progression and unlock management
import type { TierUnlock, ResourceState } from '../../system-core/types/index';

export class ProgressionManager {
  private currentTier = -1;
  private startTime = Date.now();
  private unlockedFeatures = new Set<string>();

  constructor(private unlockTree: Record<string, TierUnlock>) {}

  /**
   * Check if conditions are met for next tier advancement
   */
  checkAdvancement(resources: ResourceState): boolean {
    const nextTierKey = (this.currentTier + 1).toString();
    const nextTier = this.unlockTree[nextTierKey];
    
    if (!nextTier) return false;

    // Time requirement
    const timeElapsed = (Date.now() - this.startTime) / 1000;
    if (timeElapsed < nextTier.timeRequirement) {
      return false;
    }

    // Resource requirements  
    if (nextTier.resourceRequirements && typeof nextTier.resourceRequirements === 'object') {
      for (const [resource, required] of Object.entries(nextTier.resourceRequirements)) {
        if ((resources[resource] || 0) < (required as number)) {
          return false;
        }
      }
    }

    // Prerequisites (other tiers unlocked)
    for (const prereq of nextTier.prerequisites) {
      if (!this.unlockedFeatures.has(prereq)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Advance to next tier and unlock features
   */
  advanceTier(): TierUnlock | null {
    const nextTierKey = (this.currentTier + 1).toString();
    const nextTier = this.unlockTree[nextTierKey];
    
    if (!nextTier) return null;

    this.currentTier++;
    
    // Unlock all features for this tier
    for (const feature of nextTier.unlocks) {
      this.unlockedFeatures.add(feature);
    }

    console.log(`[PROGRESSION] 🜁⊙⟦${nextTier.name}⟧ unlocked`);
    
    return nextTier;
  }

  getCurrentTier(): number {
    return this.currentTier;
  }

  isUnlocked(feature: string): boolean {
    return this.unlockedFeatures.has(feature);
  }

  getUnlockedFeatures(): string[] {
    return Array.from(this.unlockedFeatures);
  }

  // [Ω:progression:review@SCP-LORE] Validate narrative consistency
  getProgressionState() {
    return {
      currentTier: this.currentTier,
      unlockedFeatures: Array.from(this.unlockedFeatures),
      timeElapsed: (Date.now() - this.startTime) / 1000,
      nextTier: this.unlockTree[(this.currentTier + 1).toString()]?.name || null
    };
  }
}