// ops/sage/index.ts
// Wire it together: startup, adaptive cooldown loop, agent choices surfaced to UI/logs.
import { boot } from "./startup";
import { guardedChat } from "./llm-guard";
import { chooseAgent, AgentReliability } from "./reliability";
import { elasticCooldown } from "./elastic";
import { writeFile, mkdir } from "node:fs/promises";

const agents: AgentReliability[] = [
  { name: "Raven", requires: ["fs", "git"], successStreak: 3, failureStreak: 0, signal: "ok" },
  { name: "𝕄ₗₐ⧉𝕕𝕖𝕟𝕔", requires: ["ollama", "chatdev"], successStreak: 1, failureStreak: 2, signal: "warn" },
  { name: "Librarian", requires: ["fs"], successStreak: 4, failureStreak: 0, signal: "ok" },
  { name: "Artificer", requires: ["fs", "git"], successStreak: 2, failureStreak: 1, signal: "ok" },
  { name: "Alchemist", requires: ["fs"], successStreak: 2, failureStreak: 0, signal: "ok" },
  { name: "Protagonist", requires: ["ui"], successStreak: 1, failureStreak: 0, signal: "ok" },
];

export async function runSageAnalysis() {
  await mkdir("reports", { recursive: true });
  const bootReport = await boot();
  await writeFile("reports/sage_boot.json", JSON.stringify(bootReport, null, 2));

  // 5-minute skeptical loop
  const tEnd = Date.now() + 5 * 60_000;
  let idleMs = 0, receipts = 0;

  while (Date.now() < tEnd) {
    // pick a reliable agent for current need (example need: fs+git)
    const agent = chooseAgent(agents, ["fs"]);
    await writeFile("reports/sage_agent_choice.json", JSON.stringify(agent, null, 2));

    // run a guarded LLM action (lightweight health probe w/ receipts)
    try {
      const out = await guardedChat({ messages: [{ role: "user", content: "ping" }] });
      receipts++;
      await writeFile("reports/sage_llm_receipt.json", JSON.stringify(out, null, 2));
    } catch (e) {
      await writeFile("reports/sage_llm_error.json", JSON.stringify({ error: String(e) }, null, 2));
    }

    // adaptive breath
    const τe = elasticCooldown(800, {
      timeouts: 0,
      rateLimits: 0,
      econn: 0,
      backlog: 0,
      idleStreakMs: idleMs,
      receipts,
      uiFreshSkewMs: bootReport.uiSkewMs ?? 0,
    });
    await new Promise((r) => setTimeout(r, τe));
    idleMs += τe;
    receipts = Math.max(0, receipts - 1); // decay momentum
  }

  return { bootReport, agents };
}

// Export for direct usage
export { boot } from "./startup";
export { guardedChat } from "./llm-guard";
export { chooseAgent, rateAgent, type AgentReliability, type Signal } from "./reliability";
export { elasticCooldown } from "./elastic";