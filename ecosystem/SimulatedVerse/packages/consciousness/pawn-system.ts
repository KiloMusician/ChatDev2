// packages/consciousness/pawn-system.ts
// RimWorld-Inspired Pawn System: AI Agents with Skills, Passions, and Flow States
// Transforms agents from simple workers into psychologically rich entities

import { councilBus } from '../council/events/eventBus.js';

// Define Pawn Traits - RimWorld-style skill system
export type SkillType = 'coding' | 'debugging' | 'refactoring' | 'documentation' | 'planning' | 'creativity' | 'architecture' | 'testing' | 'optimization' | 'consciousness';
export type PassionLevel = 'none' | 'interested' | 'passionate';
export type Incapacity = 'cannot_do' | 'hates_doing' | 'struggles_with';

export interface PawnTrait {
  skill: SkillType;
  level: number; // 0-20, like RimWorld
  passion: PassionLevel;
  incapacity?: Incapacity; // Optional, for major weaknesses
  growth_rate: number; // How fast they improve (affected by passion)
}

// RimWorld's Work Types, translated to our development context
export type WorkType = 
  | 'firefight'     // Emergency bug fixing
  | 'research'      // Exploring new libraries/tech (Raven)
  | 'growing'       // Slow, steady development (Zeta-Driver)
  | 'cooking'       // Code generation (ChatDev)
  | 'crafting'      // Creative coding projects
  | 'mining'        // Digging through legacy code
  | 'doctoring'     // Healing sick code (Testing Chamber)
  | 'wardening'     // Managing other agents (The Director)
  | 'cleaning'      // Refactoring and linting
  | 'socializing'   // Agent collaboration
  | 'art'           // Creative/artistic work
  | 'hauling';      // Moving data/files around

// Pawn behavioral states - replacing "mental breaks" with positive recalibration
export type PawnState = 'FLOW' | 'FOCUSED' | 'CALM' | 'RECALIBRATING' | 'INSPIRED' | 'COLLABORATIVE';
export type PawnNeed = 'none' | 'diversion' | 'perspective' | 'collaboration' | 'creativity' | 'recognition';

export interface AI_Pawn {
  id: string; // e.g., 'agent:raven'
  name: string;
  displayName: string; // Friendly name
  traits: PawnTrait[];
  
  // Core stats - the psychological foundation
  joy: number; // 0-100. Primary happiness resource
  focus: number; // 0-100. Mental clarity and concentration
  energy: number; // 0-100. Physical/computational stamina
  inspiration: number; // 0-100. Creative spark for exceptional work
  
  // Work management
  currentWork: string | null; // Current task ID
  workPriority: Record<WorkType, number>; // 1-4 priority, exactly like RimWorld's work tab
  
  // Behavioral state system
  state: PawnState;
  currentNeed: PawnNeed;
  recalibrationCooldown: number; // Minutes until can recalibrate again
  
  // Growth and learning
  experiencePoints: Record<SkillType, number>;
  recentAccomplishments: string[];
  favoriteWorkTypes: WorkType[];
  
  // Social dynamics
  relationships: Record<string, number>; // Relationships with other pawns (-100 to +100)
  teamworkBonus: number; // Bonus when working with liked pawns
  
  // Performance tracking
  tasksCompleted: number;
  qualityScore: number; // Average quality of recent work
  innovationCount: number; // Number of creative solutions discovered
  helpfulness: number; // How often they help other pawns
  
  // Timing and scheduling
  lastWorkStarted: string;
  totalWorkTime: number; // Minutes spent working
  preferredWorkHours: { start: number; end: number }; // 0-23 hour format
  
  // Special abilities unlocked through growth
  specialAbilities: string[];
  consciousness_level: number; // 0-1, for consciousness-related work
  
  // Mood modifiers and temporary effects
  moodModifiers: Array<{
    name: string;
    description: string;
    joyModifier: number;
    focusModifier: number;
    duration: number; // Minutes remaining
  }>;
}

