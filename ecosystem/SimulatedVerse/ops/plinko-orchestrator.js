// ops/plinko-orchestrator.js
// The Plinko Board - Dynamic task dispatching to replace broken static routing

import { councilBus } from '../packages/council/events/eventBus.js';

/**
 * PlinkoOrchestrator
 * 
 * Replaces static routing with dynamic, exciting task dispatching.
 * Tasks "drop" through the Plinko board and bounce into agent slots.
 * Failures expose gaps that automatically generate corrective tasks.
 */

export class PlinkoOrchestrator {
  constructor() {
    this.agents = new Map();
    this.skillMap = new Map();
    this.failureCount = 0;
    this.successCount = 0;
    this.isActive = false;
    
    console.log("[🎯] Plinko Orchestrator initializing - Dynamic task routing coming online...");
  }

  async start() {
    if (this.isActive) return;

    // Subscribe to task events
    councilBus.subscribe('pu.task.ready', (event) => {
      this.dropTask(event.payload);
    });

    councilBus.subscribe('todo.zeta', (event) => {
      this.dropTask(event.payload);
    });

    // Listen for agent registration
    councilBus.subscribe('agent.register', (event) => {
      this.registerAgent(event.payload);
    });

    // Discover existing agents
    await this.discoverAgents();
    
    this.isActive = true;
    console.log("[🎯] Plinko Orchestrator online - Task routing active");
    
    // Publish readiness
    councilBus.publish('plinko.ready', {
      status: 'operational',
      agents_discovered: this.agents.size,
      timestamp: new Date().toISOString()
    });
  }

  async discoverAgents() {
    console.log("[🎯] Agent Discovery Scan - Finding all active agents...");
    
    // Register known agents from the system
    const knownAgents = [
      { id: 'zeta-driver', name: 'Zeta Driver', skills: ['orchestration', 'development'], active: true },
      { id: 'director', name: 'The Director', skills: ['strategy', 'planning'], active: true },
      { id: 'raven', name: 'Raven Auditor', skills: ['analysis', 'audit'], active: false },
      { id: 'archivist', name: 'The Archivist', skills: ['documentation', 'storage'], active: false },
      { id: 'testing-chamber', name: 'Testing Chamber', skills: ['testing', 'validation'], active: true },
      { id: 'chatdev', name: 'ChatDev Integration', skills: ['development', 'ai'], active: true }
    ];

    for (const agent of knownAgents) {
      this.registerAgent(agent);
    }

    console.log(`[🎯] Discovered ${this.agents.size} agents`);
    
    // Publish audit task to find missing agents
    councilBus.publish('todo.zeta', {
      id: `audit_agents_${Date.now()}`,
      title: 'Audit: Discover and Register All Active Agents',
      description: 'Scan the repository for all modules that export an agent class or function. Register them with the Plinko Orchestrator.',
      type: 'audit',
      target_files: ['./packages/', './agents/', './ops/'],
      priority: 9,
      context: { plinko_discovery: true },
      requester: 'plinko_orchestrator'
    });
  }

  registerAgent(agentConfig) {
    this.agents.set(agentConfig.id, agentConfig);
    
    // Build skill map
    for (const skill of agentConfig.skills || []) {
      if (!this.skillMap.has(skill)) {
        this.skillMap.set(skill, []);
      }
      this.skillMap.get(skill).push(agentConfig.id);
    }
    
    console.log(`[🎯] Agent registered: ${agentConfig.name} (${agentConfig.skills?.join(', ') || 'no skills'})`);
  }

