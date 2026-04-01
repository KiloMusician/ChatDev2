// packages/archivist/stub.ts
/**
 * Archivist stub: persist every Council event with lightweight
 * OmniTag/MegaTag-ish headers for later retrieval.
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { councilBus } from "../council/events/eventBus";

// Define BusEvent interface locally since it's not exported
interface BusEvent {
  id: string;
  topic: string;
  payload: any;
  timestamp: string;
  ts?: number;
}

const ROOT = process.env.ARCHIVE_DIR || "archive";

function tagHeaders(ev: BusEvent) {
  return {
    id: crypto.createHash("sha1").update(`${ev.topic}|${ev.ts}|${JSON.stringify(ev.payload).slice(0,256)}`).digest("hex"),
    created_at: new Date(ev.ts || Date.now()).toISOString(),
    topic: ev.topic,
    tags: {
      "source": "CouncilBus",
      "megatag": "ΞNuSyQ::Music::MHSA",
      "omnitag": {
        "tick": (ev as any)?.payload?.tick ?? null,
        "invariance/T6I": (ev as any)?.payload?.invariance?.find?.((x:any)=>x.op==="T6I")?.ratio ?? null
      }
    }
  };
}

export function startArchivist() {
  fs.mkdirSync(ROOT, { recursive: true });
  (councilBus as any).subscribeAll((ev: BusEvent) => {
    const head = tagHeaders(ev);
    const dir = path.join(ROOT, ev.topic.replace(/\./g, "_"));
    fs.mkdirSync(dir, { recursive: true });
    const file = path.join(dir, `${head.id}.json`);
    fs.writeFile(file, JSON.stringify({ head, payload: ev.payload }, null, 2), () => {});
  });
  console.log("[archivist] stub active; writing to", ROOT);
}