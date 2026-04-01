#!/usr/bin/env node
/**
 * 🔍 DUPLICATE FILE SCANNER - Culture-Ship Health Analyzer
 * Zero-token local-first duplicate detection using SHA1 hashing
 */

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { glob } from "glob";

const SCAN_ROOTS = ["src", "modules", "client/src", "server", "shared"];
const IGNORE_PATTERNS = ["node_modules/**", "dist/**", ".git/**", "*.log"];

async function scanDuplicates() {
  console.log("🔍 Culture-Ship: Scanning for duplicate files...");
  
  const duplicateMap = new Map();
  let totalFiles = 0;
  let duplicateGroups = 0;

  for (const root of SCAN_ROOTS) {
    if (!fs.existsSync(root)) continue;
    
    try {
      const pattern = `${root}/**/*.*`;
      const files = await glob(pattern, { 
        ignore: IGNORE_PATTERNS,
        nodir: true 
      });
      
      for (const file of files) {
        try {
          const buffer = fs.readFileSync(file);
          const hash = crypto.createHash("sha1").update(buffer).digest("hex");
          
          if (!duplicateMap.has(hash)) {
            duplicateMap.set(hash, []);
          }
          duplicateMap.get(hash).push({
            path: file,
            size: buffer.length,
            modified: fs.statSync(file).mtime
          });
          totalFiles++;
        } catch (error) {
          console.warn(`⚠️ Could not process ${file}: ${error.message}`);
        }
      }
    } catch (error) {
      console.warn(`⚠️ Could not scan ${root}: ${error.message}`);
    }
  }

  // Report duplicates
  const duplicates = [];
  for (const [hash, files] of duplicateMap.entries()) {
    if (files.length > 1) {
      duplicateGroups++;
      const group = {
        hash: hash.slice(0, 8),
        size: files[0].size,
        count: files.length,
        files: files.map(f => f.path).sort()
      };
      duplicates.push(group);
      
      console.log(`📋 DUP ${group.hash} (${group.size} bytes, ${group.count} copies):`);
      group.files.forEach(file => console.log(`   → ${file}`));
    }
  }

  console.log(`\n📊 Culture-Ship Duplicate Scan Results:`);
  console.log(`   📁 Total files scanned: ${totalFiles}`);
  console.log(`   🔍 Duplicate groups found: ${duplicateGroups}`);
  console.log(`   💾 Total duplicate files: ${duplicates.reduce((sum, g) => sum + g.count, 0)}`);
  
  return {
    totalFiles,
    duplicateGroups,
    duplicates,
    timestamp: new Date().toISOString()
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const result = await scanDuplicates();
    process.exit(result.duplicateGroups > 0 ? 1 : 0);
  } catch (error) {
    console.error("❌ Duplicate scanner failed:", error);
    process.exit(1);
  }
}