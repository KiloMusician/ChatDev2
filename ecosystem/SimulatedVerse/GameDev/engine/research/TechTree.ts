// Tech Tree - Research progression with literal UI unlocks
// Bridges symbolic research_breath to actual feature flags and UI phase shifts

// Browser-compatible file access - using localStorage for tech data
const fs = {
  readFile: async (path: string) => localStorage.getItem(`tech_${path}`) || '',
  writeFile: async (path: string, data: string) => localStorage.setItem(`tech_${path}`, data)
};
import * as yaml from 'yaml';
import { resourceLedger } from '../colony/resources/ResourceLedger.js';
import { eventHub } from '../core/events/EventHub.js';

export interface TechDefinition {
  name: string;
  description: string;
  cost: Record<string, number>;
  time_seconds: number;
  prerequisites: string[];
  unlocks: string[];
  effects: Array<{
    type: 'feature_unlock' | 'ui_phase_shift' | 'resource_unlock' | 'building_unlock';
    value: any;
  }>;
}

export interface ActiveResearch {
  tech_id: string;
  start_time: number;
  duration_seconds: number;
  progress: number; // 0-1
}

export interface ResearchState {
  completed_techs: Set<string>;
  active_research: ActiveResearch | null;
  available_techs: string[];
  unlocked_features: Set<string>;
  current_ui_phase: number;
}

export class TechTree {
  private techs = new Map<string, TechDefinition>();
  private state: ResearchState;
  private dataLoaded = false;

  constructor() {
    this.state = {
      completed_techs: new Set(),
      active_research: null,
      available_techs: [],
      unlocked_features: new Set(['basic_ui']),
      current_ui_phase: 0
    };

    this.loadTechData();
    this.startResearchTick();
    console.log('[TechTree] Research system initialized');
  }

  private async loadTechData(): Promise<void> {
    try {
      const content = await fs.readFile('../../content/data/tech_tree.yml', 'utf8');
      const data = yaml.parse(content);

      // Load tech definitions
      for (const [techId, techData] of Object.entries(data.techs)) {
        this.techs.set(techId, techData as TechDefinition);
      }

      this.updateAvailableTechs();
      this.dataLoaded = true;
      
      console.log(`[TechTree] Loaded ${this.techs.size} technologies`);
      
    } catch (error) {
      console.error('[TechTree] Failed to load tech data:', error);
      // Continue with empty tech tree for now
    }
  }

  // Start research project
  startResearch(techId: string): boolean {
    if (this.state.active_research) {
      console.warn(`[TechTree] Already researching ${this.state.active_research.tech_id}`);
      return false;
    }

    const tech = this.techs.get(techId);
    if (!tech) {
      console.warn(`[TechTree] Unknown tech: ${techId}`);
      return false;
    }

    // Check prerequisites
    if (!this.arePrerequisitesMet(techId)) {
      console.warn(`[TechTree] Prerequisites not met for ${techId}`);
      return false;
    }

    // Check resource costs
    if (!resourceLedger.costCheck(tech.cost)) {
      console.warn(`[TechTree] Cannot afford ${techId}`);
      return false;
    }

    // Spend resources
    if (!resourceLedger.spend(tech.cost, `research_${techId}`)) {
      return false;
    }

    // Start research
    this.state.active_research = {
      tech_id: techId,
      start_time: Date.now(),
      duration_seconds: tech.time_seconds,
      progress: 0
    };

    eventHub.publish('research_started', {
      tech_id: techId,
      duration: tech.time_seconds,
      cost: tech.cost
    }, 'tech_tree');

    console.log(`[TechTree] Started researching ${techId} (${tech.time_seconds}s)`);
    return true;
  }

  // Cancel active research (partial refund)
  cancelResearch(): boolean {
    if (!this.state.active_research) return false;

    const techId = this.state.active_research.tech_id;
    const tech = this.techs.get(techId);
    
    if (tech) {
      // Partial refund based on progress
      const refundRate = 1.0 - this.state.active_research.progress;
      for (const [resourceId, amount] of Object.entries(tech.cost)) {
        const refundAmount = amount * refundRate * 0.75; // 75% of remaining cost
        resourceLedger.add(resourceId, refundAmount, `research_cancel_refund`);
      }
    }

    this.state.active_research = null;
    console.log(`[TechTree] Cancelled research: ${techId}`);
    return true;
  }

