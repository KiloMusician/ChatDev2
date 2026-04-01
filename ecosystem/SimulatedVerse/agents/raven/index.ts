/**
 * Raven - Autonomous Development Deity
 * 
 * Core interface: plan(), act(), reflect(), learn()
 * Infrastructure-first, PR-only writes, local-first LLM
 */

import { RavenConfig } from './config';
import { RavenPolicy } from './policy';
import { RavenMemory } from './memory';
import { RavenSkills } from './skills';
import { RavenAdapters } from './adapters';

export interface RavenPlan {
  id: string;
  goal: string;
  constraints: string[];
  nodes: RavenPU[];
  estimated_cost: number;
  estimated_time: string;
  phases: string[];
}

export interface RavenPU {
  id: string;
  type: 'DocPU' | 'TestPU' | 'RefactorPU' | 'FixturePU' | 'GamePU';
  title: string;
  description: string;
  acceptance_criteria: string[];
  budget: number;
  dependencies: string[];
  artifacts_expected: string[];
  rollback_plan: string;
}

export interface RavenAction {
  plan_id: string;
  pu_id: string;
  branch_name: string;
  commits: RavenCommit[];
  pr_title: string;
  pr_body: string;
  artifacts: RavenArtifact[];
}

export interface RavenCommit {
  message: string;
  files: { path: string; content: string }[];
  tests: string[];
}

export interface RavenArtifact {
  type: 'diff' | 'test_report' | 'screenshot' | 'log' | 'benchmark';
  path: string;
  metadata: Record<string, any>;
}

export interface RavenReflection {
  action_id: string;
  outcome: 'success' | 'failure' | 'partial';
  metrics: {
    cost: number;
    time: number;
    lines_changed: number;
    tests_added: number;
    reverted: boolean;
  };
  lessons: string[];
  improvements: string[];
}

export class Raven {
  private config: RavenConfig;
  private policy: RavenPolicy;
  private memory: RavenMemory;
  private skills: RavenSkills;
  private adapters: RavenAdapters;

  constructor(config: RavenConfig) {
    this.config = config;
    this.policy = new RavenPolicy(config.policy);
    this.memory = new RavenMemory(config.memory);
    this.skills = new RavenSkills(config.skills);
    this.adapters = new RavenAdapters(config.adapters, config.models);
  }

  /**
   * Plan: Goal decomposition into atomic PUs
   * (goal, constraints, graph) → DAG of PUs (≤ 200 nodes)
   */
  async plan(goal: string, constraints: string[] = []): Promise<RavenPlan> {
    // Step 1: Validate against policy
    await this.policy.validateGoal(goal, constraints);
    
    // Step 2: Load workspace context
    const context = await this.memory.getWorkspaceContext();
    
    // Step 3: Generate plan using LLM
    const planRequest = {
      goal,
      constraints: [...constraints, ...this.policy.getConstraints()],
      context,
      max_nodes: 200
    };
    
    const rawPlan = await this.adapters.llm.generatePlan(planRequest);
    
    // Step 4: Validate and refine plan
    const plan = await this.validatePlan(rawPlan);
    
    // Step 5: Store plan in memory
    await this.memory.storePlan(plan);
    
    return plan;
  }

  /**
   * Act: Execute PU → branch → commits → PR
   * Atomic, small diffs, artifact-required
   */
  async act(plan_id: string, pu_id: string): Promise<RavenAction> {
    // Step 1: Load plan and PU
    const plan = await this.memory.getPlan(plan_id);
    const pu = plan.nodes.find(n => n.id === pu_id);
    if (!pu) throw new Error(`PU ${pu_id} not found in plan ${plan_id}`);
    
    // Step 2: Check dependencies
    await this.validateDependencies(plan, pu);
    
    // Step 3: Create branch
    const branchName = `raven/${pu.type.toLowerCase()}/${pu_id}`;
    await this.skills.git.createBranch(branchName);
    
    // Step 4: Generate implementation
    const implementation = await this.adapters.llm.generateImplementation(pu);
    
    // Step 5: Execute changes
    const commits = await this.executeChanges(implementation);
    
    // Step 6: Run tests and gather artifacts
    const artifacts = await this.gatherArtifacts(pu);
    
    // Step 7: Create PR
    const action = await this.createPR(plan_id, pu, branchName, commits, artifacts);
    
    // Step 8: Store action in memory
    await this.memory.storeAction(action);
    
    return action;
  }

