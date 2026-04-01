#!/usr/bin/env tsx
/**
 * ΞNuSyQ Theater Eradicator - Hunt TODO/PLACEHOLDER/HARDCODED patterns
 * Target: Δ negative per cycle, replace with diffs & metrics
 */
import { execSync } from "node:child_process";
import { writeReport, writeReceipt } from "./receipts.js";

type TheaterPattern = {
  pattern: string;
  regex: RegExp;
  severity: "low" | "medium" | "high" | "critical";
};

const THEATER_PATTERNS: TheaterPattern[] = [
  { pattern: "TODO", regex: /TODO|FIXME|XXX/gi, severity: "medium" },
  { pattern: "PLACEHOLDER", regex: /PLACEHOLDER|placeholder/gi, severity: "high" },
  { pattern: "HARDCODED", regex: /HARDCODED|hardcoded/gi, severity: "critical" },
  { pattern: "MOCK_DATA", regex: /MOCK_DATA|mock.*data|fake.*data/gi, severity: "high" },
  { pattern: "console.log", regex: /console\.log|console\.warn|console\.error/gi, severity: "low" },
  { pattern: "THEATER", regex: /THEATER|theater.*disabled|fake.*progression/gi, severity: "critical" }
];

type ScanResult = {
  file: string;
  matches: Array<{
    line: number;
    content: string;
    pattern: string;
    severity: string;
  }>;
};

export async function scanTheaterPatterns(): Promise<ScanResult[]> {
  const results: ScanResult[] = [];
  
  try {
    // Get all relevant source files
    const files = execSync(
      "find . -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' | grep -v node_modules | grep -v .git | head -100",
      { encoding: "utf8" }
    ).trim().split("\\n").filter(Boolean);
    
    for (const file of files) {
      try {
        const content = execSync(`cat "${file}"`, { encoding: "utf8" });
        const lines = content.split("\\n");
        const matches: ScanResult["matches"] = [];
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          
          for (const pattern of THEATER_PATTERNS) {
            const match = line.match(pattern.regex);
            if (match) {
              matches.push({
                line: i + 1,
                content: line.trim(),
                pattern: pattern.pattern,
                severity: pattern.severity
              });
            }
          }
        }
        
        if (matches.length > 0) {
          results.push({ file, matches });
        }
      } catch {
        // Skip files that can't be read
      }
    }
  } catch (error) {
    writeReceipt({
      ts: Date.now(),
      actor: "theater-audit",
      action: "scan_patterns",
      ok: false,
      error: error instanceof Error ? error.message : String(error)
    });
  }
  
  return results;
}

export function calculateTheaterScore(results: ScanResult[]): number {
  let totalScore = 0;
  let totalLines = 0;
  
  for (const result of results) {
    for (const match of result.matches) {
      switch (match.severity) {
        case "critical": totalScore += 10; break;
        case "high": totalScore += 5; break;
        case "medium": totalScore += 2; break;
        case "low": totalScore += 1; break;
      }
      totalLines++;
    }
  }
  
  // Normalize to 0-1 scale (rough heuristic)
  return totalLines > 0 ? Math.min(totalScore / (totalLines * 10), 1) : 0;
}

export async function generateTheaterAudit() {
  const results = await scanTheaterPatterns();
  const score = calculateTheaterScore(results);
  
  const audit = {
    timestamp: Date.now(),
    score,
    total_files: results.length,
    total_matches: results.reduce((sum, r) => sum + r.matches.length, 0),
    by_severity: {
      critical: 0,
      high: 0, 
      medium: 0,
      low: 0
    },
    results,
    action_plan: score > 0.3 ? "immediate_cleanup" : "monitoring"
  };
  
  // Count by severity
  for (const result of results) {
    for (const match of result.matches) {
      audit.by_severity[match.severity as keyof typeof audit.by_severity]++;
    }
  }
  
  writeReport("theater_audit.json", audit);
  
  writeReceipt({
    ts: Date.now(),
    actor: "theater-audit",
    action: "generate_audit",
    inputs: { files_scanned: results.length },
    outputs: { score, matches: audit.total_matches },
    ok: true
  });
  
  return audit;
}

// Auto-run when executed
if (import.meta.url === `file://${process.argv[1]}`) {
  generateTheaterAudit().then((audit) => {
    console.log(`[Theater] Score: ${audit.score.toFixed(3)} (${audit.total_matches} matches in ${audit.total_files} files)`);
    console.log(`[Theater] Critical: ${audit.by_severity.critical}, High: ${audit.by_severity.high}`);
    
    if (audit.score > 0.5) {
      console.log("[Theater] ⚠️  Score > 0.5 - immediate cleanup required");
    }
    
    process.exit(0);
  });
}