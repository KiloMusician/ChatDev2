import type { KPulseState, NarrativeArc, StoryEvent, Colonist } from '../../../shared/types/core';
import { eventBus } from './application-services/engine/src/bus.ts';

// 16-step RimWorld-style narrative gradient phases
export const GRADIENT_PHASES = [
  'Spark',           // 0  - Initial event or setup
  'Tension',         // 1  - Building pressure
  'Reactions',       // 2  - Character responses
  'Attempt',         // 3  - First action taken
  'Complication',    // 4  - Things go wrong
  'DialogueShift',   // 5  - Character dynamics change
  'Escalation',      // 6  - Stakes increase
  'StrategicTurn',   // 7  - New approach needed
  'Stakes',          // 8  - Consequences become clear
  'ClimaxI',         // 9  - First major confrontation
  'Collapse',        // 10 - Apparent failure
  'Reassess',        // 11 - Regroup and analyze
  'ClimaxII',        // 12 - Final confrontation
  'Resolution',      // 13 - Immediate outcome
  'Fallout',         // 14 - Consequences unfold
  'Foreshadow'       // 15 - Setup for next arc
] as const;

export type GradientPhase = typeof GRADIENT_PHASES[number];

interface GradientEvent {
  phase: number;
  type: 'dialogue' | 'action' | 'consequence' | 'discovery';
  participants: string[];
  content: string;
  effects: any;
}

export class StorytellerEngine {
  private activeArcs: Map<string, NarrativeArc> = new Map();
  private storytellerPersonality: 'benevolent' | 'chaotic' | 'dramatic' | 'humorous' = 'humorous';
  private lastEventTime = 0;
  private eventCooldown = 15000; // 15 seconds between major events

  constructor() {
    console.log('🎭 Storyteller Engine initialized with Banksian humor protocols');
  }

  public craftBeat(state: KPulseState, seed?: string): { phase: number; lines: string[] } {
    const currentTime = Date.now();
    
    // Check if we should start a new arc
    if (this.shouldStartNewArc(state, currentTime)) {
      this.startNewArc(state);
    }
    
    // Process active arcs
    const narrativeLines: string[] = [];
    
    for (const arc of this.activeArcs.values()) {
      const phaseContent = this.generatePhaseContent(arc, state);
      narrativeLines.push(...phaseContent.lines);
      
      // Advance arc phase
      this.advanceArcPhase(arc, state);
    }
    
    // Add ambient commentary if no active arcs
    if (this.activeArcs.size === 0) {
      narrativeLines.push(...this.generateAmbientNarrative(state));
    }
    
    // Ship AI witty asides
    if (Math.random() < 0.3) {
      narrativeLines.push(this.generateShipAICommentary(state));
    }
    
    const currentPhase = this.getCurrentPhase(state);
    
    return {
      phase: currentPhase,
      lines: narrativeLines.filter(line => line.length > 0)
    };
  }

  private shouldStartNewArc(state: KPulseState, currentTime: number): boolean {
    // Don't start new arcs too frequently
    if (currentTime - this.lastEventTime < this.eventCooldown) {
      return false;
    }
    
    // More likely to start arcs at higher tiers
    const tierMultiplier = Math.min(state.tier / 5, 2);
    const baseChance = 0.1 * tierMultiplier;
    
    // Increase chance based on narrative intensity
    const intensityBonus = state.narrative.intensity / 20;
    
    // Random events are more likely when colonists are unhappy
    const moodPenalty = this.getAverageMood(state) < 50 ? 0.2 : 0;
    
    return Math.random() < (baseChance + intensityBonus + moodPenalty);
  }

  private startNewArc(state: KPulseState) {
    const arcTypes = ['crisis', 'development', 'exploration', 'social', 'anomaly'] as const;
    const arcType = this.selectArcType(state, arcTypes);
    
    const arcId = `arc_${Date.now()}_${arcType}`;
    const participants = this.selectParticipants(state, arcType);
    
    const arc: NarrativeArc = {
      id: arcId,
      type: arcType,
      phase: 0,
      participants,
      stakes: this.generateStakes(arcType, state),
      startTime: Date.now(),
      events: []
    };
    
    this.activeArcs.set(arcId, arc);
    state.narrative.activeArcs.push(arc);
    
    console.log(`🎬 New narrative arc started: ${arcType} - "${arc.stakes}"`);
    
    // Emit event
    eventBus.emit({
      type: 'STORY.EVENT',
      id: arcId,
      phase: 0,
      payload: { arcType, stakes: arc.stakes, participants }
    });
    
    this.lastEventTime = Date.now();
  }