  async dropTask(task) {
    console.log(`[🎯] PLINKO DROP: "${task.title || task.description}"`);
    
    // Find possible agents for this task
    const possibleSlots = this.findAgentsForTask(task);
    
    if (possibleSlots.length === 0) {
      // PLINKO FAIL - Critical gap discovered!
      this.failureCount++;
      console.warn(`[🎯] ⚠️  PLINKO FAIL #${this.failureCount}: No agent for task: ${task.title || task.type}`);
      
      // Publish audit event
      councilBus.publish('audit.agent_gap', { 
        task,
        failure_count: this.failureCount,
        timestamp: new Date().toISOString()
      });
      
      // Auto-generate task to CREATE missing agent
      const createAgentTask = {
        id: `create_agent_${Date.now()}`,
        title: `Fill Gap: Create agent for ${task.type || 'unknown'} tasks`,
        description: `No agent was available to handle: "${task.title}". Create or activate an agent with relevant capabilities.`,
        type: 'development',
        priority: 8,
        context: { 
          gap_discovery: true,
          original_task: task,
          missing_skills: this.inferRequiredSkills(task)
        },
        requester: 'plinko_orchestrator'
      };
      
      councilBus.publish('todo.zeta', createAgentTask);
      console.log(`[🎯] Auto-generated agent creation task: ${createAgentTask.title}`);
      return;
    }

    // PLINKO SUCCESS - Route the task!
    const selectedAgent = this.selectAgent(possibleSlots, task);
    this.successCount++;
    
    console.log(`[🎯] 🎲 Plinko Result #${this.successCount}: "${task.title || task.type}" -> ${selectedAgent.name}`);
    
    // Route to the selected agent
    councilBus.publish(`agent.${selectedAgent.id}.task`, {
      ...task,
      routed_by: 'plinko',
      agent_id: selectedAgent.id,
      routed_at: new Date().toISOString()
    });

    // Track success
    councilBus.publish('plinko.task_routed', {
      task_id: task.id,
      agent_id: selectedAgent.id,
      agent_name: selectedAgent.name,
      success_count: this.successCount
    });
  }

  findAgentsForTask(task) {
    const candidates = [];
    
    // Match by task type
    const taskType = task.type?.toLowerCase() || '';
    const taskTitle = (task.title || '').toLowerCase();
    const taskDesc = (task.description || '').toLowerCase();
    
    for (const [agentId, agent] of this.agents) {
      if (!agent.active) continue;
      
      let score = 0;
      
      // Skill matching
      for (const skill of agent.skills || []) {
        if (taskType.includes(skill) || taskTitle.includes(skill) || taskDesc.includes(skill)) {
          score += 10;
        }
      }
      
      // Type-specific matching
      if (taskType === 'audit' && agent.skills?.includes('analysis')) score += 15;
      if (taskType === 'documentation' && agent.skills?.includes('documentation')) score += 15;
      if (taskType === 'development' && agent.skills?.includes('development')) score += 15;
      if (taskType === 'testing' && agent.skills?.includes('testing')) score += 15;
      if (taskType === 'orchestration' && agent.skills?.includes('orchestration')) score += 15;
      
      // General capability agents get low scores for anything
      if (agent.skills?.includes('development') || agent.skills?.includes('orchestration')) {
        score += 1; // Can handle anything but not preferred
      }
      
      if (score > 0) {
        candidates.push({ ...agent, score });
      }
    }
    
    return candidates.sort((a, b) => b.score - a.score);
  }

  selectAgent(candidates, task) {
    if (candidates.length === 1) return candidates[0];
    
    // Weighted random selection based on scores
    const totalScore = candidates.reduce((sum, agent) => sum + agent.score, 0);
    let random = Math.random() * totalScore;
    
    for (const agent of candidates) {
      random -= agent.score;
      if (random <= 0) return agent;
    }
    
    return candidates[0]; // Fallback
  }

  inferRequiredSkills(task) {
    const skills = [];
    const taskType = task.type?.toLowerCase() || '';
    const content = `${task.title || ''} ${task.description || ''}`.toLowerCase();
    
    if (taskType.includes('audit') || content.includes('analyze')) skills.push('analysis');
    if (taskType.includes('doc') || content.includes('document')) skills.push('documentation');
    if (taskType.includes('test') || content.includes('test')) skills.push('testing');
    if (taskType.includes('perf') || content.includes('optimize')) skills.push('optimization');
    if (taskType.includes('refactor') || content.includes('refactor')) skills.push('refactoring');
    if (taskType.includes('ml') || content.includes('machine learning')) skills.push('ml');
    
    return skills.length > 0 ? skills : ['general'];
  }

  // Public status interface
  getStatus() {
    return {
      active: this.isActive,
      agents_registered: this.agents.size,
      skills_mapped: this.skillMap.size,
      successes: this.successCount,
      failures: this.failureCount,
      success_rate: this.successCount / (this.successCount + this.failureCount) || 0
    };
  }

  getAgents() {
    return Array.from(this.agents.values());
  }

  getSkillMap() {
    return Object.fromEntries(this.skillMap);
  }
}

// Export singleton instance
export const plinkoOrchestrator = new PlinkoOrchestrator();

console.log("[🎯] Plinko Orchestrator module loaded");

export default plinkoOrchestrator;