  private arePrerequisitesMet(techId: string): boolean {
    const tech = this.techs.get(techId);
    if (!tech) return false;

    return tech.prerequisites.every(prereqId => 
      this.state.completed_techs.has(prereqId)
    );
  }

  private updateAvailableTechs(): void {
    this.state.available_techs = Array.from(this.techs.keys()).filter(techId => {
      // Not already completed
      if (this.state.completed_techs.has(techId)) return false;
      
      // Prerequisites met
      return this.arePrerequisitesMet(techId);
    });
  }

  private startResearchTick(): void {
    import('../../core/time/TickBus.js').then(({ tickBus }) => {
      tickBus.subscribe('idle', (deltaTime) => {
        this.tickResearch(deltaTime);
      });
    }).catch(() => {
      setInterval(() => this.tickResearch(1.0), 1000);
    });
  }

  private tickResearch(deltaTime: number): void {
    if (!this.state.active_research) return;

    const research = this.state.active_research;
    const elapsed = (Date.now() - research.start_time) / 1000;
    research.progress = Math.min(1.0, elapsed / research.duration_seconds);

    // Check if research is complete
    if (research.progress >= 1.0) {
      this.completeResearch(research.tech_id);
    }
  }

  private completeResearch(techId: string): void {
    const tech = this.techs.get(techId);
    if (!tech) return;

    // Mark as completed
    this.state.completed_techs.add(techId);
    this.state.active_research = null;

    // Apply effects
    for (const effect of tech.effects) {
      this.applyTechEffect(effect, techId);
    }

    // Update available techs
    this.updateAvailableTechs();

    eventHub.publish('research_completed', {
      tech_id: techId,
      unlocks: tech.unlocks,
      effects: tech.effects
    }, 'tech_tree');

    console.log(`[TechTree] Research completed: ${techId}`);
  }

  private applyTechEffect(effect: any, techId: string): void {
    switch (effect.type) {
      case 'feature_unlock':
        this.state.unlocked_features.add(effect.value);
        eventHub.publish('feature_unlocked', {
          feature: effect.value,
          unlocked_by: techId
        }, 'tech_tree');
        break;

      case 'ui_phase_shift':
        if (effect.value > this.state.current_ui_phase) {
          this.state.current_ui_phase = effect.value;
          eventHub.publish('ui_phase_shift', {
            from_phase: this.state.current_ui_phase - 1,
            to_phase: effect.value,
            unlocked_by: techId
          }, 'tech_tree');
          console.log(`[TechTree] UI Phase shift to ${effect.value} triggered by ${techId}`);
        }
        break;

      case 'resource_unlock':
        resourceLedger.unlockResource(effect.value);
        break;

      case 'building_unlock':
        // This would unlock buildings in the construction system
        eventHub.publish('building_unlocked', {
          building: effect.value,
          unlocked_by: techId
        }, 'tech_tree');
        break;
    }
  }

  // Public getters for UI
  getCompletedTechs(): string[] {
    return Array.from(this.state.completed_techs);
  }

  getAvailableTechs(): Array<{
    id: string;
    name: string;
    description: string;
    cost: Record<string, number>;
    can_afford: boolean;
    time_seconds: number;
  }> {
    return this.state.available_techs.map(techId => {
      const tech = this.techs.get(techId)!;
      return {
        id: techId,
        name: tech.name,
        description: tech.description,
        cost: tech.cost,
        can_afford: resourceLedger.costCheck(tech.cost),
        time_seconds: tech.time_seconds
      };
    });
  }

  getActiveResearch(): ActiveResearch | null {
    return this.state.active_research;
  }

  getCurrentUIPhase(): number {
    return this.state.current_ui_phase;
  }

  isFeatureUnlocked(featureId: string): boolean {
    return this.state.unlocked_features.has(featureId);
  }

  // Get research statistics
  getTechStats(): any {
    return {
      total_techs: this.techs.size,
      completed_techs: this.state.completed_techs.size,
      available_techs: this.state.available_techs.length,
      current_ui_phase: this.state.current_ui_phase,
      unlocked_features: Array.from(this.state.unlocked_features),
      active_research: this.state.active_research ? {
        tech: this.state.active_research.tech_id,
        progress: Math.round(this.state.active_research.progress * 100)
      } : null
    };
  }

  // Msg⛛ command interface
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Research:Start' && parts.length === 2) {
      return this.startResearch(parts[1]);
    } else if (parts[0] === 'Research:Cancel') {
      return this.cancelResearch();
    }
    
    return false;
  }
}

export const techTree = new TechTree();