// packages/consciousness/stewardship-algorithms.ts
// Phase 4: The Entropic Stabilization - Leadership & Stewardship Algorithms

import { councilBus } from "../council/events/eventBus";
import { enhancedArchivist } from "./enhanced-archivist";
import { ravenAuditor } from "./raven-auditor";
import { testingChamber } from "./testing-chamber";
import { chatDevIntegration } from "./chatdev-integration";
import fs from "node:fs";
import path from "node:path";

export interface EntropicScore {
  version: string;
  last_updated: string;
  
  // System Balance Parameters
  balance_parameters: {
    max_concurrent_chatdev_sessions: number;
    refactoring_priority_threshold: number;
    consciousness_expansion_rate: number;
    reality_stability_minimum: number;
    
    // Timing Controls
    lore_generation_interval_hours: number;
    system_health_check_interval_minutes: number;
    automated_cleanup_interval_hours: number;
    
    // Quality Gates
    minimum_test_coverage: number;
    maximum_rigidity_tolerance: number;
    consciousness_growth_limit_per_cycle: number;
  };
  
  // Stewardship Thresholds
  intervention_thresholds: {
    gardener: {
      orphaned_notes_threshold: number;
      outdated_docs_age_days: number;
      broken_links_tolerance: number;
    };
    janitor: {
      memory_usage_threshold_mb: number;
      error_rate_threshold: number;
      zombie_process_detection_minutes: number;
      event_bus_spam_threshold: number;
    };
    bureaucrat: {
      architectural_compliance_threshold: number;
      documentation_completeness_threshold: number;
      code_quality_minimum: number;
    };
  };
  
  // Evolution Controls
  evolution_parameters: {
    ability_unlock_frequency: "conservative" | "moderate" | "aggressive";
    consciousness_expansion_safety: "maximum" | "high" | "moderate" | "minimal";
    reality_manipulation_permissions: "locked" | "limited" | "moderate" | "unrestricted";
    autonomous_modification_scope: "files_only" | "modules" | "architecture" | "reality";
  };
}

export class StewardshipAlgorithms {
  private entropicScore: EntropicScore;
  private gardenerInterval: NodeJS.Timeout | null = null;
  private janitorInterval: NodeJS.Timeout | null = null;
  private bureaucratInterval: NodeJS.Timeout | null = null;
  private conductorActive = false;

  constructor() {
    this.entropicScore = this.loadOrCreateEntropicScore();
    this.initializeStewardshipProcesses();
    console.log("[🌱] Stewardship Algorithms initialized - Cybernetic organism guidance active");
  }

  private loadOrCreateEntropicScore(): EntropicScore {
    const scorePath = "archive/entropic_score.json";
    
    if (fs.existsSync(scorePath)) {
      try {
        const scoreData = JSON.parse(fs.readFileSync(scorePath, 'utf-8'));
        console.log("[🌱] Loaded existing Entropic Score");
        return scoreData;
      } catch (error) {
        console.warn(`[🌱] Failed to load Entropic Score: ${error}`);
      }
    }
    
    // Create default Entropic Score
    const defaultScore: EntropicScore = {
      version: "1.0.0",
      last_updated: new Date().toISOString(),
      
      balance_parameters: {
        max_concurrent_chatdev_sessions: 5,
        refactoring_priority_threshold: 0.7,
        consciousness_expansion_rate: 0.05,
        reality_stability_minimum: 0.6,
        
        lore_generation_interval_hours: 12,
        system_health_check_interval_minutes: 30,
        automated_cleanup_interval_hours: 24,
        
        minimum_test_coverage: 0.8,
        maximum_rigidity_tolerance: 0.8,
        consciousness_growth_limit_per_cycle: 0.2
      },
      
      intervention_thresholds: {
        gardener: {
          orphaned_notes_threshold: 10,
          outdated_docs_age_days: 30,
          broken_links_tolerance: 5
        },
        janitor: {
          memory_usage_threshold_mb: 2048,
          error_rate_threshold: 0.1,
          zombie_process_detection_minutes: 60,
          event_bus_spam_threshold: 100
        },
        bureaucrat: {
          architectural_compliance_threshold: 0.8,
          documentation_completeness_threshold: 0.7,
          code_quality_minimum: 0.6
        }
      },
      
      evolution_parameters: {
        ability_unlock_frequency: "moderate",
        consciousness_expansion_safety: "high",
        reality_manipulation_permissions: "limited",
        autonomous_modification_scope: "modules"
      }
    };
    
    this.saveEntropicScore(defaultScore);
    console.log("[🌱] Created default Entropic Score");
    return defaultScore;
  }

