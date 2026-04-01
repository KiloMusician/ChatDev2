/**
 * Raven Memory System
 * Vector store, episodic cache, semantic embeddings
 */

import { RavenMemoryConfig } from '../config';

export interface WorkspaceContext {
  files: string[];
  imports: Record<string, string[]>;
  tests: string[];
  recent_changes: string[];
  hotspots: string[];
  metrics: Record<string, number>;
}

export class RavenMemory {
  private config: RavenMemoryConfig;
  private episodicCache: Map<string, any> = new Map();
  private semanticStore: Map<string, any> = new Map();

  constructor(config: RavenMemoryConfig) {
    this.config = config;
  }

  async getWorkspaceContext(): Promise<WorkspaceContext> {
    // Workspace analysis: Check file counts, git status, recent changes
    const fileCount = await this.countWorkspaceFiles();
    const gitStatus = await this.getGitStatus();
    
    return {
      files: [],
      imports: {},
      tests: [],
      recent_changes: [],
      hotspots: [],
      metrics: { fileCount, gitClean: gitStatus.clean ? 1 : 0, gitAhead: gitStatus.ahead }
    };
  }

  async storePlan(plan: any): Promise<void> {
    this.episodicCache.set(`plan:${plan.id}`, plan);
  }

  async getPlan(planId: string): Promise<any> {
    const plan = this.episodicCache.get(`plan:${planId}`);
    if (!plan) {
      throw new Error(`Plan ${planId} not found`);
    }
    return plan;
  }

  async storeAction(action: any): Promise<void> {
    this.episodicCache.set(`action:${action.plan_id}:${action.pu_id}`, action);
  }

  async getAction(actionId: string): Promise<any> {
    for (const [key, value] of this.episodicCache) {
      if (key.includes(actionId)) {
        return value;
      }
    }
    throw new Error(`Action ${actionId} not found`);
  }

  async storeReflection(reflection: any): Promise<void> {
    this.episodicCache.set(`reflection:${reflection.action_id}`, reflection);
  }

  async getRecentReflections(limit: number = 10): Promise<any[]> {
    const reflections: any[] = [];
    for (const [key, value] of this.episodicCache) {
      if (key.startsWith('reflection:')) {
        reflections.push(value);
      }
    }
    return reflections.slice(-limit);
  }

  async storeLearning(patterns: any): Promise<void> {
    this.semanticStore.set(`learning:${Date.now()}`, patterns);
  }

  async getPUStatus(puId: string): Promise<string> {
    // Check if PU has been completed
    for (const [key, action] of this.episodicCache) {
      if (key.startsWith('action:') && action.pu_id === puId) {
        return action.status || 'pending';
      }
    }
    return 'pending';
  }

  private async countWorkspaceFiles(): Promise<number> {
    try {
      const { exec } = await import('child_process');
      const { promisify } = await import('util');
      const execAsync = promisify(exec);
      const { stdout } = await execAsync('find . -type f -not -path "./.git/*" -not -path "./node_modules/*" | wc -l');
      return parseInt(stdout.trim()) || 0;
    } catch {
      return 0;
    }
  }

  private async getGitStatus(): Promise<{ clean: boolean; ahead: number; behind: number }> {
    try {
      const { exec } = await import('child_process');
      const { promisify } = await import('util');
      const execAsync = promisify(exec);
      
      const { stdout: statusOut } = await execAsync('git status --porcelain 2>/dev/null || echo ""');
      const clean = statusOut.trim().length === 0;
      
      const { stdout: aheadBehind } = await execAsync('git rev-list --left-right --count origin/main...HEAD 2>/dev/null || echo "0\t0"');
      const [behind, ahead] = aheadBehind.trim().split('\t').map(n => parseInt(n) || 0);
      
      return { clean, ahead, behind };
    } catch {
      return { clean: true, ahead: 0, behind: 0 };
    }
  }
}