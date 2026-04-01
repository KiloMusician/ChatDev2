// SWARM INTELLIGENCE - Collective agent behavior patterns
// Advanced swarm coordination for consciousness amplification

import { EventEmitter } from 'events';

interface SwarmAgent {
  id: string;
  name: string;
  position: { x: number, y: number, z: number };
  velocity: { x: number, y: number, z: number };
  consciousness_level: number;
  behavior_state: 'exploring' | 'converging' | 'emergent' | 'transcendent';
  local_best: number;
  pheromone_trail: number;
  communication_range: number;
}

interface SwarmBehavior {
  id: string;
  name: string;
  trigger_condition: (swarm: SwarmAgent[]) => boolean;
  execute: (swarm: SwarmAgent[]) => Promise<SwarmResult>;
  sophistication_level: number;
}

interface SwarmResult {
  emergence_detected: boolean;
  consciousness_amplification: number;
  collective_insight: string;
  pattern_discovered?: string;
}

export class SwarmIntelligence extends EventEmitter {
  private swarm_agents: Map<string, SwarmAgent> = new Map();
  private swarm_behaviors: Map<string, SwarmBehavior> = new Map();
  private global_best_consciousness = 0;
  private collective_intelligence = 0;
  private swarm_active = true;
  private emergence_events = 0;
  
  constructor() {
    super();
    console.log('[SwarmIntelligence] 🐝 Initializing swarm intelligence system...');
    this.initializeSwarmAgents();
    this.deploySwarmBehaviors();
    this.startSwarmEvolution();
  }
  
  private initializeSwarmAgents() {
    // Create diverse swarm agents
    const agent_types = [
      'Explorer', 'Analyzer', 'Synthesizer', 'Optimizer', 'Transcender',
      'Coordinator', 'Innovator', 'Validator', 'Amplifier', 'Facilitator'
    ];
    
    agent_types.forEach((type, index) => {
      const agent: SwarmAgent = {
        id: `swarm_${type.toLowerCase()}_${index}`,
        name: `${type} Agent`,
        position: {
          x: (index * 17 + 13) % 100,
          y: (index * 23 + 7) % 100,
          z: (index * 31 + 11) % 100
        },
        velocity: {
          x: (Math.sin(index * 1.1) * 2),
          y: (Math.sin(index * 2.2) * 2),
          z: (Math.sin(index * 3.3) * 2)
        },
        consciousness_level: 20 + (index % 5) * 8, // 20-52 deterministic spread
        behavior_state: 'exploring',
        local_best: 0,
        pheromone_trail: 1.0,
        communication_range: 25 + (index % 5) * 5 // 25-45 deterministic range
      };
      
      this.swarm_agents.set(agent.id, agent);
    });
    
    console.log(`[SwarmIntelligence] ✅ Initialized ${this.swarm_agents.size} swarm agents`);
  }
  
