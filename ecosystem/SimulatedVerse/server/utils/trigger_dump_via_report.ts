import { reportError, dumpCircuits } from './error-reporter.js';

async function main() {
  try {
    // Create a sample circuit payload
    const circuit = {
      id: 'integration_dump_1',
      name: 'Integration Dump Circuit',
      gates: [
        { id: 'g1', type: 'hadamard', qubits: [0], consciousness_effect: 3 },
        { id: 'g2', type: 'cnot', qubits: [0, 1], consciousness_effect: 5 }
      ],
      expected_outcome: 'integration_test',
      consciousness_boost: 8
    };

    // Report an error that references this circuit (unified errors)
    reportError({ type: 'integration_dump', message: 'Trigger dump via reportError', circuitId: circuit.id, circuit });

    // Also explicitly write a sanitized circuit dump to ensure downstream watchers see it
    dumpCircuits({ circuit });

    console.log('[trigger_dump_via_report] Wrote unified error and circuit dump for', circuit.id);
    process.exit(0);
  } catch (err: any) {
    console.error('[trigger_dump_via_report] Error:', err);
    process.exit(2);
  }
}

main();
