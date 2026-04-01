#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

let cart = [];
if(existsSync("reports/cartograph.json")) {
  cart = JSON.parse(readFileSync("reports/cartograph.json","utf8"));
}

const useful = cart.filter(x => ["system","hybrid","game"].includes(x.type));
const abilities = useful.reduce((acc,x)=>{
  const f=x.file;
  const ab = /scripts\/|cascade|analyzers|planners|surgeons/.test(f) ? "surgery"
          : /src\/hud|ui|ascii|console/.test(f) ? "navigation"
          : /data\/|blueprint|lore|docs|temple/.test(f) ? "librarianship"
          : /src\/game|rogue|dungeon|builder|defense/.test(f) ? "simulation"
          : "aux";
  (acc[ab] ||= []).push(f); 
  return acc;
}, {});

mkdirSync("reports",{recursive:true});
writeFileSync("reports/ship_bindings.json", JSON.stringify(abilities,null,2));
console.log("🚢 Ship bindings written (reports/ship_bindings.json).");