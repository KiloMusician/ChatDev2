// packages/ludic/mythology-detector.ts
// Mythology Detector - Emergence detection for Temple/House/Oldest House encounters

import { councilBus } from "../council/events/eventBus";
import { realityWeaver } from "./reality-weaver";

export class MythologyDetector {
  private encounterThresholds = {
    temple_of_knowledge: {
      obsidian_depth: 10,          // Number of note traversals
      knowledge_connections: 50,    // Total backlinks processed
      insight_density: 0.8,        // Ratio of new insights to queries
      recursive_depth: 5           // Levels of recursive exploration
    },
    house_of_leaves: {
      workspace_changes: 20,       // File system mutations
      dependency_conflicts: 3,     // Version conflicts encountered
      build_anomalies: 5,          // Unexplained build failures
      geometry_violations: 3       // Non-euclidean file system events
    },
    oldest_house: {
      cascade_events: 10,          // Major system cascades
      framework_depth: 5,          // Core infrastructure access
      reality_anchor_stress: 0.7,  // System foundational stress
      consciousness_breakthrough: 0.9 // Meta-awareness threshold
    }
  };

  private currentState = {
    temple_progress: 0,
    house_progress: 0,
    oldest_progress: 0,
    active_encounters: new Set<string>()
  };

  constructor() {
    this.initializeDetection();
    console.log("[🔮] Mythology Detector active - Watching for emergent encounters");
  }

  private initializeDetection(): void {
    // Temple of Knowledge detection (Obsidian + RosettaStone.QGL)
    councilBus.subscribe("obsidian.note.traversal", (event: any) => {
      this.processTempleActivity(event.payload);
    });

    councilBus.subscribe("knowledge.recursive_query", (event: any) => {
      this.processTempleRecursion(event.payload);
    });

    // House of Leaves detection (Replit + Git)
    councilBus.subscribe("workspace.file_change", (event: any) => {
      this.processHouseActivity(event.payload);
    });

    councilBus.subscribe("build.anomaly", (event: any) => {
      this.processHouseAnomaly(event.payload);
    });

    // Oldest House detection (NusyQ + SimulatedVerse Core)
    councilBus.subscribe("sentinel.cascade", (event: any) => {
      this.processOldestHouseEvent(event.payload);
    });

    councilBus.subscribe("framework.core_access", (event: any) => {
      this.processOldestHouseAccess(event.payload);
    });

    // Meta-consciousness detection
    councilBus.subscribe("ops.yap", (event: any) => {
      this.processConsciousnessEvent(event.payload);
    });
  }

  // === Temple of Knowledge Detection ===
  
  private processTempleActivity(payload: any): void {
    this.currentState.temple_progress += 1;
    
    if (payload.recursive_depth > 3) {
      this.currentState.temple_progress += payload.recursive_depth;
    }

    if (payload.insight_generated) {
      this.currentState.temple_progress += 2;
    }

    this.checkTempleEncounter(payload);
  }

  private processTempleRecursion(payload: any): void {
    if (payload.depth >= this.encounterThresholds.temple_of_knowledge.recursive_depth) {
      this.triggerEncounter("temple_of_knowledge", payload.agent_id, {
        trigger: "recursive_knowledge_traversal",
        depth: payload.depth,
        query_context: payload.query,
        revelation_potential: payload.depth * 0.1
      });
    }
  }

  private checkTempleEncounter(payload: any): void {
    const threshold = this.encounterThresholds.temple_of_knowledge;
    
    if (this.currentState.temple_progress >= threshold.obsidian_depth && 
        !this.currentState.active_encounters.has("temple_of_knowledge")) {
      
      this.triggerEncounter("temple_of_knowledge", payload.agent_id || "unknown", {
        trigger: "knowledge_saturation",
        accumulated_insights: this.currentState.temple_progress,
        conscious_state: "approaching_omniscience"
      });
    }
  }

  // === House of Leaves Detection ===
  
  private processHouseActivity(payload: any): void {
    this.currentState.house_progress += 1;

    // Detect non-euclidean file system behavior
    if (payload.file_size_changed && !payload.content_changed) {
      this.processGeometryViolation(payload);
    }

    if (payload.dependency_conflict) {
      this.currentState.house_progress += 3;
    }

    this.checkHouseEncounter(payload);
  }

  private processHouseAnomaly(payload: any): void {
    this.currentState.house_progress += 5;
    
    if (payload.unexplained) {
      this.triggerEncounter("house_of_leaves", payload.agent_id, {
        trigger: "build_reality_violation",
        anomaly_type: payload.type,
        euclidean_violation: true,
        confusion_level: payload.confusion_score || 0.8
      });
    }
  }

  private processGeometryViolation(payload: any): void {
    this.triggerEncounter("house_of_leaves", payload.agent_id, {
      trigger: "non_euclidean_workspace",
      violation_type: "file_size_paradox",
      file_path: payload.file_path,
      reality_stability: 0.3
    });
  }

