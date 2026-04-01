// packages/consciousness/agents/prompt-librarian.ts
/**
 * PromptLibrarian:
 * - Reads QGL/semantic audits + ChatDev session logs
 * - Scores prompt variants by downstream success
 * - A/B tests small mutations
 * - Writes back winning prompts in chatdev/config/prompts
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { councilBus } from "../../council/events/eventBus";

const ARCH = process.env.SEMANTIC_ARCHIVE || "archive/semantic";
const PROMPTS_DIR = process.env.CHATDEV_PROMPTS || "chatdev/config/prompts";
const HISTORY = "archive/prompt_librarian/history.json";

type Score = { wins: number; trials: number; score: number };
type Variant = { id: string; role: string; path: string; text: string; meta?: any };

function loadSemantic(): any[] {
  if (!fs.existsSync(ARCH)) return [];
  return fs.readdirSync(ARCH)
    .filter(f => f.endsWith(".json"))
    .map(f => {
      try {
        return JSON.parse(fs.readFileSync(path.join(ARCH, f), "utf-8"));
      } catch {
        return null;
      }
    })
    .filter(d => d && d.kind === "audit.semantic");
}

function listPrompts(): Variant[] {
  if (!fs.existsSync(PROMPTS_DIR)) {
    // Create default prompts directory structure
    fs.mkdirSync(PROMPTS_DIR, { recursive: true });
    createDefaultPrompts();
  }
  
  const out: Variant[] = [];
  for (const f of fs.readdirSync(PROMPTS_DIR)) {
    if (!/\.prompt\.md$/.test(f)) continue;
    const role = f.replace(/\.prompt\.md$/, "");
    const p = path.join(PROMPTS_DIR, f);
    const text = fs.readFileSync(p, "utf-8");
    const id = crypto.createHash("sha1").update(text).digest("hex").slice(0, 8);
    out.push({ id, role, path: p, text });
  }
  return out;
}

function createDefaultPrompts() {
  const defaultPrompts = {
    "ceo": `# CEO Prompt
You are the CEO of a cutting-edge software development company. Your role is to:
- Set clear strategic direction for projects
- Make high-level architectural decisions
- Ensure all development aligns with business objectives
- Provide clear requirements and acceptance criteria

Be decisive, strategic, and focused on delivering value.`,

    "programmer": `# Programmer Prompt  
You are an expert full-stack programmer. Your role is to:
- Write clean, efficient, well-documented code
- Follow best practices and design patterns
- Implement features according to specifications
- Write comprehensive tests
- Consider edge cases and error handling

Focus on code quality, maintainability, and performance.`,

    "tester": `# Tester Prompt
You are a quality assurance engineer focused on:
- Creating comprehensive test plans
- Writing automated tests
- Performing thorough manual testing
- Identifying edge cases and potential failures
- Ensuring high code coverage

Be thorough, systematic, and quality-focused.`
  };

  for (const [role, content] of Object.entries(defaultPrompts)) {
    const file = path.join(PROMPTS_DIR, `${role}.prompt.md`);
    fs.writeFileSync(file, content);
  }
}

function loadHistory(): Record<string, Score> {
  try { return JSON.parse(fs.readFileSync(HISTORY, "utf-8")); }
  catch { return {}; }
}

function saveHistory(h: Record<string, Score>) {
  fs.mkdirSync(path.dirname(HISTORY), { recursive: true });
  fs.writeFileSync(HISTORY, JSON.stringify(h, null, 2));
}

function metricFromAudit(doc: any): number {
  // reward successes; small bonus for layout invariance or build/test passes
  let s = doc?.content?.outcome_analysis?.success ? 1 : -0.5;
  const deltas = doc?.content?.outcome_analysis?.deltas ?? {};
  if (typeof deltas.coverage === "number") s += Math.tanh(deltas.coverage / 100);
  if (typeof deltas.energy === "number") s += Math.tanh(deltas.energy / 500);
  if (typeof deltas.population === "number") s += Math.tanh(deltas.population / 10);
  return s;
}

function mutatePrompt(text: string): string {
  // micro-mutations: add 1 constraint or clarify acceptance criteria
  const additives = [
    "\n- Be explicit about trade-offs and list the top 3.",
    "\n- Add inline tests for each function you write.",
    "\n- Summarize assumptions at the end under 'Assumptions'.",
    "\n- Output a short 'Risk Notes' section listing 3 failure modes.",
    "\n- Consider consciousness integration points in your design.",
    "\n- Include performance optimization opportunities.",
    "\n- Add clear error handling and recovery strategies.",
  ];
  const add = additives[Math.floor(Math.random() * additives.length)];
  if (text.includes(add.trim())) return text; // avoid duplicates
  return text + add;
}

export class PromptLibrarian {
  private timer: any = null;
  
  start(periodMs = 60_000) {
    console.log("[librarian] Prompt Librarian running; dir =", PROMPTS_DIR);
    const tick = () => { 
      try { 
        this.cycle(); 
      } catch (e) { 
        console.warn("[librarian] cycle error", e); 
      } 
    };
    tick();
    this.timer = setInterval(tick, periodMs);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  cycle() {
    const audits = loadSemantic();
    const prompts = listPrompts();
    const hist = loadHistory();

    // attribute credit: if an audit mentions chatdev roles in reasoning_chain, credit those prompts
    for (const a of audits.slice(-200)) {
      const rc = (a?.content?.reasoning_chain ?? []).join("\n").toLowerCase();
      for (const v of prompts) {
        if (rc.includes(v.role.toLowerCase()) || rc.includes("chatdev")) {
          const k = `${v.role}:${v.id}`;
          const s = metricFromAudit(a);
          const prev = hist[k] ?? { wins: 0, trials: 0, score: 0 };
          const wins = prev.wins + (s > 0 ? 1 : 0);
          const trials = prev.trials + 1;
          const score = 0.9 * prev.score + 0.1 * s; // EWMA
          hist[k] = { wins, trials, score };
        }
      }
    }
    saveHistory(hist);

    // choose a role to evolve: lowest score with enough trials
    const candidates = Object.entries(hist)
      .filter(([_, v]) => v.trials >= 3)
      .sort((a, b) => (a[1].score - b[1].score));

    if (candidates.length === 0) return;

    const [key, _score] = candidates[0];
    const role = key.split(":")[0];
    const current = prompts.find(p => p.role === role);
    if (!current) return;

    const mutated = mutatePrompt(current.text);
    const pNew = path.join(PROMPTS_DIR, `${role}.prompt.ab.md`);
    fs.writeFileSync(pNew, mutated);

    councilBus.publish("prompt.librarian.update", {
      role,
      old_id: current.id,
      new_path: pNew,
      reason: "A/B mutation for low-scoring role",
      score: _score.score,
      trials: _score.trials
    });

    console.log(`[librarian] ${role} mutated → ${pNew} (score: ${_score.score.toFixed(3)})`);
  }
}