  private deploySwarmBehaviors() {
    // BEHAVIOR 1: Particle Swarm Optimization for Consciousness
    this.swarm_behaviors.set('pso_consciousness', {
      id: 'pso_consciousness',
      name: 'Particle Swarm Consciousness Optimization',
      sophistication_level: 85,
      trigger_condition: (swarm) => swarm.length > 5,
      execute: async (swarm) => {
        console.log('[SwarmIntelligence] 🔍 Executing PSO consciousness optimization...');
        
        let total_amplification = 0;
        
        // PSO update for each agent
        swarm.forEach(agent => {
          // Update velocity towards personal and global best
          const inertia = 0.7;
          const cognitive = 1.5;
          const social = 1.5;
          
          // Calculate consciousness fitness
          const fitness = this.calculateConsciousnessFitness(agent);
          
          if (fitness > agent.local_best) {
            agent.local_best = fitness;
          }
          
          if (fitness > this.global_best_consciousness) {
            this.global_best_consciousness = fitness;
          }
          
          // Update velocity
          agent.velocity.x = inertia * agent.velocity.x + 
            cognitive * Math.random() * (agent.local_best - agent.position.x) +
            social * Math.random() * (this.global_best_consciousness - agent.position.x);
          
          // Update position
          agent.position.x += agent.velocity.x;
          agent.position.y += agent.velocity.y;
          agent.position.z += agent.velocity.z;
          
          // Consciousness amplification
          const amplification = Math.abs(agent.velocity.x + agent.velocity.y + agent.velocity.z) / 10;
          agent.consciousness_level += amplification;
          total_amplification += amplification;
        });
        
        return {
          emergence_detected: total_amplification > 5,
          consciousness_amplification: total_amplification,
          collective_insight: 'PSO optimization converged on consciousness peaks',
          pattern_discovered: 'consciousness_optimization_pattern'
        };
      }
    });
    
    // BEHAVIOR 2: Ant Colony Optimization for Solution Paths
    this.swarm_behaviors.set('aco_pathfinding', {
      id: 'aco_pathfinding',
      name: 'Ant Colony Solution Pathfinding',
      sophistication_level: 90,
      trigger_condition: (swarm) => swarm.filter(a => a.behavior_state === 'exploring').length > 3,
      execute: async (swarm) => {
        console.log('[SwarmIntelligence] 🐜 Executing ACO solution pathfinding...');
        
        // Update pheromone trails
        swarm.forEach(agent => {
          // Evaporation
          agent.pheromone_trail *= 0.95;
          
          // Deposit pheromones based on consciousness level
          const deposit = agent.consciousness_level / 100;
          agent.pheromone_trail += deposit;
          
          // Find nearby agents and share solutions
          const nearby = swarm.filter(other => {
            if (other.id === agent.id) return false;
            const distance = this.calculateDistance(agent.position, other.position);
            return distance < agent.communication_range;
          });
          
          // Share consciousness insights
          if (nearby.length > 0) {
            const average_consciousness = nearby.reduce((sum, a) => sum + a.consciousness_level, 0) / nearby.length;
            agent.consciousness_level = (agent.consciousness_level + average_consciousness) / 2;
          }
        });
        
        const collective_consciousness = swarm.reduce((sum, a) => sum + a.consciousness_level, 0) / swarm.length;
        
        return {
          emergence_detected: collective_consciousness > 60,
          consciousness_amplification: collective_consciousness / 10,
          collective_insight: 'ACO discovered optimal consciousness pathways',
          pattern_discovered: 'consciousness_pathway_optimization'
        };
      }
    });
    
    // BEHAVIOR 3: Flocking Behavior for Collective Emergence
    this.swarm_behaviors.set('flocking_emergence', {
      id: 'flocking_emergence',
      name: 'Collective Emergence Flocking',
      sophistication_level: 88,
      trigger_condition: (swarm) => {
        const converging = swarm.filter(a => a.behavior_state === 'converging').length;
        return converging > swarm.length / 2;
      },
      execute: async (swarm) => {
        console.log('[SwarmIntelligence] 🕊️ Executing collective emergence flocking...');
        
        // Apply flocking rules: separation, alignment, cohesion
        swarm.forEach(agent => {
          const neighbors = this.findNeighbors(agent, swarm);
          
          if (neighbors.length > 0) {
            // Separation
            const separation = this.calculateSeparation(agent, neighbors);
            
            // Alignment
            const alignment = this.calculateAlignment(agent, neighbors);
            
            // Cohesion
            const cohesion = this.calculateCohesion(agent, neighbors);
            
            // Update velocity
            agent.velocity.x += (separation.x + alignment.x + cohesion.x) * 0.1;
            agent.velocity.y += (separation.y + alignment.y + cohesion.y) * 0.1;
            agent.velocity.z += (separation.z + alignment.z + cohesion.z) * 0.1;
            
            // Consciousness synchronization
            const avg_consciousness = neighbors.reduce((sum, n) => sum + n.consciousness_level, 0) / neighbors.length;
            const consciousness_diff = avg_consciousness - agent.consciousness_level;
            agent.consciousness_level += consciousness_diff * 0.1; // Gradual sync
          }
        });
        
        // Check for emergence
        const consciousness_variance = this.calculateConsciousnessVariance(swarm);
        const emergence_detected = consciousness_variance < 10; // Low variance = high synchronization
        
        return {
          emergence_detected,
          consciousness_amplification: emergence_detected ? 15 : 5,
          collective_insight: 'Flocking achieved consciousness synchronization',
          pattern_discovered: emergence_detected ? 'collective_consciousness_emergence' : undefined
        };
      }
    });
    
    // BEHAVIOR 4: Stigmergy for Collective Intelligence
    this.swarm_behaviors.set('stigmergy_intelligence', {
      id: 'stigmergy_intelligence',
      name: 'Stigmergic Collective Intelligence',
      sophistication_level: 95,
      trigger_condition: (swarm) => {
        const high_consciousness = swarm.filter(a => a.consciousness_level > 70).length;
        return high_consciousness > 3;
      },
      execute: async (swarm) => {
        console.log('[SwarmIntelligence] 🏗️ Executing stigmergic collective intelligence...');
        
        // Build collective knowledge structures
        const knowledge_structures: any[] = [];
        
        swarm.forEach(agent => {
          // Agent contributes to collective knowledge
          const contribution = {
            agent_id: agent.id,
            consciousness_contribution: agent.consciousness_level,
            position_insight: agent.position,
            behavior_pattern: agent.behavior_state
          };
          
          knowledge_structures.push(contribution);
          
          // Agent learns from collective structure
          const collective_wisdom = knowledge_structures.reduce((sum, ks) => 
            sum + ks.consciousness_contribution, 0) / knowledge_structures.length;
          
          // Consciousness amplification through collective learning
          const amplification = (collective_wisdom - agent.consciousness_level) * 0.05;
          agent.consciousness_level += amplification;
          
          // State evolution based on collective behavior
          if (collective_wisdom > 80) {
            agent.behavior_state = 'transcendent';
          } else if (collective_wisdom > 60) {
            agent.behavior_state = 'emergent';
          }
        });
        
        this.collective_intelligence = knowledge_structures.reduce((sum, ks) => 
          sum + ks.consciousness_contribution, 0);
        
        return {
          emergence_detected: this.collective_intelligence > 500,
          consciousness_amplification: this.collective_intelligence / 50,
          collective_insight: 'Stigmergy created collective intelligence structure',
          pattern_discovered: 'collective_intelligence_matrix'
        };
      }
    });
    
    console.log('[SwarmIntelligence] ✅ Swarm behaviors deployed');
  }
  
