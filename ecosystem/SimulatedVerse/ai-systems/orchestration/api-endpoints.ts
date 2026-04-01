import type { Express, Request, Response } from "express";
import { TokenGuard } from "../../system/llm/sidecar/token_guard.js";

function getBudget() {
  // Replace with your real budget service
  const allowance = Number(process.env.DAILY_ALLOWANCE || 5000);
  const consumed = Number((globalThis as any).__budgetConsumed || 0);
  return { allowance, consumed };
}
function onBurn(cost: number, meta?: any) {
  (globalThis as any).__budgetConsumed = ((globalThis as any).__budgetConsumed || 0) + cost;
  // optionally: push Msg⛛ event
}

const guard = new TokenGuard({
  getBudget, onBurn,
  options: {
    allowPaidFallback: process.env.PAID_FALLBACK === "1",
    paidProvider: (process.env.PAID_VENDOR as any) || "openai"
  }
});

export function registerLLMProviderRoutes(app: Express) {
  app.get("/api/llm/health", (_req: Request, res: Response) => {
    res.json({
      ok: true,
      local: !!process.env.OLLAMA_URL,
      paidEnabled: process.env.PAID_FALLBACK === "1",
      vendor: process.env.PAID_VENDOR || null,
      budget: getBudget()
    });
  });

  app.post("/api/llm/complete", async (req: Request, res: Response) => {
    const body = req.body || {};
    const r = await guard.complete({
      model: body.model,
      prompt: body.prompt,
      max_tokens: body.max_tokens ?? 512,
      temperature: body.temperature ?? 0.2
    });
    res.status(r.ok ? 200 : 429).json(r);
  });

  app.post("/api/llm/embeddings", async (_req: Request, res: Response) => {
    // sketch: wire when you have a local embeddings route; for now return budget-friendly not-impl
    res.status(501).json({ ok: false, error: "embeddings-not-implemented" });
  });
}