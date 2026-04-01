import { readFileSync, existsSync } from 'fs';
import path from 'path';

const statePath = path.join(process.cwd(), 'state', 'quantum_circuits.json');

function fail(msg: string) {
  console.error('[test_persisted_circuits] FAIL:', msg);
  process.exit(3);
}

function pass(msg?: string) {
  if (msg) console.log('[test_persisted_circuits] OK:', msg);
  process.exit(0);
}

console.log('[test_persisted_circuits] Checking', statePath);

if (!existsSync(statePath)) {
  console.log('[test_persisted_circuits] No persisted circuit file; nothing to validate. Passing.');
  pass();
}

try {
  const raw = readFileSync(statePath, 'utf8');
  const parsed = JSON.parse(raw);

  if (!Array.isArray(parsed) && typeof parsed === 'object' && parsed !== null && parsed.circuits) {
    // support object with circuits key
    parsed.circuits = parsed.circuits || parsed;
  }

  const circuits = Array.isArray(parsed) ? parsed : (parsed.circuits || []);

  let totalGates = 0;
  const offenders: Array<{ circuitId?: string; gateIndex: number; gate: any }> = [];

  for (const c of circuits) {
    const cid = c.id || c._id || c.name || '<unknown>';
    const gates = Array.isArray(c.gates) ? c.gates : [];
    for (let i = 0; i < gates.length; i++) {
      const g = gates[i];
      totalGates++;
      // If an 'operation' key exists or value looks non-primitive, flag it.
      if (Object.prototype.hasOwnProperty.call(g, 'operation')) {
        offenders.push({ circuitId: cid, gateIndex: i, gate: { ...g, operation: typeof g.operation } });
        continue;
      }
      // ensure has_operation boolean marker exists
      if (!Object.prototype.hasOwnProperty.call(g, 'has_operation')) {
        offenders.push({ circuitId: cid, gateIndex: i, gate: { ...g } });
        continue;
      }
    }
  }

  if (offenders.length > 0) {
    console.error('[test_persisted_circuits] Found persisted gates with disallowed fields or missing markers:');
    for (const o of offenders) {
      console.error(` - circuit=${o.circuitId} gateIndex=${o.gateIndex} gatePreview=${JSON.stringify(o.gate).slice(0,200)}`);
    }
    fail(`Found ${offenders.length} offending gates across ${circuits.length} circuits (total gates scanned=${totalGates})`);
  }

  pass(`No offending gates found across ${circuits.length} circuits (total gates scanned=${totalGates})`);

} catch (e: any) {
  console.error('[test_persisted_circuits] Error parsing file:', e?.message || e);
  process.exit(4);
}
