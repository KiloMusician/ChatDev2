#!/usr/bin/env node
/**
 * 🔗 IMPORT VALIDATOR - Culture-Ship Health Analyzer  
 * Zero-token local-first import resolution checking
 */

import fs from "node:fs";
import path from "node:path";
import { glob } from "glob";

const EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"];
const INDEX_FILES = ["index.ts", "index.tsx", "index.js", "index.jsx", "index.mjs"];

async function checkImports() {
  console.log("🔗 Culture-Ship: Validating import statements...");
  
  const files = await glob("**/*.{ts,tsx,js,jsx,mjs,cjs}", { 
    ignore: ["node_modules/**", "dist/**", ".git/**"],
    nodir: true 
  });
  
  let totalImports = 0;
  let brokenImports = 0;
  const issues = [];

  for (const file of files) {
    try {
      const content = fs.readFileSync(file, "utf8");
      const importRegex = /(?:import.*from\s+['"`]([^'"`]+)['"`]|require\(['"`]([^'"`]+)['"`]\))/g;
      
      let match;
      while ((match = importRegex.exec(content)) !== null) {
        const importPath = match[1] || match[2];
        totalImports++;
        
        // Skip non-relative imports (npm packages)
        if (!importPath.startsWith(".")) continue;
        
        const resolved = await resolveImport(file, importPath);
        if (!resolved.exists) {
          brokenImports++;
          issues.push({
            file,
            importPath,
            line: getLineNumber(content, match.index),
            suggestion: resolved.suggestion
          });
          
          console.log(`❌ BROKEN: ${file}:${getLineNumber(content, match.index)}`);
          console.log(`   Import: "${importPath}"`);
          console.log(`   Tried: ${resolved.attempted.join(", ")}`);
          if (resolved.suggestion) {
            console.log(`   💡 Suggestion: "${resolved.suggestion}"`);
          }
        }
      }
    } catch (error) {
      console.warn(`⚠️ Could not process ${file}: ${error.message}`);
    }
  }
  
  console.log(`\n📊 Culture-Ship Import Validation Results:`);
  console.log(`   📁 Files scanned: ${files.length}`);
  console.log(`   🔗 Total imports: ${totalImports}`);
  console.log(`   ❌ Broken imports: ${brokenImports}`);
  console.log(`   ✅ Success rate: ${((totalImports - brokenImports) / totalImports * 100).toFixed(1)}%`);
  
  return {
    totalFiles: files.length,
    totalImports,
    brokenImports,
    issues,
    timestamp: new Date().toISOString()
  };
}

async function resolveImport(fromFile, importPath) {
  const fromDir = path.dirname(fromFile);
  const basePath = path.resolve(fromDir, importPath);
  
  const attempted = [];
  const candidates = [
    basePath,
    ...EXTENSIONS.map(ext => basePath + ext),
    ...INDEX_FILES.map(idx => path.join(basePath, idx))
  ];
  
  for (const candidate of candidates) {
    attempted.push(candidate);
    if (fs.existsSync(candidate)) {
      return { exists: true, resolved: candidate, attempted };
    }
  }
  
  // Try to suggest a fix
  let suggestion = null;
  const nearby = await findSimilarFiles(basePath);
  if (nearby.length > 0) {
    suggestion = path.relative(fromDir, nearby[0]);
    if (!suggestion.startsWith(".")) suggestion = "./" + suggestion;
  }
  
  return { exists: false, attempted, suggestion };
}

async function findSimilarFiles(targetPath) {
  const targetName = path.basename(targetPath);
  const searchPattern = `**/${targetName}*`;
  
  try {
    const matches = await glob(searchPattern, {
      ignore: ["node_modules/**", "dist/**", ".git/**"],
      nodir: true
    });
    return matches.slice(0, 3); // Return top 3 candidates
  } catch {
    return [];
  }
}

function getLineNumber(content, index) {
  return content.slice(0, index).split('\n').length;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const result = await checkImports();
    process.exit(result.brokenImports > 0 ? 1 : 0);
  } catch (error) {
    console.error("❌ Import checker failed:", error);
    process.exit(1);
  }
}