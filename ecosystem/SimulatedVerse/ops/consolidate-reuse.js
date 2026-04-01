// ops/consolidate-reuse.js
// Smart file consolidation - never delete content, only alias and recycle empties
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPORT_DIR = path.join(__dirname, "../public/ops-report");
fs.mkdirSync(REPORT_DIR, { recursive: true });

function sha1(content) { 
  return crypto.createHash("sha1").update(content).digest("hex"); 
}

function readFileSafe(filePath) { 
  try { 
    return fs.readFileSync(filePath, "utf-8"); 
  } catch { 
    return null; 
  } 
}

function chooseCore(paths) {
  // Heuristic: prefer packages/* > apps/* > client/* ; prefer non-test files
  const score = (p) => {
    let s = 0;
    if (p.startsWith("packages/")) s += 3;
    else if (p.startsWith("apps/")) s += 2;
    else if (p.startsWith("client/")) s += 1;
    
    // Prefer non-test files
    if (/\.(spec|test)\./.test(p)) s -= 0.5;
    
    // Prefer index files
    if (p.includes("/index.")) s += 0.3;
    
    // Prefer src directories
    if (p.includes("/src/")) s += 0.2;
    
    return s;
  };
  
  return [...paths].sort((a, b) => score(b) - score(a))[0];
}

function findDuplicates() {
  const patterns = [
    "**/*.{ts,tsx,js,jsx,css,json}",
    "!node_modules/**",
    "!client/dist/**", 
    "!public/**",
    "!.git/**",
    "!**/*.recycled",
    "!**/__alias_to_core*"
  ];
  
  const byHash = new Map();
  const files = [];
  
  try {
    // Use find for better cross-platform compatibility
    const result = fs.readdirSync('.', { withFileTypes: true, recursive: true })
      .filter(dirent => dirent.isFile())
      .map(dirent => path.join(dirent.path || '', dirent.name))
      .filter(f => /\.(ts|tsx|js|jsx|css|json)$/.test(f))
      .filter(f => !f.includes('node_modules') && !f.includes('.git'))
      .slice(0, 200); // Limit for performance
      
    for (const f of result) {
      files.push(f);
    }
  } catch (e) {
    console.warn("[consolidate] Failed to scan files:", e.message);
  }
  
  for (const filePath of files) {
    const content = readFileSafe(filePath);
    if (content === null) continue;
    
    // Normalize whitespace for comparison
    const normalized = content.replace(/\s+/g, " ").trim();
    const contentLength = normalized.length;
    
    // Skip tiny files unless they're completely empty
    if (contentLength < 10 && contentLength > 0) continue;
    
    const hash = sha1(normalized);
    const arr = byHash.get(hash) || [];
    arr.push({ file: filePath, length: contentLength, content: normalized });
    byHash.set(hash, arr);
  }
  
  const duplicates = [];
  for (const [hash, fileGroup] of byHash.entries()) {
    if (fileGroup.length > 1) {
      const core = chooseCore(fileGroup.map(f => f.file));
      duplicates.push({ 
        hash: hash.slice(0, 8), 
        files: fileGroup,
        core,
        duplicateCount: fileGroup.length
      });
    }
  }
  
  return duplicates.slice(0, 20); // Limit output
}

function createAliases(duplicates) {
  const actions = [];
  
  for (const dupGroup of duplicates) {
    const { core, files } = dupGroup;
    
    for (const fileInfo of files) {
      const { file: filePath, length, content } = fileInfo;
      
      if (filePath === core) continue; // Skip the core file
      
      if (length === 0) {
        // Truly empty file → recycle (rename with .recycled extension)
        const recycledName = filePath + ".recycled";
        try {
          if (!fs.existsSync(recycledName)) {
            fs.renameSync(filePath, recycledName);
            actions.push({ 
              type: "recycle_empty", 
              from: filePath, 
              to: recycledName, 
              core 
            });
          }
        } catch (e) {
          console.warn("[consolidate] Failed to recycle:", filePath, e.message);
        }
      } else if (length < 200 && !content.includes('import') && !content.includes('export')) {
        // Very small non-import file → repurpose as alias
        const dir = path.dirname(filePath);
        const ext = path.extname(filePath) || ".ts";
        const aliasName = path.join(dir, "__alias_to_core" + ext);
        
        try {
          const relativePath = path.relative(dir, core).replace(/\\/g, "/");
          const aliasContent = ext.match(/tsx?$/) 
            ? `// Auto-generated alias to core implementation\nexport * from "./${relativePath}";\nexport { default as __core_default } from "./${relativePath}";\n`
            : `// Auto-generated alias to core implementation\nmodule.exports = require("./${relativePath}");\n`;
          
          if (!fs.existsSync(aliasName)) {
            fs.writeFileSync(aliasName, aliasContent);
            actions.push({ 
              type: "alias_created", 
              alias: aliasName, 
              core, 
              replaced: filePath 
            });
          }
        } catch (e) {
          console.warn("[consolidate] Failed to create alias:", filePath, e.message);
        }
      }
    }
  }
  
  return actions;
}

function generateReport(duplicates, actions) {
  const report = {
    timestamp: Date.now(),
    summary: {
      duplicates_found: duplicates.length,
      actions_taken: actions.length,
      empty_files_recycled: actions.filter(a => a.type === 'recycle_empty').length,
      aliases_created: actions.filter(a => a.type === 'alias_created').length
    },
    duplicates: duplicates.slice(0, 10), // Limit for UI
    actions: actions.slice(0, 20),
    policy: "NO_DELETIONS - only aliasing and recycling empty files"
  };
  
  const reportPath = path.join(REPORT_DIR, "consolidate.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  return report;
}

async function main() {
  console.log("[consolidate] 🔍 Scanning for duplicate files...");
  
  const duplicates = findDuplicates();
  console.log(`[consolidate] 📦 Found ${duplicates.length} duplicate groups`);
  
  const actions = createAliases(duplicates);
  console.log(`[consolidate] ✅ Performed ${actions.length} consolidation actions`);
  
  const report = generateReport(duplicates, actions);
  console.log(`[consolidate] 📋 Report written: ${report.summary.duplicates_found} dupes, ${report.summary.actions_taken} actions`);
  
  // Log summary for visibility
  if (actions.length > 0) {
    console.log("[consolidate] Actions taken:");
    actions.slice(0, 5).forEach(action => {
      if (action.type === 'recycle_empty') {
        console.log(`  ♻️  Recycled empty: ${action.from} → ${action.to}`);
      } else if (action.type === 'alias_created') {
        console.log(`  🔗 Created alias: ${action.alias} → ${action.core}`);
      }
    });
  }
}

// Graceful error handling
main().catch(e => {
  console.error("[consolidate] 💥 Fatal error:", e.message);
  process.exit(1);
});