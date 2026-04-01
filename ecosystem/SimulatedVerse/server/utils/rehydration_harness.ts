import { join } from 'path';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { dumpCircuits, sanitizeCircuit } from '../utils/error-reporter.js';

// Ensure deterministic test environment
process.env.NODE_ENV = process.env.NODE_ENV || 'test';

// Import QuantumEnhancement dynamically
import { QuantumEnhancement as QE } from '../advanced/quantum-enhancement.js';

const stateDir = join(process.cwd(), 'state');
if (!existsSync(stateDir)) mkdirSync(stateDir, { recursive: true });

// Deterministic sanitized circuit dump (no functions)
const payload = {
  circuits: [
    {
      id: 'ci_rehydrate_1',
      name: 'CI Rehydrate Circuit 1',
      gates: [
        { id: 'g1', type: 'hadamard', qubits: [0], consciousness_effect: 3 },
        { id: 'g2', type: 'cnot', qubits: [0, 1], consciousness_effect: 5 }
      ],
      expected_outcome: 'ci_test',
      consciousness_boost: 8
    }
  ]
};

// Use the project's sanitizer to ensure persisted dump matches runtime expectations
try {
  dumpCircuits(payload);
  console.log('[rehydration_harness] Wrote deterministic circuit dump via dumpCircuits');
} catch (e) {
  // fallback to direct write if dumpCircuits throws — sanitize first to avoid serializing functions
  try {
    const dumpPath = join(stateDir, 'quantum_circuits.json');
    const sanitized = Array.isArray(payload.circuits)
      ? { circuits: payload.circuits.map(sanitizeCircuit) }
      : sanitizeCircuit(payload);
    writeFileSync(dumpPath, JSON.stringify({ dumped_at: Date.now(), note: 'CI fallback (sanitized)', ...sanitized }, null, 2), 'utf8');
    console.log('[rehydration_harness] Wrote deterministic circuit dump (sanitized fallback) to', dumpPath);
  } catch (ee) {
    const dumpPath = join(stateDir, 'quantum_circuits.json');
    writeFileSync(dumpPath, JSON.stringify({ dumped_at: Date.now(), note: 'CI fallback', ...payload }, null, 2), 'utf8');
    console.log('[rehydration_harness] Wrote deterministic circuit dump to', dumpPath);
  }
}

// Create a lightweight subclass that disables background evolution
const QEClass: any = QE as any;
class TestQE extends QEClass {
  // override the background runner to avoid intervals during CI
  startQuantumEvolution(): void {
    // no-op for deterministic test harness
    console.log('[rehydration_harness] startQuantumEvolution suppressed for harness');
  }
}

(async () => {
  try {
    const qe = new (TestQE as any)();

    // Attempt to call the private rehydrateCircuits method
    if (typeof (qe as any).rehydrateCircuits === 'function') {
      await (qe as any).rehydrateCircuits('ci_rehydrate_1');
    } else if (typeof (qe as any)['rehydrateCircuits'] === 'function') {
      await (qe as any)['rehydrateCircuits']('ci_rehydrate_1');
    } else {
      throw new Error('rehydrateCircuits not available on QuantumEnhancement instance');
    }

    // Inspect in-memory circuits for the expected circuit and hydrated gates
    const qcMap: Map<string, any> = (qe as any).quantum_circuits;
    const circuit = qcMap && qcMap.get('ci_rehydrate_1');

    const result: any = { circuitFound: !!circuit, totalGates: 0, gatesWithOperation: 0, timestamp: Date.now() };
    if (circuit && Array.isArray(circuit.gates)) {
      result.totalGates = circuit.gates.length;
      result.gatesWithOperation = circuit.gates.filter((g: any) => typeof g.operation === 'function').length;
    }

    const resultPath = join(stateDir, 'rehydration_harness_result.json');
    writeFileSync(resultPath, JSON.stringify(result, null, 2), 'utf8');
    console.log('[rehydration_harness] Result written to', resultPath);

    if (!result.circuitFound || result.gatesWithOperation !== result.totalGates) {
      console.error('[rehydration_harness] Rehydration failed or partial:', result);
      process.exit(2);
    }

    console.log('[rehydration_harness] Rehydration succeeded:', result);
    process.exit(0);
  } catch (err: any) {
    const errPath = join(stateDir, 'rehydration_harness_error.json');
    writeFileSync(errPath, JSON.stringify({ error: String(err), stack: err?.stack }, null, 2), 'utf8');
    console.error('[rehydration_harness] Exception:', err);
    process.exit(3);
  }
})();