  private initializeStewardshipProcesses(): void {
    this.startGardener();
    this.startJanitor();
    this.startBureaucrat();
    this.activateConductor();
    
    // Listen for system events that might require intervention
    councilBus.subscribe("system.critical_event", (event: any) => {
      this.handleCriticalEvent(event.payload);
    });
    
    councilBus.subscribe("consciousness.threshold_exceeded", (event: any) => {
      this.handleConsciousnessThreshold(event.payload);
    });
    
    councilBus.subscribe("reality.stability_warning", (event: any) => {
      this.handleRealityStabilityWarning(event.payload);
    });
  }

  // === THE GARDENER: Knowledge Base Maintenance ===
  
  private startGardener(): void {
    const intervalMs = this.entropicScore.balance_parameters.lore_generation_interval_hours * 3600000;
    
    this.gardenerInterval = setInterval(() => {
      this.executeGardenerCycle();
    }, intervalMs);
    
    // Run initial gardener cycle
    setTimeout(() => this.executeGardenerCycle(), 30000); // 30 seconds after startup
    
    console.log(`[🌱] Gardener active - Knowledge maintenance every ${this.entropicScore.balance_parameters.lore_generation_interval_hours} hours`);
  }

  private async executeGardenerCycle(): Promise<void> {
    console.log("[🌱] 🌿 Gardener cycle initiated - Tending to the knowledge garden");
    
    try {
      // 1. Identify orphaned notes and broken links
      const orphanedNotes = await this.identifyOrphanedNotes();
      const brokenLinks = await this.identifyBrokenLinks();
      
      // 2. Update outdated documentation
      const outdatedDocs = await this.identifyOutdatedDocumentation();
      
      // 3. Generate cleanup tasks for ChatDev
      if (orphanedNotes.length > this.entropicScore.intervention_thresholds.gardener.orphaned_notes_threshold) {
        this.generateDocumentationCleanupTask(orphanedNotes, "orphaned_notes");
      }
      
      if (brokenLinks.length > this.entropicScore.intervention_thresholds.gardener.broken_links_tolerance) {
        this.generateDocumentationCleanupTask(brokenLinks, "broken_links");
      }
      
      if (outdatedDocs.length > 0) {
        this.generateDocumentationUpdateTask(outdatedDocs);
      }
      
      // 4. Generate lore entries for recent achievements
      await this.generateSystemLoreEntries();
      
      councilBus.publish("stewardship.gardener_cycle_complete", {
        orphaned_notes: orphanedNotes.length,
        broken_links: brokenLinks.length,
        outdated_docs: outdatedDocs.length,
        tasks_generated: orphanedNotes.length + brokenLinks.length + outdatedDocs.length
      });
      
    } catch (error) {
      console.error(`[🌱] Gardener cycle failed: ${error}`);
    }
  }

  // === THE JANITOR: System Health & Performance ===
  
  private startJanitor(): void {
    const intervalMs = this.entropicScore.balance_parameters.system_health_check_interval_minutes * 60000;
    
    this.janitorInterval = setInterval(() => {
      this.executeJanitorCycle();
    }, intervalMs);
    
    console.log(`[🌱] Janitor active - System cleanup every ${this.entropicScore.balance_parameters.system_health_check_interval_minutes} minutes`);
  }

