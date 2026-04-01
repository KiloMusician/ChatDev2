#!/usr/bin/env tsx
/**
 * ΞNuSyQ Receipt System - Proof-gated logging
 * All actions must write receipts or they didn't happen
 */
import { writeFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const REPORTS_DIR = "reports";

export function ensureReportsDir() {
  if (!existsSync(REPORTS_DIR)) {
    mkdirSync(REPORTS_DIR, { recursive: true });
  }
}

export type Receipt = {
  ts: number;
  actor: string;
  action: string;
  inputs?: any;
  outputs?: any;
  ok: boolean;
  error?: string;
};

export function writeReceipt(receipt: Receipt) {
  ensureReportsDir();
  const entry = JSON.stringify(receipt);
  appendFileSync(join(REPORTS_DIR, "run_ledger.ndjson"), entry + "\n");
}

export function writeReport(filename: string, data: any) {
  ensureReportsDir();
  writeFileSync(join(REPORTS_DIR, filename), JSON.stringify(data, null, 2));
}

export function logAction(actor: string, action: string, inputs: any, fn: () => any) {
  const start = Date.now();
  try {
    const outputs = fn();
    writeReceipt({
      ts: start,
      actor,
      action,
      inputs,
      outputs,
      ok: true
    });
    return outputs;
  } catch (error) {
    writeReceipt({
      ts: start,
      actor,
      action,
      inputs,
      ok: false,
      error: error instanceof Error ? error.message : String(error)
    });
    throw error;
  }
}

// Initialize ledger
writeReceipt({
  ts: Date.now(),
  actor: "sage",
  action: "receipt_system_init",
  ok: true
});