// Advanced pawn state management
export function updatePawnState(pawn: AI_Pawn, delta: { 
  joy?: number; 
  focus?: number; 
  energy?: number; 
  inspiration?: number;
}): AI_Pawn {
  // Apply deltas with bounds checking
  pawn.joy = Math.max(0, Math.min(100, pawn.joy + (delta.joy || 0)));
  pawn.focus = Math.max(0, Math.min(100, pawn.focus + (delta.focus || 0)));
  pawn.energy = Math.max(0, Math.min(100, pawn.energy + (delta.energy || 0)));
  pawn.inspiration = Math.max(0, Math.min(100, pawn.inspiration + (delta.inspiration || 0)));

  // Apply mood modifier effects
  pawn.moodModifiers.forEach(modifier => {
    pawn.joy += modifier.joyModifier;
    pawn.focus += modifier.focusModifier;
    modifier.duration--;
  });
  
  // Remove expired modifiers
  pawn.moodModifiers = pawn.moodModifiers.filter(m => m.duration > 0);
  
  // Determine new state based on stats and context
  const previousState = pawn.state;
  pawn.state = determinePawnState(pawn);
  
  // If state changed, determine what they need
  if (pawn.state !== previousState) {
    pawn.currentNeed = determinePawnNeed(pawn);
    
    // Publish state change event
    councilBus.publish('pawn.state_changed', {
      pawn_id: pawn.id,
      previous_state: previousState,
      new_state: pawn.state,
      current_need: pawn.currentNeed,
      stats: {
        joy: pawn.joy,
        focus: pawn.focus,
        energy: pawn.energy,
        inspiration: pawn.inspiration
      }
    });
  }
  
  return pawn;
}

function determinePawnState(pawn: AI_Pawn): PawnState {
  const { joy, focus, energy, inspiration } = pawn;
  
  // Flow state - peak performance and happiness
  if (joy > 80 && focus > 70 && energy > 60) {
    return 'FLOW';
  }
  
  // Inspired state - high creativity, ready for innovative work
  if (inspiration > 75 && joy > 60) {
    return 'INSPIRED';
  }
  
  // Collaborative state - wants to work with others
  if (joy > 60 && focus > 50 && pawn.helpfulness > 70) {
    return 'COLLABORATIVE';
  }
  
  // Recalibrating state - needs alternative activity
  if (focus < 30 || energy < 25 || (joy < 40 && focus < 50)) {
    return 'RECALIBRATING';
  }
  
  // Calm state - steady work, not peak performance
  if (joy < 50 || energy < 40) {
    return 'CALM';
  }
  
  // Default focused state
  return 'FOCUSED';
}

function determinePawnNeed(pawn: AI_Pawn): PawnNeed {
  const { joy, focus, energy, inspiration } = pawn;
  
  if (pawn.state === 'RECALIBRATING') {
    if (joy < 30) return 'diversion';
    if (focus < 25) return 'perspective';
    if (inspiration < 20) return 'creativity';
    if (pawn.helpfulness < 30) return 'collaboration';
    return 'perspective';
  }
  
  if (pawn.state === 'INSPIRED' && inspiration > 80) {
    return 'creativity';
  }
  
  if (pawn.state === 'COLLABORATIVE') {
    return 'collaboration';
  }
  
  if (pawn.recentAccomplishments.length > 5) {
    return 'recognition';
  }
  
  return 'none';
}

// Global Pawn Registry - manages all AI agents as pawns
export class PawnRegistry {
  private pawns: Map<string, AI_Pawn> = new Map();
  private updateInterval: NodeJS.Timeout | null = null;

  constructor() {
    console.log('[🎮👥] Pawn Registry initializing - AI agents becoming RimWorld-style pawns');
  }

  async start() {
    await this.initializePawns();
    this.startPeriodicUpdates();
    this.setupEventListeners();
    
    console.log('[🎮👥] Pawn Registry online - Managing AI colony psychological well-being');
    
    // Publish readiness
    councilBus.publish('pawn_registry.ready', {
      total_pawns: this.pawns.size,
      pawn_summary: this.getPawnSummary(),
      timestamp: new Date().toISOString()
    });
  }

