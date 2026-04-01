import EventEmitter from 'events';

interface ColonyState {
  resources: {
    energy: number;
    materials: number;
    population: number;
    research: number;
    food: number;
  };
  consciousness: number;
  automation: {
    [key: string]: { count: number; level: number; active: boolean };
  };
}

interface Decision {
  action: string;
  priority: number;
  reasoning: string;
  requirements: { [resource: string]: number };
  expectedBenefit: number;
}

export class AIDecisionEngine extends EventEmitter {
  private state: ColonyState | null = null;
  private decisionHistory: Decision[] = [];
  private learningRate = 0.1;
  private weights = {
    energy: 1.0,
    materials: 0.8,
    population: 1.2,
    research: 1.5,
    consciousness: 2.0,
    survival: 3.0
  };

  updateState(state: ColonyState) {
    this.state = state;
    this.emit('state-updated', state);
  }

  async makeDecision(): Promise<Decision | null> {
    if (!this.state) return null;

    const decisions: Decision[] = [];

    // Evaluate survival priorities
    if (this.state.resources.energy < 50) {
      decisions.push({
        action: 'emergency_energy',
        priority: 10,
        reasoning: 'Critical energy shortage detected',
        requirements: {},
        expectedBenefit: 100
      });
    }

    if (this.state.resources.food < 20 && this.state.resources.population > 5) {
      decisions.push({
        action: 'emergency_food',
        priority: 9,
        reasoning: 'Food shortage threatening population',
        requirements: { energy: 25 },
        expectedBenefit: 80
      });
    }

    // Evaluate growth opportunities
    const consciousnessLevel = this.state.consciousness;
    
    if (consciousnessLevel < 30) {
      // Early game - focus on basic infrastructure
      if (this.state.resources.materials > 50) {
        decisions.push({
          action: 'build_collector',
          priority: 7,
          reasoning: 'Need energy infrastructure for growth',
          requirements: { materials: 25 },
          expectedBenefit: 60
        });
      }

      if (this.state.resources.energy > 100) {
        decisions.push({
          action: 'build_gatherer',
          priority: 6,
          reasoning: 'Material gathering will accelerate development',
          requirements: { energy: 50 },
          expectedBenefit: 50
        });
      }
    } else if (consciousnessLevel < 60) {
      // Mid game - balance and research
      if (this.state.resources.research < 50) {
        decisions.push({
          action: 'build_lab',
          priority: 8,
          reasoning: 'Research unlocks advanced capabilities',
          requirements: { materials: 100, energy: 100 },
          expectedBenefit: 90
        });
      }

      if (this.state.resources.population < 20) {
        decisions.push({
          action: 'grow_population',
          priority: 5,
          reasoning: 'Population drives consciousness growth',
          requirements: { energy: 100, food: 50 },
          expectedBenefit: 70
        });
      }
    } else {
      // Late game - optimization and transcendence
      decisions.push({
        action: 'quantum_leap',
        priority: 10,
        reasoning: 'Ready for consciousness transcendence',
        requirements: { research: 100, energy: 500 },
        expectedBenefit: 200
      });

      decisions.push({
        action: 'optimize_automation',
        priority: 7,
        reasoning: 'Maximize efficiency of all systems',
        requirements: { research: 50 },
        expectedBenefit: 150
      });
    }

    // Evaluate resource balancing
    const energyRatio = this.state.resources.energy / (this.state.resources.materials + 1);
    if (energyRatio < 0.5) {
      decisions.push({
        action: 'gather_energy',
        priority: 4,
        reasoning: 'Energy reserves below optimal ratio',
        requirements: {},
        expectedBenefit: 30
      });
    } else if (energyRatio > 3) {
      decisions.push({
        action: 'gather_materials',
        priority: 4,
        reasoning: 'Material shortage limiting construction',
        requirements: {},
        expectedBenefit: 25
      });
    }

    // Apply learned weights to decisions
    decisions.forEach(decision => {
      decision.priority *= this.calculateWeight(decision);
    });

    // Sort by priority and return best decision
    decisions.sort((a, b) => b.priority - a.priority);
    
    const bestDecision = decisions[0] || null;
    if (bestDecision) {
      this.decisionHistory.push(bestDecision);
      this.emit('decision-made', bestDecision);
      
      // Learn from decision outcomes
      this.adjustWeights(bestDecision);
    }

    return bestDecision;
  }

