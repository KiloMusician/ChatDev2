import fs from "fs/promises";
const STATE = "state/ship_state.json";
const CFG = "modules/culture_ship/manifest.yml";

export async function ensureState() {
  try { await fs.access(STATE); } catch { await fs.mkdir("state", { recursive: true }); await fs.writeFile(STATE, JSON.stringify({ lastTick: null, crew: {}, health: {} }, null, 2)); }
}
export async function getState() { await ensureState(); return JSON.parse(await fs.readFile(STATE, "utf8")); }
export async function saveState(x) { await fs.writeFile(STATE, JSON.stringify(x, null, 2)); }
export async function loadConfig() { try { return (await fs.readFile(CFG, "utf8")); } catch { return ""; } }
export const nowISO = () => new Date().toISOString();