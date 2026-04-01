import fs from "node:fs/promises";
import path from "node:path";

const FILE = path.resolve(".ship/memory.json");
// Memory type: { softLock, lastRun, heuristics, health, drivers }

const DEFAULT = {
  softLock:{active:false},
  lastRun:0,
  heuristics:{preferZeroToken:true, suspicionOfDupes:false},
  health:{brokenImports:0, lastScore:0.7},
  drivers:{pilotEnabled:true, taskmasterEnabled:true, councilEnabled:true, librarianEnabled:true, intermediaryEnabled:true}
};

export class ShipMemory {
  static async load() {
    try { return JSON.parse(await fs.readFile(FILE,"utf-8")); } catch { return DEFAULT; }
  }
  static async save(m) {
    await fs.mkdir(path.dirname(FILE),{recursive:true});
    await fs.writeFile(FILE, JSON.stringify(m,null,2));
  }
}