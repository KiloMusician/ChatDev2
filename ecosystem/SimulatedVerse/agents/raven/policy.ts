/**
 * Raven Policy Engine
 * Infrastructure-first constraints, do-no-harm, diff-or-die
 */

import { RavenPolicyConfig } from './config';

export class RavenPolicy {
  private config: RavenPolicyConfig;

  constructor(config: RavenPolicyConfig) {
    this.config = config;
  }

  async validateGoal(goal: string, constraints: string[]): Promise<void> {
    // Validate goal against policy constraints
    if (!goal || goal.length < 10) {
      throw new Error('Goal must be descriptive (min 10 characters)');
    }

    // Check for forbidden operations
    const forbiddenPatterns = [
      'delete all',
      'drop table',
      'rm -rf',
      'push main',
      'force push'
    ];

    for (const pattern of forbiddenPatterns) {
      if (goal.toLowerCase().includes(pattern)) {
        throw new Error(`Goal contains forbidden operation: ${pattern}`);
      }
    }
  }

  async validatePlan(rawPlan: any): Promise<any> {
    // Validate plan against policy
    if (!rawPlan.nodes || rawPlan.nodes.length === 0) {
      throw new Error('Plan must contain at least one PU');
    }

    if (rawPlan.nodes.length > 200) {
      throw new Error('Plan exceeds maximum node count (200)');
    }

    // Validate each PU
    for (const pu of rawPlan.nodes) {
      await this.validatePU(pu);
    }

    return rawPlan;
  }

  private async validatePU(pu: any): Promise<void> {
    // Ensure PU has required fields
    const requiredFields = ['id', 'type', 'title', 'description'];
    for (const field of requiredFields) {
      if (!pu[field]) {
        throw new Error(`PU missing required field: ${field}`);
      }
    }

    // Validate PU type
    const validTypes = ['DocPU', 'TestPU', 'RefactorPU', 'FixturePU', 'GamePU'];
    if (!validTypes.includes(pu.type)) {
      throw new Error(`Invalid PU type: ${pu.type}`);
    }

    // Check if touching forbidden paths
    if (pu.files) {
      for (const file of pu.files) {
        if (this.isForbiddenPath(file)) {
          throw new Error(`PU attempts to modify forbidden path: ${file}`);
        }
      }
    }
  }

  private isForbiddenPath(path: string): boolean {
    return this.config.forbidden_paths.some(forbidden => 
      path.startsWith(forbidden)
    );
  }

  getConstraints(): string[] {
    return [
      'infrastructure-first',
      'pr-only-writes',
      'small-diffs',
      'single-concern',
      'tests-required',
      'artifacts-required',
      'no-main-writes'
    ];
  }

  async updateFromLearnings(patterns: any): Promise<void> {
    // Update policy based on learned patterns
    // This could involve adjusting thresholds, adding new constraints, etc.
  }
}