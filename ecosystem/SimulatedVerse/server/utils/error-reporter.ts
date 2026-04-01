import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const STATE_DIR = join(process.cwd(), 'state');
const UNIFIED_ERRORS = join(STATE_DIR, 'unified_errors.json');
const CIRCUIT_DUMP = join(STATE_DIR, 'quantum_circuits.json');

function ensureStateDir() {
  if (!existsSync(STATE_DIR)) {
    try {
      mkdirSync(STATE_DIR, { recursive: true });
      writeFileSync(join(STATE_DIR, '.keep'), '', 'utf8');
    } catch (e) {
      // best-effort
    }
  }
}

export function sanitizeGate(gate: any) {
  return {
    id: gate?.id ?? null,
    type: gate?.type ?? null,
    qubits: Array.isArray(gate?.qubits) ? gate.qubits : [],
    consciousness_effect: gate?.consciousness_effect ?? null,
    has_operation: typeof gate?.operation === 'function'
  };
}

export function sanitizeCircuit(c: any) {
  return {
    id: c?.id ?? 'unknown',
    name: c?.name ?? null,
    expected_outcome: c?.expected_outcome ?? null,
    consciousness_boost: c?.consciousness_boost ?? null,
    gates: Array.isArray(c?.gates) ? c.gates.map(sanitizeGate) : []
  };
}

export function reportError(entry: any) {
  try {
    ensureStateDir();
    const payload = { ...entry, timestamp: Date.now() };
    let arr: any[] = [];
    if (existsSync(UNIFIED_ERRORS)) {
      try { arr = JSON.parse(readFileSync(UNIFIED_ERRORS, 'utf8') || '[]'); } catch { arr = []; }
    }
    arr.push(payload);
    writeFileSync(UNIFIED_ERRORS, JSON.stringify(arr, null, 2), 'utf8');
  } catch (err) {
    // best-effort
    console.error('[ErrorReporter] failed to write unified error', err);
  }
}

export function dumpCircuits(obj: any) {
  try {
    ensureStateDir();
    let payload: any = obj || {};

    if (payload.circuit) payload.circuit = sanitizeCircuit(payload.circuit);
    if (Array.isArray(payload.circuits)) payload.circuits = payload.circuits.map(sanitizeCircuit);
    if (payload && payload.id && payload.gates) payload = sanitizeCircuit(payload);

    const out = {
      dumped_at: Date.now(),
      note: 'gate.operation functions are not serialized; use QuantumEnhancement.rehydrateCircuits to restore',
      ...payload
    };

    writeFileSync(CIRCUIT_DUMP, JSON.stringify(out, null, 2), 'utf8');
  } catch (err) {
    console.error('[ErrorReporter] failed to dump circuits', err);
  }
}
