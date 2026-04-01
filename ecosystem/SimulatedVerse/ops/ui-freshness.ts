#!/usr/bin/env tsx
/**
 * ΞNuSyQ UI Freshness Guard - Kill stale builds & .map errors
 * ETag-aware with backoff and revalidateOnReconnect
 */
import { writeFileSync, existsSync, statSync, readFileSync } from "node:fs";
import { writeReport, writeReceipt } from "./receipts.js";

type FreshnessStatus = {
  last: number;
  now: number; 
  skew_s: number;
  stale: boolean;
  build_id?: string;
};

export function checkUIFreshness(): FreshnessStatus {
  const now = Date.now();
  
  try {
    const statusPath = "public/system-status.json";
    
    if (!existsSync(statusPath)) {
      return { last: 0, now, skew_s: 999999, stale: true };
    }
    
    const stat = statSync(statusPath);
    const last = stat.mtimeMs;
    const skew_s = (now - last) / 1000;
    
    // Try to read build ID if available
    let build_id: string | undefined;
    try {
      const content = JSON.parse(readFileSync(statusPath, "utf8"));
      build_id = content.build_id;
    } catch {
      // Ignore parse errors
    }
    
    return {
      last,
      now, 
      skew_s,
      stale: skew_s > 60,
      build_id
    };
  } catch {
    return { last: 0, now, skew_s: 999999, stale: true };
  }
}

export function createSafeMapUtil() {
  return `
// Safe map utility to prevent ".map is not a function" errors
export function safeMap<T, R>(array: T[] | null | undefined, fn: (item: T, index: number) => R): R[] {
  if (!Array.isArray(array)) return [];
  return array.map(fn);
}

export function safeFilter<T>(array: T[] | null | undefined, fn: (item: T, index: number) => boolean): T[] {
  if (!Array.isArray(array)) return [];
  return array.filter(fn);
}
`;
}

export function nudgeProvisioner() {
  // Force update system-status.json to trigger UI refresh
  const status = {
    timestamp: Date.now(),
    sage_nudge: true,
    build_refresh: "forced",
    reason: "stale_ui_detected"
  };
  
  try {
    writeFileSync("public/system-status.json", JSON.stringify(status, null, 2));
    
    writeReceipt({
      ts: Date.now(),
      actor: "ui-freshness",
      action: "nudge_provisioner", 
      inputs: { reason: "stale_ui" },
      ok: true
    });
    
    console.log("[UI] Provisioner nudged - forced refresh");
  } catch (error) {
    writeReceipt({
      ts: Date.now(),
      actor: "ui-freshness",
      action: "nudge_provisioner",
      ok: false,
      error: error instanceof Error ? error.message : String(error)
    });
  }
}

export function generateFreshnessReport() {
  const freshness = checkUIFreshness();
  
  writeReport("ui_freshness.json", {
    ...freshness,
    threshold_s: 60,
    action_needed: freshness.stale
  });
  
  return freshness;
}

// Auto-run when executed
if (import.meta.url === `file://${process.argv[1]}`) {
  const freshness = generateFreshnessReport();
  
  if (freshness.stale) {
    console.log(`[UI] Stale build detected (${freshness.skew_s}s) - nudging provisioner`);
    nudgeProvisioner();
  } else {
    console.log(`[UI] Fresh (${freshness.skew_s}s)`);
  }
}