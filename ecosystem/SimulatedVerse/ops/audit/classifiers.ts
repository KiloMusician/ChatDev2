// Lightweight, regex-based classification with confidence scoring.
// Add/adjust without touching history; prefer "anneal then refine".
export type Rule = { rx: RegExp; category: string; notes?: string; boost?: number };

export const RULES: Rule[] = [
  // LLM / Agents
  { rx: /^(ollama|@?langchain|llamaindex|ai|promptfoo|semantic-kernel)$/i, category: "llm/agents", boost: 0.9 },
  { rx: /^openai$|^anthropic$|^@vercel\/ai$/i, category: "llm/agents", boost: 0.8 },

  // Game engines & sim
  { rx: /^(phaser|pixi\.?js|three|babylon|konva)$/i, category: "game/engine", boost: 0.9 },
  { rx: /^(rot-js|@mikewesthad\/dungeon|pathfinding|easystarjs|xstate|bitecs|matter-js|planck-js|cannon-es)$/i, category: "game/sim", boost: 0.85 },
  { rx: /^(tone|howler|scribbletune|soundfont-player)$/i, category: "game/audio", boost: 0.85 },

  // UI
  { rx: /^(react-error-boundary|swr|react-query|zustand|jotai|immer|recharts|visx|d3|clsx|tailwindcss|monaco-editor)$/i, category: "ui/web", boost: 0.8 },

  // Observability
  { rx: /^(pino|winston|opentelemetry-|prom-client|rrweb|openreplay.*)$/i, category: "ops/observability", boost: 0.8 },

  // Queues / orchestration
  { rx: /^(bullmq|p-queue|node-cron|temporalio?)$/i, category: "ops/orchestration", boost: 0.85 },

  // Validation & types
  { rx: /^(zod|ajv|ajv-formats|ts-pattern|json-schema-to-typescript|io-ts|superstruct)$/i, category: "ops/validation", boost: 0.85 },

  // Data / RAG / vector
  { rx: /^(chromadb|weaviate-ts-client|pgvector|pg|nanoid)$/i, category: "data/vector", boost: 0.85 },

  // Testing / QA
  { rx: /^(vitest|jest|msw|fast-check|@testing-library\/(react|dom)|playwright|stryker-js)$/i, category: "qa/tests", boost: 0.9 },

  // ASCII / TUI
  { rx: /^(blessed|neo-blessed|react-blessed|ink|terminal-kit|xterm|xterm-addon-fit|cli-table3|asciichart|sparkly|ora|boxen|figlet|kleur|chalk|log-update|listr2|ansi-escapes|wrap-ansi|enquirer|strip-ansi|blessed-contrib)$/i, category: "ui/ascii", boost: 0.9 },

  // Net / utilities
  { rx: /^(undici|p-map|neverthrow|deepmerge|yaml|qs|jsondiffpatch|jmespath)$/i, category: "ops/utils", boost: 0.7 }
];

export function classify(name: string): { category: string; confidence: number; notes?: string } {
  let winner = { category: "misc/unknown", confidence: 0.3 as number, notes: undefined as string | undefined };
  for (const r of RULES) {
    if (r.rx.test(name)) {
      const conf = (r.boost ?? 0.6);
      if (conf > winner.confidence) winner = { category: r.category, confidence: conf, notes: r.notes };
    }
  }
  return winner;
}