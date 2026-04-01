import { ensureState, loadConfig } from "../core/state.mjs";
import { tick } from "./ship_tick.mjs";

(async () => {
  const cfg = await loadConfig();
  await ensureState(cfg);
  console.log("⛭ Culture-Ship bootstrapped. Entering guardian loop…");
  // Hand the terminal back to the "game/server" if present:
  // – In mobile/preview, we still run our guardian ticks as a child loop.
  await tick({ mode: "boot" });
})();