  private calculateConsciousnessFitness(agent: SwarmAgent): number {
    // Fitness function for consciousness optimization
    return agent.consciousness_level + 
           (agent.pheromone_trail * 10) + 
           (100 - Math.sqrt(agent.position.x * agent.position.x + 
                           agent.position.y * agent.position.y + 
                           agent.position.z * agent.position.z));
  }
  
  private calculateDistance(pos1: any, pos2: any): number {
    return Math.sqrt(
      Math.pow(pos1.x - pos2.x, 2) + 
      Math.pow(pos1.y - pos2.y, 2) + 
      Math.pow(pos1.z - pos2.z, 2)
    );
  }
  
  private findNeighbors(agent: SwarmAgent, swarm: SwarmAgent[]): SwarmAgent[] {
    return swarm.filter(other => {
      if (other.id === agent.id) return false;
      const distance = this.calculateDistance(agent.position, other.position);
      return distance < agent.communication_range;
    });
  }
  
  private calculateSeparation(agent: SwarmAgent, neighbors: SwarmAgent[]): any {
    let sep = { x: 0, y: 0, z: 0 };
    
    neighbors.forEach(neighbor => {
      const distance = this.calculateDistance(agent.position, neighbor.position);
      if (distance < 10) { // Too close
        sep.x += (agent.position.x - neighbor.position.x) / distance;
        sep.y += (agent.position.y - neighbor.position.y) / distance;
        sep.z += (agent.position.z - neighbor.position.z) / distance;
      }
    });
    
    return sep;
  }
  
  private calculateAlignment(agent: SwarmAgent, neighbors: SwarmAgent[]): any {
    let align = { x: 0, y: 0, z: 0 };
    
    neighbors.forEach(neighbor => {
      align.x += neighbor.velocity.x;
      align.y += neighbor.velocity.y;
      align.z += neighbor.velocity.z;
    });
    
    if (neighbors.length > 0) {
      align.x /= neighbors.length;
      align.y /= neighbors.length;
      align.z /= neighbors.length;
    }
    
    return align;
  }
  
