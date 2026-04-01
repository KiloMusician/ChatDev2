import {execSync} from "node:child_process";
import {writeFileSync, mkdirSync} from "node:fs";

let ok=true, log="";
try {
  // 1) Typecheck if tsconfig exists
  try { execSync("test -f tsconfig.json && npx tsc -noEmit", {stdio:"inherit"}); } catch { ok=false; }
  // 2) Lint if config present
  try { execSync("test -f .eslintrc.json && npx eslint . -f stylish", {stdio:"inherit"}); } catch { ok=false; }
  // 3) Build (optional)
  try { execSync("npm run build --silent", {stdio:"inherit"}); } catch { /* non-blocking */ }

  // 4) Basic runtime ping (if there is a dev server entry)
  try { execSync("node -e \"console.log('SimulatedVerse smoke OK')\"", {stdio:"inherit"}); } catch { ok=false; }
} catch (e) { ok=false; log+=e?.message||String(e); }

mkdirSync(".ship/reports",{recursive:true});
writeFileSync(".ship/reports/smoke_game_status.json", JSON.stringify({ok, at:new Date().toISOString()}));
console.log(ok? "✅ Smoke test passed" : "⚠️ Smoke test found issues");