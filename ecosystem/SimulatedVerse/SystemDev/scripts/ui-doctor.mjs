import {execSync} from "node:child_process";
import {writeFileSync, mkdirSync} from "node:fs";

const out = {};
try { out.routes = execSync(`rg -n "route|router|Link|NavLink" --hidden -S client || true`).toString(); } catch {}
try { out.aria = execSync(`rg -n "aria-|role=" --hidden -S client || true`).toString(); } catch {}
try { out.css = execSync(`rg -n "(min-width|max-width|@media|z-index)" --hidden -S client || true`).toString(); } catch {}
try { out.components = execSync(`find client/src/components -name "*.tsx" -o -name "*.ts" | wc -l`).toString().trim(); } catch {}

mkdirSync("reports",{recursive:true});
writeFileSync("reports/ui_doctor.json", JSON.stringify(out,null,2));
console.log("✅ UI doctor complete");