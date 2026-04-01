// packages/conductor/autoMapper.ts
/**
 * Conductor auto-mapper:
 * - Inputs: 12-tone row square, register masks, section targets
 * - Outputs: per-bar unions & per-instrument pc assignments
 * - Maintains ICV bias and a T6I invariance floor by injecting an "invariant pad"
 */
import type { LayoutSpec, ScanResult } from "../council/events/topics";
import { publishLayout, publishCascade } from "../council/events/publishers";

export type RegisterMask = { name: string; range: [number, number]; pcs?: number[] };
export type SectionPolicy = {
  bars: number;
  targetICV?: Partial<Record<1|2|3|4|5|6, number>>; // min counts per bar union
  invarianceFloorT6I?: number; // 0..1
  invariantPadWeight?: number; // 0..1 fraction of voices reserved for pad
  padSource?: "intersection" | "rowHexachordA" | "rowHexachordB";
};

export type AutoMapRequest = {
  sectionId: string;
  row: number[];            // 12 pcs
  square: number[][];       // 12x12
  registers: RegisterMask[];
  policy: SectionPolicy;
  recentWindows?: ScanResult["windows"]; // optional context for intersection pad
};

function ic(a: number, b: number) {
  const d = (b - a + 12) % 12;
  return Math.min(d, 12 - d);
}

function icvOf(set: number[]) {
  const s = Array.from(new Set(set)).sort((a,b)=>a-b);
  const v = [0,0,0,0,0,0];
  for (let i=0;i<s.length;i++) for (let j=i+1;j<s.length;j++) {
    const c = ic(s[i], s[j]) - 1;
    if (c>=0) v[c]++;
  }
  return v as [number,number,number,number,number,number];
}

function invarianceT6I(set: number[]) {
  const a = new Set(set);
  const inv = new Set(set.map(p => (6 - p + 12) % 12));
  let keep = 0;
  a.forEach(p => { if (inv.has(p)) keep++; });
  return a.size ? keep / a.size : 1.0;
}

function takeIntersectionPad(windows?: AutoMapRequest["recentWindows"]) {
  if (!windows || windows.length===0) return [];
  const all = windows.map(w => new Set(w.pcs));
  let acc = new Set<number>(all[0]);
  for (let i=1;i<all.length;i++) {
    acc = new Set([...acc].filter(x => all[i].has(x)));
  }
  return [...acc].sort((a,b)=>a-b);
}

function hexachords(row: number[]) { return [row.slice(0,6), row.slice(6,12)]; }

/** Greedy assign pcs to registers, keeping ic targets loosely and reserving pad voices */
export function autoMap(req: AutoMapRequest) {
  const { sectionId, row, square, registers, policy, recentWindows } = req;
  const bars = policy.bars ?? 8;
  const padWeight = policy.invariantPadWeight ?? 0.25;
  const floor = policy.invarianceFloorT6I ?? 0.35;

  const [A, B] = hexachords(row);
  let pad: number[] = [];
  if (policy.padSource === "intersection") pad = takeIntersectionPad(recentWindows);
  else if (policy.padSource === "rowHexachordA") pad = A;
  else if (policy.padSource === "rowHexachordB") pad = B;

  const out: LayoutSpec = { sectionId, bars: [] };

  for (let bar=1; bar<=bars; bar++) {
    // choose a square row for this bar (cycle down the diagonal for variety)
    const Pi = square[(bar-1)%12];
    // pad assignment: reserve a fraction of registers to sustain pad pcs
    const nPadRegs = Math.max(1, Math.floor(registers.length * padWeight));
    const padRegs = registers.slice(0, nPadRegs);
    const leadRegs = registers.slice(nPadRegs);

    // choose union: some subset of Pi plus pad to meet ic targets
    let union = Array.from(new Set([...(Pi.slice(0,6)), ...pad])).sort((a,b)=>a-b);

    // refine union to satisfy minimal ICV targets if provided
    if (policy.targetICV) {
      let loops = 0;
      while (loops < 24) {
        const v = icvOf(union);
        let ok = true;
        for (const k of Object.keys(policy.targetICV)) {
          const idx = Number(k)-1 as 0|1|2|3|4|5;
          const need = policy.targetICV[idx+1 as 1|2|3|4|5|6] ?? 0;
          if (v[idx] < need) { ok = false; break; }
        }
        if (ok) break;
        // add another pc from Pi if available
        for (const p of Pi) if (!union.includes(p)) { union.push(p); break; }
        union = Array.from(new Set(union)).sort((a,b)=>a-b);
        loops++;
      }
    }

    // invariance pad: if T6I is low, bolster with pad pcs / inversion
    const inv = invarianceT6I(union);
    if (inv < floor) {
      const invSet = union.map(p => (6 - p + 12) % 12);
      union = Array.from(new Set([...union, ...pad, ...invSet])).sort((a,b)=>a-b);
    }

    // Assign pcs to registers (round-robin; pad regs sustain pad)
    const assigns: Record<string, number[]> = {};
    const pcs = union.slice();
    let idx = 0;
    for (const r of padRegs) assigns[r.name] = pad.slice();
    for (const r of leadRegs) {
      const take = [];
      for (let k=0;k<Math.max(2, Math.floor(union.length/leadRegs.length)); k++) {
        if (pcs.length===0) break;
        take.push(pcs[idx % pcs.length]);
        idx++;
      }
      assigns[r.name] = Array.from(new Set(take)).sort((a,b)=>a-b);
    }

    out.bars.push({ bar, union: union.sort((a,b)=>a-b), assignments: assigns });
  }

  publishLayout(out);
  if (policy.invarianceFloorT6I) {
    const lastBar = out.bars[out.bars.length-1];
    const inv = invarianceT6I(lastBar.union);
    if (inv < floor) publishCascade({ kind: "invariance_dip", op: "T6I", ratio: inv, sectionId });
  }
  return out;
}