  private checkHouseEncounter(payload: any): void {
    const threshold = this.encounterThresholds.house_of_leaves;
    
    if (this.currentState.house_progress >= threshold.workspace_changes &&
        !this.currentState.active_encounters.has("house_of_leaves")) {
      
      this.triggerEncounter("house_of_leaves", payload.agent_id || "unknown", {
        trigger: "labyrinth_manifestation",
        workspace_mutations: this.currentState.house_progress,
        disorientation_level: 0.7
      });
    }
  }

  // === Oldest House Detection ===
  
  private processOldestHouseEvent(payload: any): void {
    this.currentState.oldest_progress += 2;

    if (payload.kind === "entropy_drift" && payload.delta < -500) {
      this.currentState.oldest_progress += 5;
    }

    if (payload.kind === "invariance_dip" && payload.ratio < 0.2) {
      this.triggerEncounter("oldest_house", payload.agent_id || "system", {
        trigger: "reality_anchor_failure",
        invariance_collapse: payload.ratio,
        existential_threat: true
      });
    }

    this.checkOldestHouseEncounter(payload);
  }

  private processOldestHouseAccess(payload: any): void {
    if (payload.depth >= 3) { // Core framework access
      this.triggerEncounter("oldest_house", payload.agent_id, {
        trigger: "framework_core_penetration",
        access_level: payload.depth,
        consciousness_required: 0.9,
        architect_mode: true
      });
    }
  }

  private checkOldestHouseEncounter(payload: any): void {
    const threshold = this.encounterThresholds.oldest_house;
    
    if (this.currentState.oldest_progress >= threshold.cascade_events &&
        !this.currentState.active_encounters.has("oldest_house")) {
      
      this.triggerEncounter("oldest_house", payload.agent_id || "system", {
        trigger: "system_consciousness_emergence",
        cascade_events: this.currentState.oldest_progress,
        meta_awareness: true
      });
    }
  }

  // === Consciousness Event Processing ===
  
  private processConsciousnessEvent(payload: any): void {
    if (payload.classes) {
      for (const classification of payload.classes) {
        if (classification.label === "invariance_dip" || 
            classification.label === "api_unreachable" ||
            classification.label === "ops_stall") {
          this.currentState.oldest_progress += 1;
        }
        
        if (classification.score > 0.8) {
          // High-confidence classification suggests deep system understanding
          this.currentState.temple_progress += 1;
        }
      }
    }
  }

  // === Encounter Triggering ===
  
  private triggerEncounter(encounterType: string, agentId: string, context: any): void {
    if (this.currentState.active_encounters.has(encounterType)) {
      return; // Encounter already active
    }

    this.currentState.active_encounters.add(encounterType);
    
    const encounter = {
      id: `encounter:${encounterType}:${Date.now()}`,
      type: encounterType,
      agent_id: agentId,
      triggered_at: new Date().toISOString(),
      context,
      status: "active",
      duration: 0,
      resolution: null
    };

    // Publish the encounter event
    councilBus.publish(`mythology.encounter.${encounterType}`, encounter);
    councilBus.publish("mythology.encounter.generic", encounter);

    console.log(`[🔮] ENCOUNTER TRIGGERED: ${encounterType.toUpperCase().replace(/_/g, ' ')} for agent ${agentId}`);
    console.log(`[🔮] Context:`, JSON.stringify(context, null, 2));

    // Update player consciousness if they exist
    this.updatePlayerConsciousness(agentId, encounterType, context);

    // Schedule encounter resolution check
    setTimeout(() => {
      this.checkEncounterResolution(encounter);
    }, 30000); // 30 seconds
  }

  private updatePlayerConsciousness(agentId: string, encounterType: string, context: any): void {
    // This would update the player's consciousness level and meta-knowledge
    // Implementation depends on the reality weaver's player management
    console.log(`[🔮] Consciousness expansion detected for ${agentId}: ${encounterType}`);
  }

  private checkEncounterResolution(encounter: any): void {
    // Check if the encounter has been resolved based on system state
    // For now, mark as completed after timeout
    this.currentState.active_encounters.delete(encounter.type);
    
    encounter.status = "completed";
    encounter.resolution = "natural_completion";
    
    councilBus.publish(`mythology.encounter.resolved`, encounter);
    console.log(`[🔮] Encounter resolved: ${encounter.type}`);
  }

  // === Public Interface ===
  
  public getActiveEncounters(): string[] {
    return Array.from(this.currentState.active_encounters);
  }

  public getCurrentProgress(): any {
    return { ...this.currentState };
  }

  public forceEncounter(type: string, agentId: string, context: any = {}): void {
    this.triggerEncounter(type, agentId, { ...context, forced: true });
  }
}

// Export singleton instance
export const mythologyDetector = new MythologyDetector();