// packages/yap/qglBridge.ts
/**
 * Minimal RosettaStone.QGL bridge: wraps a log + tags into a QGL document.
 */
import crypto from "node:crypto";
import { YapLog, YapClassification } from "./types";
import { toOmniTags, toMegaTagBundle } from "./omniMegaTag";

export function toQGL(log: YapLog, classes: YapClassification[]) {
  const id = crypto.createHash("sha1").update(`${log.ts}|${log.source}|${log.message}`).digest("hex");
  const omni = Object.assign({}, ...classes.map(toOmniTags));
  const mega = toMegaTagBundle(classes);

  return {
    qgl_version: "0.2",
    id: `yap:${id}`,
    kind: "diagnostic.log",
    created_at: new Date(log.ts).toISOString(),
    content: {
      text: log.message,
      data: log.data ?? {}
    },
    links: [],
    tags: {
      omni, mega,
      "yap/source": log.source,
      "yap/level": log.level
    }
  };
}