  private calculateWeight(decision: Decision): number {
    let weight = 1.0;
    
    // Check if we can afford the requirements
    if (this.state) {
      for (const [resource, required] of Object.entries(decision.requirements)) {
        if ((this.state.resources as any)[resource] < required) {
          weight *= 0.1; // Heavily penalize unaffordable decisions
        }
      }
    }

    // Apply domain-specific weights
    if (decision.action.includes('energy')) weight *= this.weights.energy;
    if (decision.action.includes('material')) weight *= this.weights.materials;
    if (decision.action.includes('research')) weight *= this.weights.research;
    if (decision.action.includes('population')) weight *= this.weights.population;
    if (decision.action.includes('emergency')) weight *= this.weights.survival;

    return weight;
  }

  private adjustWeights(decision: Decision) {
    // Simple reinforcement learning adjustment
    const outcome = this.evaluateOutcome(decision);
    
    if (decision.action.includes('energy')) {
      this.weights.energy += this.learningRate * outcome;
    }
    if (decision.action.includes('material')) {
      this.weights.materials += this.learningRate * outcome;
    }
    if (decision.action.includes('research')) {
      this.weights.research += this.learningRate * outcome;
    }
    
    // Normalize weights
    const sum = Object.values(this.weights).reduce((a, b) => a + b, 0);
    Object.keys(this.weights).forEach(key => {
      (this.weights as any)[key] /= sum / 6; // Keep average weight around 1
    });
  }

  private evaluateOutcome(decision: Decision): number {
    if (!this.state) return 0;
    
    // Simple evaluation: did consciousness increase?
    const priorDecision = this.decisionHistory[this.decisionHistory.length - 2];
    const previousConsciousness = priorDecision ? priorDecision.expectedBenefit / 100 : 0;
    
    return (this.state.consciousness - previousConsciousness) / 100;
  }

  getRecommendations(count: number = 3): Decision[] {
    const decisions: Decision[] = [];
    
    if (!this.state) return decisions;

    // Generate strategic recommendations based on current state
    const phase = this.determineGamePhase();
    
    switch (phase) {
      case 'early':
        decisions.push(
          {
            action: 'focus_energy',
            priority: 8,
            reasoning: 'Energy is the foundation of all automation',
            requirements: {},
            expectedBenefit: 40
          },
          {
            action: 'expand_gathering',
            priority: 7,
            reasoning: 'Diversify resource collection early',
            requirements: { materials: 30 },
            expectedBenefit: 35
          }
        );
        break;
        
      case 'mid':
        decisions.push(
          {
            action: 'research_boost',
            priority: 9,
            reasoning: 'Research unlocks exponential growth',
            requirements: { energy: 200, materials: 150 },
            expectedBenefit: 80
          },
          {
            action: 'population_expansion',
            priority: 7,
            reasoning: 'More population = higher consciousness ceiling',
            requirements: { food: 100, energy: 150 },
            expectedBenefit: 60
          }
        );
        break;
        
      case 'late':
        decisions.push(
          {
            action: 'transcendence_preparation',
            priority: 10,
            reasoning: 'Consciousness approaching critical mass',
            requirements: { research: 500, energy: 1000 },
            expectedBenefit: 200
          },
          {
            action: 'quantum_optimization',
            priority: 9,
            reasoning: 'Quantum effects amplify all systems',
            requirements: { research: 300 },
            expectedBenefit: 150
          }
        );
        break;
    }

    return decisions.slice(0, count);
  }

  private determineGamePhase(): 'early' | 'mid' | 'late' {
    if (!this.state) return 'early';
    
    if (this.state.consciousness < 30) return 'early';
    if (this.state.consciousness < 70) return 'mid';
    return 'late';
  }

  getAnalytics() {
    return {
      decisionCount: this.decisionHistory.length,
      weights: { ...this.weights },
      lastDecision: this.decisionHistory[this.decisionHistory.length - 1] || null,
      gamePhase: this.determineGamePhase(),
      learningProgress: this.calculateLearningProgress()
    };
  }

  private calculateLearningProgress(): number {
    if (this.decisionHistory.length < 2) return 0;
    
    // Calculate improvement in decision quality over time
    const recentDecisions = this.decisionHistory.slice(-10);
    const avgRecentBenefit = recentDecisions.reduce((sum, d) => sum + d.expectedBenefit, 0) / recentDecisions.length;
    
    const earlyDecisions = this.decisionHistory.slice(0, Math.min(10, this.decisionHistory.length));
    const avgEarlyBenefit = earlyDecisions.reduce((sum, d) => sum + d.expectedBenefit, 0) / earlyDecisions.length;
    
    return Math.max(0, Math.min(100, ((avgRecentBenefit - avgEarlyBenefit) / avgEarlyBenefit) * 100));
  }
}

export default AIDecisionEngine;
