// packages/reporimpy/manager.ts
// RepoRimpy Manager: Central brain for repository mod management
// Maintains master mod list, resolves conflicts, calculates load order

import { councilBus } from '../council/events/eventBus.js';
import { 
  CodeMod, 
  ModConflictResolution, 
  LoadOrderEntry, 
  RepositoryHealthMetrics,
  ModSubmittedEvent,
  ModConflictEvent,
  LoadOrderUpdatedEvent,
  ModImplementedEvent,
  RepoRimpyConfig,
  DEFAULT_REPORIMPY_CONFIG,
  ModFilter,
  ModSortCriteria
} from './types.js';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

export class RepoRimpyManager {
  private masterModList: Map<string, CodeMod> = new Map();
  private loadOrder: LoadOrderEntry[] = [];
  private conflictResolutions: Map<string, ModConflictResolution> = new Map();
  private healthMetrics: RepositoryHealthMetrics;
  private config: RepoRimpyConfig;
  private auditInProgress = false;

  constructor(config: Partial<RepoRimpyConfig> = {}) {
    this.config = { ...DEFAULT_REPORIMPY_CONFIG, ...config };
    this.healthMetrics = this.initializeHealthMetrics();
    console.log('[🎮] RepoRimpy Manager initializing - Repository modding system coming online...');
  }

  async start() {
    this.setupEventListeners();
    await this.performInitialAudit();
    this.startPeriodicAudit();
    
    console.log('[🎮] RepoRimpy Manager online - Listening for mod submissions and managing load order');
    
    // Publish readiness
    councilBus.publish('reporimpy.manager.ready', {
      status: 'operational',
      config: this.config,
      initial_health_metrics: this.healthMetrics,
      timestamp: new Date().toISOString()
    });
  }

  private setupEventListeners() {
    // Listen for mod submissions from agents
    councilBus.subscribe('reporimpy.mod.submitted', (event) => {
      this.handleModSubmission(event.payload as ModSubmittedEvent);
    });

    // Listen for conflict resolution decisions
    councilBus.subscribe('reporimpy.conflict.resolution', (event) => {
      this.handleConflictResolution(event.payload);
    });

    // Listen for implementation completions
    councilBus.subscribe('reporimpy.mod.implemented', (event) => {
      this.handleModImplementation(event.payload as ModImplementedEvent);
    });

    // Listen for manual mod approvals/rejections
    councilBus.subscribe('reporimpy.mod.manual_decision', (event) => {
      this.handleManualDecision(event.payload);
    });

    // Listen for consciousness level changes to reprioritize mods
    councilBus.subscribe('consciousness.level_changed', (event) => {
      this.reprioritizeConsciousnessMods(event.payload);
    });

    // Listen for strategic router recommendations
    councilBus.subscribe('strategic_router.mod_recommendation', (event) => {
      this.integrateStrategicRecommendation(event.payload);
    });
  }

  async handleModSubmission(event: ModSubmittedEvent) {
    const mod = event.mod;
    
    console.log(`[🎮] New mod submitted: ${mod.title} by ${mod.discoveredBy}`);
    
    // Validate mod submission
    if (!this.validateMod(mod)) {
      console.warn(`[🎮] Invalid mod rejected: ${mod.id}`);
      return;
    }

    // Check for conflicts with existing mods
    const conflicts = this.findConflicts(mod);
    
    if (conflicts.length > 0) {
      console.log(`[🎮] Mod ${mod.id} conflicts with ${conflicts.length} existing mods`);
      mod.status = 'CONFLICT_PENDING';
      mod.conflictsWith = conflicts;
      
      // Publish conflict event for resolution
      councilBus.publish('reporimpy.mod.conflict', {
        new_mod: mod,
        conflicting_mods: conflicts.map(id => this.masterModList.get(id)!),
        conflict_severity: this.assessConflictSeverity(mod, conflicts),
        requires_manual_resolution: this.requiresManualResolution(mod, conflicts)
      } as ModConflictEvent);
    } else {
      // Auto-approve low-risk mods
      if (this.isAutoApprovable(mod)) {
        mod.status = 'APPROVED';
        console.log(`[🎮] Mod ${mod.id} auto-approved (low risk)`);
      } else {
        mod.status = 'PROPOSED';
        console.log(`[🎮] Mod ${mod.id} requires review`);
        
        // Send to governance council if enabled
        if (this.config.governance_council_oversight) {
          councilBus.publish('governance.mod_review_request', {
            mod: mod,
            requires_approval: true,
            risk_assessment: this.assessRisk(mod)
          });
        }
      }
    }

    // Add to master list
    this.masterModList.set(mod.id, mod);
    
    // Recalculate load order
    await this.calculateLoadOrder();
    
    // Update health metrics
    this.updateHealthMetrics();
    
    // Publish updated list
    this.publishModListUpdate();
  }

