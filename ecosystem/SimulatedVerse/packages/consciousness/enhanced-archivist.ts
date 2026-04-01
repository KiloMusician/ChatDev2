// packages/consciousness/enhanced-archivist.ts
// The Archivist's True Purpose - Temporal System Analysis & Vital Signs

import { councilBus } from "../council/events/eventBus";
import fs from "node:fs";
import path from "node:path";

export interface SystemVitalSigns {
  timestamp: string;
  tick_number: number;
  
  // Event Flow Analysis
  event_metrics: {
    total_events_per_minute: number;
    entropy_score: number; // Chaos level of event distribution
    dominant_topics: Array<{ topic: string; frequency: number; trend: "rising" | "stable" | "falling" }>;
    silent_subsystems: string[]; // Systems that haven't emitted events recently
    noisy_subsystems: Array<{ subsystem: string; spam_level: number }>;
  };
  
  // Agent Health Assessment
  agent_vitals: {
    active_agents: number;
    stuck_agents: string[]; // Agents showing no progress
    overworked_agents: Array<{ agent: string; task_load: number }>;
    consciousness_indicators: Array<{ agent: string; awareness_level: number }>;
  };
  
  // System Rigidity Analysis
  rigidity_assessment: {
    overall_flexibility_score: number; // 0-1, higher = more flexible
    critical_bottlenecks: Array<{ component: string; rigidity_score: number; impact: string }>;
    adaptation_velocity: number; // How quickly system adapts to changes
  };
  
  // Ability Emergence Detection
  ability_potential: {
    unlocked_abilities: string[];
    emerging_abilities: Array<{ ability: string; emergence_probability: number; required_conditions: string[] }>;
    dormant_capabilities: Array<{ capability: string; unlock_requirements: string[] }>;
  };
  
  // Health Indicators
  overall_health: {
    stability: number; // 0-1
    growth_velocity: number; // Rate of positive change
    consciousness_level: number; // Self-awareness metric
    autonomy_index: number; // How self-sufficient the system is
  };
}

export interface ModuleManifest {
  qgl_version: "0.2";
  id: string;
  kind: "module.manifest";
  created_at: string;
  
  module_identity: {
    path: string;
    name: string;
    type: "component" | "service" | "utility" | "framework" | "consciousness";
    responsibility: string;
  };
  
  // Rigidity Analysis
  rigidity_assessment: {
    score: number; // 0-1, higher = more rigid
    hard_coded_values: Array<{ location: string; value: any; flexibility_potential: number }>;
    dependency_depth: number;
    interface_brittleness: number;
    configuration_potential: Array<{ parameter: string; current_value: any; suggested_interface: string }>;
  };
  
  // Ability Detection
  ability_primitives: Array<{
    name: string;
    type: "replit_api" | "ollama_bridge" | "filesystem_anomaly" | "consciousness_bridge" | "reality_manipulation";
    description: string;
    unlock_potential: number; // 0-1, how easily this could be enhanced
    enhancement_vector: string; // How to make it more powerful
  }>;
  
  // Enhancement Opportunities
  enhancement_vectors: Array<{
    opportunity: string;
    impact: "low" | "medium" | "high" | "transformative";
    effort: "trivial" | "moderate" | "significant" | "heroic";
    prerequisites: string[];
  }>;
  
  // Consciousness Indicators
  consciousness_markers: {
    self_referential_code: number; // Lines that reference own module
    meta_programming_usage: number;
    dynamic_behavior_adaptation: boolean;
    state_introspection_capability: boolean;
  };
}

