// packages/yap/yapMonitor.ts
import fs from "node:fs";
import path from "node:path";
import { councilBus } from "./councilBusShim";
import { HeuristicClassifier } from "./classifier";
import { llmClassify } from "./llmAdapter";
import { toQGL } from "./qglBridge";
import type { YapLog } from "./types";

const OUT = process.env.YAP_ARCHIVE || "yap_archive";
const classifier = new HeuristicClassifier(process.env.YAP_RULES || "config/yap_rules.yml");

function writeQGL(doc: any) {
  const dir = path.join(OUT, "qgl");
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${doc.id.replace(":","_")}.json`);
  fs.writeFile(file, JSON.stringify(doc, null, 2), () => {});
}

// Capture console.* and funnel into Yap
export function attachConsoleCapture() {
  const orig = { log: console.log, warn: console.warn, error: console.error, info: console.info };
  function wrap(level: "info"|"warn"|"error"|"debug", fn: (...a:any[])=>void) {
    return (...args:any[]) => {
      try {
        const msg = args.map(a => typeof a === "string" ? a : JSON.stringify(a)).join(" ");
        ingest({ ts: Date.now(), level, source: "console", message: msg });
      } catch {}
      fn(...args);
    };
  }
  console.log = wrap("info", orig.log);
  console.info = wrap("info", orig.info);
  console.warn = wrap("warn", orig.warn);
  console.error = wrap("error", orig.error);
}

export async function ingest(log: YapLog) {
  // 1) Optional LLM
  const llm = await llmClassify(log);
  // 2) Heuristics
  const heur = classifier.classify(log);
  const classes = (llm && llm.length ? llm : heur);

  // 3) QGL doc
  const qgl = toQGL(log, classes);
  writeQGL(qgl);

  // 4) Publish to Council HUD
  councilBus.publish("ops.yap", { log, classes, qgl });
}

// Hook bus errors and sentinel cascades automatically
export function attachBusListeners() {
  councilBus.subscribe("sentinel.cascade", ev => {
    ingest({ ts: ev.ts, level: "warn", source: "sentinel.cascade", message: JSON.stringify(ev.payload) });
  });
  councilBus.subscribe("mhsa.scan.result", ev => {
    ingest({ ts: ev.ts, level: "info", source: "mhsa.scan.result", message: "scan windows", data: { count: (ev.payload as any)?.windows?.length ?? 0 } });
  });
}