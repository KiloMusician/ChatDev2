import fs from "fs/promises";
export async function budgetGuard() {
  try {
    const s = JSON.parse(await fs.readFile("state/budget.json", "utf8"));
    // Hard floor: only local ops if below thresholds
    return (s.monthly_remaining_usd || 0) > (s.min_floor_usd || 0.50);
  } catch { return false; } // default to local-only
}