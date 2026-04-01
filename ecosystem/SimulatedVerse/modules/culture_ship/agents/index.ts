/**
 * Agent registry. Load all agents and expose a helper to run a cycle.
 */
import { AgentBus } from "./agent_bus";
import type { AgentContext } from "./types";

// Agents
import { Intermediary } from "./intermediary";
import { NeuroTide } from "./neurotide";
import { Librarian } from "./librarian";
import { Artificer } from "./artificer";
import { Alchemist } from "./alchemist";
import { Pilot } from "./pilot";
import { Council } from "./council";

export async function runAgentsCycle(opts?: {
  dryRun?: boolean;
  tokenBudget?: number;
}) {
  const bus = new AgentBus(".", "reports", opts?.dryRun ?? true, opts?.tokenBudget ?? 0);
  const ctx: AgentContext = bus.init();

  // Register in the canonical order
  bus.register(Intermediary);
  bus.register(NeuroTide);
  bus.register(Librarian);
  bus.register(Artificer);
  bus.register(Alchemist);
  bus.register(Pilot);
  bus.register(Council);

  // Journals
  for (const a of ["Intermediary","NeuroTide","Librarian","Artificer","Alchemist","Pilot","Council"] as const) {
    ctx.appendJournal(a, `cycle:start dryRun=${ctx.dryRun} brokenImports=${ctx.insights.brokenImports} dupes=${ctx.insights.dupes} todos=${ctx.insights.todos} smokeOk=${ctx.insights.smokeOk}`);
  }

  const { reports, tasks } = await bus.cycle();

  // Summaries
  const lines = [
    `Agents cycle complete (dryRun=${ctx.dryRun})`,
    `Tasks proposed: ${tasks.length}`,
    `Insights: brokenImports=${ctx.insights.brokenImports} dupes=${ctx.insights.dupes} todos=${ctx.insights.todos} smokeOk=${ctx.insights.smokeOk}`,
  ];
  ctx.appendJournal("NeuroTide", lines.join(" | "));
  return { reports, tasks };
}

export * from "./types";
export * from "./agent_bus";