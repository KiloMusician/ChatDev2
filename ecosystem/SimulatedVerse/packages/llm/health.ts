export async function llmHealth() {
  try {
    const r = await fetch(process.env.LLM_GATEWAY_HEALTH || "http://127.0.0.1:4455/llm/health", {
      method: "GET",
      signal: AbortSignal.timeout(2000)
    });
    if (!r.ok) return { ok: false, reason: "bad_status" };
    const j = await r.json() as any;
    return { ok: (j.ollama || j.openai) ? true : false, ...j };
  } catch {
    return { ok: false, reason: "network" };
  }
}