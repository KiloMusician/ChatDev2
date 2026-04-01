#!/usr/bin/env tsx
// Quick QSA test with just the ops/ directory
import { promises as fs } from "node:fs";

async function main() {
  console.log("[qsa-test] Creating sample reports for demonstration...");
  
  await fs.mkdir("reports/qsa", { recursive: true });
  
  // Sample repo audit
  const audit = {
    stats: { files: 156, scanned: 156 },
    quadRules: ["system", "ui", "simulation", "bridge"],
    ts: Date.now()
  };
  
  // Sample abilities found
  const abilities = [
    { path: "ops/qsa/scan-repo.ts", quad: "system", size: 6043 },
    { path: "ops/chatdev-adapter/index.ts", quad: "system", size: 2891 },
    { path: "packages/council/bridges/chatdev-bridge.ts", quad: "bridge", size: 1024 },
    { path: "apps/web/src/components/QSAReportPane.tsx", quad: "ui", size: 1845 }
  ];
  
  // Sample issues found
  const issues = [
    { path: "some-file.ts", quad: "system", placeholders: true, hardcoded: false, sample: "// TODO: implement this" },
    { path: "other-file.ts", quad: "ui", placeholders: false, hardcoded: true, sample: "console.error('hardcoded error')" }
  ];
  
  // Sample dupes
  const dupes = {
    exact: [{ hash: "abc123", paths: ["file1.ts", "file1-copy.ts"] }],
    near: [{ stem: "similar", a: "similar1.ts", b: "similar2.ts", sim: 0.95 }]
  };
  
  // Sample spam
  const spam = {
    spam: [{ path: "huge-log.txt", quad: "unknown", size: 3000000, usefulRatio: 0.02 }],
    storms: [{ stem: "report", count: 90, samples: ["report1.json", "report2.json"] }]
  };
  
  await fs.writeFile("reports/qsa/repo_audit.json", JSON.stringify(audit, null, 2));
  await fs.writeFile("reports/qsa/abilities.json", JSON.stringify(abilities, null, 2));
  await fs.writeFile("reports/qsa/issues.json", JSON.stringify(issues, null, 2));
  await fs.writeFile("reports/qsa/dupes.json", JSON.stringify(dupes, null, 2));
  await fs.writeFile("reports/qsa/spam.json", JSON.stringify(spam, null, 2));
  
  console.log("[qsa-test] ✅ Sample reports created in reports/qsa/");
}

main().catch(e => { console.error(e); process.exit(1); });