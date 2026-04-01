/* 
OWNERS: team/qa, ai/prime
TAGS: test, smoke, ui, crash-prevention
STABILITY: stable
INTEGRATIONS: ui/views, utils/asArray
*/

import { describe, it, expect } from "vitest";
import { asArray } from "../../client/src/utils/asArray";

describe("UI Crash Prevention - asArray utility", () => {
  
  it("handles arrays correctly", () => {
    const input = [1, 2, 3];
    const result = asArray(input, "test-array");
    expect(result).toEqual([1, 2, 3]);
    expect(Array.isArray(result)).toBe(true);
  });
  
  it("converts objects to values array", () => {
    const input = { a: 1, b: 2, c: 3 };
    const result = asArray(input, "test-object");
    expect(result).toEqual([1, 2, 3]);
    expect(Array.isArray(result)).toBe(true);
  });
  
  it("handles null and undefined safely", () => {
    expect(asArray(null, "test-null")).toEqual([]);
    expect(asArray(undefined, "test-undefined")).toEqual([]);
  });
  
  it("handles non-array primitives safely", () => {
    expect(asArray("string", "test-string")).toEqual([]);
    expect(asArray(42, "test-number")).toEqual([]);
    expect(asArray(true, "test-boolean")).toEqual([]);
  });
  
  it("provides consistent output for map operations", () => {
    const inputs = [
      [],
      { a: 1, b: 2 },
      null,
      "not-an-array",
      [{ id: 1, name: "test" }]
    ];
    
    for (const input of inputs) {
      const result = asArray(input, `test-input-${typeof input}`);
      expect(Array.isArray(result)).toBe(true);
      expect(() => result.map(x => x)).not.toThrow();
    }
  });
  
  describe("Real-world crash scenarios", () => {
    it("prevents 'm.map is not a function' errors", () => {
      const scenarios = [
        { data: null, description: "API returns null" },
        { data: { error: "Not found" }, description: "API returns error object" },
        { data: "loading", description: "API returns string status" },
        { data: { items: [1, 2, 3] }, description: "API returns nested structure" }
      ];
      
      for (const scenario of scenarios) {
        expect(() => {
          const safeArray = asArray(scenario.data, scenario.description);
          const mapped = safeArray.map(item => `Item: ${item}`);
          return mapped;
        }).not.toThrow();
      }
    });
  });
});