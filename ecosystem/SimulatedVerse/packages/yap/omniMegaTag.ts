// packages/yap/omniMegaTag.ts
import { YapClassification } from "./types";

export function toOmniTags(cls: YapClassification): Record<string, any> {
  const tags: Record<string, any> = {};
  for (const t of cls.tags) tags[t.key] = t.value;
  tags["omnitag/kind"] = cls.label;
  return tags;
}

export function toMegaTagBundle(classifications: YapClassification[]) {
  // compress classifications into a high-level bundle for retrieval
  const bundle: Record<string, any> = {};
  for (const c of classifications) {
    bundle[`meg/${c.label}`] = (bundle[`meg/${c.label}`] ?? 0) + c.score;
    for (const t of c.tags) bundle[`tag/${t.key}`] = t.value;
  }
  return bundle;
}