#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

let bp = {
  "stats": {"mining_power": 1, "labs": 1, "synergy.mech": 0},
  "currencies": ["scrap","ore","credits","insight","energy"]
};

if(existsSync("data/idle/blueprint.json")) {
  bp = JSON.parse(readFileSync("data/idle/blueprint.json","utf8"));
}

let t=0, tier=1, mining=0, research=0, stats={...bp.stats, labs:1};

for(let i=0;i<300;i++){ // 5 minutes @ 1s ticks
  const rateMining = stats.mining_power*(1+(stats["synergy.mech"]||0));
  mining += rateMining;
  const rateResearch = stats.labs*(1+ (0/1000));
  research += rateResearch;
  t++;
}

mkdirSync("reports",{recursive:true});
writeFileSync("reports/idle_sim_preview.json", JSON.stringify({t, mining, research},null,2));
console.log("⏱️ Idle sim preview (reports/idle_sim_preview.json).");