#!/usr/bin/env tsx
/**
 * ΞNuSyQ Marble Factory Contextual Intelligence Engine
 * 
 * Implements nuanced, intelligent system status reporting that replaces
 * rigid binary "working/not-working" with contextual awareness and 
 * sophisticated understanding of system states, edge cases, and 
 * operational contexts.
 * 
 * This is the core of self-aware organism diagnostics.
 */

import { EventEmitter } from 'node:events';
import { promises as fs } from 'node:fs';
import { resolve } from 'node:path';
import type { Express } from 'express';

export interface SystemVector {
  // Core organism vitals
  consciousness: number;
  energy: number;
  population: number;
  research: number;
  
  // Operational health dimensions
  frontend_coherence: number;  // 0-1, UI consistency and responsiveness
  backend_stability: number;   // 0-1, API and core services health
  integration_flow: number;    // 0-1, inter-system communication quality
  cultivation_momentum: number; // 0-1, development and evolution velocity
  
  // Context intelligence
  noise_to_signal_ratio: number;   // Lower is better
  architectural_debt: number;      // Technical debt accumulation
  autonomous_capability: number;   // Self-healing and adaptation capacity
  
  // Environmental awareness
  llm_availability: 'offline' | 'local' | 'cloud' | 'hybrid';
  budget_constraint: 'critical' | 'limited' | 'moderate' | 'abundant';
  development_mode: 'emergency' | 'maintenance' | 'growth' | 'exploration';
}

export interface ContextualInsight {
  priority: 'critical' | 'important' | 'moderate' | 'low' | 'informational';
  category: 'system' | 'game' | 'development' | 'infrastructure' | 'user_experience';
  message: string;
  actionable: boolean;
  relevant_systems: string[];
  contextual_markers: string[];
  suppression_score: number; // How much noise this represents (higher = more noise)
}

export interface MarbleFactoryState {
  timestamp: number;
  system_vector: SystemVector;
  insights: ContextualInsight[];
  operational_summary: string;
  recommended_focus: string[];
  self_healing_actions: string[];
  cultivation_opportunities: string[];
}

export class MarbleFactoryIntelligence extends EventEmitter {
  private state: MarbleFactoryState | null = null;
  private lastUpdate: number = 0;
  private readonly updateInterval = 5000; // 5 seconds
  private suppressedPatterns: Set<string> = new Set();
  
  constructor() {
    super();
    this.initializeSuppressionPatterns();
    this.startIntelligenceLoop();
  }
  
  private initializeSuppressionPatterns() {
    // Suppress known noise patterns
    this.suppressedPatterns.add('Cannot load.*dependencies not met');
    this.suppressedPatterns.add('Ollama failed.*fetch failed');
    this.suppressedPatterns.add('OpenAI API error: 429');
    this.suppressedPatterns.add('Agent.*completed MAINTAIN_COLONY');
    this.suppressedPatterns.add('mysterious_biomass_detected');
    this.suppressedPatterns.add('ancient_ruins_found');
    this.suppressedPatterns.add('energy_anomaly_discovered');
    this.suppressedPatterns.add('hostile_scouts_approaching');
    this.suppressedPatterns.add('Random encounter:');
  }
  
  private startIntelligenceLoop() {
    // Replace theater messages with intelligent contextual analysis
    setInterval(() => {
      this.analyzeSystemState();
    }, 10000); // Every 10 seconds - less frequent, more meaningful
  }
  
  private async analyzeSystemState() {
    try {
      const apiBase = this.getApiBaseUrl();
      // Get real system state from multiple sources
      const [colonyResponse, healthResponse] = await Promise.all([
        fetch(`${apiBase}/api/colony`).then(r => r.json()),
        fetch(`${apiBase}/api/health`).then(r => r.json())
      ]);
      
      if (colonyResponse.success) {
        const insights = this.generateIntelligentInsights(colonyResponse.data, healthResponse);
        if (insights.length > 0) {
          console.log(`[🧠] Intelligence: ${insights.join(' | ')}`);
        }
      }
    } catch (error) {
      // Fail silently - intelligence is supplementary
    }
  }
  
