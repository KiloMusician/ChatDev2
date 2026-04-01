import {execSync} from "node:child_process";
import {writeFileSync, mkdirSync} from "node:fs";
import {existsSync} from "node:fs";

try {
  const out = execSync(`rg -n "(TODO|FIXME|PLACEHOLDER|XXX)" --hidden -S . | head -1000 || true`, {stdio:"pipe", maxBuffer: 1024*1024}).toString();
  if (!existsSync("reports")) mkdirSync("reports",{recursive:true});
  writeFileSync("reports/scan_todos.txt", out);
  console.log(`✅ TODO/FIXME scan complete. Matches: ${out.split("\n").filter(Boolean).length}`);
} catch(e) {
  // Fallback to simple grep if ripgrep fails
  try {
    const out = execSync(`grep -rn "TODO\\|FIXME\\|PLACEHOLDER\\|XXX" . | head -500 || true`, {stdio:"pipe"}).toString();
    if (!existsSync("reports")) mkdirSync("reports",{recursive:true});
    writeFileSync("reports/scan_todos.txt", out);
    console.log(`✅ TODO/FIXME scan complete (fallback). Matches: ${out.split("\n").filter(Boolean).length}`);
  } catch(e2) {
    if (!existsSync("reports")) mkdirSync("reports",{recursive:true});
    writeFileSync("reports/scan_todos.txt", "");
    console.log(`⚠️ TODO/FIXME scan failed, empty report created`);
  }
}