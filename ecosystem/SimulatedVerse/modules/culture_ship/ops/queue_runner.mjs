import { dryrunGuard } from "../policies/dryrun_guard.mjs";
import { codemod } from "../surgery/codemod.mjs";
import { renameAndRewire } from "../surgery/rename_rewire.mjs";

const handlers = {
  "surgical-edit": codemod,
  "rename-rewire": renameAndRewire,
  "delete-file": async (t) => { console.log("🗑️ Delete file:", t.data); return true; },
  "write-file": async (t) => { console.log("📝 Write file:", t.data); return true; },
  "import.fix": async (t) => { console.log("🔧 Fix imports:", t.data); return true; },
};

export async function runQueue({ plan, budget }) {
  let done = 0;
  for (const t of plan.items || []) {
    if (!(await dryrunGuard(t))) continue;
    const fn = handlers[t.kind];
    if (!fn) { console.log("⚠️ Unknown task:", t.kind); continue; }
    const ok = await fn(t, { budget });
    if (ok) done++;
  }
  return { done };
}