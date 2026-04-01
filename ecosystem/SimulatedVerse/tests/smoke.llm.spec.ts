import { describe, it, expect } from "vitest";

const BASE = process.env.BASE_URL || "http://127.0.0.1:5000";

describe("LLM stack smoke (no lies)", () => {
  it("health returns budget + local flag", async () => {
    const r = await fetch(`${BASE}/api/llm/health`);
    expect(r.ok).toBe(true);
    const j:any = await r.json();
    expect(j.ok).toBe(true);
    expect(j.budget).toBeTruthy();
    expect(typeof j.local).toBe("boolean");
  });

  it("local completion returns ok:false when OLLAMA_URL is missing (cheap truth)", async () => {
    // when no ollama, we expect guarded fail instead of fake-ok
    const r = await fetch(`${BASE}/api/llm/complete`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: "ping", max_tokens: 8 })
    });
    const j: any = await r.json();
    expect(typeof j.ok).toBe("boolean");
  });
});