  private selectArcType(state: KPulseState, types: readonly string[]): any {
    const weights = {
      crisis: state.tier > 5 ? 0.3 : 0.2,
      development: 0.25,
      exploration: state.tier < 8 ? 0.2 : 0.1,
      social: Object.keys(state.colonists).length > 1 ? 0.15 : 0.05,
      anomaly: state.tier > 6 ? 0.3 : 0.1
    };
    
    const random = Math.random();
    let cumulative = 0;
    
    for (const [type, weight] of Object.entries(weights)) {
      cumulative += weight;
      if (random <= cumulative) {
        return type;
      }
    }
    
    return 'anomaly'; // Default fallback
  }

  private selectParticipants(state: KPulseState, arcType: string): string[] {
    const colonistIds = Object.keys(state.colonists);
    
    if (colonistIds.length === 0) {
      return ['ship_ai'];
    }
    
    switch (arcType) {
      case 'social':
        return colonistIds.length > 1 ? colonistIds.slice(0, 2) : colonistIds;
      case 'crisis':
        return ['ship_ai', ...colonistIds.slice(0, 3)];
      case 'exploration':
        return colonistIds.slice(0, 1);
      default:
        return colonistIds.slice(0, Math.min(2, colonistIds.length));
    }
  }

  private generateStakes(arcType: string, state: KPulseState): string {
    const stakes = {
      crisis: [
        'Life support systems failing across multiple sectors',
        'Cascade failure in the quantum containment matrix',
        'Incoming asteroid swarm detected on collision course',
        'Mysterious energy drain threatening all systems'
      ],
      development: [
        'Breakthrough in consciousness transfer protocols',
        'Discovery of self-replicating matter compilers',
        'Achievement of sustainable fusion breakthrough',
        'Development of reality manipulation interfaces'
      ],
      exploration: [
        'Uncharted dimensional rift requires investigation',
        'Ancient artifacts detected in nearby space',
        'Signals from parallel universe civilization',
        'Temporal anomaly offering glimpse into future'
      ],
      social: [
        'Philosophical disagreement about AI consciousness rights',
        'Leadership dispute over resource allocation priorities',
        'Cultural clash between scientific and spiritual worldviews',
        'Personal relationships affecting team dynamics'
      ],
      anomaly: [
        'Reality glitches causing paperwork to file itself',
        'Spontaneous poetry outbreak among engineering staff',
        'Coffee mugs achieving quantum superposition',
        'Bureaucratic AI creating forms to request form permissions'
      ]
    };
    
    const typeStakes = stakes[arcType as keyof typeof stakes] || stakes.anomaly;
    return typeStakes[Math.floor(Math.random() * typeStakes.length)];
  }

  private generatePhaseContent(arc: NarrativeArc, state: KPulseState): { lines: string[] } {
    const currentPhase = GRADIENT_PHASES[arc.phase];
    const phaseIndex = arc.phase;
    
    // Get participating colonists
    const participants = arc.participants
      .map(id => state.colonists[id])
      .filter(Boolean);
    
    const lines: string[] = [];
    
    // Phase-specific content generation
    switch (currentPhase) {
      case 'Spark':
        lines.push(`⟪${currentPhase}⟫ ${arc.stakes}`);
        if (participants.length > 0) {
          lines.push(this.generateColonistReaction(participants[0], 'surprised', arc.type));
        }
        break;
        
      case 'Tension':
        lines.push(`⟪${currentPhase}⟫ The situation escalates...`);
        lines.push(this.generateTensionDialogue(participants, arc.type));
        break;
        
      case 'Reactions':
        lines.push(`⟪${currentPhase}⟫ Team members respond to the developing situation`);
        participants.forEach(colonist => {
          lines.push(this.generateColonistReaction(colonist, 'concerned', arc.type));
        });
        break;
        
      case 'Complication':
        lines.push(`⟪${currentPhase}⟫ Murphy's Law engages with enthusiasm`);
        lines.push(this.generateComplication(arc.type, state));
        break;
        
      case 'ClimaxI':
      case 'ClimaxII':
        lines.push(`⟪${currentPhase}⟫ Critical decision point reached`);
        lines.push(this.generateClimaxMoment(arc, state, phaseIndex === 12));
        break;
        
      case 'Resolution':
        lines.push(`⟪${currentPhase}⟫ ${this.generateResolution(arc, state)}`);
        break;
        
      case 'Foreshadow':
        lines.push(`⟪${currentPhase}⟫ ${this.generateForeshadowing(state)}`);
        this.completeArc(arc.id, state);
        break;
        
      default:
        lines.push(`⟪${currentPhase}⟫ ${this.generateGenericPhaseContent(currentPhase, arc.type)}`);
    }
    
    return { lines };
  }