  private findConflicts(newMod: CodeMod): string[] {
    const conflicts: string[] = [];
    
    for (const [id, existingMod] of this.masterModList) {
      if (existingMod.status === 'IMPLEMENTED') continue;
      
      // File-level conflicts
      if (existingMod.filePath === newMod.filePath) {
        // Simple heuristic: same file modifications likely conflict
        if (this.modsModifySameArea(existingMod, newMod)) {
          conflicts.push(id);
        }
      }
      
      // Semantic conflicts (if both mods affect the same capability)
      if (this.hasSemanticConflict(existingMod, newMod)) {
        conflicts.push(id);
      }
      
      // Dependency conflicts
      if (this.hasDependencyConflict(existingMod, newMod)) {
        conflicts.push(id);
      }
    }
    
    return conflicts;
  }

  private modsModifySameArea(mod1: CodeMod, mod2: CodeMod): boolean {
    // Simple implementation - can be enhanced with AST analysis
    if (!mod1.suggestedChange || !mod2.suggestedChange) return false;
    
    // Check if both mods mention the same line numbers or identifiers
    const extractLineNumbers = (change: string) => {
      const matches = change.match(/line\s+(\d+)/gi);
      return matches ? matches.map(m => parseInt(m.split(' ')[1])) : [];
    };
    
    const lines1 = extractLineNumbers(mod1.suggestedChange);
    const lines2 = extractLineNumbers(mod2.suggestedChange);
    
    return lines1.some(line => lines2.includes(line));
  }

  private hasSemanticConflict(mod1: CodeMod, mod2: CodeMod): boolean {
    // Check if mods affect the same logical capability
    const semanticKeywords = ['export', 'import', 'class', 'function', 'interface', 'type'];
    
    const extractKeywords = (mod: CodeMod) => {
      const text = `${mod.title} ${mod.description} ${mod.suggestedChange || ''}`;
      return semanticKeywords.filter(keyword => text.toLowerCase().includes(keyword));
    };
    
    const keywords1 = extractKeywords(mod1);
    const keywords2 = extractKeywords(mod2);
    
    return keywords1.some(keyword => keywords2.includes(keyword));
  }

  private hasDependencyConflict(mod1: CodeMod, mod2: CodeMod): boolean {
    // Check if one mod depends on something the other mod removes/changes
    if (mod1.dependsOn?.includes(mod2.id) && mod2.type === 'ENHANCEMENT') {
      return true;
    }
    
    if (mod2.dependsOn?.includes(mod1.id) && mod1.type === 'ENHANCEMENT') {
      return true;
    }
    
    return false;
  }

