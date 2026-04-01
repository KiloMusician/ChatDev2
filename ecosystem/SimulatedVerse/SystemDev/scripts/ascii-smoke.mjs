#!/usr/bin/env node
import { writeFileSync, mkdirSync, existsSync } from "node:fs";

const report = { ok:true, checks:[] };

function check(cond, name){ 
  report.checks.push({name, ok:!!cond}); 
  if(!cond) report.ok=false; 
}

try {
  check(existsSync("styles/ascii.css"), "fonts-config-present? (styles/ascii.css exists)");
  check(existsSync("ascii/ui/AsciiView.ts"), "<ascii-view> component exists");
  check(existsSync("ascii/core/Buffer2D.ts"), "Buffer2D core component exists");
  check(existsSync("ascii/core/Bus.ts"), "Event bus system exists");
  check(existsSync("modules/culture_ship/ui/asciiHud.ts"), "HUD integration exists");
} catch { 
  report.ok=false; 
}

mkdirSync("reports",{recursive:true});
writeFileSync("reports/ascii_smoke.json", JSON.stringify(report,null,2));
console.log(report.ok ? "✅ ASCII smoke passed" : "⚠️ ASCII smoke found issues");