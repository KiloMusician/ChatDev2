import { emitReceipt } from "./events";
export function receipt(type:string, data:any) {
  const r = {
    type, data,
    ts: new Date().toISOString(),
    subsystem: "GameDev",
    law: "receipts-first",
  };
  emitReceipt(r);
  // Optional: POST to a tiny receipts endpoint or write to console logger
  console.debug("[RECEIPT]", r);
}