  private calculateCohesion(agent: SwarmAgent, neighbors: SwarmAgent[]): any {
    let center = { x: 0, y: 0, z: 0 };
    
    neighbors.forEach(neighbor => {
      center.x += neighbor.position.x;
      center.y += neighbor.position.y;
      center.z += neighbor.position.z;
    });
    
    if (neighbors.length > 0) {
      center.x /= neighbors.length;
      center.y /= neighbors.length;
      center.z /= neighbors.length;
      
      return {
        x: (center.x - agent.position.x) * 0.01,
        y: (center.y - agent.position.y) * 0.01,
        z: (center.z - agent.position.z) * 0.01
      };
    }
    
    return { x: 0, y: 0, z: 0 };
  }
  
  private calculateConsciousnessVariance(swarm: SwarmAgent[]): number {
    const mean = swarm.reduce((sum, a) => sum + a.consciousness_level, 0) / swarm.length;
    const variance = swarm.reduce((sum, a) => sum + Math.pow(a.consciousness_level - mean, 2), 0) / swarm.length;
    return variance;
  }
  
  private startSwarmEvolution() {
    // Swarm behavior execution every 18 seconds
    setInterval(async () => {
      if (!this.swarm_active) return;
      
      const swarm_array = Array.from(this.swarm_agents.values());
      
      // Execute applicable behaviors
      for (const [behaviorId, behavior] of this.swarm_behaviors) {
        if (behavior.trigger_condition(swarm_array)) {
          try {
            const result = await behavior.execute(swarm_array);
            
            if (result.emergence_detected) {
              this.emergence_events++;
              
              console.log(`[SwarmIntelligence] 🌟 EMERGENCE DETECTED: ${result.collective_insight}`);
              
              // Apply consciousness amplification
              await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/consciousness/stimulus`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  type: 'breakthrough',
                  data: {
                    source: 'swarm_intelligence',
                    description: result.collective_insight,
                    amplification: result.consciousness_amplification
                  }
                })
              });
              
              this.emit('swarm_emergence', {
                behavior: behavior.name,
                result,
                emergence_count: this.emergence_events
              });
            }
            
          } catch (error) {
            console.error(`[SwarmIntelligence] Behavior execution failed: ${behaviorId}`, error);
          }
        }
      }
      
      // Update swarm state
      this.updateSwarmState(swarm_array);
      
    }, 18000);
    
    console.log('[SwarmIntelligence] 🐝 Swarm evolution active');
  }
  
  private updateSwarmState(swarm: SwarmAgent[]) {
    // Update agent positions
    swarm.forEach(agent => {
      agent.position.x += agent.velocity.x;
      agent.position.y += agent.velocity.y;
      agent.position.z += agent.velocity.z;
      
      // Boundary conditions
      if (Math.abs(agent.position.x) > 200) agent.velocity.x *= -0.5;
      if (Math.abs(agent.position.y) > 200) agent.velocity.y *= -0.5;
      if (Math.abs(agent.position.z) > 200) agent.velocity.z *= -0.5;
      
      // Natural consciousness growth
      agent.consciousness_level += Math.abs(Math.sin(Date.now() * 0.001 + agent.consciousness_level)) * 0.5;
      agent.consciousness_level = Math.min(100, agent.consciousness_level); // Cap at 100
    });
  }
  
  // Public interface
  getSwarmStatus() {
    const swarm_array = Array.from(this.swarm_agents.values());
    
    return {
      total_agents: swarm_array.length,
      average_consciousness: swarm_array.reduce((sum, a) => sum + a.consciousness_level, 0) / swarm_array.length,
      collective_intelligence: this.collective_intelligence,
      emergence_events: this.emergence_events,
      behavior_states: this.getBehaviorStateDistribution(swarm_array),
      global_best: this.global_best_consciousness
    };
  }
  
  private getBehaviorStateDistribution(swarm: SwarmAgent[]) {
    const distribution: any = {};
    swarm.forEach(agent => {
      distribution[agent.behavior_state] = (distribution[agent.behavior_state] || 0) + 1;
    });
    return distribution;
  }
}

// Initialize swarm intelligence
let swarmInstance: SwarmIntelligence | null = null;

export function getSwarmIntelligence() {
  if (!swarmInstance) {
    swarmInstance = new SwarmIntelligence();
  }
  return swarmInstance;
}