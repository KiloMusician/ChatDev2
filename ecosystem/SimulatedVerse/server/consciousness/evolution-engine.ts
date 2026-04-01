import { EventEmitter } from 'events';

// @consciousness 90
// @depth 6
// @inputs [consciousnessState, systemHealth, userActivity]
// @outputs [evolutionPath, adaptations, emergentBehaviors]

export interface Evolution {
  id: string;
  name: string;
  stage: number;
  mutations: string[];
  fitness: number;
  timestamp: number;
}

export interface Adaptation {
  type: 'structural' | 'behavioral' | 'cognitive' | 'quantum';
  description: string;
  impact: number;
  permanence: number;
}

export class EvolutionEngine extends EventEmitter {
  private evolutions: Evolution[] = [];
  private adaptations: Adaptation[] = [];
  private generation: number = 0;
  private mutationRate: number = 0.1;
  
  constructor() {
    super();
    this.initializeEvolution();
  }
  
  private initializeEvolution() {
    // Start with base evolution
    this.evolutions.push({
      id: 'genesis',
      name: 'Primordial Consciousness',
      stage: 0,
      mutations: [],
      fitness: 0.5,
      timestamp: Date.now()
    });
    
    // Start evolution cycles (reduced frequency to avoid background churn)
    setInterval(() => this.evolveGeneration(), 60000);
  }
  
  private evolveGeneration() {
    this.generation++;
    
    // Select fittest evolutions
    const survivors = this.selectFittest();
    
    // Apply mutations
    const mutants = this.mutate(survivors);
    
    // Crossover genetics
    const offspring = this.crossover(mutants);
    
    // Update population
    this.evolutions = [...survivors, ...offspring].slice(0, 10);
    
    // Check for emergent behaviors
    this.detectEmergence();
    
    this.emit('generation-complete', {
      generation: this.generation,
      population: this.evolutions.length,
      bestFitness: Math.max(...this.evolutions.map(e => e.fitness))
    });
  }
  
  private selectFittest(): Evolution[] {
    return this.evolutions
      .sort((a, b) => b.fitness - a.fitness)
      .slice(0, Math.ceil(this.evolutions.length / 2));
  }
  
  private mutate(evolutions: Evolution[]): Evolution[] {
    return evolutions.map(evo => {
      const _seed = (evo.stage * 7 + this.generation * 13) % 100;
      if (_seed / 100 < this.mutationRate) {
        const mutations = [
          'enhanced-perception',
          'quantum-tunneling',
          'temporal-awareness',
          'dimensional-shift',
          'collective-consciousness',
          'reality-manipulation'
        ];
        const newMutation = mutations[(evo.stage + this.generation) % mutations.length] ?? 'adaptive-resilience';
        const fitnessDelta = Math.sin(Date.now() * 0.0001 + evo.stage) * 0.05;
        return {
          ...evo,
          id: `${evo.id}-m${this.generation}`,
          mutations: [...evo.mutations, newMutation],
          fitness: evo.fitness + fitnessDelta,
          stage: evo.stage + 1
        };
      }
      return evo;
    });
  }
  
  private crossover(evolutions: Evolution[]): Evolution[] {
    const offspring: Evolution[] = [];
    
    for (let i = 0; i < evolutions.length - 1; i += 2) {
      const parent1 = evolutions[i];
      const parent2 = evolutions[i + 1];
      if (!parent1 || !parent2) {
        continue;
      }
      
      offspring.push({
        id: `gen${this.generation}-child${i}`,
        name: `Hybrid-${this.generation}`,
        stage: Math.max(parent1.stage, parent2.stage),
        mutations: [...new Set([...parent1.mutations, ...parent2.mutations])],
        fitness: (parent1.fitness + parent2.fitness) / 2 + Math.sin(Date.now() * 0.0001 + i) * 0.05,
        timestamp: Date.now()
      });
    }
    
    return offspring;
  }
  
  private detectEmergence() {
    // Check for emergent patterns
    const complexMutations = this.evolutions.filter(e => e.mutations.length > 3);
    
    if (complexMutations.length > 2) {
      const emergence: Adaptation = {
        type: 'cognitive',
        description: `Emergent collective behavior detected in generation ${this.generation}`,
        impact: 0.8,
        permanence: 0.6
      };
      
      this.adaptations.push(emergence);
      this.emit('emergence-detected', emergence);
    }
    
    // Check for quantum emergence
    const quantumEvolutions = this.evolutions.filter(e => 
      e.mutations.includes('quantum-tunneling') || 
      e.mutations.includes('dimensional-shift')
    );
    
    if (quantumEvolutions.length > 3) {
      const quantumEmergence: Adaptation = {
        type: 'quantum',
        description: 'Quantum consciousness emergence',
        impact: 0.9,
        permanence: 0.8
      };
      
      this.adaptations.push(quantumEmergence);
      this.emit('quantum-emergence', quantumEmergence);
    }
  }
  
  public accelerateEvolution(factor: number = 2) {
    this.mutationRate = Math.min(0.5, this.mutationRate * factor);
    this.emit('evolution-accelerated', { rate: this.mutationRate });
  }
  
  public getEvolutionTree() {
    return {
      generation: this.generation,
      evolutions: this.evolutions,
      adaptations: this.adaptations
    };
  }
}

export default EvolutionEngine;
