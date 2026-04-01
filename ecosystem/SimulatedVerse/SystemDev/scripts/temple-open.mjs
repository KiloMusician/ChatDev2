import {writeFileSync, mkdirSync} from "node:fs";
import {existsSync, readFileSync} from "node:fs";
mkdirSync("modules/culture_ship/temples/temple_of_knowledge/floors",{recursive:true});
const f1 = "modules/culture_ship/temples/temple_of_knowledge/floors/01_foundation.md";
if(!existsSync(f1)){
  writeFileSync(f1, `# Temple of Knowledge — Floor 1 (Foundation)
- Ethic: Preserve life; intervene only under Special Circumstances.
- Infrastructure-first: local tools over paid APIs.
- Mobile-first HUD toggles; never regress small screens.
- Big Red Button: \`npm run cascade\` when low tokens.
- Next: Floor 2 unlocks after 3 clean cascades + 1 green smoke.
`);
}
const hudPath="modules/culture_ship/temples/index.md";
writeFileSync(hudPath, `# 🛕 Temple of Knowledge
- [Floor 1: Foundation](./temples/temple_of_knowledge/floors/01_foundation.md)
- Run: \`npm run cascade\` then \`npm run temple:open\`
`);
console.log("🛕 Temple opened. See modules/culture_ship/temples/index.md");