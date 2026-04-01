/* 
OWNERS: ai/raven, team/qa
TAGS: smoke:test, verification:matrix, ops:health
STABILITY: critical
HEALTH: implementing
INTEGRATIONS: game/boot, agent/gateway, ops/worker
*/

import fs from "node:fs";
import fetch from "node-fetch";

const out = "ops/smokes/latest.json";
const results = [];
const push = (name, ok, reason = "", detail = {}) => results.push({ name, ok, reason, detail });

console.log("🔥 Running CoreLink Foundation Smoke Matrix...");

try {
  const boot = await fetch("http://127.0.0.1:5000/api/game/boot-smoke").then(r => r.json());
  push("boot", !!boot.ok, boot?.summary?.reason || "", { resources: boot?.summary?.resources });
  console.log(`  Boot: ${boot.ok ? '✅' : '❌'} ${boot?.summary?.resources || 0} resources`);
} catch (e) { 
  push("boot", false, String(e)); 
  console.log(`  Boot: ❌ ${e}`);
}

try {
  const gw = await fetch("http://127.0.0.1:5000/api/agent/raven/execute", {
    method: "POST", 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify({ 
      input: { goal: "hello-smoke-test" }, 
      proof_kind: "file" 
    })
  }).then(r => r.json());
  
  push("agent_gateway", !!gw.ok, gw?.error || "", { job_id: gw?.job_id });
  console.log(`  Agent Gateway: ${gw.ok ? '✅' : '❌'} ${gw?.job_id || gw?.error}`);
} catch (e) { 
  push("agent_gateway", false, String(e)); 
  console.log(`  Agent Gateway: ❌ ${e}`);
}

try {
  const worker = await fetch("http://127.0.0.1:5000/api/ops/worker/state").then(r => r.json());
  push("worker", !!worker.running, worker.running ? "active" : "stopped", { 
    jobs_today: worker.jobs_completed_today || 0,
    success_rate: worker.success_rate || 0
  });
  console.log(`  Worker: ${worker.running ? '✅' : '⚠️'} ${worker.jobs_completed_today || 0} jobs today`);
} catch (e) { 
  push("worker", false, String(e)); 
  console.log(`  Worker: ❌ ${e}`);
}

try {
  const proofs = await fetch("http://127.0.0.1:5000/api/proofs/stats").then(r => r.json());
  push("proofs", (proofs.total || 0) > 0, `${proofs.total || 0} total, ${proofs.today || 0} today`, proofs);
  console.log(`  Proofs: ${proofs.total > 0 ? '✅' : '⚠️'} ${proofs.total || 0} total, ${proofs.today || 0} today`);
} catch (e) { 
  push("proofs", false, String(e)); 
  console.log(`  Proofs: ❌ ${e}`);
}

const summary = {
  ts: new Date().toISOString(),
  results,
  passed: results.filter(r => r.ok).length,
  total: results.length,
  success_rate: results.filter(r => r.ok).length / results.length
};

fs.mkdirSync("ops/smokes", { recursive: true });
fs.writeFileSync(out, JSON.stringify(summary, null, 2));

console.log(`\n🎯 Smoke Summary: ${summary.passed}/${summary.total} passed (${(summary.success_rate * 100).toFixed(1)}%)`);
console.log(`📊 Results saved to: ${out}`);

if (summary.success_rate < 0.6) {
  console.log("⚠️  System needs attention - success rate below 60%");
  process.exit(1);
} else {
  console.log("✅ System ready for operation");
  process.exit(0);
}