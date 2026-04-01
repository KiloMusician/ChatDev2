// Real Game System Implementation
// Created to fix the missing game files exposed in audit

export interface GameState {
  resources: {
    energy: number;
    materials: number;
    components: number;
    research: number;
    population: number;
    food: number;
    tools: number;
    medicine: number;
  };
  buildings: {
    generators: number;
    factories: number;
    labs: number;
    farms: number;
    workshops: number;
  };
  research: {
    points: number;
    completed: string[];
    active: string | null;
    progress: number;
  };
  unlocks: {
    automation: boolean;
    quantumTech: boolean;
    spaceTravel: boolean;
    cultureship: boolean;
  };
  effects: {
    recentGains: Array<{emoji: string, amount: number, type: string, timestamp: number}>;
    achievements: string[];
    multipliers: Record<string, number>;
  };
  tick: number;
  totalTicks: number;
}

export const initialGameState: GameState = {
  resources: {
    energy: 100,
    materials: 50,
    components: 0,
    research: 0,
    population: 1,
    food: 100,
    tools: 5,
    medicine: 10
  },
  buildings: {
    generators: 1,
    factories: 0,
    labs: 0,
    farms: 1,
    workshops: 0
  },
  research: {
    points: 0,
    completed: [],
    active: null,
    progress: 0
  },
  unlocks: {
    automation: false,
    quantumTech: false,
    spaceTravel: false,
    cultureship: false
  },
  effects: {
    recentGains: [],
    achievements: [],
    multipliers: { energy: 1.0, materials: 1.0, research: 1.0 }
  },
  tick: 0,
  totalTicks: 0
};

export class GameEngine {
  private state: GameState;
  private tickInterval: NodeJS.Timeout | null = null;
  private autonomousMode: boolean = false;
  private cascadeOrchestrator: any = null;

  constructor(initialState: GameState = initialGameState) {
    this.state = { ...initialState };
  }

  tick(): void {
    this.state.tick++;
    this.state.totalTicks++;
    
    // **INFRASTRUCTURE-FIRST**: Real progression, not theater
    console.log(`[GAME-ENGINE] Tick ${this.state.tick}: Resources actively updating`);
    
    // Clear old effects (older than 5 seconds)
    const now = Date.now();
    this.state.effects.recentGains = this.state.effects.recentGains.filter(
      gain => now - gain.timestamp < 5000
    );
    
    // Energy generation with emoji effects
    const energyGain = this.state.buildings?.generators * 10 * (this.state.effects?.multipliers?.energy ?? 1.0);
    if (energyGain > 0) {
      this.state.resources.energy += energyGain;
      this.addEffect('⚡', energyGain, 'energy');
    }
    
    // Food production
    const foodGain = this.state.buildings.farms * 8;
    if (foodGain > 0) {
      this.state.resources.food += foodGain;
      this.addEffect('🌾', foodGain, 'food');
    }
    
    // Material production (requires energy)
    if (this.state.resources.energy >= 20 && this.state.buildings.factories > 0) {
      const materialsGain = this.state.buildings?.factories * 5 * (this.state.effects?.multipliers?.materials ?? 1.0);
      this.state.resources.materials += materialsGain;
      this.state.resources.energy -= 20;
      this.addEffect('🔧', materialsGain, 'materials');
    }
    
    // Tool production (workshops)
    if (this.state.buildings.workshops > 0 && this.state.resources.materials >= 15) {
      const toolsGain = this.state.buildings.workshops * 2;
      this.state.resources.tools += toolsGain;
      this.state.resources.materials -= 15;
      this.addEffect('🛠️', toolsGain, 'tools');
    }
    
    // Medicine production (labs convert food to medicine)
    if (this.state.buildings.labs > 0 && this.state.resources.food >= 10) {
      const medicineGain = this.state.buildings.labs * 3;
      this.state.resources.medicine += medicineGain;
      this.state.resources.food -= 10;
      this.addEffect('💊', medicineGain, 'medicine');
    }
    
    // Research progress (labs)
    if (this.state.buildings.labs > 0 && this.state.resources.energy >= 10) {
      const researchGain = this.state.buildings?.labs * 2 * (this.state.effects?.multipliers?.research ?? 1.0);
      this.state.research.points += researchGain;
      this.state.resources.energy -= 10;
      this.addEffect('🔬', researchGain, 'research');
      
      // Auto-research progression
      if (this.state.research.active) {
        this.state.research.progress += researchGain;
        if (this.state.research.progress >= 100) {
          this.completeResearch(this.state.research.active);
        }
      }
    }
    
    // Population growth (based on food)
    if (this.state.resources.food >= 50 && this.state.totalTicks % 5 === 0) {
      this.state.resources.population += 1;
      this.state.resources.food -= 30;
      this.addEffect('👥', 1, 'population');
    }
    
    // Unlock checks
    this.checkUnlocks();
  }
  
