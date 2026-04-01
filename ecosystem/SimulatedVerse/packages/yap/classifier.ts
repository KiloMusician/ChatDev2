// packages/yap/classifier.ts
import fs from "node:fs";
import yaml from "js-yaml";
import { YapLog, YapClassification, YapTag } from "./types";

type Rule = { label: string; contains_any?: string[]; tags?: YapTag[] };

export class HeuristicClassifier {
  private rules: Rule[] = [];
  constructor(ruleFile = "config/yap_rules.yml") {
    try {
      const raw = fs.readFileSync(ruleFile, "utf-8");
      const y = yaml.load(raw) as any;
      this.rules = (y?.heuristics ?? []) as Rule[];
    } catch {
      this.rules = [];
    }
  }
  classify(log: YapLog): YapClassification[] {
    const text = `${log.source} ${log.level} ${log.message} ${JSON.stringify(log.data ?? {})}`.toLowerCase();
    const out: YapClassification[] = [];
    for (const r of this.rules) {
      const hits = (r.contains_any ?? []).filter(k => text.includes(String(k).toLowerCase()));
      if (hits.length) {
        out.push({
          label: r.label,
          score: Math.min(1, 0.5 + hits.length * 0.1),
          tags: r.tags ?? [],
          reasons: hits.map(h => `hit:${h}`)
        });
      }
    }
    if (out.length === 0) {
      out.push({ label: "unclassified", score: 0.1, tags: [], reasons: [] });
    }
    return out;
  }
}