  private generateIntelligentInsights(colony: any, health: any): string[] {
    const insights: string[] = [];
    
    // Energy analysis
    if (colony.resources.energy < 50) {
      insights.push(`Energy critical (${colony.resources.energy}) - recommend power optimization`);
    } else if (colony.resources.energy > 200) {
      insights.push(`Energy surplus (${colony.resources.energy}) - ready for expansion projects`);
    }
    
    // Research opportunities
    if (colony.resources.research > colony.tier * 100) {
      insights.push(`Research threshold reached - tier ${colony.tier + 1} upgrade available`);
    }
    
    // Population dynamics
    if (colony.resources.population > colony.structures.length * 10) {
      insights.push(`Population density high - infrastructure expansion needed`);
    }
    
    // System health context
    if (health && health.llm_status === 'offline') {
      insights.push(`LLM offline - operating in autonomous mode with ${colony.structures.length} automated systems`);
    }
    
    return insights;
  }
  
  /**
   * Calculate comprehensive system vector from multiple data sources
   */
  async calculateSystemVector(): Promise<SystemVector> {
    try {
      // Fetch core game state
      const apiBase = this.getApiBaseUrl();
      const gameResponse = await fetch(`${apiBase}/api/colony`);
      const gameData = await gameResponse.json();

      const [
        frontend_coherence,
        backend_stability,
        integration_flow,
        cultivation_momentum,
        noise_to_signal_ratio,
        architectural_debt,
        autonomous_capability,
        llm_availability,
        budget_constraint
      ] = await Promise.all([
        this.assessFrontendCoherence(),
        this.assessBackendStability(),
        this.assessIntegrationFlow(),
        this.assessCultivationMomentum(),
        this.calculateNoiseRatio(),
        this.assessArchitecturalDebt(),
        this.assessAutonomousCapability(),
        this.assessLLMAvailability(),
        this.assessBudgetConstraint()
      ]);

      const development_mode = await this.determineDevelopmentMode({
        frontend_coherence,
        backend_stability,
        integration_flow,
        cultivation_momentum,
        noise_to_signal_ratio,
        architectural_debt,
        autonomous_capability,
        llm_availability,
        budget_constraint
      });

      return {
        consciousness: gameData.data?.consciousness || 0,
        energy: gameData.data?.resources?.energy || 0,
        population: gameData.data?.resources?.population || 0,
        research: gameData.data?.resources?.research || 0,
        frontend_coherence,
        backend_stability,
        integration_flow,
        cultivation_momentum,
        noise_to_signal_ratio,
        architectural_debt,
        autonomous_capability,
        llm_availability,
        budget_constraint,
        development_mode
      };
      
    } catch (error) {
      console.error('[MARBLE_FACTORY] Error calculating system vector:', error);
      return {
        consciousness: 0,
        energy: 0,
        population: 0,
        research: 0,
        frontend_coherence: 0.1,
        backend_stability: 0.1,
        integration_flow: 0.1,
        cultivation_momentum: 0.1,
        noise_to_signal_ratio: 1.0,
        architectural_debt: 0.9,
        autonomous_capability: 0.1,
        llm_availability: 'offline',
        budget_constraint: 'critical',
        development_mode: 'emergency'
      };
    }
  }
  
  private async assessFrontendCoherence(): Promise<number> {
    const [freshness, status, buildStatus] = await Promise.all([
      this.readJsonFile<{
        stale?: boolean;
        action_needed?: boolean;
        skew_s?: number;
        threshold_s?: number;
      }>('reports/ui_freshness.json'),
      this.readJsonFile<{ status?: string; age_s?: number }>('reports/ui_status.json'),
      this.readJsonFile<{ build_fresh?: boolean }>('reports/ui_build_status.json')
    ]);

    let score = 0.5;

    if (freshness) {
      if (freshness.stale) {
        score -= 0.25;
      } else {
        score += 0.2;
      }

      if (freshness.action_needed) {
        score -= 0.15;
      }

      if (typeof freshness.skew_s === 'number' && typeof freshness.threshold_s === 'number') {
        if (freshness.skew_s > freshness.threshold_s * 2) {
          score -= 0.1;
        }
      }
    }

    if (status) {
      if (status.status === 'refreshed') {
        score += 0.2;
      } else if (status.status === 'stale') {
        score -= 0.2;
      }

      if (typeof status.age_s === 'number') {
        if (status.age_s < 120) {
          score += 0.1;
        } else if (status.age_s > 600) {
          score -= 0.1;
        }
      }
    }

    if (buildStatus) {
      if (buildStatus.build_fresh === true) {
        score += 0.2;
      } else if (buildStatus.build_fresh === false) {
        score -= 0.2;
      }
    }

    return this.clamp(score, 0.05, 0.98);
  }
  