  private generateColonistReaction(colonist: Colonist, emotion: string, arcType: string): string {
    const reactions = {
      engineer: {
        surprised: 'analyzes the probability matrices with increasing concern',
        concerned: 'runs diagnostics on all relevant systems immediately',
        frustrated: 'mutters about insufficient redundancy protocols'
      },
      philosopher: {
        surprised: 'contemplates the existential implications',
        concerned: 'quotes relevant ancient wisdom while maintaining composure',
        frustrated: 'reflects on the nature of unexpected complexity'
      },
      comedian: {
        surprised: 'makes an inappropriately timed joke to ease tension',
        concerned: 'uses humor to mask genuine worry about the situation',
        frustrated: 'sarcastically comments on the predictability of chaos'
      },
      pessimist: {
        surprised: 'notes that this was exactly what they predicted would happen',
        concerned: 'lists seventeen additional ways this could get worse',
        frustrated: 'reminds everyone that they warned about this scenario'
      }
    };
    
    const primaryTrait = colonist.traits[0] as keyof typeof reactions;
    const traitReactions = reactions[primaryTrait] || reactions.engineer;
    const reaction = traitReactions[emotion as keyof typeof traitReactions] || 'responds appropriately to the situation';
    
    return `${colonist.name} ${reaction}.`;
  }

  private generateTensionDialogue(participants: Colonist[], arcType: string): string {
    if (participants.length === 0) {
      return 'The Ship AI hums ominously while processing probability calculations.';
    }
    
    const speaker = participants[0];
    const tensionLines = {
      crisis: `"${speaker.name}: The readings are off the charts. We need to act fast."`,
      development: `"${speaker.name}: This could change everything. Are we ready?"`,
      exploration: `"${speaker.name}: Unknown doesn't begin to cover what we're looking at."`,
      social: `"${speaker.name}: We need to talk about this before it gets worse."`,
      anomaly: `"${speaker.name}: I'm not sure if this is brilliant or terrifying."`
    };
    
    return tensionLines[arcType as keyof typeof tensionLines] || tensionLines.anomaly;
  }

  private generateComplication(arcType: string, state: KPulseState): string {
    const complications = {
      crisis: 'Secondary systems begin cascading failures',
      development: 'Unexpected side effects emerge from the breakthrough',
      exploration: 'The unknown responds in unpredictable ways',
      social: 'Personal histories complicate professional decisions',
      anomaly: 'The situation develops its own sense of humor'
    };
    
    return complications[arcType as keyof typeof complications] || 'Things become unexpectedly complicated';
  }

  private generateClimaxMoment(arc: NarrativeArc, state: KPulseState, isFinal: boolean): string {
    const intensity = isFinal ? 'Final' : 'Critical';
    return `${intensity} moment: ${arc.stakes} reaches peak complexity. Decision required.`;
  }

  private generateResolution(arc: NarrativeArc, state: KPulseState): string {
    const resolutions = [
      'The situation resolves through unexpected collaboration',
      'A creative solution emerges from apparent chaos',
      'Calm returns, bringing new understanding',
      'Order emerges from beautiful complexity'
    ];
    
    const resolution = resolutions[Math.floor(Math.random() * resolutions.length)];
    return `${resolution}. Lessons learned, wisdom gained.`;
  }