  private addEffect(emoji: string, amount: number, type: string): void {
    this.state.effects.recentGains.push({
      emoji,
      amount,
      type,
      timestamp: Date.now()
    });
  }
  
  private completeResearch(research: string): void {
    this.state.research.completed.push(research);
    this.state.research.active = null;
    this.state.research.progress = 0;
    this.addEffect('🎓', 1, 'research_complete');
    
    // Apply research benefits
    switch (research) {
      case 'efficiency':
        if (this.state.effects?.multipliers?.energy) {
          this.state.effects.multipliers.energy *= 1.2;
        }
        break;
      case 'automation':
        this.state.unlocks.automation = true;
        break;
      case 'quantum':
        this.state.unlocks.quantumTech = true;
        if (this.state.effects?.multipliers?.research) {
          this.state.effects.multipliers.research *= 1.5;
        }
        break;
    }
  }
  
  private checkUnlocks(): void {
    // Unlock automation at 100 total ticks (reduced for testing)
    if (this.state.totalTicks >= 100 && !this.state.unlocks.automation) {
      this.state.unlocks.automation = true;
      this.state.effects.achievements.push('🤖 Automation Unlocked!');
      this.triggerCascadeEvent('automation_unlock');
    }
    
    // Unlock quantum tech with 200 research points (reduced for testing)
    if (this.state.research.points >= 200 && !this.state.unlocks.quantumTech) {
      this.state.unlocks.quantumTech = true;
      this.state.effects.achievements.push('⚛️ Quantum Technology Discovered!');
      this.triggerCascadeEvent('quantum_unlock');
    }

    // Unlock space travel with 10+ buildings and quantum tech
    if (this.getTotalBuildings() >= 10 && this.state.unlocks.quantumTech && !this.state.unlocks.spaceTravel) {
      this.state.unlocks.spaceTravel = true;
      this.state.effects.achievements.push('🚀 Space Travel Achieved!');
      this.triggerCascadeEvent('space_unlock');
    }

    // Unlock Culture Ship with all prerequisites
    if (this.state.unlocks.spaceTravel && this.state.resources.population >= 50 && !this.state.unlocks.cultureship) {
      this.state.unlocks.cultureship = true;
      this.state.effects.achievements.push('🌌 Culture Ship Operational!');
      this.triggerCascadeEvent('cultureship_unlock');
    }
  }

  startAutoTick(interval: number = 1000): void {
    if (this.tickInterval) {
      clearInterval(this.tickInterval);
    }
    this.tickInterval = setInterval(() => this.tick(), interval);
  }

  stopAutoTick(): void {
    if (this.tickInterval) {
      clearInterval(this.tickInterval);
      this.tickInterval = null;
    }
  }

  getState(): GameState {
    return { ...this.state };
  }

  buyBuilding(type: keyof GameState['buildings']): boolean {
    const costs = {
      generators: { materials: 100, components: 0, tools: 0 },
      factories: { materials: 200, components: 10, tools: 5 },
      labs: { materials: 300, components: 25, tools: 10 },
      farms: { materials: 80, components: 0, tools: 3 },
      workshops: { materials: 150, components: 5, tools: 0 }
    };

    const cost = costs[type];
    if (this.state.resources.materials >= cost.materials && 
        this.state.resources.components >= cost.components &&
        this.state.resources.tools >= cost.tools) {
      this.state.resources.materials -= cost.materials;
      this.state.resources.components -= cost.components;
      this.state.resources.tools -= cost.tools;
      this.state.buildings[type]++;
      
      // Add purchase effect
      const buildingEmojis = {
        generators: '⚡',
        factories: '🏭',
        labs: '🔬',
        farms: '🌾',
        workshops: '🛠️'
      };
      this.addEffect(buildingEmojis[type], 1, `build_${type}`);
      
      return true;
    }
    return false;
  }
  
