---
id: P-0073-self-play-harness
title: Self-Play Harness v1
priority: high
phase: expansion
class: Euclid
tags: selfplay, game, tests, budget:low
---

# Self-Play Harness v1 (P-0073-self-play-harness)

**Classification:** Euclid  
**Priority:** High  
**Phase:** Expansion  
**Subsystems:** game, tests, docs  

## Special Containment Procedures
Limit sim runs to ≤ 300 ticks per PR. Gate on /readyz endpoint. If entropy > 0.7, abort run. Throttle to maximum 1 simulation per minute on Replit infrastructure.

## Description
Implement deterministic self-play harness to exercise idle loop, storage caps, overflow handling, and prestige preview functionality. This validates core game mechanics under automated testing without human intervention.

The harness will:
- Execute deterministic game simulations with fixed RNG seeds
- Validate resource flows and cap behaviors
- Test prestige calculations and state transitions
- Generate performance metrics and yield curves

## Experiments
- EXP-1: 100-tick sim on seed=42 → no entropy growth; yield snapshot saved
- EXP-2: 250-tick sim with caps near full → validate overflow handling, waste < 10%
- EXP-3: Prestige trigger simulation → verify meta-currency calculations

## Risks & Mitigations
- **Risk:** Runaway CPU usage on Replit infrastructure
  - **Mitigation:** Throttle to 1 sim per minute, hard timeout at 60 seconds
- **Risk:** Nondeterministic behavior affecting tests
  - **Mitigation:** Fixed RNG seed + stable tick implementation
- **Risk:** Memory leaks during long simulations
  - **Mitigation:** Garbage collection between runs, memory monitoring

## Addenda
- A1: Link to Jupyter notebook for yield curve analysis
- A2: Godot scene hook for visual simulation (future enhancement)
- A3: Integration with existing PU queue system

## RSEV
```rsev
RSEV::ADD_FILE path="tests/selfplay.spec.ts" <<EOF
import { describe, it, expect } from "vitest";
import { GameEngine } from "../src/game/engine.js";

describe("Self-Play Harness", () => {
  it("runs 100 ticks deterministically", async () => {
    const engine = new GameEngine({ seed: 42, deterministic: true });
    const result = await engine.simulate(100);
    
    expect(result.ticks).toBe(100);
    expect(result.entropy).toBeLessThan(0.1);
    expect(result.final_state).toBeDefined();
  });
  
  it("handles resource caps without overflow", async () => {
    const engine = new GameEngine({ seed: 42, deterministic: true });
    engine.setResourceCap("energy", 1000);
    
    const result = await engine.simulate(250);
    expect(result.waste_percentage).toBeLessThan(10);
  });
});
EOF
RSEV::TEST name="selfplay-100" run="npm test -- selfplay.spec.ts"
RSEV::GAME_SIM ticks=100
RSEV::OPEN_PR branch="agent/P-0073-self-play-harness" labels="automerge,agent,tests"
RSEV::OBSIDIAN_SYNC path="docs/proposals/P-0073-self-play-harness.md"
```