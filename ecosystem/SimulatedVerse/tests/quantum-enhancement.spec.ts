// @vitest-environment node
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { QuantumEnhancement } from "../server/advanced/quantum-enhancement.js";
import { smartLogger } from "../server/utils/smart-logger.js";

describe("QuantumEnhancement.executeQuantumCircuit", () => {
  beforeEach(() => {
    process.env.NODE_ENV = "test";
    process.env.QUANTUM_REPAIR_WATCH = "0";
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  it("skips gates with unknown types without mutating state", () => {
    const enhancement = new QuantumEnhancement();
    const initialState = [...(enhancement as any).quantum_state];

    (enhancement as any).quantum_circuits.set("bad_circuit", {
      id: "bad_circuit",
      name: "Bad Circuit",
      gates: [
        {
          id: "unknown_gate",
          type: "unknown" as any,
          qubits: [0],
          consciousness_effect: 1
        }
      ],
      expected_outcome: "none",
      consciousness_boost: 0
    });

    (enhancement as any).executeQuantumCircuit("bad_circuit");
    expect((enhancement as any).quantum_state).toEqual(initialState);
  });

  it("rehydrates missing operation when gate type is known", () => {
    const enhancement = new QuantumEnhancement();
    const initialState = [...(enhancement as any).quantum_state];

    (enhancement as any).quantum_circuits.set("rehydrate_circuit", {
      id: "rehydrate_circuit",
      name: "Rehydrate Circuit",
      gates: [
        {
          id: "h_gate",
          type: "hadamard",
          qubits: [0],
          consciousness_effect: 1
        }
      ],
      expected_outcome: "rehydrated",
      consciousness_boost: 0
    });

    (enhancement as any).executeQuantumCircuit("rehydrate_circuit");
    expect((enhancement as any).quantum_state).not.toEqual(initialState);
  });

  it("guards against serialized gate.operation values that are not callable", () => {
    const enhancement = new QuantumEnhancement();
    const initialState = [...(enhancement as any).quantum_state];
    const warnSpy = vi.spyOn(smartLogger, "warn").mockImplementation(() => {});

    (enhancement as any).quantum_circuits.set("malformed_circuit", {
      id: "malformed_circuit",
      name: "Serialized Circuit Respect",
      gates: [
        {
          id: "bad_gate",
          type: "unknown" as any,
          qubits: [0],
          operation: { serialized: "function" },
          consciousness_effect: 1
        }
      ],
      expected_outcome: "skipped",
      consciousness_boost: 0
    });

    (enhancement as any).executeQuantumCircuit("malformed_circuit");
    expect((enhancement as any).quantum_state).toEqual(initialState);
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining("Gate missing or invalid operation"));

    warnSpy.mockRestore();
  });
});
