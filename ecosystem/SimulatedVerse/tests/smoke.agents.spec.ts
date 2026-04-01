import { describe, it, expect } from "vitest";
const BASE = process.env.BASE_URL || "http://127.0.0.1:5000";

describe("Agents list is live, not manifest-only", () => {
  it("exposes mounted + health", async () => {
    const r = await fetch(`${BASE}/api/agents`);
    expect(r.ok).toBe(true);
    const j: any = await r.json();
    expect(Array.isArray(j.agents)).toBe(true);
    const a = j.agents[0] || {};
    expect("health" in a).toBe(true);
    expect("mounted" in a).toBe(true);
  });
});