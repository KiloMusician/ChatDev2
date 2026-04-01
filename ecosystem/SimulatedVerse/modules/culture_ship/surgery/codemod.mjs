import fs from "node:fs/promises";

// Example: fix a relative import path
export async function codemod(task) {
  if (task.action === "fix_import_path") {
    const { file, from, to } = task.data; // e.g., { file:"src/x.ts", from:"../a", to:"./a" }
    try {
      const src = await fs.readFile(file, "utf8");
      const out = src.replace(new RegExp(`from\\s+['"]${from}['"]`, "g"), `from "${to}"`);
      if (out !== src) {
        await fs.writeFile(file, out);
        console.log(`🔧 Fixed import in ${file}: ${from} → ${to}`);
      }
      return true;
    } catch (e) {
      console.warn(`⚠️ Failed to fix import in ${file}:`, e.message);
      return false;
    }
  }
  return false;
}