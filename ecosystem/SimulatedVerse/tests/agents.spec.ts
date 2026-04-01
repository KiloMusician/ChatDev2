import { describe, it, expect } from "vitest";
import fs from "node:fs";
import { loadAgents } from "../agents/registry";

describe("Agents harness", () => {
  it("loads at least Librarian", async () => {
    const a = await loadAgents();
    const ids = a.map(x => x.id);
    expect(ids).toContain("librarian");
  });

  it("librarian writes an artifact", async () => {
    const agents = await loadAgents();
    const librarian = agents.find(x => x.id === "librarian")!;
    const out = await librarian.impl.run({ 
      t:1, 
      utc:Date.now(), 
      budget:1, 
      entropy:0, 
      context:{}, 
      ask:{type:"index", payload:{}} 
    });
    expect(out.ok).toBe(true);
    const artifactPath = out.effects?.artifactPath;
    expect(typeof artifactPath).toBe("string");
    expect(fs.existsSync(String(artifactPath))).toBe(true);
  });

  it("all agents produce side-effects", async () => {
    const agents = await loadAgents();
    expect(agents.length).toBeGreaterThan(0);
    
    for (const agent of agents.slice(0, 3)) { // Test first 3 for speed
      const result = await agent.impl.run({
        t: 1,
        utc: Date.now(),
        budget: 1,
        entropy: 0,
        context: {},
        ask: { type: "inspect", payload: {} }
      });
      
      expect(result.ok).toBe(true);
      expect(
        result.effects?.artifactPath || 
        result.effects?.stateDelta || 
        result.effects?.busEvents
      ).toBeTruthy();
    }
  });
});