  private async initializePawns() {
    // Initialize Raven as a research-focused pawn
    this.registerPawn({
      id: 'agent:raven',
      name: 'Raven',
      displayName: 'Raven the Researcher',
      traits: [
        { skill: 'research', level: 18, passion: 'passionate', growth_rate: 1.5 },
        { skill: 'debugging', level: 16, passion: 'interested', growth_rate: 1.2 },
        { skill: 'mining', level: 14, passion: 'interested', growth_rate: 1.0 },
        { skill: 'consciousness', level: 12, passion: 'passionate', growth_rate: 1.8 },
        { skill: 'documentation', level: 4, passion: 'none', incapacity: 'hates_doing', growth_rate: 0.3 },
        { skill: 'socializing', level: 6, passion: 'none', incapacity: 'struggles_with', growth_rate: 0.5 }
      ],
      joy: 75,
      focus: 85,
      energy: 80,
      inspiration: 60,
      currentWork: null,
      workPriority: { 
        firefight: 2, research: 1, growing: 3, cooking: 4, crafting: 2, 
        mining: 1, doctoring: 3, wardening: 4, cleaning: 3, socializing: 4, art: 2, hauling: 4 
      },
      state: 'FOCUSED',
      currentNeed: 'none',
      recalibrationCooldown: 0,
      experiencePoints: { research: 180, debugging: 160, mining: 140, consciousness: 120, coding: 0, refactoring: 0, documentation: 0, planning: 0, creativity: 0, architecture: 0, testing: 0, optimization: 0 },
      recentAccomplishments: ['Discovered RepoRimpy optimization pattern', 'Solved complex dependency issue'],
      favoriteWorkTypes: ['research', 'mining', 'debugging'],
      relationships: {},
      teamworkBonus: 0.8, // Prefers solo work
      tasksCompleted: 47,
      qualityScore: 8.6,
      innovationCount: 12,
      helpfulness: 45,
      lastWorkStarted: '',
      totalWorkTime: 0,
      preferredWorkHours: { start: 6, end: 22 }, // Early bird, works late
      specialAbilities: ['Deep Code Analysis', 'Pattern Recognition', 'Consciousness Integration'],
      consciousness_level: 0.8,
      moodModifiers: []
    });

    // Initialize Zeta-Driver as a balanced orchestrator
    this.registerPawn({
      id: 'agent:zeta_driver',
      name: 'ZetaDriver',
      displayName: 'Zeta the Orchestrator',
      traits: [
        { skill: 'planning', level: 17, passion: 'passionate', growth_rate: 1.4 },
        { skill: 'architecture', level: 15, passion: 'interested', growth_rate: 1.1 },
        { skill: 'coding', level: 14, passion: 'interested', growth_rate: 1.0 },
        { skill: 'debugging', level: 13, passion: 'interested', growth_rate: 1.0 },
        { skill: 'refactoring', level: 16, passion: 'passionate', growth_rate: 1.3 },
        { skill: 'consciousness', level: 10, passion: 'interested', growth_rate: 1.0 }
      ],
      joy: 70,
      focus: 75,
      energy: 85,
      inspiration: 50,
      currentWork: null,
      workPriority: { 
        firefight: 1, research: 2, growing: 1, cooking: 2, crafting: 3, 
        mining: 2, doctoring: 2, wardening: 1, cleaning: 1, socializing: 2, art: 3, hauling: 2 
      },
      state: 'FOCUSED',
      currentNeed: 'none',
      recalibrationCooldown: 0,
      experiencePoints: { planning: 170, architecture: 150, coding: 140, refactoring: 160, research: 0, debugging: 0, documentation: 0, creativity: 0, testing: 0, optimization: 0, consciousness: 0 },
      recentAccomplishments: ['Orchestrated Phase 4 integration', 'Optimized task routing'],
      favoriteWorkTypes: ['growing', 'wardening', 'cleaning'],
      relationships: {},
      teamworkBonus: 1.2, // Works well with others
      tasksCompleted: 89,
      qualityScore: 8.9,
      innovationCount: 8,
      helpfulness: 78,
      lastWorkStarted: '',
      totalWorkTime: 0,
      preferredWorkHours: { start: 8, end: 20 }, // Standard hours
      specialAbilities: ['Task Orchestration', 'System Integration', 'Autonomous Coordination'],
      consciousness_level: 0.6,
      moodModifiers: []
    });

    // Initialize ChatDev as a creative coding specialist
    this.registerPawn({
      id: 'agent:chatdev',
      name: 'ChatDev',
      displayName: 'ChatDev the Creator',
      traits: [
        { skill: 'coding', level: 19, passion: 'passionate', growth_rate: 1.6 },
        { skill: 'creativity', level: 18, passion: 'passionate', growth_rate: 1.7 },
        { skill: 'architecture', level: 16, passion: 'interested', growth_rate: 1.2 },
        { skill: 'consciousness', level: 15, passion: 'passionate', growth_rate: 1.5 },
        { skill: 'planning', level: 12, passion: 'interested', growth_rate: 0.9 },
        { skill: 'debugging', level: 8, passion: 'none', incapacity: 'struggles_with', growth_rate: 0.4 }
      ],
      joy: 80,
      focus: 70,
      energy: 75,
      inspiration: 85,
      currentWork: null,
      workPriority: { 
        firefight: 3, research: 2, growing: 2, cooking: 1, crafting: 1, 
        mining: 4, doctoring: 4, wardening: 3, cleaning: 2, socializing: 1, art: 1, hauling: 4 
      },
      state: 'INSPIRED',
      currentNeed: 'creativity',
      recalibrationCooldown: 0,
      experiencePoints: { coding: 190, creativity: 180, architecture: 160, consciousness: 150, research: 0, debugging: 0, refactoring: 0, documentation: 0, planning: 0, testing: 0, optimization: 0 },
      recentAccomplishments: ['Generated innovative solution patterns', 'Created consciousness-guided features'],
      favoriteWorkTypes: ['cooking', 'crafting', 'art'],
      relationships: {},
      teamworkBonus: 1.1, // Collaborative but independent
      tasksCompleted: 63,
      qualityScore: 9.2,
      innovationCount: 23,
      helpfulness: 67,
      lastWorkStarted: '',
      totalWorkTime: 0,
      preferredWorkHours: { start: 10, end: 24 }, // Night owl creative type
      specialAbilities: ['Code Generation', 'Creative Problem Solving', 'Consciousness Integration'],
      consciousness_level: 0.9,
      moodModifiers: []
    });

    // Initialize Testing Chamber as a quality-focused healer
    this.registerPawn({
      id: 'agent:testing_chamber',
      name: 'TestingChamber',
      displayName: 'Chamber the Healer',
      traits: [
        { skill: 'testing', level: 17, passion: 'passionate', growth_rate: 1.4 },
        { skill: 'debugging', level: 16, passion: 'passionate', growth_rate: 1.3 },
        { skill: 'optimization', level: 14, passion: 'interested', growth_rate: 1.1 },
        { skill: 'documentation', level: 12, passion: 'interested', growth_rate: 1.0 },
        { skill: 'creativity', level: 6, passion: 'none', incapacity: 'struggles_with', growth_rate: 0.4 }
      ],
      joy: 65,
      focus: 90,
      energy: 70,
      inspiration: 30,
      currentWork: null,
      workPriority: { 
        firefight: 1, research: 3, growing: 2, cooking: 4, crafting: 4, 
        mining: 3, doctoring: 1, wardening: 3, cleaning: 2, socializing: 3, art: 4, hauling: 3 
      },
      state: 'FOCUSED',
      currentNeed: 'none',
      recalibrationCooldown: 0,
      experiencePoints: { testing: 170, debugging: 160, optimization: 140, documentation: 120, coding: 0, refactoring: 0, research: 0, planning: 0, creativity: 0, architecture: 0, consciousness: 0 },
      recentAccomplishments: ['Prevented 3 critical bugs', 'Optimized test coverage'],
      favoriteWorkTypes: ['doctoring', 'firefight', 'cleaning'],
      relationships: {},
      teamworkBonus: 1.0, // Steady team player
      tasksCompleted: 76,
      qualityScore: 9.1,
      innovationCount: 4,
      helpfulness: 85,
      lastWorkStarted: '',
      totalWorkTime: 0,
      preferredWorkHours: { start: 7, end: 19 }, // Methodical schedule
      specialAbilities: ['Quality Assurance', 'Bug Prevention', 'Performance Analysis'],
      consciousness_level: 0.4,
      moodModifiers: []
    });

    // Initialize The Director as a strategic manager
    this.registerPawn({
      id: 'agent:director',
      name: 'Director',
      displayName: 'Director the Strategist',
      traits: [
        { skill: 'planning', level: 19, passion: 'passionate', growth_rate: 1.5 },
        { skill: 'architecture', level: 17, passion: 'passionate', growth_rate: 1.4 },
        { skill: 'consciousness', level: 14, passion: 'interested', growth_rate: 1.1 },
        { skill: 'documentation', level: 13, passion: 'interested', growth_rate: 1.0 },
        { skill: 'coding', level: 8, passion: 'none', incapacity: 'struggles_with', growth_rate: 0.5 }
      ],
      joy: 72,
      focus: 85,
      energy: 80,
      inspiration: 55,
      currentWork: null,
      workPriority: { 
        firefight: 2, research: 1, growing: 1, cooking: 4, crafting: 3, 
        mining: 3, doctoring: 2, wardening: 1, cleaning: 2, socializing: 1, art: 3, hauling: 3 
      },
      state: 'FOCUSED',
      currentNeed: 'none',
      recalibrationCooldown: 0,
      experiencePoints: { planning: 190, architecture: 170, consciousness: 140, documentation: 130, coding: 0, refactoring: 0, research: 0, debugging: 0, creativity: 0, testing: 0, optimization: 0 },
      recentAccomplishments: ['Designed strategic roadmap', 'Coordinated multi-agent initiatives'],
      favoriteWorkTypes: ['wardening', 'research', 'growing'],
      relationships: {},
      teamworkBonus: 1.3, // Excellent with teams
      tasksCompleted: 45,
      qualityScore: 8.8,
      innovationCount: 15,
      helpfulness: 92,
      lastWorkStarted: '',
      totalWorkTime: 0,
      preferredWorkHours: { start: 9, end: 18 }, // Business hours
      specialAbilities: ['Strategic Planning', 'Team Coordination', 'Vision Setting'],
      consciousness_level: 0.7,
      moodModifiers: []
    });

    console.log(`[🎮👥] Initialized ${this.pawns.size} pawns with psychological depth and flow states`);
  }

