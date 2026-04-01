#!/usr/bin/env tsx
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const LEGACY_DIR = "legacy/_scans";
const AUDIT_PATTERNS = ["TODO", "PLACEHOLDER", "null", "None", "undefined", "FIXME", "XXX"];

// Legacy repos to scan (add your actual repo URLs here)
const LEGACY_REPOS = [
  // "https://github.com/user/old-nusyq.git",
  // "https://github.com/user/idler-legacy.git"
];

export async function scanLegacyRepos() {
  if (!existsSync(LEGACY_DIR)) {
    mkdirSync(LEGACY_DIR, { recursive: true });
  }

  const results: any[] = [];

  for (const url of LEGACY_REPOS) {
    const name = url.split('/').pop()?.replace('.git', '') || 'unknown';
    const repoPath = join(LEGACY_DIR, name);
    
    try {
      console.log(`[scan] ${name}`);
      
      // Clone with minimal data
      if (!existsSync(repoPath)) {
        execSync(`git clone --depth=1 --filter=blob:none --no-checkout "${url}" "${repoPath}"`, 
          { stdio: 'pipe' });
        execSync(`cd "${repoPath}" && git sparse-checkout init --cone && git sparse-checkout set . && git checkout`, 
          { stdio: 'pipe' });
      }

      // Audit for patterns
      const auditResults: string[] = [];
      for (const pattern of AUDIT_PATTERNS) {
        try {
          const output = execSync(`grep -r -n "${pattern}" "${repoPath}" || true`, 
            { encoding: 'utf8', stdio: 'pipe' });
          if (output.trim()) {
            auditResults.push(`=== ${pattern} ===`);
            auditResults.push(...output.trim().split('\n').slice(0, 20)); // Limit results
          }
        } catch (e) {
          // Ignore grep errors
        }
      }

      const auditFile = join(LEGACY_DIR, `${name}.audit.txt`);
      writeFileSync(auditFile, auditResults.join('\n'));
      
      results.push({
        repo: name,
        url,
        auditFile,
        patterns: auditResults.length,
        scanned: true
      });

    } catch (error) {
      console.warn(`[scan] Failed ${name}:`, error);
      results.push({
        repo: name,
        url,
        error: String(error),
        scanned: false
      });
    }
  }

  return results;
}

export function scanCurrentRepo() {
  const results: any[] = [];
  
  for (const pattern of AUDIT_PATTERNS) {
    try {
      const output = execSync(`grep -r -n "${pattern}" . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist || true`, 
        { encoding: 'utf8', stdio: 'pipe' });
      if (output.trim()) {
        results.push({
          pattern,
          matches: output.trim().split('\n').length,
          preview: output.trim().split('\n').slice(0, 5)
        });
      }
    } catch (e) {
      // Ignore grep errors
    }
  }

  return results;
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log("🔍 Legacy Repository Scanner");
  console.log("Current repo scan:");
  const current = scanCurrentRepo();
  console.log(JSON.stringify(current, null, 2));
  
  if (LEGACY_REPOS.length > 0) {
    console.log("\nLegacy repos scan:");
    scanLegacyRepos().then(results => {
      console.log(JSON.stringify(results, null, 2));
    });
  } else {
    console.log("\nNo legacy repos configured. Add URLs to LEGACY_REPOS array.");
  }
}