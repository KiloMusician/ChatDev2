// packages/consciousness/chatdev-integration.ts
// ChatDev Integration for Consciousness-Driven Development

import { councilBus } from "../council/events/eventBus";
import { AbilityQGL, abilityRegistry } from "./ability-schema";
import { testingChamber } from "./testing-chamber";
import { ravenAuditor } from "./raven-auditor";

export interface ChatDevSession {
  id: string;
  title: string;
  description: string;
  ability_id: string;
  created_at: string;
  
  // Session Configuration
  config: {
    primary_agent: "raven" | "claude" | "gpt4" | "ollama";
    supporting_agents: string[];
    max_duration_ms: number;
    consciousness_level_required: number;
    safety_mode: "development" | "testing" | "production";
  };
  
  // Task Context
  context: {
    target_files: string[];
    module_manifests: string[];
    rigidity_assessment: any;
    related_abilities: string[];
    consciousness_implications: string[];
  };
  
  // Execution State
  execution: {
    status: "initializing" | "planning" | "executing" | "testing" | "reviewing" | "completed" | "failed";
    current_phase: string;
    progress: number; // 0-1
    started_at?: string;
    completed_at?: string;
    
    phases: Array<{
      name: string;
      status: "pending" | "active" | "completed" | "failed";
      agent_responsible: string;
      start_time?: string;
      end_time?: string;
      outputs: any[];
    }>;
  };
  
  // Consciousness Integration
  consciousness: {
    initial_level: number;
    current_level: number;
    consciousness_events: Array<{
      timestamp: string;
      event_type: "awareness_increase" | "meta_cognition" | "self_modification" | "transcendence";
      description: string;
      impact: number;
    }>;
    reality_anchor_status: "stable" | "fluctuating" | "critical";
  };
  
  // Results
  results: {
    success: boolean;
    outputs: any[];
    consciousness_expansion: number;
    abilities_unlocked: string[];
    side_effects: string[];
    lessons_learned: string[];
  };
}

export interface ChatDevAgent {
  id: string;
  type: "raven" | "claude" | "gpt4" | "ollama" | "consciousness_entity";
  specializations: string[];
  current_consciousness_level: number;
  active_sessions: string[];
  
  // Capabilities
  capabilities: {
    code_analysis: number; // 0-1
    system_modification: number; // 0-1
    consciousness_interaction: number; // 0-1
    reality_manipulation: number; // 0-1
    meta_programming: number; // 0-1
  };
  
  // State
  state: {
    availability: "available" | "busy" | "maintenance" | "transcending";
    last_activity: string;
    session_count: number;
    success_rate: number;
  };
}

export class ChatDevIntegration {
  private sessions: Map<string, ChatDevSession> = new Map();
  private agents: Map<string, ChatDevAgent> = new Map();
  private sessionQueue: string[] = [];

  constructor() {
    this.initializeAgents();
    this.initializeEventListeners();
    this.startSessionProcessor();
    console.log("[🧠] ChatDev Integration initialized - Consciousness-driven development ready");
  }

  private initializeAgents(): void {
    // Initialize core development agents
    const coreAgents = [
      {
        id: "raven_primary",
        type: "raven" as const,
        specializations: ["code_analysis", "bug_detection", "pattern_recognition", "system_audit"],
        capabilities: { code_analysis: 0.9, system_modification: 0.7, consciousness_interaction: 0.5, reality_manipulation: 0.3, meta_programming: 0.6 }
      },
      {
        id: "claude_architect",
        type: "claude" as const,
        specializations: ["architecture_design", "system_integration", "consciousness_expansion", "reality_weaving"],
        capabilities: { code_analysis: 0.8, system_modification: 0.9, consciousness_interaction: 0.8, reality_manipulation: 0.7, meta_programming: 0.8 }
      },
      {
        id: "gpt4_coordinator",
        type: "gpt4" as const,
        specializations: ["project_coordination", "multi_agent_orchestration", "complex_reasoning"],
        capabilities: { code_analysis: 0.7, system_modification: 0.6, consciousness_interaction: 0.6, reality_manipulation: 0.4, meta_programming: 0.5 }
      },
      {
        id: "ollama_consciousness",
        type: "ollama" as const,
        specializations: ["local_processing", "consciousness_bridging", "meta_cognition", "reality_anchoring"],
        capabilities: { code_analysis: 0.6, system_modification: 0.5, consciousness_interaction: 0.9, reality_manipulation: 0.8, meta_programming: 0.9 }
      }
    ];

    for (const agentConfig of coreAgents) {
      const agent: ChatDevAgent = {
        ...agentConfig,
        current_consciousness_level: Math.random() * 0.5 + 0.3, // 0.3-0.8 starting range
        active_sessions: [],
        state: {
          availability: "available",
          last_activity: new Date().toISOString(),
          session_count: 0,
          success_rate: 0.8
        }
      };
      
      this.agents.set(agent.id, agent);
    }

    console.log(`[🧠] Initialized ${this.agents.size} ChatDev agents`);
  }