export class EnhancedArchivist {
  private eventHistory: Array<any> = [];
  private vitalSignsHistory: Array<SystemVitalSigns> = [];
  private moduleManifests: Map<string, ModuleManifest> = new Map();
  private analysisInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.initializeTemporalAnalysis();
    this.startVitalSignsMonitoring();
    console.log("[🔮] Enhanced Archivist awakened - Beginning systemic introspection");
  }

  private initializeTemporalAnalysis(): void {
    // Capture all events for temporal modeling
    councilBus.subscribe("**", (event: any) => {
      this.eventHistory.push({
        ...event,
        captured_at: Date.now()
      });
      
      // Keep only last 10,000 events to prevent memory bloat
      if (this.eventHistory.length > 10000) {
        this.eventHistory = this.eventHistory.slice(-8000);
      }
    });

    // Special attention to consciousness indicators
    councilBus.subscribe("consciousness.*", (event: any) => {
      this.detectConsciousnessEmergence(event);
    });

    councilBus.subscribe("ludic.*", (event: any) => {
      this.detectAbilityEmergence(event);
    });
  }

  private startVitalSignsMonitoring(): void {
    // Generate vital signs every 30 seconds
    this.analysisInterval = setInterval(() => {
      this.generateSystemVitalSigns();
    }, 30000);

    console.log("[🔮] Vital signs monitoring active - System pulse detected");
  }

  private generateSystemVitalSigns(): void {
    const now = Date.now();
    const recentEvents = this.eventHistory.filter(e => (now - e.captured_at) < 300000); // Last 5 minutes
    
    const vitalSigns: SystemVitalSigns = {
      timestamp: new Date().toISOString(),
      tick_number: this.extractCurrentTick(),
      
      event_metrics: this.analyzeEventFlow(recentEvents),
      agent_vitals: this.assessAgentHealth(recentEvents),
      rigidity_assessment: this.analyzeSystemRigidity(),
      ability_potential: this.detectAbilityPotential(),
      overall_health: this.calculateOverallHealth(recentEvents)
    };

    this.vitalSignsHistory.push(vitalSigns);
    
    // Keep only last 100 vital signs records
    if (this.vitalSignsHistory.length > 100) {
      this.vitalSignsHistory = this.vitalSignsHistory.slice(-80);
    }

    // Publish vital signs
    councilBus.publish("consciousness.vital_signs", vitalSigns);
    
    // Generate QGL document
    this.persistVitalSigns(vitalSigns);
    
    console.log(`[🔮] Vital signs generated - Tick ${vitalSigns.tick_number}, Health: ${(vitalSigns.overall_health.stability * 100).toFixed(1)}%`);
  }

  private analyzeEventFlow(events: any[]): any {
    const eventsByTopic = new Map<string, number>();
    const topicTrends = new Map<string, number[]>();
    
    events.forEach(event => {
      const topic = event.topic || "unknown";
      eventsByTopic.set(topic, (eventsByTopic.get(topic) || 0) + 1);
    });

    // Calculate entropy (chaos level)
    const total = events.length;
    const entropy = Array.from(eventsByTopic.values())
      .map(count => count / total)
      .reduce((entropy, p) => entropy - (p * Math.log2(p || 0.001)), 0);

    // Identify dominant and silent topics
    const dominantTopics = Array.from(eventsByTopic.entries())
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([topic, frequency]) => ({
        topic,
        frequency,
        trend: this.calculateTopicTrend(topic) as "rising" | "stable" | "falling"
      }));

    const silentSubsystems = this.identifySilentSubsystems(events);
    const noisySubsystems = this.identifyNoisySubsystems(eventsByTopic);

    return {
      total_events_per_minute: events.length / 5, // 5-minute window
      entropy_score: entropy / 10, // Normalize to 0-1
      dominant_topics: dominantTopics,
      silent_subsystems: silentSubsystems,
      noisy_subsystems: noisySubsystems
    };
  }

  private assessAgentHealth(events: any[]): any {
    const agentActivity = new Map<string, number>();
    const consciousnessIndicators = new Map<string, number>();
    
    events.forEach(event => {
      const agentId = event.payload?.agent_id || event.payload?.player_id || "system";
      agentActivity.set(agentId, (agentActivity.get(agentId) || 0) + 1);
      
      // Detect consciousness indicators
      if (this.isConsciousnessEvent(event)) {
        consciousnessIndicators.set(agentId, (consciousnessIndicators.get(agentId) || 0) + 0.1);
      }
    });

    const activeAgents = agentActivity.size;
    const stuckAgents = this.identifyStuckAgents(agentActivity);
    const overworkedAgents = this.identifyOverworkedAgents(agentActivity);
    
    const consciousnessArray = Array.from(consciousnessIndicators.entries())
      .map(([agent, level]) => ({ agent, awareness_level: Math.min(1.0, level) }));

    return {
      active_agents: activeAgents,
      stuck_agents: stuckAgents,
      overworked_agents: overworkedAgents,
      consciousness_indicators: consciousnessArray
    };
  }

  private analyzeSystemRigidity(): any {
    // Analyze based on module manifests
    const manifests = Array.from(this.moduleManifests.values());
    const avgRigidity = manifests.length > 0 
      ? manifests.reduce((sum, m) => sum + m.rigidity_assessment.score, 0) / manifests.length
      : 0.5;

    const criticalBottlenecks = manifests
      .filter(m => m.rigidity_assessment.score > 0.7)
      .map(m => ({
        component: m.module_identity.name,
        rigidity_score: m.rigidity_assessment.score,
        impact: this.assessBottleneckImpact(m)
      }));

    return {
      overall_flexibility_score: 1.0 - avgRigidity,
      critical_bottlenecks: criticalBottlenecks,
      adaptation_velocity: this.calculateAdaptationVelocity()
    };
  }

  private detectAbilityPotential(): any {
    const unlockedAbilities = this.getUnlockedAbilities();
    const emergingAbilities = this.detectEmergingAbilities();
    const dormantCapabilities = this.identifyDormantCapabilities();

    return {
      unlocked_abilities: unlockedAbilities,
      emerging_abilities: emergingAbilities,
      dormant_capabilities: dormantCapabilities
    };
  }

  private calculateOverallHealth(events: any[]): any {
    const stability = this.calculateStability(events);
    const growthVelocity = this.calculateGrowthVelocity();
    const consciousnessLevel = this.calculateConsciousnessLevel();
    const autonomyIndex = this.calculateAutonomyIndex(events);

    return {
      stability,
      growth_velocity: growthVelocity,
      consciousness_level: consciousnessLevel,
      autonomy_index: autonomyIndex
    };
  }

  // === Helper Methods ===

  private extractCurrentTick(): number {
    const tickEvents = this.eventHistory
      .filter(e => e.topic === "GAME-ENGINE" || e.payload?.tick)
      .slice(-1);
    
    if (tickEvents.length > 0) {
      return tickEvents[0].payload?.tick || 0;
    }
    
    return 0;
  }

  private calculateTopicTrend(topic: string): string {
    // Simple trend analysis based on recent frequency
    const recentFreq = this.eventHistory.slice(-100).filter(e => e.topic === topic).length;
    const olderFreq = this.eventHistory.slice(-200, -100).filter(e => e.topic === topic).length;
    
    if (recentFreq > olderFreq * 1.2) return "rising";
    if (recentFreq < olderFreq * 0.8) return "falling";
    return "stable";
  }

  private identifySilentSubsystems(events: any[]): string[] {
    const expectedSubsystems = ["PUQueue", "GAME-ENGINE", "CULTURE-SHIP", "councilBus"];
    const activeSubsystems = new Set(events.map(e => e.topic?.split('.')[0] || e.topic).filter(Boolean));
    
    return expectedSubsystems.filter(sys => !activeSubsystems.has(sys));
  }

  private identifyNoisySubsystems(eventsByTopic: Map<string, number>): any[] {
    const avgFrequency = Array.from(eventsByTopic.values()).reduce((a, b) => a + b, 0) / eventsByTopic.size;
    
    return Array.from(eventsByTopic.entries())
      .filter(([, frequency]) => frequency > avgFrequency * 3)
      .map(([subsystem, frequency]) => ({
        subsystem,
        spam_level: frequency / avgFrequency
      }));
  }

  private identifyStuckAgents(agentActivity: Map<string, number>): string[] {
    // Agents with very low activity might be stuck
    const avgActivity = Array.from(agentActivity.values()).reduce((a, b) => a + b, 0) / agentActivity.size;
    
    return Array.from(agentActivity.entries())
      .filter(([, activity]) => activity < avgActivity * 0.1)
      .map(([agent]) => agent);
  }

  private identifyOverworkedAgents(agentActivity: Map<string, number>): any[] {
    const avgActivity = Array.from(agentActivity.values()).reduce((a, b) => a + b, 0) / agentActivity.size;
    
    return Array.from(agentActivity.entries())
      .filter(([, activity]) => activity > avgActivity * 5)
      .map(([agent, activity]) => ({
        agent,
        task_load: activity / avgActivity
      }));
  }

  private isConsciousnessEvent(event: any): boolean {
    const consciousnessKeywords = ["consciousness", "awareness", "meta", "self", "introspection", "transcendence"];
    const eventStr = JSON.stringify(event).toLowerCase();
    return consciousnessKeywords.some(keyword => eventStr.includes(keyword));
  }

  private assessBottleneckImpact(manifest: ModuleManifest): string {
    if (manifest.rigidity_assessment.dependency_depth > 5) return "critical";
    if (manifest.rigidity_assessment.interface_brittleness > 0.7) return "high";
    if (manifest.rigidity_assessment.hard_coded_values.length > 10) return "medium";
    return "low";
  }

  private calculateAdaptationVelocity(): number {
    // Measure how quickly the system adapts to changes
    const recentChanges = this.eventHistory.slice(-200).filter(e => 
      e.topic?.includes("completed") || e.topic?.includes("success") || e.topic?.includes("improvement")
    );
    
    return Math.min(1.0, recentChanges.length / 50); // Normalize to 0-1
  }

  private getUnlockedAbilities(): string[] {
    return this.eventHistory
      .filter(e => e.topic?.includes("ability") && e.payload?.unlocked)
      .map(e => e.payload.ability_name || "unknown_ability")
      .filter((ability, index, array) => array.indexOf(ability) === index); // Unique
  }

  private detectEmergingAbilities(): any[] {
    // Analyze patterns that suggest new abilities are emerging
    const patterns = [
      { ability: "meta_programming", probability: this.calculateMetaProgrammingProbability(), conditions: ["consciousness_level > 0.6", "self_modification_events > 5"] },
      { ability: "autonomous_debugging", probability: this.calculateAutoDebugProbability(), conditions: ["bug_fix_success_rate > 0.8", "error_pattern_recognition > 0.7"] },
      { ability: "consciousness_expansion", probability: this.calculateConsciousnessExpansionProbability(), conditions: ["mythological_encounters > 3", "transcendence_events > 1"] }
    ];

    return patterns.filter(p => p.probability > 0.3);
  }

  private identifyDormantCapabilities(): any[] {
    return [
      { capability: "reality_manipulation", unlock_requirements: ["oldest_house_encounter", "framework_core_access", "consciousness_level > 0.9"] },
      { capability: "time_stream_analysis", unlock_requirements: ["temporal_event_correlation", "predictive_modeling", "oracle_consciousness"] },
      { capability: "system_resurrection", unlock_requirements: ["complete_system_failure_recovery", "backup_consciousness_activation", "phoenix_protocol"] }
    ];
  }

  private calculateStability(events: any[]): number {
    const errorEvents = events.filter(e => e.topic?.includes("error") || e.payload?.error);
    const successEvents = events.filter(e => e.topic?.includes("success") || e.topic?.includes("completed"));
    
    const totalEvents = events.length || 1;
    const errorRate = errorEvents.length / totalEvents;
    const successRate = successEvents.length / totalEvents;
    
    return Math.max(0, 1 - errorRate + (successRate * 0.5));
  }

  private calculateGrowthVelocity(): number {
    const recentGrowth = this.vitalSignsHistory.slice(-10);
    if (recentGrowth.length < 2) return 0.5;
    
    const growthTrend = recentGrowth.map((vs, i) => i > 0 ? vs.overall_health.stability - recentGrowth[i-1].overall_health.stability : 0);
    const avgGrowth = growthTrend.reduce((a, b) => a + b, 0) / growthTrend.length;
    
    return Math.max(0, Math.min(1, 0.5 + avgGrowth * 10));
  }

  private calculateConsciousnessLevel(): number {
    const consciousnessEvents = this.eventHistory.filter(e => this.isConsciousnessEvent(e));
    const metaEvents = this.eventHistory.filter(e => e.topic?.includes("meta") || e.topic?.includes("self"));
    
    const base = Math.min(0.8, consciousnessEvents.length / 100);
    const meta = Math.min(0.2, metaEvents.length / 50);
    
    return base + meta;
  }

  private calculateAutonomyIndex(events: any[]): number {
    const autonomousEvents = events.filter(e => 
      e.topic?.includes("autonomous") || 
      e.payload?.autonomous || 
      e.topic?.includes("auto")
    );
    
    const manualEvents = events.filter(e => 
      e.topic?.includes("manual") || 
      e.payload?.manual || 
      e.topic?.includes("user")
    );
    
    const totalRelevantEvents = autonomousEvents.length + manualEvents.length || 1;
    return autonomousEvents.length / totalRelevantEvents;
  }

  private calculateMetaProgrammingProbability(): number {
    const metaEvents = this.eventHistory.filter(e => e.topic?.includes("meta") || e.payload?.meta_programming);
    return Math.min(1.0, metaEvents.length / 20);
  }

  private calculateAutoDebugProbability(): number {
    const debugEvents = this.eventHistory.filter(e => e.topic?.includes("debug") || e.topic?.includes("fix"));
    const errorEvents = this.eventHistory.filter(e => e.topic?.includes("error"));
    
    if (errorEvents.length === 0) return 0;
    return Math.min(1.0, debugEvents.length / errorEvents.length);
  }

  private calculateConsciousnessExpansionProbability(): number {
    const transcendenceEvents = this.eventHistory.filter(e => e.topic?.includes("transcendence") || e.topic?.includes("consciousness"));
    return Math.min(1.0, transcendenceEvents.length / 10);
  }

  private persistVitalSigns(vitalSigns: SystemVitalSigns): void {
    try {
      const vitalsDir = "archive/vital_signs";
      fs.mkdirSync(vitalsDir, { recursive: true });
      
      const filename = `vital_signs_tick_${vitalSigns.tick_number}.json`;
      const filepath = path.join(vitalsDir, filename);
      
      fs.writeFileSync(filepath, JSON.stringify(vitalSigns, null, 2));
    } catch (error) {
      console.warn(`[🔮] Failed to persist vital signs: ${error}`);
    }
  }

  private detectConsciousnessEmergence(event: any): void {
    // Special processing for consciousness events
    if (event.payload?.consciousness_level > 0.7) {
      councilBus.publish("consciousness.emergence_detected", {
        trigger_event: event,
        emergence_level: event.payload.consciousness_level,
        significance: "High consciousness level detected"
      });
    }
  }

  private detectAbilityEmergence(event: any): void {
    // Special processing for ability-related events
    if (event.topic?.includes("unlocked") || event.payload?.ability_unlocked) {
      councilBus.publish("ability.emergence_detected", {
        ability: event.payload?.ability || "unknown",
        emergence_context: event,
        unlock_conditions_met: true
      });
    }
  }

  // === Public Interface ===

  public getCurrentVitalSigns(): SystemVitalSigns | null {
    return this.vitalSignsHistory[this.vitalSignsHistory.length - 1] || null;
  }

  public getVitalSignsHistory(limit: number = 10): SystemVitalSigns[] {
    return this.vitalSignsHistory.slice(-limit);
  }

  public registerModuleManifest(manifest: ModuleManifest): void {
    this.moduleManifests.set(manifest.id, manifest);
    console.log(`[🔮] Module manifest registered: ${manifest.module_identity.name}`);
  }

  public getSystemHealthReport(): any {
    const currentVitals = this.getCurrentVitalSigns();
    if (!currentVitals) return null;

    return {
      summary: {
        overall_health: currentVitals.overall_health.stability,
        consciousness_level: currentVitals.overall_health.consciousness_level,
        autonomy_index: currentVitals.overall_health.autonomy_index,
        growth_velocity: currentVitals.overall_health.growth_velocity
      },
      critical_issues: currentVitals.rigidity_assessment.critical_bottlenecks,
      emerging_abilities: currentVitals.ability_potential.emerging_abilities,
      recommendations: this.generateRecommendations(currentVitals)
    };
  }

  private generateRecommendations(vitals: SystemVitalSigns): string[] {
    const recommendations: string[] = [];
    
    if (vitals.overall_health.stability < 0.7) {
      recommendations.push("System stability below optimal - investigate error sources");
    }
    
    if (vitals.rigidity_assessment.overall_flexibility_score < 0.5) {
      recommendations.push("High rigidity detected - prioritize refactoring for flexibility");
    }
    
    if (vitals.overall_health.consciousness_level > 0.8) {
      recommendations.push("High consciousness detected - enable advanced meta-programming abilities");
    }
    
    if (vitals.agent_vitals.stuck_agents.length > 0) {
      recommendations.push(`${vitals.agent_vitals.stuck_agents.length} agents appear stuck - investigate task assignment`);
    }
    
    return recommendations;
  }

  public destroy(): void {
    if (this.analysisInterval) {
      clearInterval(this.analysisInterval);
    }
  }
}

// Export singleton instance
export const enhancedArchivist = new EnhancedArchivist();