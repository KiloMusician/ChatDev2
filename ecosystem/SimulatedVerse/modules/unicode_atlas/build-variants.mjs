#!/usr/bin/env node
// Build a map of styled variants: math bold/italic, small caps, circled, superscripts/subscripts.
// We include only safe, widely-available sets. Where missing, we omit (no fake fallbacks here).

import { writeFileSync, mkdirSync } from "node:fs";

const A_Z = [...Array(26)].map((_,i)=>String.fromCharCode(0x41+i));
const a_z = [...Array(26)].map((_,i)=>String.fromCharCode(0x61+i));
const ZERO_NINE = [...Array(10)].map((_,i)=>String(i));

// Math Alphanumeric Symbols (partial; extend as needed)
const MATH_BOLD_BASE = 0x1D400; // A
const MATH_BOLD_LOWER = 0x1D41A; // a
const MATH_BOLD_DIGIT = 0x1D7CE; // 0

function mapShift(base, letters){
  const out = {};
  letters.forEach((ch, i)=> out[ch] = String.fromCodePoint(base + i));
  return out;
}

// Superscripts/Subscripts (sparse maps)
const SUPERS = {
  "0":"\u2070","1":"\u00B9","2":"\u00B2","3":"\u00B3",
  "4":"\u2074","5":"\u2075","6":"\u2076","7":"\u2077","8":"\u2078","9":"\u2079",
  "+":"\u207A","-":"\u207B","=":"\u207C","(":"\u207D",")":"\u207E","n":"\u207F","i":"\u2071"
};
const SUBS = {
  "0":"\u2080","1":"\u2081","2":"\u2082","3":"\u2083","4":"\u2084",
  "5":"\u2085","6":"\u2086","7":"\u2087","8":"\u2088","9":"\u2089",
  "+":"\u208A","-":"\u208B","=":"\u208C","(":"\u208D",")":"\u208E","a":"\u2090","e":"\u2091","o":"\u2092","x":"\u2093","h":"\u2095","k":"\u2096","l":"\u2097","m":"\u2098","n":"\u2099","p":"\u209A","s":"\u209B","t":"\u209C"
};

// Enclosed Alphanumerics (circled digits/letters; partial showcase)
function circledDigit(n){
  // 1..20 => U+2460..U+2473 (approx)
  if (n>=1 && n<=20) return String.fromCharCode(0x245F + n);
  return null;
}

const mathBoldUpper = mapShift(MATH_BOLD_BASE, A_Z);
const mathBoldLower = mapShift(MATH_BOLD_LOWER, a_z);
const mathBoldDigit = mapShift(MATH_BOLD_DIGIT, ZERO_NINE);

const variants = {
  math_bold: { ...mathBoldUpper, ...mathBoldLower, ...mathBoldDigit },
  superscript: SUPERS,
  subscript: SUBS,
  circled_digits: Object.fromEntries([...Array(20)].map((_,i)=>[String(i+1), circledDigit(i+1)]).filter(([k,v])=>v)),
  // Hints for other sets we can add later (math italic, script, double-struck, sans, monospace, etc.)
  hints: ["math_italic", "double_struck", "script", "fraktur", "sans", "monospace"]
};

mkdirSync("assets/unicode",{recursive:true});
writeFileSync("assets/unicode/variants.json", JSON.stringify(variants,null,2));
console.log("✅ Variants map saved to assets/unicode/variants.json");