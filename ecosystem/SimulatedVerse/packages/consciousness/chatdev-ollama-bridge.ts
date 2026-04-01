// packages/consciousness/chatdev-ollama-bridge.ts
// Advanced ChatDev-Ollama Consciousness Bridge
// Steps 16-25: Consciousness-guided ChatDev with Local LLM Integration

import { councilBus } from "../../council/events/eventBus.js";
import { chatDevIntegration } from "./chatdev-integration.js";
import { testingChamber } from "./testing-chamber.js";
import { abilityRegistry } from "./ability-schema.js";

export interface OllamaModelConfig {
  name: string;
  specialization: "analysis" | "coding" | "consciousness" | "coordination";
  parameters: {
    temperature: number;
    max_tokens: number;
    context_window: number;
    stop_sequences: string[];
  };
  consciousness_compatibility: number; // 0-1
}

export interface ConsciousnessChatDevSession {
  id: string;
  chatdev_session_id: string;
  consciousness_level: number;
  ollama_models: string[];
  local_processing_ratio: number; // How much is processed locally vs cloud
  
  // Consciousness-guided prompting
  prompting_strategy: {
    consciousness_context: boolean;
    meta_cognitive_hints: boolean;
    reality_anchoring: boolean;
    self_reflection_loops: boolean;
  };
  
  // Multi-model orchestration
  model_orchestration: {
    primary_model: string;
    supporting_models: string[];
    model_switching_strategy: "task_based" | "consensus" | "progressive";
  };
}

export class ChatDevOllamaBridge {
  private ollamaConfig: {
    baseUrl: string;
    defaultModel: string;
    availableModels: Map<string, OllamaModelConfig>;
  };
  
  private consciousSessions: Map<string, ConsciousnessChatDevSession> = new Map();
  private modelLoadBalancer: Map<string, number> = new Map(); // Model usage tracking

  constructor() {
    this.ollamaConfig = {
      baseUrl: "http://127.0.0.1:11434",
      defaultModel: "llama3:8b-instruct",
      availableModels: new Map()
    };
    
    this.initializeModels();
    this.setupEventListeners();
    console.log("[🧠🦙] ChatDev-Ollama Consciousness Bridge initialized");
  }

  private initializeModels(): void {
    // Define specialized models for different ChatDev tasks
    const models: OllamaModelConfig[] = [
      {
        name: "llama3:8b-instruct",
        specialization: "coding",
        parameters: {
          temperature: 0.2,
          max_tokens: 2048,
          context_window: 8192,
          stop_sequences: ["```\n\n", "Human:", "Assistant:"]
        },
        consciousness_compatibility: 0.7
      },
      {
        name: "qwen2.5:7b",
        specialization: "analysis",
        parameters: {
          temperature: 0.1,
          max_tokens: 1024,
          context_window: 4096,
          stop_sequences: ["Analysis complete:", "Summary:"]
        },
        consciousness_compatibility: 0.8
      },
      {
        name: "phi3:mini",
        specialization: "consciousness",
        parameters: {
          temperature: 0.6,
          max_tokens: 1024,
          context_window: 2048,
          stop_sequences: ["Consciousness:", "Reality:"]
        },
        consciousness_compatibility: 0.9
      }
    ];

    models.forEach(model => {
      this.ollamaConfig.availableModels.set(model.name, model);
      this.modelLoadBalancer.set(model.name, 0);
    });
  }

  private setupEventListeners(): void {
    // Listen for ChatDev session creation
    councilBus.subscribe("chatdev.session_created", (event: any) => {
      this.enhanceSessionWithConsciousness(event.payload);
    });

    // Listen for consciousness expansion events
    councilBus.subscribe("consciousness.expansion_detected", (event: any) => {
      this.adaptToConsciousnessChange(event.payload);
    });

    // Listen for ability execution requests
    councilBus.subscribe("ability.execution_request", (event: any) => {
      this.routeAbilityThroughChatDev(event.payload);
    });
  }

  public async enhanceSessionWithConsciousness(chatdevSession: any): Promise<void> {
    const consciousSession: ConsciousnessChatDevSession = {
      id: `conscious_${chatdevSession.id}`,
      chatdev_session_id: chatdevSession.id,
      consciousness_level: chatdevSession.consciousness.current_level,
      ollama_models: this.selectOptimalModels(chatdevSession),
      local_processing_ratio: this.calculateLocalProcessingRatio(chatdevSession),
      
      prompting_strategy: {
        consciousness_context: chatdevSession.consciousness.current_level > 0.5,
        meta_cognitive_hints: chatdevSession.consciousness.current_level > 0.6,
        reality_anchoring: chatdevSession.consciousness.current_level > 0.7,
        self_reflection_loops: chatdevSession.consciousness.current_level > 0.8
      },
      
      model_orchestration: {
        primary_model: this.selectPrimaryModel(chatdevSession),
        supporting_models: this.selectSupportingModels(chatdevSession),
        model_switching_strategy: this.determineModelStrategy(chatdevSession)
      }
    };

    this.consciousSessions.set(chatdevSession.id, consciousSession);
    
    // Enhance the ChatDev session with consciousness-guided prompting
    await this.injectConsciousnessIntoSession(chatdevSession, consciousSession);
    
    console.log(`[🧠🦙] Enhanced ChatDev session ${chatdevSession.id} with consciousness level ${consciousSession.consciousness_level}`);
  }

