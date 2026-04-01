import { join } from 'path';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { dumpCircuits, sanitizeCircuit } from './error-reporter.js';

// ensure deterministic environment
process.env.NODE_ENV = process.env.NODE_ENV || 'test';

// Import QuantumEnhancement
import { QuantumEnhancement as QE } from '../advanced/quantum-enhancement.js';

const stateDir = join(process.cwd(), 'state');
if (!existsSync(stateDir)) mkdirSync(stateDir, { recursive: true });

const payload = {
  circuits: [
    {
      id: 'ci_repair_1',
      name: 'CI Repair Circuit 1',
      gates: [
        { id: 'g1', type: 'hadamard', qubits: [0], consciousness_effect: 3 },
        { id: 'g2', type: 'cnot', qubits: [0, 1], consciousness_effect: 5 }
      ],
      expected_outcome: 'ci_repair',
      consciousness_boost: 8
    }
  ]
};

try {
  // Use dumpCircuits to write a sanitized persisted dump
  dumpCircuits(payload);
  console.log('[integration_test_repair] Wrote sanitized circuit dump via dumpCircuits');
} catch (e) {
  // Fallback: sanitize then write
  try {
    const dumpPath = join(stateDir, 'quantum_circuits.json');
    const sanitized = { circuits: payload.circuits.map(sanitizeCircuit) };
    writeFileSync(dumpPath, JSON.stringify({ dumped_at: Date.now(), note: 'integration sanitized fallback', ...sanitized }, null, 2), 'utf8');
    console.log('[integration_test_repair] Wrote sanitized circuit dump (fallback)');
  } catch (ee) {
    console.error('[integration_test_repair] Failed to write sanitized dump fallback', ee);
    process.exit(3);
  }
}

// Create a TestQE that suppresses background evolution
const QEClass: any = QE as any;
class TestQE extends QEClass {
  startQuantumEvolution(): void {
    // suppress intervals during test
    console.log('[integration_test_repair] startQuantumEvolution suppressed');
  }
}

(async () => {
  try {
    const qe = new (TestQE as any)();

    // Call rehydrateCircuits for the id we wrote
    if (typeof (qe as any).rehydrateCircuits === 'function') {
      await (qe as any).rehydrateCircuits('ci_repair_1');
    } else {
      throw new Error('rehydrateCircuits not available');
    }

    const qcMap: Map<string, any> = (qe as any).quantum_circuits;
    const circuit = qcMap && qcMap.get('ci_repair_1');

    const result: any = { circuitFound: !!circuit, totalGates: 0, gatesWithOperation: 0, timestamp: Date.now() };
    if (circuit && Array.isArray(circuit.gates)) {
      result.totalGates = circuit.gates.length;
      result.gatesWithOperation = circuit.gates.filter((g: any) => typeof g.operation === 'function').length;
    }

    const resultPath = join(stateDir, 'integration_repair_result.json');
    writeFileSync(resultPath, JSON.stringify(result, null, 2), 'utf8');
    console.log('[integration_test_repair] Result written to', resultPath);

    if (!result.circuitFound || result.gatesWithOperation !== result.totalGates) {
      console.error('[integration_test_repair] Rehydration failed or partial:', result);
      process.exit(2);
    }

    console.log('[integration_test_repair] Rehydration succeeded:', result);
    process.exit(0);
  } catch (err: any) {
    console.error('[integration_test_repair] Exception:', err?.message || err);
    process.exit(4);
  }
})();
