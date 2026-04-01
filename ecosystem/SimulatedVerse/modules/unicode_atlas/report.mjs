#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

if (!existsSync("assets/unicode/atlas.json")) {
  console.log("⚠️ Run npm run unicode:build first");
  process.exit(1);
}

const atlas = JSON.parse(readFileSync("assets/unicode/atlas.json","utf8"));
const variants = JSON.parse(readFileSync("assets/unicode/variants.json","utf8"));

const planes = new Map();
for (const entry of atlas.atlas){
  const p = entry.plane;
  planes.set(p, (planes.get(p)||0)+1);
}

let md = `# Unicode Summary\n\nTotal codepoints (PUA excluded): **${atlas.count}**\n\n## Planes\n`;
for (const [p,c] of [...planes.entries()].sort((a,b)=>a[0]-b[0])){
  md += `- Plane ${p}: ${c}\n`;
}
md += `\n## Variants available\n- math_bold: ${Object.keys(variants.math_bold).length} glyphs\n- superscript: ${Object.keys(variants.superscript).length}\n- subscript: ${Object.keys(variants.subscript).length}\n- circled_digits: ${Object.keys(variants.circled_digits).length}\n`;

mkdirSync("reports",{recursive:true});
writeFileSync("reports/unicode_summary.md", md);
console.log("📝 Wrote reports/unicode_summary.md");