import { getState } from "../core/state.mjs";
import { tick } from "./ship_tick.mjs";

(async () => {
  const s = await getState();
  console.log("🛰️ Verify: lastTick =", s.lastTick);
  if (!s.lastTick) {
    console.log("No last tick found → running a safe tick now.");
    await tick({ mode: "verify" });
  } else {
    console.log("Ship operational. Ready to continue.");
  }
})();