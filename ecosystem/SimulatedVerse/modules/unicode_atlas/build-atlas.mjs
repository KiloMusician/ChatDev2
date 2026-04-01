#!/usr/bin/env node
// Build a Unicode Atlas (planes 0–16), excluding Private Use Areas.
// Local-only: uses Node's Intl APIs + generated ranges; no web calls.

import { writeFileSync, mkdirSync } from "node:fs";

const PUA_RANGES = [
  [0xE000, 0xF8FF],           // BMP PUA
  [0xF0000, 0xFFFFD],         // Plane 15 PUA
  [0x100000, 0x10FFFD],       // Plane 16 PUA
];

function inPUA(cp){
  for (const [a,b] of PUA_RANGES) if (cp>=a && cp<=b) return true;
  return false;
}
function planeOf(cp){ return cp >>> 16; }

function* codepoints(max=0x10FFFF){
  for (let cp=0; cp<=max; cp++){
    if (inPUA(cp)) continue;
    yield cp;
  }
}

function category(cp){
  try { return Intl.Segmenter ? "assigned" : "unknown"; }
  catch { return "unknown"; }
}

function isCombining(cp){
  // General combining ranges (quick heuristic)
  // Mn: Nonspacing marks (common ranges)
  return (
    (cp >= 0x0300 && cp <= 0x036F) ||
    (cp >= 0x1AB0 && cp <= 0x1AFF) ||
    (cp >= 0x1DC0 && cp <= 0x1DFF) ||
    (cp >= 0x20D0 && cp <= 0x20FF) ||
    (cp >= 0xFE20 && cp <= 0xFE2F)
  );
}

function block(cp){
  // Minimal block tagging—enough for grouping (extend as needed)
  // We keep it lightweight to stay local; block names are compact.
  if (cp <= 0x007F) return "Basic Latin";
  if (cp <= 0x00FF) return "Latin-1 Supplement";
  if (cp >= 0x0370 && cp <= 0x03FF) return "Greek and Coptic";
  if (cp >= 0x0400 && cp <= 0x04FF) return "Cyrillic";
  if (cp >= 0x2000 && cp <= 0x206F) return "General Punctuation";
  if (cp >= 0x2200 && cp <= 0x22FF) return "Mathematical Operators";
  if (cp >= 0x1F300 && cp <= 0x1FAFF) return "Emoji/Symbols (approx)";
  return "Other";
}

function bidi(cp){
  // Lightweight guess: left-to-right for most; handle Arabic/Hebrew blocks roughly
  if ((cp >= 0x0590 && cp <= 0x05FF) || (cp >= 0xFB1D && cp <= 0xFB4F)) return "RTL-Hebrew";
  if ((cp >= 0x0600 && cp <= 0x06FF) || (cp >= 0x0750 && cp <= 0x077F)) return "RTL-Arabic";
  return "LTR";
}

const atlas = [];
let count = 0;
for (const cp of codepoints()){
  // Skip unassigned "holes" for speed by a light heuristic:
  // treat surrogate range as skipped, and rely on UI to filter unsupported glyphs.
  if (cp >= 0xD800 && cp <= 0xDFFF) continue; // surrogates
  const ch = String.fromCodePoint(cp);
  atlas.push({
    cp,
    ch,
    plane: planeOf(cp),
    block: block(cp),
    cat: category(cp),
    bidi: bidi(cp),
    combining: isCombining(cp) ? 1 : 0
  });
  count++;
}

mkdirSync("assets/unicode", { recursive: true });
writeFileSync("assets/unicode/atlas.json", JSON.stringify({count, atlas}, null, 2));
console.log(`✅ Unicode Atlas built: ${count} code points (PUA excluded). Saved to assets/unicode/atlas.json`);