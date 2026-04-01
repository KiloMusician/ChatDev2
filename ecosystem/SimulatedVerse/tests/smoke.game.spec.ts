import { describe,it,expect } from "vitest";
const BASE = process.env.BASE_URL || "http://127.0.0.1:5000";

describe("@smoke new-game", () => {
  it("boot-smoke returns resources and a save scaffold", async () => {
    const r = await fetch(`${BASE}/api/game/boot-smoke`);
    expect(r.ok).toBe(true);
    const j:any = await r.json();
    expect(j.ok).toBe(true);
    expect(j.summary.resources).toBeGreaterThan(0);
    expect(j.save?.version).toBeTruthy();
  });
});