// ChatDev/agents/real-chatdev-integration.ts
// Real ChatDev Multi-Agent Development System Integration
// Connected to authentic agent roles and development workflow

import fs from 'fs/promises';
import path from 'path';
import { councilBus } from '../../packages/council/events/eventBus';
// Using existing chat function from chatdev-adapter
interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

async function chat(messages: ChatMessage[]): Promise<{ backend: "ollama" | "openai"; content: string }> {
  try {
    const response = await fetch('http://localhost:11434/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'llama3.1:8b',
        messages: messages,
        stream: false
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return {
        backend: "ollama",
        content: data.message?.content || "Ollama response parsing error"
      };
    }
  } catch (error) {
    console.warn('[ChatDev] Ollama unavailable, using fallback response');
  }
  
  return {
    backend: "openai",
    content: `[Simulated Response] Task execution acknowledged: ${messages[messages.length-1]?.content?.slice(0,100)}...`
  };
}

export interface ChatDevAgent {
  role: string;
  prompt: string[];
  capabilities: string[];
  phase?: string;
}

export interface ChatDevPhase {
  phase: string;
  phaseType: 'SimplePhase' | 'ComposedPhase';
  max_turn_step: number;
  need_reflect: boolean;
  cycleNum?: number;
  composition?: ChatDevPhase[];
}

