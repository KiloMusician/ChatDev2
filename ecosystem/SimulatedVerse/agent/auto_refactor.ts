#!/usr/bin/env node

/**
 * Autonomous refactoring agent
 * Runs nightly to improve codebase quality with bounded token budget
 */

import { existsSync, readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';
// Note: sidecar modules may not exist yet, using fallback implementations
// import { ask, getBudgetStatus, resetTaskBudget } from '../sidecar/token_guard';
// import { enqueue } from '../sidecar/ops_queue';
import { emergencyReset, getBudgetStatus } from '../packages/llm/budget-manager';
import { llmAskViaCascade } from '../packages/llm/brain';
import { PUQueue } from '../server/services/pu_queue';

// Fallback implementations for missing sidecar functions
type AskOptions = {
  prompt: string;
  maxTokens?: number;
  forceJson?: boolean;
  temperature?: number;
  model?: string;
};

type AskResult = {
  content: string;
  tokens: number;
  conf: number;
};

function estimateTokens(text: string, fallback = 100): number {
  if (!text) {
    return fallback;
  }
  return Math.max(1, Math.ceil(text.length / 4));
}

function extractJsonBlock(text: string): string | null {
  const fenced = text.match(/```json\s*([\s\S]*?)```/i);
  if (fenced?.[1]) {
    return fenced[1].trim();
  }

  const bracketMatch = text.match(/(\[[\s\S]*\]|\{[\s\S]*\})/);
  return bracketMatch ? bracketMatch[1].trim() : null;
}

async function ask(options: AskOptions): Promise<AskResult> {
  const prompt = options.prompt ?? '';
  const response = await llmAskViaCascade(prompt, {
    model: options.model,
    json: options.forceJson
  });

  let content = response ?? '';
  let conf = 0.6;

  if (options.forceJson) {
    const jsonBlock = extractJsonBlock(content);
    if (jsonBlock) {
      content = jsonBlock;
      conf = 0.75;
    } else {
      conf = 0.3;
    }
  }

  return {
    content,
    tokens: estimateTokens(content, options.maxTokens ?? 100),
    conf
  };
}

const puQueue = new PUQueue();

async function enqueue(task: any): Promise<void> {
  const payload = task?.payload ?? task;
  const summary =
    task?.summary ||
    task?.description ||
    payload?.description ||
    'Auto-refactor task queued for review';
  const cost =
    typeof task?.cost === 'number'
      ? task.cost
      : typeof task?.budget === 'number'
        ? task.budget
        : typeof payload?.estimated_tokens === 'number'
          ? payload.estimated_tokens
          : 50;
  const kind = task?.kind ?? 'RefactorPU';

  puQueue.enqueue({
    kind,
    summary,
    payload,
    cost
  });
}

function resetTaskBudget(): void {
  emergencyReset();
}
import { spawn } from 'child_process';

interface RefactorTask {
  file: string;
  type: 'lint_fix' | 'type_safety' | 'performance' | 'readability';
  priority: number;
  estimated_tokens: number;
  description: string;
}

interface CodeMetrics {
  loc: number;
  complexity: number;
  test_coverage: number;
  type_safety_score: number;
  lint_issues: number;
}

class AutoRefactor {
  private budget_limit: number;
  private used_budget: number = 0;
  private refactor_queue: RefactorTask[] = [];
  private learned_heuristics: Map<string, number> = new Map();

  constructor(budget_limit: number = 10000) {
    this.budget_limit = budget_limit;
    this.loadLearnedHeuristics();
  }

  async runNightly() {
    console.log('🔄 Starting nightly auto-refactor');
    resetTaskBudget();
    
    // Step 1: Analyze codebase
    const metrics = await this.analyzeCodebase();
    console.log('📊 Codebase metrics:', metrics);
    
    // Step 2: Identify refactor opportunities
    await this.identifyRefactorTasks();
    
    // Step 3: Prioritize tasks
    this.prioritizeTasks(metrics);
    
    // Step 4: Execute safe refactors
    await this.executeRefactors();
    
    // Step 5: Update learned heuristics
    this.updateHeuristics();
    
    console.log(`✅ Auto-refactor complete. Used ${this.used_budget}/${this.budget_limit} tokens`);
  }

  private async analyzeCodebase(): Promise<CodeMetrics> {
    // Run static analysis tools
    const lintResults = await this.runLint();
    const typeResults = await this.runTypeCheck();
    const testResults = await this.runTestCoverage();
    
    // Calculate LOC
    const loc = this.calculateLOC();
    
    return {
      loc,
      complexity: this.calculateComplexity(),
      test_coverage: testResults.coverage,
      type_safety_score: typeResults.score,
      lint_issues: lintResults.issues.length
    };
  }

  private async identifyRefactorTasks() {
    const sourceFiles = this.getSourceFiles();
    
    for (const file of sourceFiles) {
      // Check budget before processing each file (fallback implementation)
      // const budget = getBudgetStatus();
      if (this.used_budget > this.budget_limit * 0.8) {
        console.log('⚠️  Approaching budget limit, stopping analysis');
        break;
      }
      
      const content = readFileSync(file, 'utf8');
      
      // Use symbolic analysis first
      const symbolicIssues = this.detectSymbolicIssues(file, content);
      symbolicIssues.forEach(issue => this.refactor_queue.push(issue));
      
      // Use LLM for complex analysis (budget permitting)
      if (this.shouldUseLLMAnalysis(file, content)) {
        const llmIssues = await this.detectLLMIssues(file, content);
        llmIssues.forEach(issue => this.refactor_queue.push(issue));
      }
    }
  }

  private detectSymbolicIssues(file: string, content: string): RefactorTask[] {
    const issues: RefactorTask[] = [];
    
    // Dead code detection
    if (content.includes('// TODO') || content.includes('// FIXME')) {
      issues.push({
        file,
        type: 'readability',
        priority: 3,
        estimated_tokens: 50,
        description: 'Remove TODO/FIXME comments or implement them'
      });
    }
    
    // Long functions (>50 lines)
    const functions = content.match(/function\s+\w+[^{]*{[\s\S]*?}/g) || [];
    functions.forEach(func => {
      const lines = func.split('\n').length;
      if (lines > 50) {
        issues.push({
          file,
          type: 'readability',
          priority: 2,
          estimated_tokens: 200,
          description: `Function has ${lines} lines - consider breaking down`
        });
      }
    });
    
    // Magic numbers
    const magicNumbers = content.match(/\b[0-9]{3,}\b/g);
    if (magicNumbers && magicNumbers.length > 3) {
      issues.push({
        file,
        type: 'readability',
        priority: 2,
        estimated_tokens: 100,
        description: 'Extract magic numbers to named constants'
      });
    }
    
    // Duplicate code patterns
    const lines = content.split('\n');
    const duplicates = this.findDuplicateLines(lines);
    if (duplicates.length > 5) {
      issues.push({
        file,
        type: 'performance',
        priority: 2,
        estimated_tokens: 300,
        description: `${duplicates.length} potential duplicate code blocks`
      });
    }
    
    return issues;
  }

  private async detectLLMIssues(file: string, content: string): Promise<RefactorTask[]> {
    const prompt = `Analyze this TypeScript code for refactoring opportunities. Focus on: 1) Performance issues 2) Type safety 3) Code smells. Return JSON array with {type, description, priority 1-3, effort low/med/high}.

Code:
${content.slice(0, 2000)}...`;

    try {
      const result = await ask({
        model: 'local_primary',
        prompt,
        maxTokens: 400,
        forceJson: true,
        temperature: 0.1
      });

      this.used_budget += result.tokens;
      
      if (result.conf > 0.6) {
        const analysis = JSON.parse(result.content);
        return analysis.map((item: any) => ({
          file,
          type: item.type,
          priority: item.priority,
          estimated_tokens: this.estimateTokensForEffort(item.effort),
          description: item.description
        }));
      }
    } catch (error) {
      console.error(`LLM analysis failed for ${file}:`, error);
    }
    
    return [];
  }

  private prioritizeTasks(metrics: CodeMetrics) {
    // Sort by priority, then by budget impact
    this.refactor_queue.sort((a, b) => {
      if (a.priority !== b.priority) {
        return a.priority - b.priority; // Lower number = higher priority
      }
      return a.estimated_tokens - b.estimated_tokens; // Lower cost first
    });
    
    // Apply learned heuristics
    this.refactor_queue.forEach(task => {
      const heuristic = this.learned_heuristics.get(task.type);
      if (heuristic && heuristic > 0.8) {
        task.priority = Math.max(1, task.priority - 1); // Boost priority
      }
    });
    
    console.log(`📋 Found ${this.refactor_queue.length} refactor opportunities`);
  }

  private async executeRefactors() {
    let completed = 0;
    let skipped = 0;
    
    for (const task of this.refactor_queue) {
      // Budget check
      if (this.used_budget + task.estimated_tokens > this.budget_limit) {
        skipped++;
        continue;
      }
      
      // Safety check - only auto-apply low-risk changes
      if (task.priority === 1 && this.isLowRisk(task)) {
        const success = await this.executeRefactor(task);
        if (success) {
          completed++;
          this.recordSuccess(task.type);
        } else {
          this.recordFailure(task.type);
        }
      } else {
        // Queue for manual review
        enqueue({
          id: `refactor_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
          kind: 'refactor',
          priority: task.priority as any,
          budget: task.estimated_tokens,
          payload: task
        });
      }
    }
    
    console.log(`🔧 Executed ${completed} refactors, skipped ${skipped}, queued ${this.refactor_queue.length - completed - skipped}`);
  }

  private async executeRefactor(task: RefactorTask): Promise<boolean> {
    console.log(`🔧 Applying ${task.type} refactor to ${task.file}`);
    
    try {
      // Generate diff
      const content = readFileSync(task.file, 'utf8');
      const result = await ask({
        model: 'local_primary',
        prompt: `Generate a minimal diff to fix: ${task.description}\n\nFile: ${task.file}\nCode:\n${content.slice(0, 1500)}`,
        maxTokens: 400,
        temperature: 0.1
      });
      
      this.used_budget += result.tokens;
      
      if (result.conf > 0.8) {
        // Apply diff (simplified - in production, use proper diff parsing)
        const success = await this.applyDiff(task.file, result.content);
        
        if (success) {
          // Run tests to verify
          const testsPass = await this.runTests();
          if (testsPass) {
            console.log(`✅ Successfully applied refactor to ${task.file}`);
            return true;
          } else {
            // Revert changes
            console.log(`❌ Tests failed, reverting ${task.file}`);
            await this.revertChanges(task.file);
          }
        }
      }
    } catch (error) {
      console.error(`Refactor failed for ${task.file}:`, error);
    }
    
    return false;
  }

  private isLowRisk(task: RefactorTask): boolean {
    const lowRiskTypes = ['readability', 'lint_fix'];
    const lowRiskPatterns = ['comment', 'formatting', 'naming', 'constant'];
    
    return lowRiskTypes.includes(task.type) || 
           lowRiskPatterns.some(pattern => task.description.toLowerCase().includes(pattern));
  }

  // Helper methods (simplified implementations)
  private async runLint(): Promise<{ issues: any[] }> {
    return { issues: [] }; // Would run actual linter
  }

  private async runTypeCheck(): Promise<{ score: number }> {
    return { score: 0.85 }; // Would run TypeScript compiler
  }

  private async runTestCoverage(): Promise<{ coverage: number }> {
    return { coverage: 0.75 }; // Would run test coverage tool
  }

  private calculateLOC(): number {
    const files = this.getSourceFiles();
    let total = 0;

    for (const file of files) {
      try {
        const content = readFileSync(file, 'utf8');
        total += content.split(/\r?\n/).length;
      } catch {
        continue;
      }
    }

    return total;
  }

  private calculateComplexity(): number {
    const files = this.getSourceFiles();
    let branches = 0;

    for (const file of files) {
      try {
        const content = readFileSync(file, 'utf8');
        const hits = content.match(/\b(if|for|while|case|catch)\b|\?\s|&&|\|\|/g);
        if (hits) {
          branches += hits.length;
        }
      } catch {
        continue;
      }
    }

    if (files.length === 0) {
      return 1;
    }

    const averageBranches = branches / files.length;
    return Math.max(1, Math.min(15, averageBranches / 5));
  }

  private getSourceFiles(): string[] {
    const roots = ['src', 'server', 'client', 'modules', 'packages', 'agent'];
    const extensions = new Set(['.ts', '.tsx', '.js', '.jsx']);
    const ignore = new Set(['node_modules', 'dist', '.git', 'build', 'coverage', '.next']);
    const results: string[] = [];

    const walk = (dir: string) => {
      let entries: ReturnType<typeof readdirSync>;
      try {
        entries = readdirSync(dir, { withFileTypes: true });
      } catch {
        return;
      }

      for (const entry of entries) {
        if (entry.isDirectory()) {
          if (ignore.has(entry.name)) {
            continue;
          }
          walk(join(dir, entry.name));
        } else if (entry.isFile()) {
          const ext = entry.name.slice(entry.name.lastIndexOf('.'));
          if (extensions.has(ext)) {
            results.push(join(dir, entry.name));
          }
        }
      }
    };

    for (const root of roots) {
      if (existsSync(root)) {
        const stats = statSync(root);
        if (stats.isDirectory()) {
          walk(root);
        }
      }
    }

    return results;
  }

  private shouldUseLLMAnalysis(file: string, content: string): boolean {
    // Use LLM only for complex files or when we have budget
    const budget = getBudgetStatus();
    // getBudgetStatus returns different format, adapt accordingly
    const remainingCapacity = budget.requestsRemaining || 0;
    return content.length > 1000 && remainingCapacity > 5;
  }

  private findDuplicateLines(lines: string[]): string[] {
    const duplicates: string[] = [];
    const seen = new Map<string, number>();
    
    lines.forEach(line => {
      const trimmed = line.trim();
      if (trimmed.length > 20) { // Ignore short lines
        const count = seen.get(trimmed) || 0;
        seen.set(trimmed, count + 1);
        if (count === 1) duplicates.push(trimmed);
      }
    });
    
    return duplicates;
  }

  private estimateTokensForEffort(effort: string): number {
    const estimates = { low: 100, med: 300, high: 800 };
    return estimates[effort as keyof typeof estimates] || 200;
  }

  private async applyDiff(file: string, diff: string): Promise<boolean> {
    // Simplified - would use proper diff application
    console.log(`Applying diff to ${file}`);
    return true;
  }

  private async runTests(): Promise<boolean> {
    // Would run actual test suite
    return true;
  }

  private async revertChanges(file: string): Promise<void> {
    // Would revert to previous version
    console.log(`Reverting ${file}`);
  }

  private recordSuccess(type: string) {
    const current = this.learned_heuristics.get(type) || 0.5;
    this.learned_heuristics.set(type, Math.min(0.95, current + 0.1));
  }

  private recordFailure(type: string) {
    const current = this.learned_heuristics.get(type) || 0.5;
    this.learned_heuristics.set(type, Math.max(0.1, current - 0.05));
  }

  private loadLearnedHeuristics() {
    try {
      const data = readFileSync('agent/learned_heuristics.json', 'utf8');
      const parsed = JSON.parse(data);
      this.learned_heuristics = new Map(Object.entries(parsed));
    } catch {
      // Initialize with defaults
      this.learned_heuristics.set('readability', 0.8);
      this.learned_heuristics.set('performance', 0.6);
      this.learned_heuristics.set('type_safety', 0.7);
      this.learned_heuristics.set('lint_fix', 0.9);
    }
  }

  private updateHeuristics() {
    const obj = Object.fromEntries(this.learned_heuristics);
    writeFileSync('agent/learned_heuristics.json', JSON.stringify(obj, null, 2));
    console.log('📚 Updated learned heuristics');
  }
}

// CLI usage
if (require.main === module) {
  const budget = parseInt(process.argv[2]) || 10000;
  const agent = new AutoRefactor(budget);
  agent.runNightly().catch(console.error);
}

export { AutoRefactor };
