const { dumpCircuits } = require('./error-reporter');
const fs = require('fs');
const path = require('path');

// Sample circuit with functions that should be stripped by dumpCircuits
const sampleCircuit = {
  id: 'test-circuit-001',
  name: 'Test Circuit',
  expected_outcome: 'test_outcome',
  consciousness_boost: 42,
  gates: [
    { id: 'g1', type: 'hadamard', qubits: [0], operation: (s) => s, consciousness_effect: 3 },
    { id: 'g2', type: 'cnot', qubits: [0, 1], operation: function (s) { return s; }, consciousness_effect: 5 },
  ]
};

console.log('[test] Running dumpCircuits with a circuit that contains function values...');
dumpCircuits({ circuit: sampleCircuit });

const outPath = path.join(process.cwd(), 'state', 'quantum_circuits.json');

setTimeout(() => {
  if (!fs.existsSync(outPath)) {
    console.error('[test] FAILED: dump file not created at', outPath);
    process.exit(2);
  }

  const txt = fs.readFileSync(outPath, 'utf8');
  console.log('[test] Dump file content:\n', txt);

  try {
    const obj = JSON.parse(txt);
    const gates = obj.circuit && obj.circuit.gates;
    if (Array.isArray(gates) && gates.length === 2) {
      const hasOperation = gates.some((g) => Object.prototype.hasOwnProperty.call(g, 'operation'));
      if (!hasOperation) {
        console.log('[test] PASSED: operations stripped from gates');
        process.exit(0);
      } else {
        console.error('[test] FAILED: operation property still present in dump');
        process.exit(3);
      }
    } else {
      console.error('[test] FAILED: unexpected dump structure');
      process.exit(4);
    }
  } catch (e) {
    console.error('[test] FAILED: cannot parse dump JSON', e);
    process.exit(5);
  }
}, 300);
