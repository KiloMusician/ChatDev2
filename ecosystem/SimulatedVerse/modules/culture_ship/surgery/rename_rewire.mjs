import fs from "node:fs/promises";

// Rename files + fix all references (simple, extendable)
export async function renameAndRewire(task) {
  const { from, to, refs } = task; // refs = [files to patch]
  try {
    await fs.rename(from, to);
    console.log(`📁 Renamed: ${from} → ${to}`);
    
    for (const r of refs || []) {
      try {
        const src = await fs.readFile(r, "utf8");
        const out = src.replaceAll(from, to);
        if (out !== src) {
          await fs.writeFile(r, out);
          console.log(`🔗 Updated reference in ${r}`);
        }
      } catch (e) {
        console.warn(`⚠️ Failed to update reference in ${r}:`, e.message);
      }
    }
    return true;
  } catch (e) {
    console.warn(`⚠️ Failed to rename ${from} → ${to}:`, e.message);
    return false;
  }
}