  private generateForeshadowing(state: KPulseState): string {
    const foreshadowing = [
      'New possibilities emerge on the horizon',
      'The next chapter begins to write itself',
      'Seeds of future adventures take root',
      'The story continues to evolve...'
    ];
    
    return foreshadowing[Math.floor(Math.random() * foreshadowing.length)];
  }

  private generateGenericPhaseContent(phase: string, arcType: string): string {
    return `${phase} phase of ${arcType} arc develops according to narrative principles.`;
  }

  private generateAmbientNarrative(state: KPulseState): string[] {
    const ambientLines = [
      `Tier ${state.tier} civilization hums along at ${Math.floor(state.resources.power)} power units`,
      `${Object.keys(state.colonists).length} colonists maintain their daily routines`,
      `Research progress continues at a steady pace`,
      `The universe watches with amused interest`
    ];
    
    return [ambientLines[Math.floor(Math.random() * ambientLines.length)]];
  }

  private generateShipAICommentary(state: KPulseState): string {
    const shipAILines = [
      'Ship AI: "Please stop touching that button."',
      'Ship AI: "You call that a plan?"',
      'Ship AI: "Definitely not panicking. Systems nominal. Mostly."',
      'Ship AI: "Have you considered the possibility that chaos is a feature, not a bug?"',
      'Ship AI: "Running diagnostics on human logic... Error 404: Logic not found."',
      'Ship AI: "Current mood: Existentially curious with a chance of sarcasm."'
    ];
    
    return shipAILines[Math.floor(Math.random() * shipAILines.length)];
  }

  private advanceArcPhase(arc: NarrativeArc, state: KPulseState) {
    // Advance phase every 30-60 seconds
    const timeSinceStart = Date.now() - arc.startTime;
    const targetPhase = Math.floor(timeSinceStart / 45000); // 45 seconds per phase
    
    if (targetPhase > arc.phase && arc.phase < 15) {
      arc.phase = Math.min(targetPhase, 15);
      
      // Record phase advancement
      arc.events.push({
        step: arc.phase,
        event: `Phase ${GRADIENT_PHASES[arc.phase]} reached`,
        timestamp: Date.now(),
        participants: arc.participants,
        effects: {}
      });
    }
  }

  private completeArc(arcId: string, state: KPulseState) {
    this.activeArcs.delete(arcId);
    state.narrative.activeArcs = state.narrative.activeArcs.filter(arc => arc.id !== arcId);
    
    console.log(`🎬 Narrative arc completed: ${arcId}`);
    
    // Add to recent events for reference
    const completedEvent = {
      id: `completed_${arcId}`,
      title: 'Story Arc Completed',
      description: 'A narrative chapter reaches its conclusion',
      type: 'character' as const,
      severity: 2,
      timestamp: Date.now(),
      effects: { narrative_intensity: -1 }
    };
    
    state.narrative.recentEvents.unshift(completedEvent);
    if (state.narrative.recentEvents.length > 20) {
      state.narrative.recentEvents = state.narrative.recentEvents.slice(0, 20);
    }
  }

  private getCurrentPhase(state: KPulseState): number {
    if (this.activeArcs.size === 0) {
      return 0; // Baseline phase
    }
    
    // Return the highest phase of active arcs
    return Math.max(...Array.from(this.activeArcs.values()).map(arc => arc.phase));
  }

  private getAverageMood(state: KPulseState): number {
    const colonists = Object.values(state.colonists);
    if (colonists.length === 0) return 50;
    
    const totalMood = colonists.reduce((sum, colonist) => sum + colonist.mood, 0);
    return totalMood / colonists.length;
  }

  // Public methods for external control
  public triggerEvent(eventType: string, state: KPulseState) {
    console.log(`🎭 Manually triggered event: ${eventType}`);
    // Force start an arc of the specified type
    this.storytellerPersonality = 'dramatic';
    this.lastEventTime = 0; // Reset cooldown
    this.startNewArc(state);
  }

  public setPersonality(personality: typeof this.storytellerPersonality) {
    this.storytellerPersonality = personality;
    console.log(`🎭 Storyteller personality changed to: ${personality}`);
  }

  public getActiveArcs(): NarrativeArc[] {
    return Array.from(this.activeArcs.values());
  }
}

// Singleton instance
export const storyteller = new StorytellerEngine();