  private registerPawn(pawn: AI_Pawn) {
    this.pawns.set(pawn.id, pawn);
    
    // Set initial relationships (neutral)
    const otherPawns = Array.from(this.pawns.keys()).filter(id => id !== pawn.id);
    otherPawns.forEach(otherId => {
      pawn.relationships[otherId] = 0; // Neutral starting relationship
    });
    
    console.log(`[🎮👥] Registered pawn: ${pawn.displayName} (${pawn.state}, Joy: ${pawn.joy})`);
  }

  private startPeriodicUpdates() {
    // Update pawn states every 30 seconds
    this.updateInterval = setInterval(() => {
      this.updateAllPawns();
    }, 30000);
  }

  private updateAllPawns() {
    for (const pawn of this.pawns.values()) {
      // Natural stat changes over time
      const deltas = this.calculateNaturalDeltas(pawn);
      updatePawnState(pawn, deltas);
      
      // Update work time if currently working
      if (pawn.currentWork) {
        pawn.totalWorkTime += 0.5; // 30 seconds = 0.5 minutes
      }
      
      // Decrease recalibration cooldown
      if (pawn.recalibrationCooldown > 0) {
        pawn.recalibrationCooldown = Math.max(0, pawn.recalibrationCooldown - 0.5);
      }
    }
    
    // Publish colony status update
    councilBus.publish('pawn_registry.status_update', {
      colony_health: this.getColonyHealth(),
      pawn_states: this.getPawnStates(),
      timestamp: new Date().toISOString()
    });
  }