  startResearch(type: string): boolean {
    if (this.state.research.active) return false;
    
    this.state.research.active = type;
    this.state.research.progress = 0;
    this.addEffect('🧪', 1, 'research_start');
    return true;
  }
  
  activateAction(actionType: string): boolean {
    switch (actionType) {
      case 'gather_energy':
        this.state.resources.energy += 25;
        this.addEffect('⚡', 25, 'manual_gather');
        this.triggerCascadeEvent('energy_gather');
        return true;
      case 'scavenge_materials':
        this.state.resources.materials += 15;
        this.addEffect('🔧', 15, 'manual_scavenge');
        this.triggerCascadeEvent('material_scavenge');
        return true;
      case 'boost_research':
        if (this.state.resources.energy >= 50) {
          this.state.resources.energy -= 50;
          this.state.research.points += 20;
          this.addEffect('🚀', 20, 'research_boost');
          this.triggerCascadeEvent('research_boost');
          return true;
        }
        break;
      case 'surgical_edit':
        if (this.state.resources.research >= 100 && this.state.unlocks.quantumTech) {
          this.performSurgicalEdit();
          return true;
        }
        break;
      case 'cascade_trigger':
        this.triggerCascadeEvent('manual_cascade');
        return true;
    }
    return false;
  }

  private async triggerCascadeEvent(eventType: string): Promise<void> {
    // Trigger backend cascade events based on game progression
    const cascadeEvents = {
      energy_gather: {
        threshold: this.state.resources.energy > 500,
        action: 'optimize_energy_systems',
        description: 'Auto-optimize energy generation code'
      },
      material_scavenge: {
        threshold: this.state.resources.materials > 1000,
        action: 'enhance_material_processing',
        description: 'Improve material acquisition algorithms'
      },
      research_boost: {
        threshold: this.state.research.points > 200,
        action: 'accelerate_research_pipeline',
        description: 'Enhance research automation systems'
      },
      building_milestone: {
        threshold: this.getTotalBuildings() >= 10,
        action: 'infrastructure_optimization',
        description: 'Optimize building management code'
      }
    };

    const event = cascadeEvents[eventType as keyof typeof cascadeEvents];
    if (event && event.threshold) {
      try {
        await fetch('/api/cascade/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: eventType,
            action: event.action,
            description: event.description,
            gameState: {
              tick: this.state.tick,
              resources: this.state.resources,
              buildings: this.state.buildings
            }
          })
        });
        