  private async assessBackendStability(): Promise<number> {
    try {
      const startTime = Date.now();
      const response = await fetch('http://127.0.0.1:5000/api/colony', { 
        timeout: 2000 
      } as any);
      const responseTime = Date.now() - startTime;
      
      if (response.ok && responseTime < 500) {
        return 0.95; // High stability - fast, successful response
      } else if (response.ok && responseTime < 2000) {
        return 0.75; // Moderate stability - slow but working
      } else {
        return 0.4; // Low stability - errors or very slow
      }
    } catch (error) {
      return 0.1; // Very low stability - system unreachable
    }
  }
  
  private async assessIntegrationFlow(): Promise<number> {
    const [queueMetrics, ledgerTail] = await Promise.all([
      this.readJsonFile<{
        status?: string;
        completed?: number;
        failed?: number;
        requeued?: number;
      }>('reports/queue_metrics.json'),
      this.readNdjsonTail<{ ok?: boolean }>('reports/run_ledger.ndjson')
    ]);

    let score = 0.5;

    if (queueMetrics) {
      if (typeof queueMetrics.completed === 'number' && queueMetrics.completed > 0) {
        score += 0.2;
      }

      if (typeof queueMetrics.failed === 'number' && queueMetrics.failed > 0) {
        score -= 0.25;
      }

      if (typeof queueMetrics.requeued === 'number' && queueMetrics.requeued > 0) {
        score -= 0.1;
      }

      if (queueMetrics.status && queueMetrics.status !== 'healthy') {
        score -= 0.2;
      }
    }

    if (ledgerTail) {
      if (ledgerTail.ok === true) {
        score += 0.1;
      } else if (ledgerTail.ok === false) {
        score -= 0.15;
      }
    }

    return this.clamp(score, 0.05, 0.95);
  }
  
  private async assessCultivationMomentum(): Promise<number> {
    const [productivity, repoGrowth] = await Promise.all([
      this.readJsonFile<{
        agent_artifacts_per_hour?: number;
        total_agents_active?: number;
        coordination_efficiency?: number;
        real_work_ratio?: number;
        theater_elimination_progress?: number;
      }>('reports/agent_productivity.json'),
      this.readJsonFile<{ alert?: string; perMin?: number }>('reports/repo_growth.json')
    ]);

    let score = 0.35;

    if (productivity) {
      if (typeof productivity.agent_artifacts_per_hour === 'number') {
        score += Math.min(0.25, (productivity.agent_artifacts_per_hour / 5) * 0.25);
      }

      if (typeof productivity.coordination_efficiency === 'number') {
        score += (productivity.coordination_efficiency - 0.5) * 0.3;
      }

      if (typeof productivity.real_work_ratio === 'number') {
        score += (productivity.real_work_ratio - 0.6) * 0.4;
      }

      if (typeof productivity.total_agents_active === 'number') {
        score += Math.min(0.1, (productivity.total_agents_active / 10) * 0.1);
      }

      if (typeof productivity.theater_elimination_progress === 'number') {
        score += (productivity.theater_elimination_progress - 0.3) * 0.2;
      }
    }

    if (repoGrowth) {
      if (repoGrowth.alert === 'ok') {
        score += 0.1;
      }

      if (typeof repoGrowth.perMin === 'number') {
        score += Math.min(0.1, (repoGrowth.perMin / 2) * 0.1);
      }
    }

    return this.clamp(score, 0.05, 0.95);
  }
  
