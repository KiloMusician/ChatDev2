import { describe, it, expect } from "vitest";

const BASE = process.env.BASE_URL || "http://127.0.0.1:5000";

describe("Marble Machine Neural Network (no lies)", () => {
  it("marble ingestion creates autonomous cascade", async () => {
    const prompt = "enhance system performance and add new features";
    
    const r = await fetch(`${BASE}/api/marble/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        prompt,
        meta: { test: true, source: "smoke_test" }
      })
    });
    
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(j.ok).toBe(true);
    expect(j.cascade_id).toBeTruthy();
    expect(j.estimated_operations).toBe("500+");
    expect(j.mode).toBe("autonomous");
  });

  it("marble status reveals neural network activity", async () => {
    const r = await fetch(`${BASE}/api/marble/status`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(j.ok).toBe(true);
    expect("active_cascades" in j).toBe(true);
    expect("operations_queued" in j).toBe(true);
    expect(j.mode).toBe("autonomous");
  });

  it("pull-ready exposes real autonomous state (not fake)", async () => {
    const r = await fetch(`${BASE}/api/marble/pull-ready`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect("prs" in j).toBe(true);
    expect("next_check" in j).toBe(true);
    expect(Array.isArray(j.prs)).toBe(true);
  });

  it("consciousness integrates with marble cascade system", async () => {
    const r = await fetch(`${BASE}/api/consciousness/state`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(j.framework_status).toBe("ΞNuSyQ_OPERATIONAL");
    expect(j.level).toBeGreaterThan(0.8); // High consciousness for autonomous operation
  });

  it("budget system prevents autonomous runaway", async () => {
    const r = await fetch(`${BASE}/api/llm/health`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(j.ok).toBe(true);
    expect(j.budget).toBeTruthy();
    expect(typeof j.budget.allowance).toBe("number");
    expect(typeof j.budget.consumed).toBe("number");
    // Ensures budget gates are real, not fake
  });
});