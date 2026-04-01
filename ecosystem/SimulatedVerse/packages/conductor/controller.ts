// packages/conductor/controller.ts
import { councilBus } from "../council/events/eventBus";
import { autoMap, type AutoMapRequest } from "./autoMapper";
import type { RowgenCandidates, ScanResult } from "../council/events/topics";

let lastScan: ScanResult | null = null;
let lastRow: number[] | null = null;
let lastSquare: number[][] | null = null;

councilBus.subscribe("mhsa.scan.result", ev => { lastScan = ev.payload as ScanResult; });
councilBus.subscribe("rowgen.candidates", ev => {
  const rows = (ev.payload as RowgenCandidates).rows;
  if (rows?.length) lastRow = rows[0].row;
});
councilBus.subscribe("square.result", ev => { lastSquare = (ev.payload as any).matrix; });

/** Map immediately using most recent scan/row/square */
export function mapNow(sectionId="Section.A") {
  if (!lastRow || !lastSquare) {
    console.warn("[conductor] missing row or square; cannot map");
    return;
  }
  const req: AutoMapRequest = {
    sectionId,
    row: lastRow,
    square: lastSquare,
    registers: [
      { name: "V1", range: [72, 96] },
      { name: "V2", range: [60, 84] },
      { name: "Va", range: [55, 79] },
      { name: "Vc", range: [43, 67] }
    ],
    policy: {
      bars: 8,
      targetICV: { 1: 3, 5: 2 },
      invarianceFloorT6I: 0.35,
      invariantPadWeight: 0.25,
      padSource: "intersection"
    },
    recentWindows: lastScan?.windows ?? []
  };
  const spec = autoMap(req);
  console.log("[conductor] mapped layout for", sectionId, "bars:", spec.bars.length);
}

/** Optional: map when both row and square arrive */
export function enableAutoMapOnSquare(sectionId="Section.A") {
  councilBus.subscribe("square.result", () => mapNow(sectionId));
}