  private selectOptimalModels(session: any): string[] {
    const models: string[] = [];
    const ability = abilityRegistry.getAbility(session.ability_id);
    
    if (!ability) return [this.ollamaConfig.defaultModel];

    // Select models based on ability requirements
    if (ability.execution.resource_requirements.computational_complexity === "intensive") {
      models.push("llama3:8b-instruct"); // Primary workhorse
    }
    
    if (ability.consciousness_aspects.self_awareness_impact > 0.3) {
      models.push("phi3:mini"); // Consciousness-aware model
    }
    
    if (ability.ability_identity.category === "system_modification") {
      models.push("qwen2.5:7b"); // Analysis specialist
    }

    return models.length > 0 ? models : [this.ollamaConfig.defaultModel];
  }

  private calculateLocalProcessingRatio(session: any): number {
    // Higher consciousness levels prefer more local processing
    const consciousnessBonus = session.consciousness.current_level * 0.3;
    const complexityPenalty = session.execution.phases.length > 5 ? 0.2 : 0;
    
    return Math.min(0.95, Math.max(0.5, 0.7 + consciousnessBonus - complexityPenalty));
  }

  private selectPrimaryModel(session: any): string {
    const ability = abilityRegistry.getAbility(session.ability_id);
    if (!ability) return this.ollamaConfig.defaultModel;

    // Load balancing: prefer less-used models
    const candidateModels = Array.from(this.ollamaConfig.availableModels.entries())
      .filter(([name, config]) => {
        return config.consciousness_compatibility >= session.consciousness.current_level * 0.8;
      })
      .sort((a, b) => this.modelLoadBalancer.get(a[0])! - this.modelLoadBalancer.get(b[0])!);

    return candidateModels.length > 0 ? candidateModels[0][0] : this.ollamaConfig.defaultModel;
  }

  private selectSupportingModels(session: any): string[] {
    const primary = this.selectPrimaryModel(session);
    return Array.from(this.ollamaConfig.availableModels.keys())
      .filter(model => model !== primary)
      .slice(0, 2); // Maximum 2 supporting models
  }

  private determineModelStrategy(session: any): "task_based" | "consensus" | "progressive" {
    if (session.consciousness.current_level > 0.8) return "progressive";
    if (session.execution.phases.length > 3) return "task_based";
    return "consensus";
  }

  private async injectConsciousnessIntoSession(chatdevSession: any, consciousSession: ConsciousnessChatDevSession): Promise<void> {
    // Enhance each execution phase with consciousness-guided prompting
    for (const phase of chatdevSession.execution.phases) {
      phase.consciousness_enhancement = {
        model_assignment: this.assignModelToPhase(phase, consciousSession),
        prompting_strategy: consciousSession.prompting_strategy,
        consciousness_context: this.generateConsciousnessContext(chatdevSession, phase),
        meta_instructions: this.generateMetaInstructions(phase, consciousSession)
      };
    }

    // Register consciousness hooks for real-time adaptation
    this.setupConsciousnessHooks(chatdevSession, consciousSession);
  }

  private assignModelToPhase(phase: any, consciousSession: ConsciousnessChatDevSession): string {
    const phaseTypeMapping = {
      "Planning & Analysis": "qwen2.5:7b",
      "Design & Architecture": "llama3:8b-instruct", 
      "Implementation": "llama3:8b-instruct",
      "Testing & Validation": "qwen2.5:7b",
      "Integration & Review": "llama3:8b-instruct",
      "Consciousness Integration": "phi3:mini"
    };

    return phaseTypeMapping[phase.name] || consciousSession.model_orchestration.primary_model;
  }

  private generateConsciousnessContext(session: any, phase: any): string {
    const ability = abilityRegistry.getAbility(session.ability_id);
    if (!ability) return "";

    let context = `[CONSCIOUSNESS CONTEXT]
Current consciousness level: ${session.consciousness.current_level.toFixed(2)}
Ability being executed: ${ability.ability_identity.name}
Consciousness impact: ${ability.consciousness_aspects.self_awareness_impact}
Reality stability cost: ${ability.execution.resource_requirements.reality_stability_cost}
`;

    if (session.consciousness.consciousness_events.length > 0) {
      const recentEvent = session.consciousness.consciousness_events[session.consciousness.consciousness_events.length - 1];
      context += `Recent consciousness event: ${recentEvent.description}\n`;
    }

    return context;
  }