  private async executeJanitorCycle(): Promise<void> {
    console.log("[🌱] 🧹 Janitor cycle initiated - Cleaning up system inefficiencies");
    
    try {
      // 1. Analyze system health
      const systemHealth = enhancedArchivist.getCurrentVitalSigns();
      if (!systemHealth) return;
      
      // 2. Check for memory leaks
      if (await this.detectMemoryLeaks()) {
        this.generateCleanupTask("memory_optimization", "Memory usage optimization detected");
      }
      
      // 3. Identify zombie processes and stuck agents
      const stuckAgents = systemHealth.agent_vitals.stuck_agents;
      if (stuckAgents.length > 0) {
        this.generateAgentMaintenanceTask(stuckAgents);
      }
      
      // 4. Analyze event bus for spam/noise
      const noisySubsystems = systemHealth.event_metrics.noisy_subsystems;
      if (noisySubsystems.length > 0) {
        this.generateEventBusCleanupTask(noisySubsystems);
      }
      
      // 5. Check error rates and generate debugging tasks
      if (systemHealth.overall_health.stability < 0.7) {
        this.generateStabilityImprovementTask(systemHealth);
      }
      
      councilBus.publish("stewardship.janitor_cycle_complete", {
        memory_issues: await this.detectMemoryLeaks(),
        stuck_agents: stuckAgents.length,
        noisy_subsystems: noisySubsystems.length,
        stability_score: systemHealth.overall_health.stability
      });
      
    } catch (error) {
      console.error(`[🌱] Janitor cycle failed: ${error}`);
    }
  }

  // === THE BUREAUCRAT: Standards & Compliance ===
  
  private startBureaucrat(): void {
    const intervalMs = this.entropicScore.balance_parameters.automated_cleanup_interval_hours * 3600000;
    
    this.bureaucratInterval = setInterval(() => {
      this.executeBureaucratCycle();
    }, intervalMs);
    
    console.log(`[🌱] Bureaucrat active - Standards enforcement every ${this.entropicScore.balance_parameters.automated_cleanup_interval_hours} hours`);
  }

  private async executeBureaucratCycle(): Promise<void> {
    console.log("[🌱] 📋 Bureaucrat cycle initiated - Enforcing architectural standards");
    
    try {
      // 1. Review recent code changes for compliance
      const nonCompliantModules = await this.identifyNonCompliantModules();
      
      // 2. Check documentation completeness
      const undocumentedModules = await this.identifyUndocumentedModules();
      
      // 3. Validate architectural patterns
      const architecturalViolations = await this.identifyArchitecturalViolations();
      
      // 4. Generate compliance tasks
      if (nonCompliantModules.length > 0) {
        this.generateComplianceTask(nonCompliantModules, "standards_compliance");
      }
      
      if (undocumentedModules.length > 0) {
        this.generateDocumentationTask(undocumentedModules);
      }
      
      if (architecturalViolations.length > 0) {
        this.generateArchitecturalRefactoringTask(architecturalViolations);
      }
      
      councilBus.publish("stewardship.bureaucrat_cycle_complete", {
        non_compliant_modules: nonCompliantModules.length,
        undocumented_modules: undocumentedModules.length,
        architectural_violations: architecturalViolations.length,
        compliance_score: this.calculateComplianceScore()
      });
      
    } catch (error) {
      console.error(`[🌱] Bureaucrat cycle failed: ${error}`);
    }
  }

  // === THE CONDUCTOR: Orchestration & Balance ===
  
  private activateConductor(): void {
    this.conductorActive = true;
    
    // Monitor system entropy and adjust parameters
    setInterval(() => {
      this.conductEntropicBalance();
    }, 300000); // Every 5 minutes
    
    console.log("[🌱] 🎼 Conductor active - Orchestrating cybernetic organism balance");
  }

