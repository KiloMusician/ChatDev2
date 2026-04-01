# Rehydration Harness CI

This repository contains a deterministic rehydration harness used by CI to verify
that the `QuantumEnhancement.rehydrateCircuits` logic can reliably reconstruct
sanitized circuit dumps into executable in-memory circuits.

Location
- Harness script: `server/utils/rehydration_harness.ts`
- Deterministic dump written to: `state/quantum_circuits.json`
- Result file (CI artifact): `state/rehydration_harness_result.json`
- Error details (on failure): `state/rehydration_harness_error.json`

What the CI checks
1. The harness writes a deterministic sanitized circuit dump containing a circuit
   with id `ci_rehydrate_1`.
2. The harness instantiates a test `QuantumEnhancement` (background loops
   suppressed), runs `rehydrateCircuits('ci_rehydrate_1')`, and inspects the in-
   memory circuits.
3. CI asserts that the circuit was found and that all gates have callable
   `operation` functions after rehydration.

How to run locally

```bash
# from repository root
cd SimulatedVerse
npx tsx server/utils/rehydration_harness.ts
```

Exit codes
- 0: success (circuit rehydrated and all gates hydrated)
- 2: rehydration partial/failure (harness prints details)
- 3: exception during harness execution
- 4/5: CI assertion failures (missing result file or failed assertions)

Notes
- The harness sets `NODE_ENV=test` to avoid background file watchers and
  interval loops interfering with deterministic behavior.
- The harness writes its outputs under `state/`, which is included as job
  artifacts in CI for post-mortem analysis.
