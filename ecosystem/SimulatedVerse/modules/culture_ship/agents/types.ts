/**
 * Common types for Culture-Ship agents.
 * Agents run inside a local-first, zero/low-token orchestration loop.
 */
export type AgentName =
  | "Intermediary"
  | "NeuroTide"
  | "Librarian"
  | "Artificer"
  | "Alchemist"
  | "Pilot"
  | "Council";

export type Priority = "low" | "normal" | "high" | "critical";

export interface Task<T = any> {
  id: string;
  title: string;
  source: AgentName | "system" | "user";
  payload?: T;
  priority: Priority;
  tags?: string[];
  createdAt: string; // ISO
  dryRun?: boolean;
}

export interface AgentReport {
  agent: AgentName;
  startedAt: string;
  finishedAt: string;
  summary: string;
  actions: string[];
  warnings: string[];
  metrics?: Record<string, number>;
}

export interface RepoInsights {
  todos: number;
  dupes: number;
  brokenImports: number;
  smokeOk: boolean;
}

export interface AgentContext {
  repoRoot: string;
  reportsDir: string;
  dryRun: boolean;
  tokenBudget: number; // informational; agents prefer 0-cost actions
  insights: RepoInsights;
  // Utilities
  shell(cmd: string): string;             // sync, safe wrapper
  readText(path: string): string | null;
  writeText(path: string, data: string): void;
  readJSON<T = any>(path: string): T | null;
  writeJSON(path: string, data: unknown): void;
  appendJournal(agent: AgentName, line: string): void;
  queue(task: Task): void;
  dequeueAll(): Task[];
}

export interface Agent {
  name: AgentName;
  /**
   * Observe repo state; never mutates. Logs findings.
   */
  scan?(ctx: AgentContext): Promise<AgentReport> | AgentReport;
  /**
   * Convert observations to tasks. May queue dozens/hundreds of micro-tasks.
   */
  plan?(ctx: AgentContext): Promise<AgentReport> | AgentReport;
  /**
   * Execute tasks within guardrails. Must respect ctx.dryRun.
   */
  act?(ctx: AgentContext): Promise<AgentReport> | AgentReport;
}