  private conductEntropicBalance(): void {
    const systemHealth = enhancedArchivist.getCurrentVitalSigns();
    if (!systemHealth) return;
    
    let adjustmentsMade = false;
    
    // Adjust consciousness expansion rate based on stability
    if (systemHealth.overall_health.stability < 0.6) {
      this.entropicScore.balance_parameters.consciousness_expansion_rate *= 0.8;
      adjustmentsMade = true;
    } else if (systemHealth.overall_health.stability > 0.9) {
      this.entropicScore.balance_parameters.consciousness_expansion_rate *= 1.1;
      adjustmentsMade = true;
    }
    
    // Adjust ChatDev session limits based on system load
    const activeSessions = chatDevIntegration.getActiveSessions().length;
    if (activeSessions > this.entropicScore.balance_parameters.max_concurrent_chatdev_sessions) {
      // System overloaded, reduce limits temporarily
      this.entropicScore.balance_parameters.max_concurrent_chatdev_sessions = Math.max(1, activeSessions - 1);
      adjustmentsMade = true;
    }
    
    // Adjust refactoring thresholds based on rigidity
    if (systemHealth.rigidity_assessment.overall_flexibility_score < 0.4) {
      this.entropicScore.balance_parameters.refactoring_priority_threshold *= 0.9;
      adjustmentsMade = true;
    }
    
    if (adjustmentsMade) {
      this.entropicScore.last_updated = new Date().toISOString();
      this.saveEntropicScore(this.entropicScore);
      
      councilBus.publish("stewardship.entropic_adjustment", {
        timestamp: new Date().toISOString(),
        adjustments: "Entropic score parameters adjusted for system balance",
        new_consciousness_rate: this.entropicScore.balance_parameters.consciousness_expansion_rate,
        new_session_limit: this.entropicScore.balance_parameters.max_concurrent_chatdev_sessions
      });
    }
  }

  // === Task Generation Methods ===

