#!/usr/bin/env node
// Culture-Ship hook: expose Unicode + Zalgo to ASCII HUD, Conlang, and OmniTag.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

export function unicodeBootWire(){
  if (!existsSync("assets/unicode/atlas.json")) {
    console.log("⚠️ Unicode Atlas not found. Run npm run unicode:build first.");
    return { status: "missing", guidance: "Build atlas first" };
  }

  const atlas = JSON.parse(readFileSync("assets/unicode/atlas.json","utf8"));
  const variants = JSON.parse(readFileSync("assets/unicode/variants.json","utf8"));

  const wiring = {
    status: "ok",
    atlasCount: atlas.count,
    variants: Object.keys(variants),
    guidance: {
      safeZalgoProfiles: ["readable","subtle","vivid","artful"],
      accessibility: "Mirror any styled text with plain-text tooltips and aria-labels; provide stripCombining() in UI."
    }
  };
  
  mkdirSync("reports",{recursive:true});
  writeFileSync("reports/unicode_wiring.json", JSON.stringify(wiring,null,2));
  return wiring;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.log("🔗 Unicode wired:", unicodeBootWire());
}