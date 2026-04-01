import { getQuantumEnhancement } from '../advanced/quantum-enhancement';
import fs from 'fs';
import path from 'path';

async function run() {
  console.log('[test] Obtaining QuantumEnhancement instance...');
  const q = getQuantumEnhancement() as any;

  // Create a malformed circuit (operations missing)
  const circuit = {
    id: 'rehydration-test-001',
    name: 'Rehydration Test Circuit',
    gates: [
      { id: 'rg1', type: 'hadamard', qubits: [0], operation: undefined, consciousness_effect: 3 },
      { id: 'rg2', type: 'cnot', qubits: [0, 1], operation: undefined, consciousness_effect: 5 }
    ],
    expected_outcome: 'rehydrated',
    consciousness_boost: 1
  };

  // Insert into runtime circuits map
  if (!q.quantum_circuits) {
    console.error('[test] quantum_circuits map not found on instance');
    process.exit(2);
  }
  q.quantum_circuits.set(circuit.id, circuit);

  console.log('[test] Invoking rehydrateCircuits for', circuit.id);
  try {
    await q.rehydrateCircuits(circuit.id);
  } catch (e) {
    // method is private but exists at runtime; handle failures
    if (typeof q.rehydrateCircuits !== 'function') {
      console.error('[test] rehydrateCircuits method not available on instance');
      process.exit(3);
    }
  }

  const updated = q.quantum_circuits.get(circuit.id);
  if (!updated) {
    console.error('[test] Circuit missing after rehydration');
    process.exit(4);
  }

  const op1 = typeof updated.gates[0].operation === 'function';
  const op2 = typeof updated.gates[1].operation === 'function';

  console.log('[test] Gate operations rehydrated?', op1, op2);
  if (op1 && op2) {
    console.log('[test] PASSED: rehydration bound operations');
    try { fs.writeFileSync(path.join(process.cwd(), 'state', 'rehydration_result.json'), JSON.stringify({ passed: true, op1: true, op2: true }, null, 2), 'utf8'); } catch (e) {}
    process.exit(0);
  } else {
    console.error('[test] FAILED: operations not rehydrated');
    try { fs.writeFileSync(path.join(process.cwd(), 'state', 'rehydration_result.json'), JSON.stringify({ passed: false, op1, op2 }, null, 2), 'utf8'); } catch (e) {}
    process.exit(5);
  }
}

run();
