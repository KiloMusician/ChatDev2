// ops/sage/reliability.ts
// Agent + backend reliability ledger (rolling window); exposes choices to agents & UI.
export type Signal = "ok" | "warn" | "down";

export interface AgentReliability {
  name: string;
  requires: ("ollama" | "openai" | "chatdev" | "fs" | "git" | "ui")[];
  lastSuccessAt?: number;
  lastFailureAt?: number;
  successStreak: number;
  failureStreak: number;
  signal: Signal; // derived
}

export function rateAgent(a: AgentReliability): AgentReliability {
  const now = Date.now();
  const fresh = (t?: number) => (t ? now - t < 10 * 60_000 : false);
  const score =
    2 * a.successStreak -
    1 * a.failureStreak +
    (fresh(a.lastSuccessAt) ? 1 : 0) -
    (fresh(a.lastFailureAt) ? 1 : 0);

  let signal: Signal = "ok";
  if (score < -1) signal = "down";
  else if (score <= 1) signal = "warn";
  return { ...a, signal };
}

export function chooseAgent<T extends AgentReliability>(
  pool: T[],
  need: Partial<T["requires"]> = []
) {
  const eligible = pool
    .map(rateAgent)
    .filter((a) => need.every((r) => a.requires.includes(r as any)))
    .sort((a, b) => (a.signal === b.signal ? b.successStreak - a.successStreak : signalRank(a) - signalRank(b)));

  return eligible[0];

  function signalRank(a: AgentReliability) {
    return a.signal === "ok" ? 0 : a.signal === "warn" ? 1 : 2;
  }
}