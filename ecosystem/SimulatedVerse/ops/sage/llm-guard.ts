// ops/sage/llm-guard.ts
// Auto-adapt for Ollama/OpenAI/ChatDev with receipts + bounded retries.
import { request } from "undici";
import { elasticCooldown } from "./elastic";

export async function guardedChat(payload: any, opts?: { expectJson?: boolean }) {
  const receipts: any[] = [];
  let Tin = 4096, Tout = 1024, tries = 0;

  while (tries < 4) {
    tries++;
    try {
      // prefer gateway (which prefers Ollama), fall back to OpenAI once
      const res = await request(`${process.env.LLM_GATEWAY_URL ?? "http://127.0.0.1:4455"}/llm/chat`, {
        method: "POST",
        body: JSON.stringify({ ...payload, json: !!opts?.expectJson }),
        headers: { "content-type": "application/json" },
        bodyTimeout: 240_000,
        headersTimeout: 30_000,
      });
      if (res.statusCode === 200) {
        const out = await res.body.json() as any;
        receipts.push({ ok: true, backend: out.backend, tries });
        return { content: out.content, backend: out.backend, receipts, Tin, Tout };
      }
      throw new Error(`gateway_${res.statusCode}`);
    } catch (e: any) {
      const msg = String(e?.message ?? e);
      const penalty =
        msg.includes("429") ? "ratelimit" :
        msg.includes("ECONN") || msg.includes("ENOTCONN") || msg.includes("EPIPE") ? "connect" :
        "other";

      // adapt budgets & spacing
      Tin = Math.max(1024, Math.floor(0.6 * Tin));
      Tout = Math.max(512, Math.floor(0.8 * Tout));
      const wait = elasticCooldown(1000, {
        timeouts: penalty === "other" ? 1 : 0,
        rateLimits: penalty === "ratelimit" ? 1 : 0,
        econn: penalty === "connect" ? 1 : 0,
        backlog: 0,
        idleStreakMs: 0,
        receipts: 0,
        uiFreshSkewMs: 0,
      });
      receipts.push({ ok: false, msg, Tin, Tout, wait });
      await new Promise((r) => setTimeout(r, wait));
      // last retry: allow cloud fallback once (handled by gateway internally)
    }
  }
  throw new Error("guardedChat_exhausted_retries");
}