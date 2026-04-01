#!/usr/bin/env tsx
import { promises as fs } from "node:fs";

type PU = { id: string; kind: string; title: string; files?: string[]; proof: { kind: string; target: string; expect: any } };

async function main() {
  const issues = JSON.parse(await fs.readFile("reports/qsa/issues.json","utf8")).filter(Boolean);
  const dupes = JSON.parse(await fs.readFile("reports/qsa/dupes.json","utf8"));
  const spam  = JSON.parse(await fs.readFile("reports/qsa/spam.json","utf8"));

  const pus: PU[] = [];

  // 1) Hard-coded errors / placeholders
  const hard = issues.filter((x:any)=>x.hardcoded);
  if (hard.length) {
    pus.push({
      id: "pu-qsa-hardcoded-errors",
      kind: "refactor",
      title: `Eliminate ${hard.length} hard-coded error sites`,
      files: hard.slice(0,250).map((x:any)=>x.path),
      proof: { kind: "grep-absent", target: "reports/qsa/issues.json", expect: "hardcoded" }
    });
  }
  const todo = issues.filter((x:any)=>x.placeholders);
  if (todo.length) {
    pus.push({
      id: "pu-qsa-placeholders",
      kind: "cleanup",
      title: `Address ${todo.length} TODO/FIXME/TBD placeholders`,
      files: todo.slice(0,250).map((x:any)=>x.path),
      proof: { kind: "threshold", target: "reports/qsa/issues.json", expect: { placeholders_lt: Math.floor(todo.length*0.3) } }
    });
  }

  // 2) Exact / near dupes
  if (dupes.exact?.length) {
    pus.push({
      id: "pu-qsa-exact-dupes",
      kind: "consolidate",
      title: `Consolidate ${dupes.exact.length} exact duplicate clusters`,
      files: dupes.exact.flatMap((d:any)=>d.paths.slice(0,10)),
      proof: { kind: "dedupe", target: "reports/qsa/dupes.json", expect: { exact_clusters: 0 } }
    });
  }
  if (dupes.near?.length) {
    pus.push({
      id: "pu-qsa-near-dupes",
      kind: "anneal",
      title: `Anneal ${dupes.near.length} near-duplicate pairs`,
      files: dupes.near.slice(0,200).flatMap((d:any)=>[d.a,d.b]),
      proof: { kind: "threshold", target: "reports/qsa/dupes.json", expect: { near_pairs_lt: Math.floor(dupes.near.length*0.5) } }
    });
  }

  // 3) Spam storms
  if (spam.storms?.length) {
    pus.push({
      id: "pu-qsa-spam-storms",
      kind: "archive",
      title: `Archive/compress ${spam.storms.length} spam buckets`,
      files: spam.storms.flatMap((s:any)=>s.samples),
      proof: { kind: "archive", target: "reports/qsa/spam.json", expect: { storms: 0 } }
    });
  }

  await fs.writeFile("reports/qsa/pus.ndjson", pus.map(x=>JSON.stringify(x)).join("\n")+"\n");
  console.log(`[qsa] proposed ${pus.length} PUs → reports/qsa/pus.ndjson`);
}

main().catch(e=>{ console.error(e); process.exit(1); });