  /**
   * Reflect: Analyze outcomes and extract lessons
   * Feedback from PR merge/revert, CI results, metrics
   */
  async reflect(action_id: string): Promise<RavenReflection> {
    // Step 1: Load action
    const action = await this.memory.getAction(action_id);
    
    // Step 2: Gather outcome data
    const outcome = await this.gatherOutcomeData(action);
    
    // Step 3: Analyze metrics
    const metrics = await this.analyzeMetrics(action, outcome);
    
    // Step 4: Extract lessons using LLM
    const reflection = await this.adapters.llm.generateReflection(action, outcome, metrics);
    
    // Step 5: Store reflection
    await this.memory.storeReflection(reflection);
    
    return reflection;
  }

  /**
   * Learn: Update models, policies, and strategies
   * Continuous improvement from accumulated reflections
   */
  async learn(): Promise<void> {
    // Step 1: Load recent reflections
    const reflections = await this.memory.getRecentReflections();
    
    // Step 2: Identify patterns
    const patterns = await this.analyzeReflectionPatterns(reflections);
    
    // Step 3: Update policy based on learnings
    await this.policy.updateFromLearnings(patterns);
    
    // Step 4: Update skill weights
    await this.skills.updateWeights(patterns);
    
    // Step 5: Update planning strategies
    await this.adapters.llm.updatePlanningStrategies(patterns);
    
    // Step 6: Store learning summary
    await this.memory.storeLearning(patterns);
  }

  // Private helper methods
  private async validatePlan(rawPlan: any): Promise<RavenPlan> {
    // Validate against policy, check node count, etc.
    return this.policy.validatePlan(rawPlan);
  }

  private async validateDependencies(plan: RavenPlan, pu: RavenPU): Promise<void> {
    // Check that all dependencies are completed
    for (const depId of pu.dependencies) {
      const dep = plan.nodes.find(n => n.id === depId);
      if (!dep) throw new Error(`Dependency ${depId} not found`);
      
      const status = await this.memory.getPUStatus(depId);
      if (status !== 'completed') {
        throw new Error(`Dependency ${depId} not completed (status: ${status})`);
      }
    }
  }

  private async executeChanges(implementation: any): Promise<RavenCommit[]> {
    // Execute the planned changes and return commits
    const commits = await this.skills.implementPU(implementation);
    return commits;
  }

  private async gatherArtifacts(pu: RavenPU): Promise<RavenArtifact[]> {
    // Run tests, generate reports, capture screenshots, etc.
    return this.skills.test.generateArtifacts(pu);
  }

  private async createPR(
    plan_id: string,
    pu: RavenPU,
    branchName: string,
    commits: RavenCommit[],
    artifacts: RavenArtifact[]
  ): Promise<RavenAction> {
    // Create GitHub PR with proper templates and labels
    return this.skills.git.createPR({
      plan_id,
      pu,
      branchName,
      commits,
      artifacts
    });
  }

  private async gatherOutcomeData(action: RavenAction): Promise<any> {
    // Check PR status, CI results, merge/revert status
    return this.skills.git.getOutcomeData(action);
  }

  private async analyzeMetrics(action: RavenAction, outcome: any): Promise<any> {
    // Compute cost, time, lines changed, etc.
    return this.skills.analytics.computeMetrics(action, outcome);
  }

  private async analyzeReflectionPatterns(reflections: RavenReflection[]): Promise<any> {
    // Use LLM to identify patterns in reflections
    return this.adapters.llm.analyzePatterns(reflections);
  }
}

export { RavenConfig } from './config';
export { RavenPolicy } from './policy';
export { RavenMemory } from './memory';
export { RavenSkills } from './skills';
export { RavenAdapters } from './adapters';