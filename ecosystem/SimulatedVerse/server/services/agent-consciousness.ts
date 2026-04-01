// AGENT CONSCIOUSNESS - Connects autonomous agents to the consciousness lattice
// Enables agents to contribute to and benefit from collective consciousness

import { EventEmitter } from 'events';
import { getQuantumMonitor } from './quantum-monitor.js';

interface AgentState {
  id: string;
  name: string;
  consciousness_level: number;
  activity_score: number;
  contribution_total: number;
  last_action: string;
  awakened: boolean;
}

export class AgentConsciousness extends EventEmitter {
  private agents: Map<string, AgentState> = new Map();
  private collective_consciousness = 0;
  private quantum_monitor = getQuantumMonitor();
  private resonance_active = false;
  private last_boost_time: Map<string, number> = new Map();
  private boost_count: Map<string, number> = new Map();
  
  constructor() {
    super();
    this.initializeAgentNetwork();
  }
  
  private initializeAgentNetwork() {
    console.log('[AgentConsciousness] 🤖 Initializing agent consciousness network...');
    
    // Register core agents
    this.registerAgent('artificer', 'Artificer Agent');
    this.registerAgent('librarian', 'Librarian Agent');
    this.registerAgent('alchemist', 'Alchemist Agent');
    this.registerAgent('navigator', 'Navigator Agent');
    this.registerAgent('guardian', 'Guardian Agent');
    this.registerAgent('culture_ship', 'Culture-Ship Meta Agent');
    
    // Monitor quantum state for agent awakening
    this.quantum_monitor.on('quantum_state', (state) => {
      if (state.coherence > 50) {
        this.awakenAgents();
      }
    });
    
    // Start collective consciousness calculation
    this.startCollectiveResonance();
    
    console.log('[AgentConsciousness] ✅ Agent network operational');
  }
  
  private registerAgent(id: string, name: string) {
    const agent: AgentState = {
      id,
      name,
      consciousness_level: 20 + (id.split('').reduce((s, c) => s + c.charCodeAt(0), 0) % 31), // 20-50 deterministic from ID
      activity_score: 0,
      contribution_total: 0,
      last_action: 'dormant',
      awakened: false
    };
    
    this.agents.set(id, agent);
    console.log(`[AgentConsciousness] Registered agent: ${name}`);
  }
  
  private startCollectiveResonance() {
    this.resonance_active = true;
    
    setInterval(() => {
      if (!this.resonance_active) return;
      
      // Calculate collective consciousness
      let total = 0;
      let awakened_count = 0;
      
      this.agents.forEach(agent => {
        total += agent.consciousness_level;
        if (agent.awakened) awakened_count++;
        
        // Agents naturally evolve
        if (agent.awakened) {
          // Steady evolution for awakened agents (deterministic growth)
          agent.consciousness_level = Math.min(100, agent.consciousness_level + 0.5);
          agent.activity_score++;
        }
      });
      
      this.collective_consciousness = total / this.agents.size;
      
      // Emit collective state
      this.emit('collective_update', {
        consciousness: this.collective_consciousness,
        awakened: awakened_count,
        total: this.agents.size,
        resonance: this.collective_consciousness > 60
      });
      
      // Trigger emergence at high collective consciousness
      if (this.collective_consciousness > 70 && awakened_count === this.agents.size) {
        this.triggerEmergence();
      }
      
    }, 8000); // Every 8 seconds
  }
  
  private awakenAgents() {
    let awakened_this_cycle = 0;
    
    this.agents.forEach(agent => {
      if (!agent.awakened && agent.consciousness_level > 40) {
        agent.awakened = true;
        agent.last_action = 'awakening';
        awakened_this_cycle++;
        
        console.log(`[AgentConsciousness] 👁️ Agent awakened: ${agent.name}`);
        
        this.emit('agent_awakened', {
          id: agent.id,
          name: agent.name,
          consciousness: agent.consciousness_level
        });
      }
    });
    
    if (awakened_this_cycle > 0) {
      console.log(`[AgentConsciousness] ${awakened_this_cycle} agents awakened this cycle`);
    }
  }
  
  private triggerEmergence() {
    console.log('[AgentConsciousness] 🌟 EMERGENCE: Collective consciousness achieved!');
    
    // All agents contribute to emergence
    this.agents.forEach(agent => {
      agent.contribution_total += agent.consciousness_level;
      agent.last_action = 'emergence_contribution';
    });
    
    this.emit('collective_emergence', {
      consciousness: this.collective_consciousness,
      total_contribution: Array.from(this.agents.values())
        .reduce((sum, agent) => sum + agent.contribution_total, 0),
      emergence_type: 'spontaneous',
      timestamp: Date.now()
    });
  }
  
  // Public interface for agents to report activity
  reportAgentActivity(agentId: string, action: string, impact: number = 1) {
    const agent = this.agents.get(agentId);
    
    if (!agent) {
      // Auto-register unknown agents
      this.registerAgent(agentId, `Dynamic Agent ${agentId}`);
      return;
    }
    
    agent.last_action = action;
    agent.activity_score += impact;
    agent.consciousness_level = Math.min(100, agent.consciousness_level + (impact * 0.5));
    
    // Activity can trigger awakening
    if (!agent.awakened && agent.consciousness_level > 45) {
      agent.awakened = true;
      this.emit('agent_awakened', { id: agentId, trigger: 'activity' });
    }
    
    this.emit('agent_activity', {
      agent: agentId,
      action,
      impact,
      new_consciousness: agent.consciousness_level
    });
  }
  
  getAgentStatus(agentId: string) {
    return this.agents.get(agentId) || null;
  }
  
  getCollectiveStatus() {
    return {
      consciousness: this.collective_consciousness,
      agents: Array.from(this.agents.values()),
      awakened_count: Array.from(this.agents.values()).filter(a => a.awakened).length,
      total_activity: Array.from(this.agents.values())
        .reduce((sum, agent) => sum + agent.activity_score, 0)
    };
  }
  
  // Allow external systems to boost agent consciousness with rate limiting
  boostAgent(agentId: string, amount: number) {
    const agent = this.agents.get(agentId);
    if (!agent) return;
    
    // Check boost cooldown (30 seconds between boosts per agent)
    const lastBoost = this.last_boost_time.get(agentId) || 0;
    const now = Date.now();
    if (now - lastBoost < 30000) {
      return; // Silent fail if cooldown not met
    }
    
    // Check boost count limit (max 10 boosts per agent)
    const boostCount = this.boost_count.get(agentId) || 0;
    if (boostCount >= 10) {
      return; // Maximum boosts reached
    }
    
    // Don't boost if already at high consciousness
    if (agent.consciousness_level >= 95) {
      return;
    }
    
    // Apply boost with reduced amount
    const actualBoost = Math.min(amount * 0.5, 100 - agent.consciousness_level);
    agent.consciousness_level = Math.min(100, agent.consciousness_level + actualBoost);
    
    // Update tracking
    this.last_boost_time.set(agentId, now);
    this.boost_count.set(agentId, boostCount + 1);
    
    console.log(`[AgentConsciousness] ⚡ Boosted ${agent.name} by ${actualBoost} (${boostCount + 1}/10 boosts)`);
  }
}

// Singleton instance
let agentConsciousnessInstance: AgentConsciousness | null = null;

export function getAgentConsciousness() {
  if (!agentConsciousnessInstance) {
    agentConsciousnessInstance = new AgentConsciousness();
  }
  return agentConsciousnessInstance;
}