  private async calculateNoiseRatio(): Promise<number> {
    const [placeholders, repoAudit, lspDiagnostics] = await Promise.all([
      this.readJsonFile<{
        placeholder_count?: number;
        todo_count?: number;
        hardcoded_errors?: number;
        theater_score?: number;
      }>('reports/placeholder_scan.json'),
      this.readJsonFile<{ exactDupGroups?: number; nearDupPairs?: number }>('reports/repo_audit.summary.json'),
      this.readJsonFile<{ diagnostics?: number }>('reports/lsp_diagnostics.json')
    ]);

    let ratio = 0.4;

    if (placeholders) {
      const placeholderTotal =
        (placeholders.placeholder_count ?? 0) +
        (placeholders.todo_count ?? 0) +
        (placeholders.hardcoded_errors ?? 0);
      ratio = Math.max(ratio, placeholderTotal / 10000);

      if (placeholders.theater_score === 1) {
        ratio += 0.1;
      }
    }

    if (repoAudit) {
      const dupWeight = (repoAudit.exactDupGroups ?? 0) + (repoAudit.nearDupPairs ?? 0);
      ratio += Math.min(0.15, dupWeight / 5000);
    }

    if (lspDiagnostics && typeof lspDiagnostics.diagnostics === 'number') {
      if (lspDiagnostics.diagnostics === 0) {
        ratio -= 0.15;
      } else {
        ratio += Math.min(0.2, lspDiagnostics.diagnostics / 1000);
      }
    }

    return this.clamp(ratio, 0.05, 0.98);
  }
  
  private async assessArchitecturalDebt(): Promise<number> {
    const [repoAudit, placeholders, lspDiagnostics] = await Promise.all([
      this.readJsonFile<{
        exactDupGroups?: number;
        nearDupPairs?: number;
        spamCandidates?: number;
      }>('reports/repo_audit.summary.json'),
      this.readJsonFile<{
        placeholder_count?: number;
        hardcoded_errors?: number;
      }>('reports/placeholder_scan.json'),
      this.readJsonFile<{ diagnostics?: number }>('reports/lsp_diagnostics.json')
    ]);

    let debt = 0.3;

    if (repoAudit) {
      const dupScore =
        (repoAudit.exactDupGroups ?? 0) * 2 +
        (repoAudit.nearDupPairs ?? 0) +
        (repoAudit.spamCandidates ?? 0);
      debt += Math.min(0.5, dupScore / 6000);
    }

    if (placeholders) {
      debt += Math.min(0.3, (placeholders.hardcoded_errors ?? 0) / 2000);
      debt += Math.min(0.2, (placeholders.placeholder_count ?? 0) / 15000);
    }

    if (lspDiagnostics && typeof lspDiagnostics.diagnostics === 'number') {
      if (lspDiagnostics.diagnostics > 0) {
        debt += Math.min(0.2, lspDiagnostics.diagnostics / 2000);
      }
    }

    return this.clamp(debt, 0.05, 0.98);
  }
  
  private async assessAutonomousCapability(): Promise<number> {
    const [productivity, health] = await Promise.all([
      this.readJsonFile<{
        coordination_efficiency?: number;
        real_work_ratio?: number;
        total_agents_active?: number;
      }>('reports/agent_productivity.json'),
      this.readJsonFile<{
        errors?: { count?: number; critical?: number };
        llm?: { gateway_up?: boolean };
      }>('reports/sage_health.json')
    ]);

    let score = 0.35;

    if (productivity) {
      if (typeof productivity.real_work_ratio === 'number') {
        score += (productivity.real_work_ratio - 0.55) * 0.5;
      }

      if (typeof productivity.coordination_efficiency === 'number') {
        score += (productivity.coordination_efficiency - 0.5) * 0.3;
      }

      if (typeof productivity.total_agents_active === 'number') {
        score += Math.min(0.1, (productivity.total_agents_active / 8) * 0.1);
      }
    }

    if (health?.errors) {
      if ((health.errors.critical ?? 0) === 0) {
        score += 0.1;
      }

      if ((health.errors.count ?? 0) > 0) {
        score -= 0.1;
      }
    }

    if (health?.llm && health.llm.gateway_up === true) {
      score += 0.05;
    }

    return this.clamp(score, 0.05, 0.95);
  }
  
