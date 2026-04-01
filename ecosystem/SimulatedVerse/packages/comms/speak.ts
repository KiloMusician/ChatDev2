// packages/comms/speak.ts
import fs from "node:fs";
import path from "node:path";
import { councilBus } from "../council/events/eventBus";

type SpeakMsg = {
  ts: number;           // epoch ms
  from: string;         // agent id e.g. "skeptic", "raven", "Mladenč"
  level?: "info"|"warn"|"error"|"success";
  title: string;
  text: string;         // short message; details go to QGL/Archive
  tags?: Record<string, any>;
};

const OUT = path.resolve("public/inbox.json");

// Append to /public/inbox.json (ETag-friendly for UI polling)
export function speak(msg: Omit<SpeakMsg, "ts">) {
  const rec: SpeakMsg = { ts: Date.now(), level: "info", ...msg };
  let list: SpeakMsg[] = [];
  try { list = JSON.parse(fs.readFileSync(OUT, "utf-8") || "[]"); } catch {}
  list.unshift(rec);
  list = list.slice(0, 500); // cap
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(list, null, 2));
  councilBus.publish("ops.speak", rec);
  return rec;
}

// Convenience
export const shout  = (from: string, title: string, text: string, tags?: any) =>
  speak({ from, level:"warn", title, text, tags });

export const cheer  = (from: string, title: string, text: string, tags?: any) =>
  speak({ from, level:"success", title, text, tags });

export const whisper= (from: string, title: string, text: string, tags?: any) =>
  speak({ from, level:"info", title, text, tags });