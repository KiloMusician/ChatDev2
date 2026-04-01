#!/usr/bin/env node
import { zalgoSafe, stripCombining, PROFILES } from "./lib/zalgo.mjs";

const samples = [
  "Harmony",
  "ΞNuSyQ",
  "OmniTag",
  "MegaTag",
  "SimulatedVerse"
];

for (const name of samples){
  console.log(`\n-- ${name} --`);
  for (const prof of Object.keys(PROFILES)){
    const z = zalgoSafe(name, prof);
    console.log(prof.padEnd(9), ":", z, " | plain:", stripCombining(z));
  }
}