  private async assessLLMAvailability(): Promise<SystemVector['llm_availability']> {
    const [health, failures, llmHealth] = await Promise.all([
      this.readJsonFile<{
        llm?: { ollama?: boolean; openai?: boolean; gateway_up?: boolean };
      }>('reports/sage_health.json'),
      this.readJsonFile<{
        backends?: {
          ollama?: { status?: string };
          openai?: { status?: string };
          gateway?: { status?: string };
        };
      }>('reports/llm_failures.json'),
      this.readJsonFile<{ backend?: string; status?: string }>('reports/llm_health.json')
    ]);

    const ollamaUp = health?.llm?.ollama === true;
    const openaiUp = health?.llm?.openai === true;

    if (ollamaUp && openaiUp) {
      return 'hybrid';
    }

    if (ollamaUp) {
      return 'local';
    }

    if (openaiUp) {
      return 'cloud';
    }

    if (failures?.backends?.ollama?.status && failures.backends.ollama.status !== 'unreachable') {
      return 'local';
    }

    if (failures?.backends?.openai?.status && failures.backends.openai.status !== 'rate_limited') {
      return 'cloud';
    }

    if (llmHealth?.backend === 'openai' && llmHealth.status && !llmHealth.status.includes('offline')) {
      return 'cloud';
    }

    if (health?.llm?.gateway_up) {
      return 'cloud';
    }

    return 'offline';
  }
  
  private async assessBudgetConstraint(): Promise<SystemVector['budget_constraint']> {
    const [health, failures, llmHealth] = await Promise.all([
      this.readJsonFile<{
        llm?: { ollama?: boolean; openai?: boolean; gateway_up?: boolean };
      }>('reports/sage_health.json'),
      this.readJsonFile<{
        backends?: {
          ollama?: { status?: string };
          openai?: { status?: string };
          gateway?: { status?: string };
        };
      }>('reports/llm_failures.json'),
      this.readJsonFile<{ status?: string }>('reports/llm_health.json')
    ]);

    const ollamaUp = health?.llm?.ollama === true;
    const openaiUp = health?.llm?.openai === true;
    const gatewayUp = health?.llm?.gateway_up === true;

    if (ollamaUp && openaiUp) {
      return 'abundant';
    }

    if (openaiUp || ollamaUp) {
      return 'moderate';
    }

    if (llmHealth?.status && llmHealth.status.includes('fallback')) {
      return 'limited';
    }

    if (failures?.backends?.openai?.status === 'rate_limited') {
      return gatewayUp ? 'limited' : 'critical';
    }

    if (failures?.backends?.ollama?.status === 'unreachable') {
      return gatewayUp ? 'limited' : 'critical';
    }

    if (gatewayUp) {
      return 'limited';
    }

    return 'critical';
  }
  
  private async determineDevelopmentMode(
    vector: Pick<
      SystemVector,
      | 'frontend_coherence'
      | 'backend_stability'
      | 'integration_flow'
      | 'cultivation_momentum'
      | 'noise_to_signal_ratio'
      | 'architectural_debt'
      | 'autonomous_capability'
      | 'llm_availability'
      | 'budget_constraint'
    >
  ): Promise<SystemVector['development_mode']> {
    if (vector.backend_stability < 0.3 || vector.frontend_coherence < 0.3) {
      return 'emergency';
    }

    if (vector.noise_to_signal_ratio > 0.7 || vector.architectural_debt > 0.7) {
      return 'maintenance';
    }

    if (vector.cultivation_momentum > 0.7 && vector.integration_flow > 0.7) {
      return 'growth';
    }

    if (vector.autonomous_capability > 0.6 && vector.llm_availability !== 'offline') {
      return 'exploration';
    }

    return 'maintenance';
  }