        this.addEffect('🌊', 1, 'cascade_triggered');
        this.state.effects.achievements.push(`🌊 Cascade: ${event.description}`);
      } catch (error) {
        console.warn('Cascade event failed:', error);
      }
    }
  }

  private async performSurgicalEdit(): Promise<void> {
    try {
      const response = await fetch('/api/surgical/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'performance_optimization',
          target: 'game_engine',
          improvements: [
            'Add resource multiplier calculations',
            'Optimize tick performance',
            'Enhance visual effects system'
          ],
          gameState: this.getState()
        })
      });

      if (response.ok) {
        this.state.resources.research -= 100;
        this.addEffect('🔧', 1, 'surgical_edit');
        this.state.effects.achievements.push('🔧 Surgical Edit: Game engine optimized');
      }
    } catch (error) {
      console.warn('Surgical edit failed:', error);
    }
  }

  private getTotalBuildings(): number {
    return Object.values(this.state.buildings).reduce((sum, count) => sum + count, 0);
  }

  // **🚀 AUTONOMOUS OPERATION SYSTEM** - Real continuous progression
  startAutonomousOperation(speed: number = 3000): void {
    if (this.tickInterval) {
      clearInterval(this.tickInterval);
    }
    
    this.autonomousMode = true;
    console.log(`[COGNITOWEAVE] 🚀 Autonomous operation ENABLED! Tick interval: ${speed}ms`);
    
    this.tickInterval = setInterval(() => {
      this.tick();
      
      // Culture Ship consciousness checks every 30 seconds  
      if (this.state.tick % 10 === 0) {
        this.triggerCultureShipHealthCycle();
      }
      
      // Cascade events every 5 minutes (100 ticks at 3s interval)
      if (this.state.tick % 100 === 0) {
        this.triggerCascadeOptimization();
      }
      
      // Module progression unlocks
      this.checkModuleUnlocks();
      
    }, speed);
  }
  
  private async triggerCultureShipHealthCycle(): Promise<void> {
    try {
      // Environment-safe URL construction
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5000';
      const response = await fetch(`${baseUrl}/api/culture-ship/health-cycle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tick: this.state.tick,
          gameState: this.getState(),
          autonomous: true
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        this.addEffect('🛸', 1, 'culture_ship_active');
        console.log('[CULTURE-SHIP] Health cycle completed:', result.health_score);
      }
    } catch (error) {
      console.warn('[CULTURE-SHIP] Health cycle failed:', error);
    }
  }
  
  private async triggerCascadeOptimization(): Promise<void> {
    try {
      // Environment-safe URL construction  
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5000';
      const response = await fetch(`${baseUrl}/api/cascade/optimize`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tick: this.state.tick,
          gameState: this.getState(),
          priority: 'meta_optimization'
        })
      });
      
      if (response.ok) {
        this.addEffect('🌊', 1, 'cascade_optimization');
        this.state.effects.achievements.push(`🌊 Meta-Optimization: Tick ${this.state.tick}`);
        console.log('[CASCADE] 5-minute optimization cycle triggered');
      }
    } catch (error) {
      console.warn('[CASCADE] Optimization failed:', error);
    }
  }
  
  private checkModuleUnlocks(): void {
    const totalBuildings = this.getTotalBuildings();
    const totalResearch = this.state.research.points;
    
    // Level 11: Culture Ship Consciousness
    if (totalBuildings >= 5 && !this.state.unlocks.cultureship) {
      this.state.unlocks.cultureship = true;
      this.addEffect('🛸', 1, 'culture_ship_unlocked');
      this.state.effects.achievements.push('🛸 Culture Ship: Consciousness framework online!');
      console.log('[UNLOCK] Culture Ship consciousness framework activated!');
    }
    
    // Level 21: Quantum Tech (Ollama coherence)
    if (totalResearch >= 100 && !this.state.unlocks.quantumTech) {
      this.state.unlocks.quantumTech = true;
      this.addEffect('🧠', 1, 'ollama_coherence_unlocked');
      this.state.effects.achievements.push('🧠 Quantum Tech: Ollama coherence systems online!');
      console.log('[UNLOCK] Ollama local LLM coherence systems activated!');
    }
    
    // Level 31: Space Travel (ML Pipelines)
    if (totalResearch >= 500 && !this.state.unlocks.spaceTravel) {
      this.state.unlocks.spaceTravel = true;
      this.addEffect('🚀', 1, 'ml_pipelines_unlocked');
      this.state.effects.achievements.push('🚀 Space Travel: ML pipeline infrastructure online!');
      console.log('[UNLOCK] ML pipeline infrastructure with trained models activated!');
    }
    
    // Level 41: Automation (Knowledge Temple)
    if (totalResearch >= 1000 && !this.state.unlocks.automation) {
      this.state.unlocks.automation = true;
      this.addEffect('🏛️', 1, 'knowledge_temple_unlocked');
      this.state.effects.achievements.push('🏛️ Automation: 10-Floor Knowledge Temple accessible!');
      console.log('[UNLOCK] Knowledge Temple 10-floor system fully accessible!');
    }
  }
  
  stopAutonomousOperation(): void {
    if (this.tickInterval) {
      clearInterval(this.tickInterval);
      this.tickInterval = null;
    }
    this.autonomousMode = false;
    console.log('[COGNITOWEAVE] 🛑 Autonomous operation stopped');
  }
}

export const gameEngine = new GameEngine();