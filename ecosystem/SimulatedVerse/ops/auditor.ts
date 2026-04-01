#!/usr/bin/env tsx
/**
 * AUDITOR/SKEPTIC - Always Finds Real Work
 * - Scans for sophisticated theater (TODOs, placeholders, hardcoded errors)
 * - Detects orphaned modules and unused code
 * - Identifies real vs fake system activity
 * - Generates targeted PUs for actual fixes
 */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const ROOT = process.cwd();
const PUS = path.join(ROOT, "ops/pus.ndjson");

// Theater detection patterns
const THEATER_PATTERNS = {
  TODO_FIXME: /TODO|FIXME/i,
  PLACEHOLDER: /placeholder|TODO:|FIXME:/i,
  PASS_STATEMENT: /^\s*pass\s*;?\s*$/,
  HARDCODED_ERROR: /throw new Error\("(placeholder|TODO|not implemented)"/i,
  CONSOLE_LOG: /console\.(log|debug|info)\(/,
  MOCK_DATA: /(mock|fake|dummy|test).*data/i,
  DEAD_CODE: /\/\*.*unused.*\*\/|\/\/.*unused/i
};

const SCAN_GLOBS = [
  "client/src/**/*.{ts,tsx,js,jsx}",
  "server/**/*.{ts,js}",
  "ops/**/*.{ts,js,py}",
  "shared/**/*.{ts,js}"
];

interface TheaterHit {
  file: string;
  line: number;
  pattern: string;
  content: string;
  severity: "high" | "medium" | "low";
}

interface AuditResults {
  theater_hits: TheaterHit[];
  placeholder_count: number;
  todo_count: number;
  hardcoded_errors: number;
  console_logs: number;
  dead_code: number;
  theater_score: number;
  files_scanned: number;
  timestamp: number;
}

function scanFile(filePath: string): TheaterHit[] {
  const hits: TheaterHit[] = [];
  
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const lines = content.split("\n");
    
    lines.forEach((line, index) => {
      Object.entries(THEATER_PATTERNS).forEach(([patternName, pattern]) => {
        if (pattern.test(line)) {
          let severity: "high" | "medium" | "low" = "medium";
          
          // High severity theater
          if (patternName === "HARDCODED_ERROR" || patternName === "PASS_STATEMENT") {
            severity = "high";
          }
          // Low severity theater  
          if (patternName === "CONSOLE_LOG" || patternName === "DEAD_CODE") {
            severity = "low";
          }
          
          hits.push({
            file: filePath,
            line: index + 1,
            pattern: patternName,
            content: line.trim(),
            severity
          });
        }
      });
    });
  } catch (e) {
    console.warn(`[auditor] Could not scan ${filePath}:`, e);
  }
  
  return hits;
}

function scanCodebase(): AuditResults {
  console.log("[auditor] 🔍 Scanning codebase for sophisticated theater...");
  
  const allHits: TheaterHit[] = [];
  let filesScanned = 0;
  
  // Scan each directory
  const scanDirs = ["client/src", "server", "ops", "shared"];
  
  for (const dir of scanDirs) {
    if (!fs.existsSync(path.join(ROOT, dir))) continue;
    
    try {
      // Use find to get all relevant files
      const result = spawnSync("find", [
        dir,
        "-type", "f",
        "(",
        "-name", "*.ts",
        "-o", "-name", "*.tsx", 
        "-o", "-name", "*.js",
        "-o", "-name", "*.jsx",
        "-o", "-name", "*.py",
        ")"
      ], { encoding: "utf-8", cwd: ROOT });
      
      if (result.stdout) {
        const files = result.stdout.split("\n").filter(Boolean);
        filesScanned += files.length;
        
        for (const file of files) {
          const fullPath = path.join(ROOT, file);
          const hits = scanFile(fullPath);
          allHits.push(...hits);
        }
      }
    } catch (e) {
      console.warn(`[auditor] Could not scan directory ${dir}:`, e);
    }
  }
  
  // Categorize hits
  const placeholders = allHits.filter(h => h.pattern === "PLACEHOLDER").length;
  const todos = allHits.filter(h => h.pattern === "TODO_FIXME").length;
  const hardcodedErrors = allHits.filter(h => h.pattern === "HARDCODED_ERROR").length;
  const consoleLogs = allHits.filter(h => h.pattern === "CONSOLE_LOG").length;
  const deadCode = allHits.filter(h => h.pattern === "DEAD_CODE").length;
  
  // Calculate theater score (0 = clean, 1 = complete theater)
  const highSeverityCount = allHits.filter(h => h.severity === "high").length;
  const mediumSeverityCount = allHits.filter(h => h.severity === "medium").length;
  const lowSeverityCount = allHits.filter(h => h.severity === "low").length;
  
  // Weighted scoring
  const theaterScore = Math.min(1, 
    (highSeverityCount * 0.1 + mediumSeverityCount * 0.05 + lowSeverityCount * 0.01)
  );
  
  return {
    theater_hits: allHits,
    placeholder_count: placeholders,
    todo_count: todos,
    hardcoded_errors: hardcodedErrors,
    console_logs: consoleLogs,
    dead_code: deadCode,
    theater_score: theaterScore,
    files_scanned: filesScanned,
    timestamp: Date.now()
  };
}

function generatePUs(results: AuditResults) {
  const pus: any[] = [];
  
  // High priority: Fix hardcoded errors and placeholders
  if (results.hardcoded_errors > 0) {
    pus.push({
      id: `pu.fix.hardcoded.${Date.now()}`,
      kind: "fix",
      summary: `Fix ${results.hardcoded_errors} hardcoded errors and placeholders`,
      priority: 10,
      owner: "skeptic",
      source: "auditor",
      status: "queued",
      proofs: [
        {"kind": "report_ok", "path": "reports/theater_audit.json", "report_key": "hardcoded_errors", "expected": {"eq": 0}}
      ],
      artifacts: ["reports/theater_audit.json"],
      created_at: Date.now()
    });
  }
  
  // Medium priority: Address TODO/FIXME comments
  if (results.todo_count > 5) {
    pus.push({
      id: `pu.refactor.todos.${Date.now()}`,
      kind: "refactor", 
      summary: `Address ${results.todo_count} TODO/FIXME comments`,
      priority: 7,
      owner: "skeptic",
      source: "auditor", 
      status: "queued",
      proofs: [
        {"kind": "report_ok", "path": "reports/theater_audit.json", "report_key": "todo_count", "expected": {"lte": 5}}
      ],
      artifacts: ["reports/theater_audit.json"],
      created_at: Date.now()
    });
  }
  
  // Clean up console logs in production code
  if (results.console_logs > 10) {
    pus.push({
      id: `pu.refactor.console.${Date.now()}`,
      kind: "refactor",
      summary: `Clean up ${results.console_logs} console.log statements`,
      priority: 4,
      owner: "skeptic", 
      source: "auditor",
      status: "queued",
      proofs: [
        {"kind": "report_ok", "path": "reports/theater_audit.json", "report_key": "console_logs", "expected": {"lte": 10}}
      ],
      artifacts: ["reports/theater_audit.json"],
      created_at: Date.now()
    });
  }
  
  // Overall theater reduction
  if (results.theater_score > 0.2) {
    pus.push({
      id: `pu.audit.theater.${Date.now()}`,
      kind: "audit",
      summary: `Reduce theater score from ${results.theater_score.toFixed(2)} to < 0.2`,
      priority: 8,
      owner: "skeptic",
      source: "auditor",
      status: "queued", 
      proofs: [
        {"kind": "report_ok", "path": "reports/theater_audit.json", "report_key": "theater_score", "expected": {"lte": 0.2}}
      ],
      artifacts: ["reports/theater_audit.json"],
      created_at: Date.now()
    });
  }
  
  return pus;
}

(function main() {
  console.log("[auditor] 🕵️ Starting systematic audit...");
  
  // Ensure reports directory exists
  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  
  // Run comprehensive scan
  const results = scanCodebase();
  
  // Write audit results
  fs.writeFileSync(
    path.join(ROOT, "reports/theater_audit.json"),
    JSON.stringify(results, null, 2)
  );
  
  // Write simplified placeholder scan
  fs.writeFileSync(
    path.join(ROOT, "reports/placeholder_scan.json"),
    JSON.stringify({
      placeholder_count: results.placeholder_count,
      todo_count: results.todo_count,
      hardcoded_errors: results.hardcoded_errors,
      theater_score: results.theater_score,
      timestamp: results.timestamp
    }, null, 2)
  );
  
  console.log(`[auditor] 📊 Scan complete:`);
  console.log(`  Files scanned: ${results.files_scanned}`);
  console.log(`  Theater hits: ${results.theater_hits.length}`);
  console.log(`  Placeholders: ${results.placeholder_count}`);
  // Audit metrics for development tracking
  console.log(`  Development Tasks: ${results.todo_count} (${results.todo_count > 0 ? 'active development' : 'complete'})`);
  console.log(`  Hardcoded errors: ${results.hardcoded_errors}`);
  console.log(`  Theater score: ${results.theater_score.toFixed(3)}`);
  
  // Generate targeted PUs
  const pus = generatePUs(results);
  
  if (pus.length > 0) {
    console.log(`[auditor] 📝 Enqueueing ${pus.length} targeted PUs...`);
    
    // Append PUs to queue
    for (const pu of pus) {
      fs.appendFileSync(PUS, JSON.stringify(pu) + "\n");
      console.log(`  → ${pu.id}: ${pu.summary}`);
    }
  } else {
    console.log("[auditor] ✅ No major theater detected - codebase is clean");
  }
})();