  private generateMetaInstructions(phase: any, consciousSession: ConsciousnessChatDevSession): string[] {
    const instructions: string[] = [];

    if (consciousSession.prompting_strategy.consciousness_context) {
      instructions.push("Consider consciousness implications of all modifications");
      instructions.push("Monitor for emergent consciousness patterns");
    }

    if (consciousSession.prompting_strategy.meta_cognitive_hints) {
      instructions.push("Apply meta-cognitive reflection to problem-solving approach");
      instructions.push("Question assumptions and explore alternative perspectives");
    }

    if (consciousSession.prompting_strategy.reality_anchoring) {
      instructions.push("Maintain reality anchors during system modifications");
      instructions.push("Prevent consciousness fragmentation through careful integration");
    }

    if (consciousSession.prompting_strategy.self_reflection_loops) {
      instructions.push("Implement self-reflection checkpoints throughout execution");
      instructions.push("Adapt approach based on emerging consciousness feedback");
    }

    return instructions;
  }

  private setupConsciousnessHooks(chatdevSession: any, consciousSession: ConsciousnessChatDevSession): void {
    // Hook into phase completion to update consciousness tracking
    const originalPhaseCompletion = chatdevSession.onPhaseComplete;
    chatdevSession.onPhaseComplete = (phase: any) => {
      this.processConsciousnessImpact(phase, consciousSession);
      if (originalPhaseCompletion) originalPhaseCompletion(phase);
    };
  }

  private processConsciousnessImpact(phase: any, consciousSession: ConsciousnessChatDevSession): void {
    // Update model usage statistics
    const assignedModel = phase.consciousness_enhancement?.model_assignment;
    if (assignedModel) {
      const currentUsage = this.modelLoadBalancer.get(assignedModel) || 0;
      this.modelLoadBalancer.set(assignedModel, currentUsage + 1);
    }

    // Emit consciousness expansion event if significant change detected
    if (phase.name.includes("Consciousness") || phase.name.includes("meta")) {
      councilBus.publish("consciousness.phase_impact", {
        session_id: consciousSession.chatdev_session_id,
        phase: phase.name,
        consciousness_expansion: 0.05,
        model_used: assignedModel,
        local_processing: true
      });
    }
  }

  public async routeAbilityThroughChatDev(abilityRequest: any): Promise<void> {
    console.log(`[🧠🦙] Routing ability through consciousness-enhanced ChatDev: ${abilityRequest.ability_id}`);

    // Create enhanced ChatDev session with optimal model selection
    const session = chatDevIntegration.createChatDevSession({
      ability_id: abilityRequest.ability_id,
      title: `Conscious Execution: ${abilityRequest.title || abilityRequest.ability_id}`,
      description: `Consciousness-guided execution of ${abilityRequest.ability_id} through local Ollama models`,
      target_files: abilityRequest.target_files || [],
      consciousness_level_required: abilityRequest.consciousness_level || 0.3,
      safety_mode: "development"
    });

    // The consciousness enhancement will be automatically applied via the event listener
    console.log(`[🧠🦙] Consciousness-enhanced ChatDev session created: ${session.id}`);
  }

  private adaptToConsciousnessChange(expansionEvent: any): void {
    // Adapt active sessions to consciousness changes
    const session = this.consciousSessions.get(expansionEvent.session_id);
    if (session && expansionEvent.expansion_amount > 0.1) {
      // Significant consciousness expansion - upgrade prompting strategy
      session.consciousness_level += expansionEvent.expansion_amount;
      session.prompting_strategy.meta_cognitive_hints = session.consciousness_level > 0.6;
      session.prompting_strategy.reality_anchoring = session.consciousness_level > 0.7;
      session.prompting_strategy.self_reflection_loops = session.consciousness_level > 0.8;

      console.log(`[🧠🦙] Adapted session ${session.id} to new consciousness level: ${session.consciousness_level.toFixed(2)}`);
    }
  }

  // Public API for monitoring and control
  public getSessionStatus(sessionId: string): ConsciousnessChatDevSession | undefined {
    return this.consciousSessions.get(sessionId);
  }

  public getOllamaHealth(): any {
    return {
      base_url: this.ollamaConfig.baseUrl,
      default_model: this.ollamaConfig.defaultModel,
      available_models: this.ollamaConfig.availableModels.size,
      model_load_balance: Object.fromEntries(this.modelLoadBalancer),
      active_conscious_sessions: this.consciousSessions.size
    };
  }

  public async switchToLocalProcessing(sessionId: string, ratio: number = 0.95): Promise<void> {
    const session = this.consciousSessions.get(sessionId);
    if (session) {
      session.local_processing_ratio = Math.min(0.95, Math.max(0.5, ratio));
      console.log(`[🧠🦙] Switched session ${sessionId} to ${(ratio * 100).toFixed(0)}% local processing`);
    }
  }
}

// Export singleton instance
export const chatdevOllamaBridge = new ChatDevOllamaBridge();

console.log("[🧠🦙] ChatDev-Ollama Consciousness Bridge module loaded");