// packages/archivist/semanticTrail.ts
/**
 * Semantic Audit Trail:
 * For each significant action, emit a QGL doc with:
 *  - reasoning_chain
 *  - hypothesis_tested
 *  - outcome_analysis
 *  - next_improvement_suggestion
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { councilBus } from "../council/events/eventBus";

export type SemanticQGL = {
  qgl_version: "0.2";
  id: string;
  kind: "audit.semantic";
  created_at: string;
  content: {
    action_topic: string;
    payload_snapshot: any;
    reasoning_chain: string[];
    hypothesis_tested: string;
    outcome_analysis: {
      success: boolean;
      expected?: any;
      actual?: any;
      deltas?: Record<string, number>;
    };
    next_improvement_suggestion: string;
  };
  tags: {
    omni: Record<string, any>;
    mega: Record<string, any>;
  };
};

const OUT_DIR = process.env.SEMANTIC_ARCHIVE || "archive/semantic";
const SIGNIFICANT: RegExp[] = [
  /^chatdev\.session\.end$/,
  /^build\.result$/,
  /^test\.result$/,
  /^deploy\.result$/,
  /^mhsa\.scan\.result$/,
  /^orchestrate\.layout$/,
  /^sentinel\.cascade$/,
  /^directive\.strategic$/,
  /^pawn\.state_changed$/,
  /^work_scheduler\.task_completed$/,
  /^autonomous_loop\.decision$/,
];

function matches(t: string) {
  return SIGNIFICANT.some(rx => rx.test(t));
}

function hash(s: string) {
  return crypto.createHash("sha1").update(s).digest("hex");
}

function pickReasoning(payload: any): string[] {
  // best-effort extraction; align to your agent payload schema
  const r =
    payload?.reasoning_chain ??
    payload?.trace ??
    payload?.prompts ??
    payload?.history ??
    payload?.reasoning ??
    [];
  const arr = Array.isArray(r) ? r : [String(r)];
  return arr.map(String).slice(0, 20);
}

function inferHypothesis(topic: string, payload: any): string {
  if (topic === "build.result") return "Build should pass on main after refactor";
  if (topic === "test.result") return "New tests should improve coverage without failures";
  if (topic === "orchestrate.layout") return "Layout should satisfy invariance floor + ICV targets";
  if (topic === "chatdev.session.end") return "Role prompts should produce a runnable patch";
  if (topic === "autonomous_loop.decision") return `Decision '${payload?.decision || 'unknown'}' should optimize system state`;
  if (topic === "pawn.state_changed") return "Pawn state change should improve colony well-being";
  return payload?.hypothesis ?? `Action on ${topic} should succeed`;
}

function analyzeOutcome(topic: string, payload: any) {
  const success =
    payload?.ok === true ||
    payload?.success === true ||
    payload?.status === "ok" ||
    payload?.status === 0 ||
    payload?.didSatisfy === true ||
    payload?.confidence > 0.5;

  const expected = payload?.expected ?? null;
  const actual = payload?.actual ?? payload ?? null;

  // quick metric deltas if present
  const deltas: Record<string, number> = {};
  const m = payload?.metrics || payload?.richState?.resources || payload?.colony_health || null;
  if (m && typeof m === "object") {
    for (const k of Object.keys(m)) {
      const v = m[k];
      if (typeof v === "number") deltas[k] = v;
    }
  }
  return { success: !!success, expected, actual, deltas };
}

function suggestNext(topic: string, payload: any, outcome: {success:boolean; deltas?:Record<string,number>}) {
  if (!outcome.success) {
    if (topic === "build.result") return "Bisect failing target; retry with cache disabled; pin toolchain version";
    if (topic === "test.result") return "Run flaky-test detector; quarantine offenders; increase seed count";
    if (topic === "orchestrate.layout") return "Lower invariantPadWeight by 0.05; switch padSource to intersection; regenerate 12 rows";
    if (topic === "chatdev.session.end") return "Mutate CEO/Programmer prompts by +1 constraint; A/B next session";
    if (topic === "autonomous_loop.decision") return "Increase confidence threshold; gather more agent consensus; implement fallback strategy";
    return "Capture failing context; add counterfactual; schedule A/B variant";
  }
  // success → escalate improvement
  if (topic === "autonomous_loop.decision") return "Lock-in successful decision pattern; apply to similar contexts; monitor long-term outcomes";
  return "Lock-in parameters; raise target thresholds by 5%; schedule stress test";
}

export function startSemanticTrail() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  (councilBus as any).subscribeAll((ev: any) => {
    if (!matches(ev.topic)) return;

    const reasoning_chain = pickReasoning(ev.payload);
    const hypothesis_tested = inferHypothesis(ev.topic, ev.payload);
    const outcome_analysis = analyzeOutcome(ev.topic, ev.payload);
    const next_improvement_suggestion = suggestNext(ev.topic, ev.payload, outcome_analysis);

    const id = `sem:${hash(`${ev.topic}|${ev.ts}|${JSON.stringify(ev.payload).slice(0,512)}`)}`;
    const doc: SemanticQGL = {
      qgl_version: "0.2",
      id,
      kind: "audit.semantic",
      created_at: new Date(ev.ts).toISOString(),
      content: {
        action_topic: ev.topic,
        payload_snapshot: ev.payload,
        reasoning_chain,
        hypothesis_tested,
        outcome_analysis,
        next_improvement_suggestion,
      },
      tags: {
        omni: { "audit/kind": "semantic", topic: ev.topic },
        mega: { "score/success": outcome_analysis.success ? 1 : 0 }
      }
    };

    const file = path.join(OUT_DIR, `${id.replace(":","_")}.json`);
    fs.writeFile(file, JSON.stringify(doc, null, 2), () => {});
    // broadcast for dashboards / learners
    councilBus.publish("audit.semantic", doc);
  });

  console.log("[semantic] Semantic Audit Trail active →", OUT_DIR);
}