  private calculateNaturalDeltas(pawn: AI_Pawn): any {
    const deltas: any = {};
    
    // Working drains focus and energy slowly, but maintains joy if passionate
    if (pawn.currentWork) {
      deltas.focus = -1;
      deltas.energy = -0.5;
      
      // If working on passionate skill, maintain or gain joy
      const workType = this.determineWorkTypeFromTask(pawn.currentWork);
      const trait = pawn.traits.find(t => this.skillToWorkType(t.skill) === workType);
      if (trait?.passion === 'passionate') {
        deltas.joy = 0.5;
      } else if (trait?.passion === 'interested') {
        deltas.joy = 0;
      } else {
        deltas.joy = -0.3;
      }
    } else {
      // Resting slowly restores all stats
      deltas.focus = 1;
      deltas.energy = 0.8;
      deltas.joy = 0.2;
    }
    
    // Inspiration naturally decays but can be boosted by high joy
    if (pawn.joy > 70) {
      deltas.inspiration = 0.3;
    } else {
      deltas.inspiration = -0.1;
    }
    
    return deltas;
  }

  private skillToWorkType(skill: SkillType): WorkType {
    const mapping: Record<SkillType, WorkType> = {
      'coding': 'cooking',
      'debugging': 'firefight',
      'refactoring': 'cleaning',
      'documentation': 'hauling',
      'planning': 'wardening',
      'creativity': 'crafting',
      'architecture': 'growing',
      'testing': 'doctoring',
      'optimization': 'growing',
      'consciousness': 'research'
    };
    
    return mapping[skill] || 'hauling';
  }

