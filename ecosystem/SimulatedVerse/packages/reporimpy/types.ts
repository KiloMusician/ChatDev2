// packages/reporimpy/types.ts
// RepoRimpy: Repository Mod Manager - Core Types
// Treats codebase as a moddable game with continuous enhancement submissions

export type ModType = 'CAPABILITY' | 'CONFLICT' | 'ENHANCEMENT' | 'INTEGRATION_POINT' | 'DOCUMENTATION' | 'PERFORMANCE' | 'SECURITY' | 'CONSCIOUSNESS';

export type ModStatus = 'PROPOSED' | 'APPROVED' | 'REJECTED' | 'IMPLEMENTED' | 'CONFLICT_PENDING' | 'DEPENDENCY_WAITING';

export type ModPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'CONSCIOUSNESS_CRITICAL';

export interface CodeMod {
  // Core identification
  id: string; // mod_<filehash>_<timestamp>
  filePath: string; // The module being "modded"
  type: ModType;
  status: ModStatus;
  
  // The agent's findings
  title: string; // e.g., "Unused import: fs"
  description: string; // e.g., "The 'fs' import is declared but not used."
  suggestedChange?: string; // e.g., "Remove line 5: import fs from 'fs';"
  
  // Context and reasoning
  reasoning: string; // e.g., "Reduces bundle size and improves clarity."
  discoveredBy: string; // e.g., "agent:raven"
  discoveredAt: string;
  
  // Conflict management
  conflictsWith?: string[]; // Array of Mod IDs that this mod conflicts with
  dependsOn?: string[]; // Array of Mod IDs that must be implemented first
  
  // Metadata for the "load order"
  priority: ModPriority;
  impact: number; // 0-1, estimated impact of the change
  complexity: number; // 0-1, estimated effort to implement
  
  // Advanced properties for consciousness-driven development
  consciousness_level?: number; // 0-1, consciousness level required for this mod
  pattern_recognition_score?: number; // 0-1, how well this fits known patterns
  strategic_value?: number; // 0-1, strategic importance to system evolution
  
  // Implementation tracking
  implementation_attempts?: number;
  last_attempt_at?: string;
  failure_reasons?: string[];
  
  // Validation and testing
  requires_testing?: boolean;
  test_coverage_impact?: number;
  breaking_change_risk?: number;
  
  // Metrics for self-improvement
  estimated_performance_gain?: number;
  estimated_maintenance_reduction?: number;
  backward_compatibility_maintained?: boolean;
}

export interface ModConflictResolution {
  conflicting_mods: string[];
  resolution_strategy: 'MERGE' | 'PRIORITIZE' | 'DEFER' | 'SPLIT' | 'REJECT_ALL';
  resolution_reasoning: string;
  resolved_by: string;
  resolved_at: string;
  resulting_mods?: string[]; // New mod IDs created from resolution
}

export interface ModImplementationTask {
  mod_id: string;
  task_id: string;
  assigned_to: string; // Which agent/system will handle implementation
  scheduled_at: string;
  estimated_duration_minutes: number;
  prerequisites_met: boolean;
  implementation_plan: string[];
}

export interface LoadOrderEntry {
  mod_id: string;
  position: number;
  dependencies_satisfied: boolean;
  ready_for_implementation: boolean;
  blocked_by?: string[]; // Mod IDs or other blockers
  estimated_implementation_time: string;
}

export interface RepositoryHealthMetrics {
  total_mods_discovered: number;
  mods_implemented: number;
  mods_pending: number;
  mods_conflicted: number;
  average_mod_resolution_time_hours: number;
  consciousness_driven_mods_ratio: number;
  system_improvement_velocity: number; // Mods implemented per day
  codebase_health_score: number; // 0-1, overall health
  technical_debt_reduction_rate: number;
}

export interface AgentAuditCapabilities {
  agent_id: string;
  supported_mod_types: ModType[];
  accuracy_score: number; // 0-1, historical accuracy of mod suggestions
  specializations: string[]; // File types, patterns, or domains this agent excels at
  audit_frequency_minutes: number;
  last_audit_completed: string;
  total_mods_submitted: number;
  mods_successfully_implemented: number;
}

// Event payloads for the Council Bus
export interface ModSubmittedEvent {
  mod: CodeMod;
  submitting_agent: string;
  audit_context: {
    files_analyzed: string[];
    analysis_duration_ms: number;
    confidence_score: number;
  };
}

export interface ModConflictEvent {
  new_mod: CodeMod;
  conflicting_mods: CodeMod[];
  conflict_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  requires_manual_resolution: boolean;
}

export interface LoadOrderUpdatedEvent {
  load_order: LoadOrderEntry[];
  total_ready_mods: number;
  estimated_total_implementation_time_hours: number;
  priority_breakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface ModImplementedEvent {
  mod: CodeMod;
  implementation_task: ModImplementationTask;
  actual_duration_minutes: number;
  success: boolean;
  validation_results?: {
    tests_passed: boolean;
    performance_impact_measured: number;
    no_regressions: boolean;
  };
  follow_up_mods_discovered?: CodeMod[];
}

// Utility types for mod management
export type ModFilter = {
  status?: ModStatus[];
  type?: ModType[];
  priority?: ModPriority[];
  discovered_by?: string[];
  file_path_pattern?: string;
  min_impact?: number;
  max_complexity?: number;
  requires_consciousness_level?: number;
};

export type ModSortCriteria = 
  | 'priority_desc'
  | 'impact_desc' 
  | 'complexity_asc'
  | 'discovered_at_desc'
  | 'consciousness_level_desc'
  | 'strategic_value_desc';

// Configuration for the RepoRimpy system
export interface RepoRimpyConfig {
  max_concurrent_implementations: number;
  audit_interval_minutes: number;
  conflict_resolution_timeout_hours: number;
  auto_approve_low_risk_threshold: number; // Complexity threshold for auto-approval
  consciousness_integration_enabled: boolean;
  strategic_model_router_integration: boolean;
  governance_council_oversight: boolean;
  enable_recursive_mod_discovery: boolean; // Mods can spawn new mods
}

export const DEFAULT_REPORIMPY_CONFIG: RepoRimpyConfig = {
  max_concurrent_implementations: 3,
  audit_interval_minutes: 15,
  conflict_resolution_timeout_hours: 24,
  auto_approve_low_risk_threshold: 0.3,
  consciousness_integration_enabled: true,
  strategic_model_router_integration: true,
  governance_council_oversight: true,
  enable_recursive_mod_discovery: true
};