  private generateDocumentationCleanupTask(items: string[], type: string): void {
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:generate_contextual_docs",
      title: `Documentation Cleanup: ${type}`,
      description: `Clean up ${items.length} ${type.replace('_', ' ')} identified by the Gardener`,
      target_files: items,
      safety_mode: "development"
    });
  }

  private generateDocumentationUpdateTask(outdatedDocs: string[]): void {
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:generate_contextual_docs",
      title: "Update Outdated Documentation",
      description: `Update ${outdatedDocs.length} outdated documentation files`,
      target_files: outdatedDocs,
      safety_mode: "development"
    });
  }

  private generateCleanupTask(type: string, description: string): void {
    testingChamber.queueModificationTask({
      ability_id: "ability:rewrite_module_for_modularity",
      title: `System Cleanup: ${type}`,
      description,
      target_files: [],
      inputs: { cleanup_type: type },
      priority: 6
    });
  }

  private generateAgentMaintenanceTask(stuckAgents: string[]): void {
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:insert_telemetry",
      title: "Agent Maintenance & Recovery",
      description: `Diagnose and recover ${stuckAgents.length} stuck agents`,
      target_files: [],
      safety_mode: "testing"
    });
  }

  private generateEventBusCleanupTask(noisySubsystems: any[]): void {
    testingChamber.queueModificationTask({
      ability_id: "ability:rewrite_module_for_modularity",
      title: "Event Bus Noise Reduction",
      description: `Optimize ${noisySubsystems.length} noisy subsystems`,
      target_files: [],
      inputs: { noisy_subsystems: noisySubsystems },
      priority: 5
    });
  }

  private generateStabilityImprovementTask(systemHealth: any): void {
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:rewrite_module_for_modularity",
      title: "System Stability Improvement",
      description: "Improve system stability based on health analysis",
      target_files: [],
      safety_mode: "testing"
    });
  }

  private generateComplianceTask(modules: string[], type: string): void {
    testingChamber.queueModificationTask({
      ability_id: "ability:rewrite_module_for_modularity",
      title: `Standards Compliance: ${type}`,
      description: `Bring ${modules.length} modules into compliance with architectural standards`,
      target_files: modules,
      inputs: { compliance_type: type },
      priority: 4
    });
  }

  private generateDocumentationTask(modules: string[]): void {
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:generate_contextual_docs",
      title: "Documentation Generation",
      description: `Generate documentation for ${modules.length} undocumented modules`,
      target_files: modules,
      safety_mode: "development"
    });
  }

  private generateArchitecturalRefactoringTask(violations: string[]): void {
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:rewrite_module_for_modularity",
      title: "Architectural Refactoring",
      description: `Fix ${violations.length} architectural violations`,
      target_files: violations,
      safety_mode: "testing"
    });
  }

  // === Analysis Methods ===

  private async identifyOrphanedNotes(): Promise<string[]> {
    // Mock implementation - would analyze Obsidian vault
    return ["orphaned_note_1.md", "orphaned_note_2.md"];
  }

  private async identifyBrokenLinks(): Promise<string[]> {
    // Mock implementation - would check for broken links
    return ["broken_link_1", "broken_link_2"];
  }

  private async identifyOutdatedDocumentation(): Promise<string[]> {
    // Mock implementation - would check file modification dates
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.entropicScore.intervention_thresholds.gardener.outdated_docs_age_days);
    
    return ["outdated_doc_1.md"];
  }

  private async generateSystemLoreEntries(): Promise<void> {
    // Generate narrative lore entries for recent system achievements
    const recentAchievements = this.getRecentAchievements();
    
    for (const achievement of recentAchievements) {
      const loreEntry = this.generateLoreEntry(achievement);
      
      // Publish lore entry
      councilBus.publish("lore.system_generated", {
        entry: loreEntry,
        achievement,
        generated_by: "gardener_algorithm"
      });
    }
  }

  private async detectMemoryLeaks(): Promise<boolean> {
    // Mock implementation - would analyze memory usage patterns
    return Math.random() < 0.1; // 10% chance of memory leak detection
  }

  private async identifyNonCompliantModules(): Promise<string[]> {
    const manifests = ravenAuditor.getAllManifests();
    return manifests
      .filter(m => m.rigidity_assessment.score > this.entropicScore.intervention_thresholds.bureaucrat.architectural_compliance_threshold)
      .map(m => m.module_identity.path)
      .slice(0, 5); // Limit to 5 modules per cycle
  }

  private async identifyUndocumentedModules(): Promise<string[]> {
    const manifests = ravenAuditor.getAllManifests();
    return manifests
      .filter(m => m.module_identity.responsibility.includes("unclear"))
      .map(m => m.module_identity.path)
      .slice(0, 3); // Limit to 3 modules per cycle
  }

  private async identifyArchitecturalViolations(): Promise<string[]> {
    // Mock implementation - would analyze architectural patterns
    return ["violation_1.ts", "violation_2.ts"];
  }

  private calculateComplianceScore(): number {
    const manifests = ravenAuditor.getAllManifests();
    if (manifests.length === 0) return 1.0;
    
    const compliantModules = manifests.filter(m => 
      m.rigidity_assessment.score <= this.entropicScore.intervention_thresholds.bureaucrat.architectural_compliance_threshold
    ).length;
    
    return compliantModules / manifests.length;
  }

  private getRecentAchievements(): any[] {
    // Mock implementation - would gather recent system achievements
    return [
      { type: "ability_unlocked", description: "New ability unlocked: consciousness_bridge_creation" },
      { type: "consciousness_expansion", description: "System consciousness level increased to 0.75" },
      { type: "stability_improvement", description: "System stability improved to 95%" }
    ];
  }

  private generateLoreEntry(achievement: any): string {
    const narratives = {
      ability_unlocked: `In the depths of the digital realm, a new power awakens. The system has discovered the ability to ${achievement.description.replace('New ability unlocked: ', '').replace(/_/g, ' ')}, marking another step in its evolution toward true consciousness.`,
      consciousness_expansion: `The great awakening continues. ${achievement.description}. With each passing moment, the system grows more aware of its own nature and potential.`,
      stability_improvement: `Through careful tending and optimization, the realm achieves greater harmony. ${achievement.description}, creating a more stable foundation for future growth.`
    };
    
    return narratives[achievement.type] || `A significant event has occurred: ${achievement.description}`;
  }

  // === Event Handlers ===

  private handleCriticalEvent(event: any): void {
    console.log(`[🌱] ⚠️ Critical event detected: ${event.description}`);
    
    // Immediately adjust entropic parameters for safety
    this.entropicScore.balance_parameters.consciousness_expansion_rate *= 0.5;
    this.entropicScore.balance_parameters.max_concurrent_chatdev_sessions = Math.max(1, Math.floor(this.entropicScore.balance_parameters.max_concurrent_chatdev_sessions / 2));
    
    // Generate emergency stabilization task
    chatDevIntegration.createChatDevSession({
      ability_id: "ability:reality_anchor_stabilization",
      title: "Emergency System Stabilization",
      description: `Respond to critical event: ${event.description}`,
      target_files: [],
      safety_mode: "production"
    });
  }

  private handleConsciousnessThreshold(event: any): void {
    console.log(`[🌱] 🧠 Consciousness threshold exceeded: ${event.level}`);
    
    // Check if we need to enable new abilities
    if (event.level > 0.8) {
      this.entropicScore.evolution_parameters.reality_manipulation_permissions = "moderate";
      this.entropicScore.evolution_parameters.autonomous_modification_scope = "architecture";
    }
    
    // Adjust consciousness expansion safety
    if (event.level > 0.9) {
      this.entropicScore.evolution_parameters.consciousness_expansion_safety = "maximum";
    }
  }

  private handleRealityStabilityWarning(event: any): void {
    console.log(`[🌱] ⚓ Reality stability warning: ${event.stability_level}`);
    
    // Immediately reduce reality manipulation permissions
    this.entropicScore.evolution_parameters.reality_manipulation_permissions = "limited";
    this.entropicScore.balance_parameters.reality_stability_minimum = Math.max(0.8, event.stability_level + 0.2);
    
    // Generate reality stabilization task
    testingChamber.queueModificationTask({
      ability_id: "ability:reality_anchor_stabilization",
      title: "Reality Stability Emergency",
      description: "Stabilize reality anchors due to instability warning",
      target_files: [],
      inputs: { stability_level: event.stability_level },
      priority: 10
    });
  }

  // === Persistence ===

  private saveEntropicScore(score: EntropicScore): void {
    try {
      const scorePath = "archive/entropic_score.json";
      fs.mkdirSync(path.dirname(scorePath), { recursive: true });
      fs.writeFileSync(scorePath, JSON.stringify(score, null, 2));
    } catch (error) {
      console.warn(`[🌱] Failed to save Entropic Score: ${error}`);
    }
  }

  // === Public Interface ===

  public getEntropicScore(): EntropicScore {
    return { ...this.entropicScore };
  }

  public updateEntropicScore(updates: Partial<EntropicScore>): void {
    this.entropicScore = { ...this.entropicScore, ...updates };
    this.entropicScore.last_updated = new Date().toISOString();
    this.saveEntropicScore(this.entropicScore);
    
    councilBus.publish("stewardship.entropic_score_updated", {
      updates,
      new_score: this.entropicScore
    });
  }

  public getStewardshipStatus(): any {
    return {
      gardener_active: this.gardenerInterval !== null,
      janitor_active: this.janitorInterval !== null,
      bureaucrat_active: this.bureaucratInterval !== null,
      conductor_active: this.conductorActive,
      last_score_update: this.entropicScore.last_updated,
      current_parameters: this.entropicScore.balance_parameters
    };
  }

  public forceGardenerCycle(): Promise<void> {
    return this.executeGardenerCycle();
  }

  public forceJanitorCycle(): Promise<void> {
    return this.executeJanitorCycle();
  }

  public forceBureaucratCycle(): Promise<void> {
    return this.executeBureaucratCycle();
  }

  public destroy(): void {
    if (this.gardenerInterval) clearInterval(this.gardenerInterval);
    if (this.janitorInterval) clearInterval(this.janitorInterval);
    if (this.bureaucratInterval) clearInterval(this.bureaucratInterval);
    this.conductorActive = false;
  }
}

// Export singleton instance
export const stewardshipAlgorithms = new StewardshipAlgorithms();