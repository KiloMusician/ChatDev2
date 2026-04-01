// ops/sage/elastic.ts
// Elastic cooldown: shortens on momentum, lengthens on strain. Always bounded.
// τ: expected duration in ms; ctx: live telemetry.
export function elasticCooldown(
  τ: number,
  ctx: {
    // failure & pressure signals
    timeouts: number; // recent count (rolling 5–10m)
    rateLimits: number; // 429s
    econn: number; // ECONNREFUSED / ENOTCONN / EPIPE cluster
    backlog: number; // pending PUs
    idleStreakMs: number; // no receipts since...
    // momentum & health signals
    receipts: number; // recent concrete receipts (diffs/tests/reports)
    uiFreshSkewMs: number; // system-status.json skew
  }
) {
  const base = Math.max(110, Math.min(11_000, Math.round(1.10 * τ))); // 0.11s…11s…11m caps
  const strain =
    0.35 * Math.min(1, ctx.timeouts / 3) +
    0.30 * Math.min(1, ctx.rateLimits / 3) +
    0.20 * Math.min(1, ctx.econn / 3) +
    0.15 * Math.min(1, ctx.backlog / 50);

  const stagnancy = Math.min(1, ctx.idleStreakMs / 60_000); // ≥60s without receipts
  const health =
    0.40 * Math.min(1, ctx.receipts / 3) +
    0.60 * Math.max(0, 1 - Math.min(1, ctx.uiFreshSkewMs / 60_000));

  // lengthen with strain/stagnancy, shorten with health/momentum
  const factor = 1 + 0.9 * strain + 0.5 * stagnancy - 0.6 * health;
  const τe = Math.max(50, Math.min(60 * 60 * 1000, Math.round(base * factor)));
  return τe;
}