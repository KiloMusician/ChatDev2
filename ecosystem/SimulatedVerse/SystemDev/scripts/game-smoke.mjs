import {writeFileSync, mkdirSync} from "node:fs";
import {existsSync} from "node:fs";

const required = [
  "client/src/components/game/AsciiViewport.tsx",
  "client/src/components/game/GameShell.tsx", 
  "client/src/components/game/BootGate.tsx",
  "client/src/components/game/TitleScreen.tsx",
  "client/src/state/gameStore.ts"
];

const ok = required.every(p=>existsSync(p));
const missing = required.filter(p=>!existsSync(p));

mkdirSync("reports",{recursive:true});
writeFileSync("reports/game_smoke.json", JSON.stringify({
  ok, 
  at: new Date().toISOString(), 
  missing,
  components_created: required.length - missing.length,
  total_required: required.length
},null,2));

console.log(ok ? "✅ Game smoke test passed - all components ready" : `⚠️ Game smoke test failed - missing ${missing.length} components`);