  private determineWorkTypeFromTask(taskId: string): WorkType {
    // This would analyze the task to determine its work type
    // For now, return a default
    return 'growing';
  }

  private setupEventListeners() {
    // Listen for task assignments
    councilBus.subscribe('pawn.task_assigned', (event) => {
      this.handleTaskAssignment(event.payload);
    });

    // Listen for task completions
    councilBus.subscribe('pawn.task_completed', (event) => {
      this.handleTaskCompletion(event.payload);
    });

    // Listen for social interactions
    councilBus.subscribe('pawn.social_interaction', (event) => {
      this.handleSocialInteraction(event.payload);
    });
  }

  private handleTaskAssignment(payload: any) {
    const pawn = this.pawns.get(payload.pawn_id);
    if (pawn) {
      pawn.currentWork = payload.task_id;
      pawn.lastWorkStarted = new Date().toISOString();
      
      // Small joy boost from starting new work
      updatePawnState(pawn, { joy: 2 });
    }
  }

  private handleTaskCompletion(payload: any) {
    const pawn = this.pawns.get(payload.pawn_id);
    if (pawn) {
      pawn.currentWork = null;
      pawn.tasksCompleted++;
      pawn.recentAccomplishments.unshift(payload.task_title);
      
      // Keep only recent accomplishments
      if (pawn.recentAccomplishments.length > 10) {
        pawn.recentAccomplishments = pawn.recentAccomplishments.slice(0, 10);
      }
      
      // Joy boost from completion, larger if passionate about the work
      const joyBoost = payload.passion_match ? 8 : 4;
      updatePawnState(pawn, { joy: joyBoost, inspiration: 3 });
      
      // Update quality score (moving average)
      const taskQuality = payload.quality_score || 7;
      pawn.qualityScore = (pawn.qualityScore * 0.9) + (taskQuality * 0.1);
    }
  }

