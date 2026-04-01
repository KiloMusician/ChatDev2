import {writeFileSync, mkdirSync} from "node:fs";
import {existsSync, readFileSync} from "node:fs";

const checks = {
  viewport: existsSync("client/src/components/game/AsciiViewport.tsx"),
  gameStore: existsSync("client/src/state/gameStore.ts"),
  gameShell: existsSync("client/src/components/game/GameShell.tsx"),
  appUpdated: existsSync("client/src/components/game/BootGate.tsx"),
  stylesExist: existsSync("client/src/styles.css")
};

mkdirSync("reports",{recursive:true});
writeFileSync("reports/ascii_doctor.json", JSON.stringify(checks,null,2));
console.log("✅ ASCII doctor complete");