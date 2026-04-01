#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { execSync } from "node:child_process";

try{ execSync("tsc -v",{stdio:"ignore"});}catch{}

const tpl = `/* AUTO-GENERATED HUD Shell (dry preview)
Import visiblePanels(flags,tier,isMobile) from src/hud/panels.ts
Render a tab bar (mobile) or sidebar (desktop). Bind each panel by key.
ASCII viewport mounts into #ascii-root div when active.
*/`;

mkdirSync("reports",{recursive:true});
writeFileSync("reports/hud_build_preview.txt", tpl);
console.log("🧩 HUD build preview generated (reports/hud_build_preview.txt). Apply manually or let ChatDev patch.");