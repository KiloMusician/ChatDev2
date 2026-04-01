/* Minimal, local-first event bus + filesystem tooling for agents */
import { execSync } from "node:child_process";
import { readFileSync, writeFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import type { Agent, AgentContext, AgentName, AgentReport, RepoInsights, Task } from "./types";

function safeRead(p: string): string | null {
  try { return readFileSync(p, "utf8"); } catch { return null; }
}
function ensureDir(p: string) {
  const dir = dirname(p);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}
function safeWrite(p: string, data: string) {
  ensureDir(p);
  writeFileSync(p, data);
}
function safeAppend(p: string, data: string) {
  ensureDir(p);
  appendFileSync(p, data);
}
function safeJSON<T = any>(p: string): T | null {
  const t = safeRead(p);
  if (!t) return null;
  try { return JSON.parse(t) as T; } catch { return null; }
}

export class AgentBus {
  private agents: Agent[] = [];
  private queueBuf: Task[] = [];
  private ctx!: AgentContext;

  constructor(
    private repoRoot = resolve("."),
    private reportsDir = resolve("reports"),
    private dryRun = true,
    private tokenBudget = 0
  ) {}

  private gatherInsights(): RepoInsights {
    const imports = safeJSON<any[]>("reports/scan_imports.json") ?? [];
    const dupes = safeJSON<any[]>("reports/scan_dupes.json") ?? [];
    const smoke = safeJSON<{ ok: boolean }>("reports/smoke_game_status.json");
    const todosTxt = safeRead("reports/scan_todos.txt") ?? "";
    return {
      todos: todosTxt.split("\n").filter(Boolean).length,
      dupes: dupes.length,
      brokenImports: imports.length,
      smokeOk: !!(smoke?.ok),
    };
  }

  init(): AgentContext {
    const insights = this.gatherInsights();
    const ctx: AgentContext = {
      repoRoot: this.repoRoot,
      reportsDir: this.reportsDir,
      dryRun: this.dryRun,
      tokenBudget: this.tokenBudget,
      insights,
      shell: (cmd: string) => {
        try { return execSync(cmd, { stdio: "pipe" }).toString(); }
        catch { return ""; }
      },
      readText: (p: string) => safeRead(p),
      writeText: (p: string, data: string) => safeWrite(p, data),
      readJSON: <T = any>(p: string) => safeJSON<T>(p),
      writeJSON: (p: string, data: unknown) => safeWrite(p, JSON.stringify(data, null, 2)),
      appendJournal: (agent: AgentName, line: string) =>
        safeAppend(`reports/agents/${agent}.log`, `[${new Date().toISOString()}] ${line}\n`),
      queue: (task: Task) => this.queueBuf.push(task),
      dequeueAll: () => {
        const copy = [...this.queueBuf];
        this.queueBuf.length = 0;
        return copy;
      },
    };
    this.ctx = ctx;
    return ctx;
  }

  register(a: Agent) {
    this.agents.push(a);
  }

  private async runPhase(
    phase: "scan" | "plan" | "act",
    filter?: (a: Agent) => boolean
  ): Promise<AgentReport[]> {
    const out: AgentReport[] = [];
    for (const a of this.agents) {
      if (!a[phase]) continue;
      if (filter && !filter(a)) continue;
      const startedAt = new Date().toISOString();
      let rep: AgentReport;
      try {
        const res = await (a[phase] as any)(this.ctx);
        rep = res ?? {
          agent: a.name,
          startedAt,
          finishedAt: new Date().toISOString(),
          summary: `${a.name}.${phase} completed`,
          actions: [],
          warnings: [],
        };
      } catch (e: any) {
        rep = {
          agent: a.name,
          startedAt,
          finishedAt: new Date().toISOString(),
          summary: `${a.name}.${phase} threw`,
          actions: [],
          warnings: [String(e?.message ?? e)],
        };
      }
      out.push(rep);
      // persist compact phase report
      const shortPath = `reports/agents/${a.name.toLowerCase()}.${phase}.json`;
      safeWrite(shortPath, JSON.stringify(rep, null, 2));
    }
    return out;
  }

  async cycle(): Promise<{ reports: AgentReport[]; tasks: Task[] }> {
    this.init();
    const reports: AgentReport[] = [];
    reports.push(...(await this.runPhase("scan")));
    reports.push(...(await this.runPhase("plan")));
    // Let Pilot own the act phase ordering; but fall back to alphabetical
    const pilot = this.agents.find(a => a.name === "Pilot");
    if (pilot?.act) {
      reports.push(...(await this.runPhase("act", a => a.name === "Pilot")));
    } else {
      reports.push(...(await this.runPhase("act")));
    }
    const tasks = this.ctx.dequeueAll();
    // Compact cycle record
    safeWrite(`reports/agents/cycle_${Date.now()}.json`, JSON.stringify({
      at: new Date().toISOString(),
      dryRun: this.dryRun,
      insights: this.ctx.insights,
      taskCount: tasks.length
    }, null, 2));
    return { reports, tasks };
  }
}