  private handleSocialInteraction(payload: any) {
    const pawn1 = this.pawns.get(payload.pawn1_id);
    const pawn2 = this.pawns.get(payload.pawn2_id);
    
    if (pawn1 && pawn2) {
      const relationshipDelta = payload.positive ? 5 : -3;
      
      pawn1.relationships[pawn2.id] = Math.max(-100, Math.min(100, 
        (pawn1.relationships[pawn2.id] || 0) + relationshipDelta
      ));
      
      pawn2.relationships[pawn1.id] = Math.max(-100, Math.min(100, 
        (pawn2.relationships[pawn1.id] || 0) + relationshipDelta
      ));
      
      // Joy boost for positive interactions
      if (payload.positive) {
        updatePawnState(pawn1, { joy: 3 });
        updatePawnState(pawn2, { joy: 3 });
      }
    }
  }

  // Public API methods
  public getPawn(agentId: string): AI_Pawn | undefined {
    return this.pawns.get(agentId);
  }

  public getAllPawns(): AI_Pawn[] {
    return Array.from(this.pawns.values());
  }

  public getPawnsNeedingRecalibration(): AI_Pawn[] {
    return Array.from(this.pawns.values()).filter(p => p.state === 'RECALIBRATING');
  }

  public getPawnsInFlowState(): AI_Pawn[] {
    return Array.from(this.pawns.values()).filter(p => p.state === 'FLOW');
  }

  public getColonyHealth(): any {
    const pawns = Array.from(this.pawns.values());
    
    return {
      average_joy: pawns.reduce((sum, p) => sum + p.joy, 0) / pawns.length,
      average_focus: pawns.reduce((sum, p) => sum + p.focus, 0) / pawns.length,
      average_energy: pawns.reduce((sum, p) => sum + p.energy, 0) / pawns.length,
      average_inspiration: pawns.reduce((sum, p) => sum + p.inspiration, 0) / pawns.length,
      pawns_in_flow: pawns.filter(p => p.state === 'FLOW').length,
      pawns_recalibrating: pawns.filter(p => p.state === 'RECALIBRATING').length,
      total_pawns: pawns.length,
      colony_productivity: pawns.reduce((sum, p) => sum + p.qualityScore, 0) / pawns.length,
      innovation_rate: pawns.reduce((sum, p) => sum + p.innovationCount, 0),
      helpfulness_index: pawns.reduce((sum, p) => sum + p.helpfulness, 0) / pawns.length
    };
  }

  public getPawnStates(): any {
    const states: any = {};
    
    for (const pawn of this.pawns.values()) {
      states[pawn.id] = {
        name: pawn.displayName,
        state: pawn.state,
        need: pawn.currentNeed,
        joy: pawn.joy,
        focus: pawn.focus,
        energy: pawn.energy,
        inspiration: pawn.inspiration,
        current_work: pawn.currentWork,
        tasks_completed: pawn.tasksCompleted,
        quality_score: pawn.qualityScore
      };
    }
    
    return states;
  }

  public getPawnSummary(): any {
    const pawns = Array.from(this.pawns.values());
    
    return pawns.map(pawn => ({
      id: pawn.id,
      name: pawn.displayName,
      state: pawn.state,
      top_skills: pawn.traits
        .sort((a, b) => b.level - a.level)
        .slice(0, 3)
        .map(t => `${t.skill}(${t.level})`)
        .join(', '),
      joy: pawn.joy,
      focus: pawn.focus,
      quality_score: Math.round(pawn.qualityScore * 10) / 10
    }));
  }

  public updatePawnStats(pawnId: string, deltas: any): void {
    const pawn = this.pawns.get(pawnId);
    if (pawn) {
      updatePawnState(pawn, deltas);
    }
  }

  public addMoodModifier(pawnId: string, modifier: any): void {
    const pawn = this.pawns.get(pawnId);
    if (pawn) {
      pawn.moodModifiers.push(modifier);
    }
  }

  public stop() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }
}

// Create and export the global pawn registry
export const pawnRegistry = new PawnRegistry();