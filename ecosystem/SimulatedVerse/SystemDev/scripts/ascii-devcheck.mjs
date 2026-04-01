#!/usr/bin/env node
import { execSync } from "node:child_process";

const tryRun = (cmd)=>{ 
  try{ 
    execSync(cmd,{stdio:"inherit"}); 
    return true; 
  }catch{ 
    return false; 
  } 
};

console.log("Devcheck: running scans and smoke…");
tryRun("node scripts/cartograph.mjs");
tryRun("node scripts/scan-placeholders.mjs");
tryRun("node scripts/ui-index.mjs");
tryRun("node scripts/ascii-smoke.mjs");
console.log("Done.");