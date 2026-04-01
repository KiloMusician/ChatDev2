import { indexRosetta } from "../src/rosetta/rosetta_stone_interpreter";
import { rosettaBreath } from "../src/rosetta/breaths/rosetta_breath";
import { writeJSON } from "../src/rosetta/io";
import * as fs from "fs";

const candidates = [
  "knowledge/RosettaStone.md",
  "knowledge/tiers.md",
  "knowledge/rosetta.txt"
].filter(fs.existsSync);

if (candidates.length===0) {
  console.log("No RosettaStone doc found (knowledge/*).");
  process.exit(0);
}
const sourcePath = candidates[0];
const text = fs.readFileSync(sourcePath,"utf8");
const idx = indexRosetta(text, sourcePath);
const res = rosettaBreath(idx);

const ts = new Date().toISOString().replace(/[:.]/g,"");
writeJSON(`reports/rosetta/index_${ts}.json`, idx);
writeJSON(`reports/rosetta/checks_${ts}.json`, res);

console.log("Rosetta index + checks written.");
if (!res.ok) process.exitCode = 2;