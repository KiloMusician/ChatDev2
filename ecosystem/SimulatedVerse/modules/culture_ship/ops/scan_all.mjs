import { execSync } from "node:child_process";
import { globSync } from "glob";
import fs from "node:fs/promises";

export async function scanAll({ fast = false } = {}) {
  console.log(`🔍 Culture-Ship scan ${fast ? "(fast)" : "(full)"}`);
  
  const results = {
    files: [],
    imports: [],
    duplicates: [],
    placeholders: [],
    health: { score: 0.7, brokenImports: 0, duplicateGroups: 0 }
  };

  try {
    // Fast scan: just critical files and imports
    const files = globSync("**/*.{ts,tsx,js,jsx,mjs,cjs}", {
      ignore: ["**/node_modules/**", "**/dist/**", "**/.git/**"]
    });
    
    results.files = files.slice(0, fast ? 50 : 1000);
    
    // Check for broken imports
    for (const file of results.files.slice(0, fast ? 20 : 100)) {
      try {
        const content = await fs.readFile(file, "utf8");
        const importMatches = content.match(/import.*from\s+['"][^'"]+['"]/g) || [];
        for (const imp of importMatches) {
          const pathMatch = imp.match(/['"]([^'"]+)['"]/);
          if (pathMatch && pathMatch[1].startsWith('./') && !pathMatch[1].includes('.')) {
            results.imports.push({ file, import: pathMatch[1], missing: true });
            results.health.brokenImports++;
          }
        }
      } catch (e) {
        // Skip files that can't be read
      }
    }

    // Quick placeholder scan
    if (!fast) {
      try {
        const todoOut = execSync('rg -c "TODO|FIXME|PLACEHOLDER" . || echo "0"', { encoding: 'utf8' });
        results.placeholders = parseInt(todoOut.trim()) || 0;
      } catch (e) {
        results.placeholders = 0;
      }
    }

    results.health.score = Math.max(0, 1 - (results.health.brokenImports * 0.02));
    
  } catch (error) {
    console.warn("⚠️ Scan error:", error.message);
  }

  return results;
}