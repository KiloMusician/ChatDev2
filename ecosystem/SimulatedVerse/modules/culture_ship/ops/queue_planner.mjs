import { suggestEdits } from "./suggest_edits.mjs";
import { findDuplicates } from "./scan_duplicates.mjs";
import { importAudit } from "./scan_imports.mjs";
import { topo } from "./toposort.mjs";

export async function queuePlan({ scan, budget }) {
  // Convert scans → concrete tasks (prefer surgical/local operations first).
  const tasks = [];
  tasks.push(...await suggestEdits(scan));  // typos, placeholders, empty files
  tasks.push(...await findDuplicates(scan)); // safe deletes, merges
  tasks.push(...await importAudit(scan));    // path fixes
  // Weighting: local fixes >> build/dev UX >> nice-to-haves
  const plan = topo(tasks); // enforce dependencies
  return { items: plan, policy: { budget } };
}