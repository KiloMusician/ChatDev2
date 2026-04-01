#!/usr/bin/env node
import { glob } from "glob";
import { mkdirSync, writeFileSync } from "node:fs";

const PANELS = glob.sync("**/*.{tsx,jsx,svelte,vue}", {ignore:["**/node_modules/**","**/dist/**","**/.git/**"]})
  .filter(f => /(hud|ui|panel|view|screen|ascii|console|map|builder|defense|labyrinth|dungeon|city)/i.test(f))
  .map(f => ({file:f, key:f.replace(/^.*\/(.*)\..+$/,'$1').toLowerCase()}));

mkdirSync("reports",{recursive:true});
writeFileSync("reports/ui_panels.json", JSON.stringify(PANELS,null,2));
console.log(`🧭 UI index: ${PANELS.length} candidate panels found (reports/ui_panels.json)`);