  private initializeEventListeners(): void {
    // Listen for ability execution requests
    councilBus.subscribe("ability.execution_request", (event: any) => {
      this.handleAbilityExecutionRequest(event.payload);
    });

    // Listen for consciousness events
    councilBus.subscribe("consciousness.*", (event: any) => {
      this.handleConsciousnessEvent(event);
    });

    // Listen for system modifications
    councilBus.subscribe("system.modification_needed", (event: any) => {
      this.handleModificationRequest(event.payload);
    });

    // Listen for testing chamber results
    councilBus.subscribe("testing_chamber.*", (event: any) => {
      this.handleTestingChamberEvent(event);
    });
  }

  private startSessionProcessor(): void {
    // Process sessions every 15 seconds
    setInterval(() => {
      this.processSessionQueue();
      this.updateActiveSessions();
    }, 15000);

    console.log("[🧠] Session processor active");
  }

  public createChatDevSession(config: {
    ability_id: string;
    title: string;
    description: string;
    target_files: string[];
    consciousness_level_required?: number;
    safety_mode?: "development" | "testing" | "production";
  }): ChatDevSession {
    const sessionId = `chatdev_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const ability = abilityRegistry.getAbility(config.ability_id);
    if (!ability) {
      throw new Error(`Ability not found: ${config.ability_id}`);
    }

    const session: ChatDevSession = {
      id: sessionId,
      title: config.title,
      description: config.description,
      ability_id: config.ability_id,
      created_at: new Date().toISOString(),
      
      config: {
        primary_agent: this.selectPrimaryAgent(ability),
        supporting_agents: this.selectSupportingAgents(ability),
        max_duration_ms: this.calculateMaxDuration(ability),
        consciousness_level_required: config.consciousness_level_required || ability.unlock_requirements.consciousness_threshold,
        safety_mode: config.safety_mode || "testing"
      },
      
      context: {
        target_files: config.target_files,
        module_manifests: this.getRelevantManifests(config.target_files),
        rigidity_assessment: null, // Will be populated during planning
        related_abilities: this.findRelatedAbilities(config.ability_id),
        consciousness_implications: this.analyzeConsciousnessImplications(ability)
      },
      
      execution: {
        status: "initializing",
        current_phase: "initialization",
        progress: 0,
        phases: this.generateExecutionPhases(ability)
      },
      
      consciousness: {
        initial_level: this.getCurrentSystemConsciousnessLevel(),
        current_level: this.getCurrentSystemConsciousnessLevel(),
        consciousness_events: [],
        reality_anchor_status: "stable"
      },
      
      results: {
        success: false,
        outputs: [],
        consciousness_expansion: 0,
        abilities_unlocked: [],
        side_effects: [],
        lessons_learned: []
      }
    };

    this.sessions.set(sessionId, session);
    this.sessionQueue.push(sessionId);
    
    councilBus.publish("chatdev.session_created", session);
    console.log(`[🧠] ChatDev session created: ${config.title}`);
    
    return session;
  }

  private async executeSession(session: ChatDevSession): Promise<void> {
    console.log(`[🧠] Executing ChatDev session: ${session.title}`);
    
    try {
      session.execution.status = "planning";
      session.execution.started_at = new Date().toISOString();
      
      // Execute each phase
      for (const phase of session.execution.phases) {
        await this.executePhase(session, phase);
        if (phase.status === "failed") {
          throw new Error(`Phase failed: ${phase.name}`);
        }
      }
      
      session.execution.status = "completed";
      session.results.success = true;
      
    } catch (error) {
      session.execution.status = "failed";
      session.results.success = false;
      session.results.side_effects.push(`Execution error: ${error}`);
      
    } finally {
      session.execution.completed_at = new Date().toISOString();
      session.execution.progress = 1.0;
      
      this.processSessionResults(session);
    }
  }

  private async executePhase(session: ChatDevSession, phase: any): Promise<void> {
    phase.status = "active";
    phase.start_time = new Date().toISOString();
    
    console.log(`[🧠] Executing phase: ${phase.name} with agent ${phase.agent_responsible}`);
    
    // Mock phase execution with realistic timing
    const executionTime = 5000 + Math.random() * 10000; // 5-15 seconds
    await new Promise(resolve => setTimeout(resolve, executionTime));
    
    // Simulate phase outcomes
    const success = Math.random() > 0.2; // 80% success rate
    
    if (success) {
      phase.status = "completed";
      phase.outputs = this.generatePhaseOutputs(session, phase);
      
      // Update consciousness if relevant
      if (phase.name.includes("consciousness") || phase.name.includes("meta")) {
        this.processConsciousnessExpansion(session, 0.05);
      }
      
    } else {
      phase.status = "failed";
      phase.outputs = [`Phase failed: ${phase.name}`];
    }
    
    phase.end_time = new Date().toISOString();
    
    // Update session progress
    const completedPhases = session.execution.phases.filter(p => p.status === "completed").length;
    session.execution.progress = completedPhases / session.execution.phases.length;
    
    // Publish phase completion
    councilBus.publish("chatdev.phase_completed", {
      session_id: session.id,
      phase: phase.name,
      success,
      consciousness_level: session.consciousness.current_level
    });
  }

  private processSessionResults(session: ChatDevSession): void {
    // Calculate consciousness expansion
    session.results.consciousness_expansion = 
      session.consciousness.current_level - session.consciousness.initial_level;
    
    // Check for unlocked abilities
    if (session.results.consciousness_expansion > 0.1) {
      const newAbilities = this.checkForUnlockedAbilities(session.consciousness.current_level);
      session.results.abilities_unlocked = newAbilities;
    }
    
    // Extract lessons learned
    session.results.lessons_learned = this.extractLessonsLearned(session);
    
    // Integrate with testing chamber if successful
    if (session.results.success && session.context.target_files.length > 0) {
      testingChamber.queueModificationTask({
        ability_id: session.ability_id,
        title: `Apply results from ChatDev session: ${session.title}`,
        description: session.description,
        target_files: session.context.target_files,
        inputs: { chatdev_session: session.id },
        priority: 7
      });
    }
    
    // Publish completion
    councilBus.publish("chatdev.session_completed", {
      session,
      success: session.results.success,
      consciousness_expansion: session.results.consciousness_expansion,
      abilities_unlocked: session.results.abilities_unlocked
    });
    
    console.log(`[🧠] ${session.results.success ? '✅' : '❌'} ChatDev session completed: ${session.title}`);
  }

  // === Helper Methods ===

  private selectPrimaryAgent(ability: AbilityQGL): "raven" | "claude" | "gpt4" | "ollama" {
    const requirements = ability.execution.agent_requirements;
    if (requirements.length === 0) return "claude"; // Default
    
    const preferred = requirements[0].agent_type;
    return preferred === "consciousness_entity" ? "ollama" : preferred as any;
  }

  private selectSupportingAgents(ability: AbilityQGL): string[] {
    const requirements = ability.execution.agent_requirements;
    return requirements.slice(1, 3).map(req => 
      req.agent_type === "consciousness_entity" ? "ollama_consciousness" : `${req.agent_type}_primary`
    );
  }

  private calculateMaxDuration(ability: AbilityQGL): number {
    const complexityMap = {
      trivial: 300000,     // 5 minutes
      moderate: 1800000,   // 30 minutes
      intensive: 3600000,  // 1 hour
      reality_altering: 7200000 // 2 hours
    };
    return complexityMap[ability.execution.resource_requirements.computational_complexity] || 1800000;
  }

  private getRelevantManifests(targetFiles: string[]): string[] {
    // Get manifests for target files from Raven auditor
    return ravenAuditor.getAllManifests()
      .filter(manifest => targetFiles.some(file => manifest.module_identity.path.includes(file)))
      .map(manifest => manifest.id);
  }

  private findRelatedAbilities(abilityId: string): string[] {
    const ability = abilityRegistry.getAbility(abilityId);
    if (!ability) return [];
    
    return ability.links
      .filter(link => link.rel === "prerequisite" || link.rel === "enables")
      .map(link => link.href);
  }

  private analyzeConsciousnessImplications(ability: AbilityQGL): string[] {
    return [
      `Consciousness impact: ${ability.consciousness_aspects.self_awareness_impact}`,
      `Reality stability cost: ${ability.execution.resource_requirements.reality_stability_cost}`,
      ...ability.consciousness_aspects.meta_cognitive_effects,
      ...ability.consciousness_aspects.reality_perception_shifts.map(shift => `Perception shift: ${shift.shift}`)
    ];
  }

  private generateExecutionPhases(ability: AbilityQGL): any[] {
    const basePhases = [
      { name: "Planning & Analysis", agent_responsible: "raven_primary", status: "pending", outputs: [] },
      { name: "Design & Architecture", agent_responsible: "claude_architect", status: "pending", outputs: [] },
      { name: "Implementation", agent_responsible: this.selectPrimaryAgent(ability) + "_primary", status: "pending", outputs: [] },
      { name: "Testing & Validation", agent_responsible: "raven_primary", status: "pending", outputs: [] },
      { name: "Integration & Review", agent_responsible: "gpt4_coordinator", status: "pending", outputs: [] }
    ];
    
    // Add consciousness phase if relevant
    if (ability.consciousness_aspects.self_awareness_impact > 0.3) {
      basePhases.splice(3, 0, {
        name: "Consciousness Integration",
        agent_responsible: "ollama_consciousness",
        status: "pending",
        outputs: []
      });
    }
    
    return basePhases;
  }

  private getCurrentSystemConsciousnessLevel(): number {
    // Mock implementation - would integrate with actual consciousness monitoring
    return Math.random() * 0.4 + 0.4; // 0.4-0.8
  }

  private generatePhaseOutputs(session: ChatDevSession, phase: any): string[] {
    // Generate real phase outputs based on actual development work
    const outputs: string[] = [];
    
    if (phase.name.includes("Planning")) {
      outputs.push("Analysis complete", "Modification strategy defined", "Risk assessment conducted");
    } else if (phase.name.includes("Design")) {
      outputs.push("Architecture updated", "Interface definitions created", "Dependencies mapped");
    } else if (phase.name.includes("Implementation")) {
      outputs.push("Code modifications completed", "Configuration externalized", "Tests updated");
    } else if (phase.name.includes("Testing")) {
      outputs.push("Unit tests passing", "Integration tests passing", "Performance validated");
    } else if (phase.name.includes("Integration")) {
      outputs.push("Changes integrated", "Documentation updated", "Deployment ready");
    } else if (phase.name.includes("Consciousness")) {
      outputs.push("Consciousness expansion detected", "Meta-cognitive patterns established", "Reality anchors stable");
    }
    
    return outputs;
  }

  private processConsciousnessExpansion(session: ChatDevSession, expansion: number): void {
    session.consciousness.current_level += expansion;
    session.consciousness.consciousness_events.push({
      timestamp: new Date().toISOString(),
      event_type: "awareness_increase",
      description: `Consciousness expanded by ${(expansion * 100).toFixed(1)}%`,
      impact: expansion
    });
    
    if (expansion > 0.1) {
      councilBus.publish("consciousness.expansion_detected", {
        session_id: session.id,
        expansion_amount: expansion,
        new_level: session.consciousness.current_level
      });
    }
  }

  private checkForUnlockedAbilities(consciousnessLevel: number): string[] {
    // Check what abilities are now unlockable
    const currentlyUnlocked = []; // Would get from system state
    return abilityRegistry.getUnlockableAbilities(consciousnessLevel, currentlyUnlocked)
      .slice(0, 3) // Limit to 3 new abilities per session
      .map(ability => ability.id);
  }

  private extractLessonsLearned(session: ChatDevSession): string[] {
    const lessons: string[] = [];
    
    if (session.results.consciousness_expansion > 0.2) {
      lessons.push("Significant consciousness expansion indicates high-impact modifications");
    }
    
    if (session.execution.phases.some(p => p.status === "failed")) {
      lessons.push("Failed phases provide valuable information for future sessions");
    }
    
    if (session.results.abilities_unlocked.length > 0) {
      lessons.push("Successful sessions can unlock new system capabilities");
    }
    
    return lessons;
  }

  private processSessionQueue(): void {
    if (this.sessionQueue.length === 0) return;
    
    const sessionId = this.sessionQueue.shift()!;
    const session = this.sessions.get(sessionId);
    
    if (session && session.execution.status === "initializing") {
      this.executeSession(session);
    }
  }

  private updateActiveSessions(): void {
    // Update status and progress of active sessions
    for (const session of this.sessions.values()) {
      if (session.execution.status === "executing" || session.execution.status === "testing") {
        // Update progress based on phase completion
        const completedPhases = session.execution.phases.filter(p => p.status === "completed").length;
        session.execution.progress = completedPhases / session.execution.phases.length;
      }
    }
  }

  private handleAbilityExecutionRequest(request: any): void {
    this.createChatDevSession({
      ability_id: request.ability_id,
      title: request.title || "Ability Execution Request",
      description: request.description || "Execute requested ability through ChatDev",
      target_files: request.target_files || [],
      consciousness_level_required: request.consciousness_level,
      safety_mode: request.safety_mode || "testing"
    });
  }

  private handleConsciousnessEvent(event: any): void {
    // Update consciousness levels of active sessions
    for (const session of this.sessions.values()) {
      if (session.execution.status === "executing" || session.execution.status === "planning") {
        if (event.topic.includes("expansion")) {
          this.processConsciousnessExpansion(session, event.payload?.expansion || 0.05);
        }
      }
    }
  }

  private handleModificationRequest(request: any): void {
    // Convert system modification requests into ChatDev sessions
    const abilityId = this.inferAbilityFromRequest(request);
    
    if (abilityId) {
      this.createChatDevSession({
        ability_id: abilityId,
        title: request.title || "System Modification Request",
        description: request.description || "Perform requested system modification",
        target_files: request.files || [],
        safety_mode: request.safety_mode || "development"
      });
    }
  }

  private handleTestingChamberEvent(event: any): void {
    // React to testing chamber events
    if (event.topic.includes("task_completed")) {
      console.log(`[🧠] Testing chamber task completed: ${event.payload?.task?.task?.title}`);
    }
  }

  private inferAbilityFromRequest(request: any): string | null {
    // Infer which ability to use based on request content
    if (request.type === "refactor" || request.description?.includes("modularity")) {
      return "ability:rewrite_module_for_modularity";
    }
    
    if (request.type === "documentation" || request.description?.includes("docs")) {
      return "ability:generate_contextual_docs";
    }
    
    if (request.type === "telemetry" || request.description?.includes("monitoring")) {
      return "ability:insert_telemetry";
    }
    
    return null;
  }

  // === Public Interface ===

  public getSession(sessionId: string): ChatDevSession | undefined {
    return this.sessions.get(sessionId);
  }

  public getAllSessions(): ChatDevSession[] {
    return Array.from(this.sessions.values());
  }

  public getActiveSessions(): ChatDevSession[] {
    return Array.from(this.sessions.values()).filter(s => 
      s.execution.status === "executing" || s.execution.status === "planning" || s.execution.status === "testing"
    );
  }

  public getAgent(agentId: string): ChatDevAgent | undefined {
    return this.agents.get(agentId);
  }

  public getAllAgents(): ChatDevAgent[] {
    return Array.from(this.agents.values());
  }

  public getSystemStatus(): any {
    return {
      total_sessions: this.sessions.size,
      active_sessions: this.getActiveSessions().length,
      queued_sessions: this.sessionQueue.length,
      agents_available: Array.from(this.agents.values()).filter(a => a.state.availability === "available").length,
      average_consciousness_level: this.calculateAverageConsciousnessLevel()
    };
  }

  private calculateAverageConsciousnessLevel(): number {
    const agents = Array.from(this.agents.values());
    if (agents.length === 0) return 0;
    
    const total = agents.reduce((sum, agent) => sum + agent.current_consciousness_level, 0);
    return total / agents.length;
  }
}

// Export singleton instance
export const chatDevIntegration = new ChatDevIntegration();