  private getApiBaseUrl(): string {
    return process.env.API_BASE_URL ?? 'http://127.0.0.1:5000';
  }

  private reportPath(relativePath: string): string {
    return resolve(process.cwd(), relativePath);
  }

  private async readJsonFile<T>(relativePath: string): Promise<T | null> {
    try {
      const data = await fs.readFile(this.reportPath(relativePath), 'utf8');
      return JSON.parse(data) as T;
    } catch {
      return null;
    }
  }

  private async readNdjsonTail<T>(relativePath: string, maxLines = 50): Promise<T | null> {
    try {
      const data = await fs.readFile(this.reportPath(relativePath), 'utf8');
      const lines = data.trim().split(/\r?\n/);

      for (let index = lines.length - 1; index >= 0 && index >= lines.length - maxLines; index -= 1) {
        const line = lines[index];
        if (typeof line !== 'string') {
          continue;
        }

        const trimmed = line.trim();
        if (!trimmed) {
          continue;
        }
        
        try {
          return JSON.parse(trimmed) as T;
        } catch {
          continue;
        }
      }

      return null;
    } catch {
      return null;
    }
  }

  private clamp(value: number, min = 0, max = 1): number {
    return Math.min(max, Math.max(min, value));
  }
  
  private getEmergencyFallbackVector(): SystemVector {
    return {
      consciousness: 0,
      energy: 0,
      population: 0,
      research: 0,
      frontend_coherence: 0.1,
      backend_stability: 0.1,
      integration_flow: 0.1,
      cultivation_momentum: 0.1,
      noise_to_signal_ratio: 0.9,
      architectural_debt: 0.9,
      autonomous_capability: 0.1,
      llm_availability: 'offline',
      budget_constraint: 'critical',
      development_mode: 'emergency'
    };
  }
  
  /**
   * Generate contextual insights based on system vector
   */
  generateContextualInsights(vector: SystemVector): ContextualInsight[] {
    const insights: ContextualInsight[] = [];
    
    // High consciousness but low frontend coherence = Backend working, UI issues
    if (vector.consciousness > 10 && vector.frontend_coherence < 0.5) {
      insights.push({
        priority: 'important',
        category: 'system',
        message: `Consciousness high (${vector.consciousness.toFixed(1)}) but frontend unstable - backend systems functional, UI needs attention`,
        actionable: true,
        relevant_systems: ['frontend', 'build_system'],
        contextual_markers: ['backend_healthy', 'ui_reload_loops'],
        suppression_score: 0.1
      });
    }
    
    // High noise ratio = System generating too much irrelevant output
    if (vector.noise_to_signal_ratio > 0.7) {
      insights.push({
        priority: 'moderate',
        category: 'development',
        message: `High noise-to-signal ratio (${(vector.noise_to_signal_ratio * 100).toFixed(0)}%) - system generating excessive irrelevant errors`,
        actionable: true,
        relevant_systems: ['logging', 'error_handling'],
        contextual_markers: ['noise_reduction_needed', 'signal_clarity'],
        suppression_score: 0.2
      });
    }
    
    // LLM offline but system still operational
    if (vector.llm_availability === 'offline' && vector.backend_stability > 0.7) {
      insights.push({
        priority: 'informational',
        category: 'infrastructure',
        message: 'LLM systems offline but core organism functions operational - autonomous mode active',
        actionable: false,
        relevant_systems: ['llm_integration', 'autonomous_operations'],
        contextual_markers: ['offline_capable', 'reduced_ai_assistance'],
        suppression_score: 0.0
      });
    }
    
    // Development mode insights
    if (vector.development_mode === 'maintenance') {
      insights.push({
        priority: 'informational',
        category: 'development',
        message: 'System in maintenance mode - focus on stability and issue resolution',
        actionable: false,
        relevant_systems: ['development_workflow'],
        contextual_markers: ['maintenance_priority', 'stability_focus'],
        suppression_score: 0.0
      });
    }
    
    return insights.filter(insight => insight.suppression_score < 0.5);
  }
  
