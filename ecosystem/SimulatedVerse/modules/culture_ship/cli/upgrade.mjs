#!/usr/bin/env node
import { Upgrades } from "../upgrades/index.js";
const name = process.argv[2];
if (!name || !Upgrades[name]) {
  console.log("Usage: node upgrade.mjs <telemetry+|surgery++|queue++|librarian+>");
  process.exit(1);
}
await Upgrades[name].apply();
console.log(`[Ship] Applied upgrade: ${name}`);