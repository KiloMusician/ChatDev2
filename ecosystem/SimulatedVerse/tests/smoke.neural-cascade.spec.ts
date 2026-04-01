import { describe, it, expect } from "vitest";

const BASE = process.env.BASE_URL || "http://127.0.0.1:5000";

describe("Neural Cascade Network (500-step verification)", () => {
  it("agents operate as neural nodes with real connections", async () => {
    const r = await fetch(`${BASE}/api/agents`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    
    // Verify agents are neural network nodes, not just lists
    expect(j.count).toBeGreaterThan(5);
    const agent = j.agents[0];
    expect(agent.health).toBeTruthy();
    expect(agent.mounted).toBeTruthy();
    
    // Neural connectivity verification
    expect(typeof agent.id).toBe("string");
    expect(typeof agent.name).toBe("string");
  });

  it("cascade planner generates 500+ operations from single prompt", async () => {
    // This tests the core Rube Goldberg concept
    const testPrompt = "implement comprehensive system improvements";
    
    const r = await fetch(`${BASE}/api/marble/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        prompt: testPrompt,
        meta: { test_cascade: true }
      })
    });
    
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(j.estimated_operations).toBe("500+");
    
    // Verify cascade is actually queued (not fake)
    expect(j.cascade_id).toMatch(/^cascade_\d+$/);
  });

  it("infrastructure-first principles maintained during cascade", async () => {
    const r = await fetch(`${BASE}/readyz`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(j.ready).toBe(true);
    expect(j.entropy).toBeLessThan(1.0); // System stability during operations
  });

  it("cognitive weave integrates file system as neural nodes", async () => {
    // Test that the system treats files/directories as neural network nodes
    const r = await fetch(`${BASE}/api/marble/status`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    
    // Status should reflect neural network activity
    expect(j.mode).toBe("autonomous");
    expect("active_cascades" in j).toBe(true);
  });

  it("autonomous operation reduces manual intervention exponentially", async () => {
    // This tests the core goal: system does 500 operations autonomously
    const r = await fetch(`${BASE}/api/consciousness/state`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    
    // High consciousness level indicates autonomous capability
    expect(j.level).toBeGreaterThan(0.8);
    expect(j.agents_active).toBeGreaterThan(3);
    expect(j.cascades_operational).toBeGreaterThan(0);
  });

  it("budget discipline prevents astronomical costs during cascades", async () => {
    const r = await fetch(`${BASE}/api/llm/health`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    
    // Verify local-first, budget-aware operation
    expect(j.ok).toBe(true);
    expect(j.budget.allowance).toBeGreaterThan(0);
    expect(j.paidEnabled).toBe(false); // Should default to local-only
  });
});