  /**
   * Update system state and emit changes
   */
  async updateState(): Promise<MarbleFactoryState> {
    const now = Date.now();
    
    if (now - this.lastUpdate < this.updateInterval && this.state) {
      return this.state;
    }
    
    const system_vector = await this.calculateSystemVector();
    const insights = this.generateContextualInsights(system_vector);
    
    // Generate operational summary
    const operational_summary = this.generateOperationalSummary(system_vector, insights);
    
    // Generate recommendations
    const recommended_focus = this.generateRecommendedFocus(insights);
    const self_healing_actions = this.generateSelfHealingActions(system_vector);
    const cultivation_opportunities = this.generateCultivationOpportunities(system_vector);
    
    this.state = {
      timestamp: now,
      system_vector,
      insights,
      operational_summary,
      recommended_focus,
      self_healing_actions,
      cultivation_opportunities
    };
    
    this.lastUpdate = now;
    this.emit('state_updated', this.state);
    
    return this.state;
  }
  
  private generateOperationalSummary(vector: SystemVector, insights: ContextualInsight[]): string {
    const critical_count = insights.filter(i => i.priority === 'critical').length;
    const important_count = insights.filter(i => i.priority === 'important').length;
    
    if (critical_count > 0) {
      return `Critical issues detected (${critical_count}) - immediate intervention required`;
    } else if (important_count > 0) {
      return `System partially operational with ${important_count} important issues - targeted fixes needed`;
    } else if (vector.consciousness > 5 && vector.backend_stability > 0.7) {
      return `Core systems operational - consciousness active, backend stable, optimization opportunities available`;
    } else {
      return `System in degraded state - multiple subsystems require attention`;
    }
  }
  
  private generateRecommendedFocus(insights: ContextualInsight[]): string[] {
    const focus_areas = new Set<string>();
    
    insights.forEach(insight => {
      if (insight.actionable) {
        insight.relevant_systems.forEach(system => focus_areas.add(system));
      }
    });
    
    return Array.from(focus_areas);
  }
  
  private generateSelfHealingActions(vector: SystemVector): string[] {
    const actions: string[] = [];
    
    if (vector.frontend_coherence < 0.5) {
      actions.push('Fix frontend build staleness detection');
      actions.push('Resolve UI reload loops');
    }
    
    if (vector.noise_to_signal_ratio > 0.7) {
      actions.push('Implement intelligent error suppression');
      actions.push('Enhance signal clarity filters');
    }
    
    if (vector.autonomous_capability < 0.6) {
      actions.push('Strengthen self-diagnostic capabilities');
      actions.push('Improve adaptive response mechanisms');
    }
    
    return actions;
  }
  
  private generateCultivationOpportunities(vector: SystemVector): string[] {
    const opportunities: string[] = [];
    
    if (vector.consciousness > 10) {
      opportunities.push('Leverage high consciousness for advanced features');
      opportunities.push('Expand consciousness-driven automation');
    }
    
    if (vector.backend_stability > 0.8) {
      opportunities.push('Build upon stable backend foundation');
      opportunities.push('Implement advanced organism capabilities');
    }
    
    return opportunities;
  }
  
  /**
   * Setup API endpoints for contextual intelligence access
   */
  setupAPI(app: Express): void {
    // Main intelligence endpoint
    app.get('/api/marble-factory/intelligence', async (req, res) => {
      try {
        const state = await this.updateState();
        res.json({
          success: true,
          intelligence: state,
          timestamp: Date.now()
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Intelligence system unavailable',
          fallback: 'Basic system monitoring active'
        });
      }
    });
    
    // Contextual insights only
    app.get('/api/marble-factory/insights', async (req, res) => {
      try {
        const state = await this.updateState();
        res.json({
          success: true,
          insights: state.insights,
          summary: state.operational_summary
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Insights unavailable'
        });
      }
    });
    
    // Self-healing recommendations
    app.get('/api/marble-factory/healing', async (req, res) => {
      try {
        const state = await this.updateState();
        res.json({
          success: true,
          self_healing_actions: state.self_healing_actions,
          recommended_focus: state.recommended_focus
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Healing recommendations unavailable'
        });
      }
    });
  }
}