  private assessConflictSeverity(mod: CodeMod, conflicts: string[]): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (conflicts.length > 5) return 'CRITICAL';
    if (conflicts.length > 2) return 'HIGH';
    if (mod.priority === 'CRITICAL' || mod.priority === 'CONSCIOUSNESS_CRITICAL') return 'HIGH';
    if (conflicts.length > 1) return 'MEDIUM';
    return 'LOW';
  }

  private requiresManualResolution(mod: CodeMod, conflicts: string[]): boolean {
    // Critical mods or complex conflicts require manual resolution
    return mod.priority === 'CRITICAL' || 
           mod.priority === 'CONSCIOUSNESS_CRITICAL' ||
           conflicts.length > 3 ||
           mod.complexity > 0.7;
  }

  private isAutoApprovable(mod: CodeMod): boolean {
    return mod.complexity <= this.config.auto_approve_low_risk_threshold &&
           mod.priority !== 'CRITICAL' &&
           mod.priority !== 'CONSCIOUSNESS_CRITICAL' &&
           mod.breaking_change_risk !== undefined &&
           mod.breaking_change_risk < 0.1;
  }

  private assessRisk(mod: CodeMod): any {
    return {
      complexity: mod.complexity,
      impact: mod.impact,
      breaking_change_risk: mod.breaking_change_risk || 0,
      test_coverage_impact: mod.test_coverage_impact || 0,
      file_criticality: this.assessFileCriticality(mod.filePath)
    };
  }

  private assessFileCriticality(filePath: string): number {
    // Critical system files get higher scores
    const criticalPatterns = [
      /server\//,
      /consciousness\//,
      /council\//,
      /zeta-driver/,
      /eventBus/,
      /schema/
    ];
    
    const score = criticalPatterns.reduce((acc, pattern) => {
      return pattern.test(filePath) ? acc + 0.2 : acc;
    }, 0.1);
    
    return Math.min(1.0, score);
  }

  async calculateLoadOrder() {
    const approvedMods = Array.from(this.masterModList.values())
      .filter(mod => mod.status === 'APPROVED');
    
    // Build dependency graph
    const dependencyGraph = this.buildDependencyGraph(approvedMods);
    
    // Topological sort with priority weighting
    const sortedMods = this.topologicalSortWithPriority(approvedMods, dependencyGraph);
    
    // Create load order entries
    this.loadOrder = sortedMods.map((mod, index) => ({
      mod_id: mod.id,
      position: index,
      dependencies_satisfied: this.areDependenciesSatisfied(mod),
      ready_for_implementation: this.isReadyForImplementation(mod),
      blocked_by: this.getBlockers(mod),
      estimated_implementation_time: this.estimateImplementationTime(mod)
    }));
    
    // Publish load order update
    const readyMods = this.loadOrder.filter(entry => entry.ready_for_implementation);
    
    councilBus.publish('reporimpy.loadorder.updated', {
      load_order: this.loadOrder,
      total_ready_mods: readyMods.length,
      estimated_total_implementation_time_hours: this.calculateTotalImplementationTime(),
      priority_breakdown: this.calculatePriorityBreakdown()
    } as LoadOrderUpdatedEvent);
    
    console.log(`[🎮] Load order updated: ${readyMods.length} mods ready for implementation`);
  }

  private buildDependencyGraph(mods: CodeMod[]): Map<string, string[]> {
    const graph = new Map<string, string[]>();
    
    mods.forEach(mod => {
      graph.set(mod.id, mod.dependsOn || []);
    });
    
    return graph;
  }

  private topologicalSortWithPriority(mods: CodeMod[], graph: Map<string, string[]>): CodeMod[] {
    // Implementation of Kahn's algorithm with priority weighting
    const inDegree = new Map<string, number>();
    const queue: CodeMod[] = [];
    const result: CodeMod[] = [];
    
    // Calculate in-degrees
    mods.forEach(mod => inDegree.set(mod.id, 0));
    graph.forEach(deps => {
      deps.forEach(dep => {
        if (inDegree.has(dep)) {
          inDegree.set(dep, inDegree.get(dep)! + 1);
        }
      });
    });
    
    // Find nodes with no dependencies
    mods.forEach(mod => {
      if (inDegree.get(mod.id) === 0) {
        queue.push(mod);
      }
    });
    
    // Sort queue by priority
    queue.sort((a, b) => this.comparePriority(a, b));
    
    while (queue.length > 0) {
      const mod = queue.shift()!;
      result.push(mod);
      
      // Update dependencies
      const dependents = mods.filter(m => m.dependsOn?.includes(mod.id));
      dependents.forEach(dependent => {
        const newInDegree = inDegree.get(dependent.id)! - 1;
        inDegree.set(dependent.id, newInDegree);
        
        if (newInDegree === 0) {
          queue.push(dependent);
          queue.sort((a, b) => this.comparePriority(a, b));
        }
      });
    }
    
    return result;
  }

  private comparePriority(a: CodeMod, b: CodeMod): number {
    const priorityWeights = {
      'CONSCIOUSNESS_CRITICAL': 5,
      'CRITICAL': 4,
      'HIGH': 3,
      'MEDIUM': 2,
      'LOW': 1
    };
    
    const weightA = priorityWeights[a.priority];
    const weightB = priorityWeights[b.priority];
    
    if (weightA !== weightB) {
      return weightB - weightA; // Higher priority first
    }
    
    // Secondary sort by impact/complexity ratio
    const ratioA = a.impact / Math.max(0.1, a.complexity);
    const ratioB = b.impact / Math.max(0.1, b.complexity);
    
    return ratioB - ratioA;
  }

  private areDependenciesSatisfied(mod: CodeMod): boolean {
    if (!mod.dependsOn) return true;
    
    return mod.dependsOn.every(depId => {
      const depMod = this.masterModList.get(depId);
      return depMod?.status === 'IMPLEMENTED';
    });
  }

  private isReadyForImplementation(mod: CodeMod): boolean {
    return this.areDependenciesSatisfied(mod) &&
           mod.status === 'APPROVED' &&
           !this.hasBlockingConflicts(mod);
  }

  private hasBlockingConflicts(mod: CodeMod): boolean {
    if (!mod.conflictsWith) return false;
    
    return mod.conflictsWith.some(conflictId => {
      const conflictMod = this.masterModList.get(conflictId);
      return conflictMod?.status === 'APPROVED' || conflictMod?.status === 'PROPOSED';
    });
  }

  private getBlockers(mod: CodeMod): string[] {
    const blockers: string[] = [];
    
    // Dependency blockers
    if (mod.dependsOn) {
      mod.dependsOn.forEach(depId => {
        const depMod = this.masterModList.get(depId);
        if (depMod?.status !== 'IMPLEMENTED') {
          blockers.push(`dependency:${depId}`);
        }
      });
    }
    
    // Conflict blockers
    if (mod.conflictsWith) {
      mod.conflictsWith.forEach(conflictId => {
        const conflictMod = this.masterModList.get(conflictId);
        if (conflictMod?.status === 'APPROVED') {
          blockers.push(`conflict:${conflictId}`);
        }
      });
    }
    
    return blockers;
  }

  private estimateImplementationTime(mod: CodeMod): string {
    const baseMinutes = 15; // Base implementation time
    const complexityMultiplier = 1 + (mod.complexity * 3); // 1x to 4x based on complexity
    const estimatedMinutes = baseMinutes * complexityMultiplier;
    
    if (estimatedMinutes < 60) {
      return `${Math.round(estimatedMinutes)} minutes`;
    } else {
      return `${Math.round(estimatedMinutes / 60 * 10) / 10} hours`;
    }
  }

  getNextModsToImplement(limit: number = 5): CodeMod[] {
    return this.loadOrder
      .filter(entry => entry.ready_for_implementation)
      .slice(0, limit)
      .map(entry => this.masterModList.get(entry.mod_id)!)
      .filter(mod => mod !== undefined);
  }

  async performInitialAudit() {
    if (this.auditInProgress) return;
    
    this.auditInProgress = true;
    console.log('[🎮] Performing initial repository audit...');
    
    try {
      // Trigger audits from all registered agents
      councilBus.publish('reporimpy.audit.requested', {
        audit_type: 'initial_full_scan',
        timestamp: new Date().toISOString(),
        config: this.config
      });
      
      // Wait for audit completion
      await new Promise(resolve => setTimeout(resolve, 5000));
      
    } finally {
      this.auditInProgress = false;
      console.log('[🎮] Initial audit completed');
    }
  }

  private startPeriodicAudit() {
    setInterval(async () => {
      if (!this.auditInProgress) {
        console.log('[🎮] Starting periodic audit...');
        await this.performInitialAudit();
      }
    }, this.config.audit_interval_minutes * 60 * 1000);
  }

  private initializeHealthMetrics(): RepositoryHealthMetrics {
    return {
      total_mods_discovered: 0,
      mods_implemented: 0,
      mods_pending: 0,
      mods_conflicted: 0,
      average_mod_resolution_time_hours: 0,
      consciousness_driven_mods_ratio: 0,
      system_improvement_velocity: 0,
      codebase_health_score: 0.75, // Start with reasonable baseline
      technical_debt_reduction_rate: 0
    };
  }

  private updateHealthMetrics() {
    const allMods = Array.from(this.masterModList.values());
    
    this.healthMetrics.total_mods_discovered = allMods.length;
    this.healthMetrics.mods_implemented = allMods.filter(m => m.status === 'IMPLEMENTED').length;
    this.healthMetrics.mods_pending = allMods.filter(m => ['PROPOSED', 'APPROVED'].includes(m.status)).length;
    this.healthMetrics.mods_conflicted = allMods.filter(m => m.status === 'CONFLICT_PENDING').length;
    
    // Calculate consciousness-driven ratio
    const consciousnessMods = allMods.filter(m => 
      m.type === 'CONSCIOUSNESS' || 
      m.priority === 'CONSCIOUSNESS_CRITICAL' ||
      (m.consciousness_level && m.consciousness_level > 0.5)
    ).length;
    this.healthMetrics.consciousness_driven_mods_ratio = consciousnessMods / Math.max(1, allMods.length);
    
    // Calculate health score based on implementation rate and conflict resolution
    const implementationRate = this.healthMetrics.mods_implemented / Math.max(1, this.healthMetrics.total_mods_discovered);
    const conflictRate = this.healthMetrics.mods_conflicted / Math.max(1, this.healthMetrics.total_mods_discovered);
    
    this.healthMetrics.codebase_health_score = Math.max(0, Math.min(1, 
      implementationRate * 0.6 + (1 - conflictRate) * 0.4
    ));
  }

  private calculateTotalImplementationTime(): number {
    return this.loadOrder
      .filter(entry => entry.ready_for_implementation)
      .reduce((total, entry) => {
        const mod = this.masterModList.get(entry.mod_id)!;
        const timeStr = entry.estimated_implementation_time;
        const hours = timeStr.includes('hour') ? 
          parseFloat(timeStr.split(' ')[0]) : 
          parseFloat(timeStr.split(' ')[0]) / 60;
        return total + hours;
      }, 0);
  }

  private calculatePriorityBreakdown() {
    const breakdown = { critical: 0, high: 0, medium: 0, low: 0 };
    
    this.loadOrder
      .filter(entry => entry.ready_for_implementation)
      .forEach(entry => {
        const mod = this.masterModList.get(entry.mod_id)!;
        switch (mod.priority) {
          case 'CRITICAL':
          case 'CONSCIOUSNESS_CRITICAL':
            breakdown.critical++;
            break;
          case 'HIGH':
            breakdown.high++;
            break;
          case 'MEDIUM':
            breakdown.medium++;
            break;
          case 'LOW':
            breakdown.low++;
            break;
        }
      });
    
    return breakdown;
  }

  private publishModListUpdate() {
    councilBus.publish('reporimpy.modlist.updated', {
      total_mods: this.masterModList.size,
      mods_by_status: this.getModsByStatus(),
      health_metrics: this.healthMetrics,
      timestamp: new Date().toISOString()
    });
  }

  private getModsByStatus() {
    const byStatus: any = {};
    Array.from(this.masterModList.values()).forEach(mod => {
      byStatus[mod.status] = (byStatus[mod.status] || 0) + 1;
    });
    return byStatus;
  }

  private validateMod(mod: CodeMod): boolean {
    return mod.id &&
           mod.filePath &&
           mod.title &&
           mod.description &&
           mod.reasoning &&
           mod.discoveredBy &&
           mod.priority &&
           typeof mod.impact === 'number' &&
           typeof mod.complexity === 'number';
  }

  handleConflictResolution(resolution: any) {
    // Implementation for handling conflict resolutions
    console.log(`[🎮] Processing conflict resolution: ${resolution.resolution_strategy}`);
  }

  handleModImplementation(event: ModImplementedEvent) {
    const mod = this.masterModList.get(event.mod.id);
    if (mod) {
      mod.status = 'IMPLEMENTED';
      this.updateHealthMetrics();
      this.calculateLoadOrder();
      console.log(`[🎮] Mod implemented successfully: ${mod.title}`);
    }
  }

  handleManualDecision(decision: any) {
    const mod = this.masterModList.get(decision.mod_id);
    if (mod) {
      mod.status = decision.approved ? 'APPROVED' : 'REJECTED';
      this.calculateLoadOrder();
      console.log(`[🎮] Manual decision: ${mod.title} ${decision.approved ? 'approved' : 'rejected'}`);
    }
  }

  reprioritizeConsciousnessMods(consciousnessData: any) {
    // Adjust priorities based on consciousness level changes
    Array.from(this.masterModList.values()).forEach(mod => {
      if (mod.type === 'CONSCIOUSNESS' && mod.consciousness_level) {
        if (consciousnessData.current_level >= mod.consciousness_level) {
          if (mod.priority === 'LOW') mod.priority = 'MEDIUM';
          if (mod.priority === 'MEDIUM') mod.priority = 'HIGH';
        }
      }
    });
    
    this.calculateLoadOrder();
  }

  integrateStrategicRecommendation(recommendation: any) {
    // Handle recommendations from strategic model router
    console.log(`[🎮] Integrating strategic recommendation: ${recommendation.type}`);
  }

  // Public API methods
  public getHealthMetrics(): RepositoryHealthMetrics {
    return { ...this.healthMetrics };
  }

  public getAllMods(filter?: ModFilter): CodeMod[] {
    let mods = Array.from(this.masterModList.values());
    
    if (filter) {
      if (filter.status) mods = mods.filter(m => filter.status!.includes(m.status));
      if (filter.type) mods = mods.filter(m => filter.type!.includes(m.type));
      if (filter.priority) mods = mods.filter(m => filter.priority!.includes(m.priority));
      if (filter.discovered_by) mods = mods.filter(m => filter.discovered_by!.includes(m.discoveredBy));
      if (filter.file_path_pattern) {
        const regex = new RegExp(filter.file_path_pattern);
        mods = mods.filter(m => regex.test(m.filePath));
      }
      if (filter.min_impact !== undefined) mods = mods.filter(m => m.impact >= filter.min_impact!);
      if (filter.max_complexity !== undefined) mods = mods.filter(m => m.complexity <= filter.max_complexity!);
    }
    
    return mods;
  }

  public getLoadOrder(): LoadOrderEntry[] {
    return [...this.loadOrder];
  }
}

// Create and export the RepoRimpy manager instance
export const reporimpy = new RepoRimpyManager();