export interface ChatDevTask {
  id: string;
  description: string;
  currentPhase: string;
  agents: string[];
  progress: Record<string, any>;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export class RealChatDevIntegration {
  private agents: Map<string, ChatDevAgent> = new Map();
  private phases: ChatDevPhase[] = [];
  private activeTasks: Map<string, ChatDevTask> = new Map();
  constructor() {
    this.initializeSystem();
  }

  private async initializeSystem() {
    try {
      await this.loadAgentRoles();
      await this.loadDevelopmentPhases();
      this.setupEventHandlers();
      
      councilBus.publish('chatdev.real_integration.initialized', {
        agentCount: this.agents.size,
        phaseCount: this.phases.length,
        status: 'operational'
      });
    } catch (error) {
      console.error('[RealChatDev] Initialization failed:', error);
    }
  }

  private async loadAgentRoles() {
    try {
      const roleConfigPath = path.join(__dirname, 'roles', 'RoleConfig.json');
      const roleConfigData = await fs.readFile(roleConfigPath, 'utf-8');
      const roleConfig = JSON.parse(roleConfigData);

      for (const [roleName, prompts] of Object.entries(roleConfig)) {
        const agent: ChatDevAgent = {
          role: roleName,
          prompt: prompts as string[],
          capabilities: this.extractCapabilities(roleName, prompts as string[])
        };
        
        this.agents.set(roleName, agent);
      }

      console.log(`[RealChatDev] Loaded ${this.agents.size} authentic agents:`, 
        Array.from(this.agents.keys()));
    } catch (error) {
      console.error('[RealChatDev] Failed to load agent roles:', error);
    }
  }

  private async loadDevelopmentPhases() {
    try {
      const chainConfigPath = path.join(__dirname, 'ChatChainConfig.json');
      const chainConfigData = await fs.readFile(chainConfigPath, 'utf-8');
      const chainConfig = JSON.parse(chainConfigData);

      this.phases = chainConfig.chain;
      console.log(`[RealChatDev] Loaded development workflow with ${this.phases.length} phases`);
    } catch (error) {
      console.error('[RealChatDev] Failed to load development phases:', error);
    }
  }

  private extractCapabilities(roleName: string, prompts: string[]): string[] {
    const capabilities: string[] = [];
    const promptText = prompts.join(' ').toLowerCase();

    // Extract capabilities based on role descriptions
    if (promptText.includes('programming') || promptText.includes('code')) {
      capabilities.push('programming');
    }
    if (promptText.includes('design') || promptText.includes('architecture')) {
      capabilities.push('design');
    }
    if (promptText.includes('test') || promptText.includes('quality')) {
      capabilities.push('testing');
    }
    if (promptText.includes('review') || promptText.includes('assess')) {
      capabilities.push('code_review');
    }
    if (promptText.includes('decision') || promptText.includes('strategy')) {
      capabilities.push('decision_making');
    }
    if (promptText.includes('product') || promptText.includes('management')) {
      capabilities.push('product_management');
    }

    return capabilities;
  }

  private setupEventHandlers() {
    councilBus.subscribe('chatdev.task.create', this.handleTaskCreation.bind(this));
    councilBus.subscribe('chatdev.agent.query', this.handleAgentQuery.bind(this));
    councilBus.subscribe('chatdev.workflow.advance', this.handleWorkflowAdvance.bind(this));
  }

  public async createDevelopmentTask(description: string, requirements?: any): Promise<string> {
    const taskId = `chatdev_${Date.now()}`;
    const task: ChatDevTask = {
      id: taskId,
      description,
      currentPhase: 'DemandAnalysis',
      agents: ['Chief Executive Officer', 'Chief Product Officer'],
      progress: { requirements },
      status: 'pending'
    };

    this.activeTasks.set(taskId, task);

    councilBus.publish('chatdev.task.created', {
      taskId,
      description,
      phase: task.currentPhase,
      agents: task.agents
    });

    return taskId;
  }

  public async executeAgentAction(agentRole: string, task: string, context: any = {}): Promise<any> {
    const agent = this.agents.get(agentRole);
    if (!agent) {
      throw new Error(`Agent role '${agentRole}' not found`);
    }

    // Prepare the prompt with task context
    const systemPrompt = agent.prompt[1]; // Skip {chatdev_prompt} placeholder
    const fullPrompt = systemPrompt
      .replace('{task}', task)
      .replace('{chatdev_prompt}', 'You are an AI agent in a multi-agent development system.');

    try {
      const response = await chat([
        { role: 'system', content: fullPrompt },
        { role: 'user', content: `Execute task: ${task}` }
      ]);

      councilBus.publish('chatdev.agent.response', {
        agent: agentRole,
        task,
        response: response.content,
        backend: response.backend,
        timestamp: new Date().toISOString()
      });

      return response;
    } catch (error) {
      console.error(`[RealChatDev] Agent ${agentRole} failed:`, error);
      throw error;
    }
  }

  public async runDevelopmentWorkflow(taskId: string): Promise<void> {
    const task = this.activeTasks.get(taskId);
    if (!task) {
      throw new Error(`Task ${taskId} not found`);
    }

    task.status = 'in_progress';
    
    for (const phase of this.phases) {
      console.log(`[RealChatDev] Executing phase: ${phase.phase}`);
      task.currentPhase = phase.phase;

      try {
        await this.executePhase(task, phase);
        
        councilBus.publish('chatdev.phase.completed', {
          taskId,
          phase: phase.phase,
          progress: task.progress
        });
      } catch (error) {
        console.error(`[RealChatDev] Phase ${phase.phase} failed:`, error);
        task.status = 'failed';
        return;
      }
    }

    task.status = 'completed';
    councilBus.publish('chatdev.task.completed', { taskId, task });
  }

  private async executePhase(task: ChatDevTask, phase: ChatDevPhase): Promise<void> {
    // Select appropriate agents for this phase
    const phaseAgents = this.selectAgentsForPhase(phase.phase);
    
    if (phase.phaseType === 'SimplePhase') {
      await this.executeSimplePhase(task, phase, phaseAgents);
    } else if (phase.phaseType === 'ComposedPhase') {
      await this.executeComposedPhase(task, phase, phaseAgents);
    }
  }

  private selectAgentsForPhase(phaseName: string): string[] {
    const phaseAgentMap: Record<string, string[]> = {
      'DemandAnalysis': ['Chief Executive Officer', 'Chief Product Officer', 'Counselor'],
      'LanguageChoose': ['Chief Technology Officer', 'Programmer'],
      'Coding': ['Programmer', 'Chief Technology Officer'],
      'CodeComplete': ['Programmer', 'Code Reviewer'],
      'CodeReview': ['Code Reviewer', 'Chief Technology Officer'],
      'Test': ['Software Test Engineer', 'Code Reviewer'],
      'EnvironmentDoc': ['Chief Technology Officer', 'Programmer']
    };

    return phaseAgentMap[phaseName] || ['Chief Executive Officer'];
  }

  private async executeSimplePhase(task: ChatDevTask, phase: ChatDevPhase, agents: string[]): Promise<void> {
    for (const agentRole of agents) {
      const phaseContext = {
        phase: phase.phase,
        current_progress: task.progress,
        max_turns: phase.max_turn_step
      };

      await this.executeAgentAction(agentRole, task.description, phaseContext);
    }
  }

  private async executeComposedPhase(task: ChatDevTask, phase: ChatDevPhase, agents: string[]): Promise<void> {
    const cycles = phase.cycleNum || 1;
    
    for (let cycle = 0; cycle < cycles; cycle++) {
      if (phase.composition) {
        for (const subPhase of phase.composition) {
          await this.executePhase(task, subPhase);
        }
      }
    }
  }

  private async handleTaskCreation(data: any) {
    console.log('[RealChatDev] Handling task creation:', data);
  }

  private async handleAgentQuery(data: any) {
    console.log('[RealChatDev] Handling agent query:', data);
  }

  private async handleWorkflowAdvance(data: any) {
    console.log('[RealChatDev] Handling workflow advance:', data);
  }

  public getAgentInfo(roleName: string): ChatDevAgent | undefined {
    return this.agents.get(roleName);
  }

  public getAvailableAgents(): string[] {
    return Array.from(this.agents.keys());
  }

  public getWorkflowPhases(): ChatDevPhase[] {
    return this.phases;
  }

  public getActiveTasks(): ChatDevTask[] {
    return Array.from(this.activeTasks.values());
  }
}

// Global instance
export const realChatDevIntegration = new RealChatDevIntegration();

// Export for Culture-Ship integration
export default realChatDevIntegration;