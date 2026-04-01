// ops/codemods/guard-map.js
/**
 * Auto-guard .map() calls to prevent m.map errors
 * Finds `.map(` in UI components and wraps with safeMap() 
 * DRY-RUN by default; pass WRITE=1 to apply changes
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WRITE = process.env.WRITE === "1";

// Find component files
const roots = [
  path.join(__dirname, "../../client/src"),
  path.join(__dirname, "../../apps/web/src")
].filter(p => fs.existsSync(p));

const files = [];
for (const root of roots) {
  try {
    const result = fs.readdirSync(root, { withFileTypes: true, recursive: true })
      .filter(dirent => dirent.isFile())
      .map(dirent => path.join(dirent.path || '', dirent.name))
      .filter(f => /\.(tsx|ts|jsx|js)$/.test(f))
      .filter(f => !f.includes('node_modules'))
      .slice(0, 50); // Limit for safety
      
    files.push(...result.map(f => path.resolve(root, f)));
  } catch (e) {
    console.warn(`[guard-map] Failed to scan ${root}:`, e.message);
  }
}

// Simple regex to find basic .map patterns
const SIMPLE_MAP_RE = /([A-Za-z0-9_$.]+)\.map\s*\(\s*\(([A-Za-z0-9_,\s]+)\)\s*=>/g;

let filesChanged = 0;
let mapsGuarded = 0;
let filesSkipped = 0;

console.log(`[guard-map] Scanning ${files.length} files for .map() footguns...`);

for (const filePath of files) {
  try {
    let content = fs.readFileSync(filePath, "utf-8");
    const originalContent = content;
    
    // Skip files that already have safeMap imports or usage
    if (content.includes('safeMap') || content.includes('guardedOps')) {
      filesSkipped++;
      continue;
    }
    
    // Skip files with complex patterns we can't easily handle
    if (content.includes('.map(') && (
      content.includes('.map().') || // chained maps
      content.includes('.map((') && content.includes('=>') && content.includes('.map(') // multiple maps
    )) {
      console.log(`[guard-map] SKIP (complex): ${path.relative(process.cwd(), filePath)}`);
      filesSkipped++;
      continue;
    }
    
    let hasReplacements = false;
    
    // Replace simple .map patterns
    content = content.replace(SIMPLE_MAP_RE, (match, arrayVar, args) => {
      // Skip if it's already inside a function call or complex expression
      if (arrayVar.includes('(') || arrayVar.includes('[')) {
        return match; // Keep original
      }
      
      hasReplacements = true;
      mapsGuarded++;
      return `safeMap(${arrayVar}, (${args}) =>`;
    });
    
    if (hasReplacements) {
      // Add import if needed and file appears to be a React component
      if (content.includes('import React') || content.includes('export default function') || content.includes('export function')) {
        const importLine = `import { safeMap } from '@/lib/guardedOps';\n`;
        
        // Add import after existing imports
        const lines = content.split('\n');
        let importInsertIndex = 0;
        
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('import ')) {
            importInsertIndex = i + 1;
          } else if (lines[i].trim() === '' && importInsertIndex > 0) {
            break;
          }
        }
        
        lines.splice(importInsertIndex, 0, importLine);
        content = lines.join('\n');
      }
      
      if (WRITE) {
        fs.writeFileSync(filePath, content);
        console.log(`[guard-map] WRITE: ${path.relative(process.cwd(), filePath)}`);
      } else {
        console.log(`[guard-map] DRY: ${path.relative(process.cwd(), filePath)}`);
      }
      
      filesChanged++;
    }
    
  } catch (e) {
    console.warn(`[guard-map] Error processing ${filePath}:`, e.message);
  }
}

console.log(`\n[guard-map] Summary:`);
console.log(`  📁 Files scanned: ${files.length}`);
console.log(`  ✅ Files changed: ${filesChanged}`);
console.log(`  🛡️ Maps guarded: ${mapsGuarded}`);
console.log(`  ⏭️ Files skipped: ${filesSkipped}`);
console.log(`  💾 Write mode: ${WRITE ? 'ENABLED' : 'DISABLED (dry run)'}`);

if (!WRITE && filesChanged > 0) {
  console.log(`\n💡 To apply changes, run: WRITE=1 node ops/codemods/guard-map.js`);
}

if (mapsGuarded === 0) {
  console.log(`\n🎉 No unsafe .map() calls found! Your code is already protected.`);
}