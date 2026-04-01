/**
 * 🔍 DUPLICATE ANALYZER - Culture-Ship Health Component
 * Zero-token hash-based duplicate detection with surgical fix suggestions
 */

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { glob } from "glob";

interface DuplicateGroup {
  hash: string;
  size: number;
  files: Array<{
    path: string;
    size: number;
    modified: Date;
    priority: number; // Keep priority (0 = delete, higher = keep)
  }>;
}

interface DuplicateAnalysis {
  totalFiles: number;
  duplicateGroups: number;
  duplicates: DuplicateGroup[];
  suggestions: Array<{
    action: "delete" | "merge" | "review";
    files: string[];
    reason: string;
  }>;
  timestamp: string;
}

const SCAN_ROOTS = ["src", "modules", "client/src", "server", "shared"];
const IGNORE_PATTERNS = ["node_modules/**", "dist/**", ".git/**", "*.log", "*.tmp"];

// File priority scoring for keep/delete decisions
const EXTENSION_PRIORITIES: Record<string, number> = {
  ".ts": 10, ".tsx": 10,
  ".js": 8, ".jsx": 8,
  ".md": 6,
  ".json": 5,
  ".txt": 3,
  ".tmp": 0, ".bak": 0
};

const PRIORITY_RULES = {
  // Extensions (higher = keep)
  extensions: EXTENSION_PRIORITIES,
  
  // Path patterns (higher = keep)  
  patterns: [
    { pattern: /\/src\//, score: 10 },
    { pattern: /\/modules\//, score: 9 },
    { pattern: /\/client\//, score: 8 },
    { pattern: /\/server\//, score: 8 },
    { pattern: /\/shared\//, score: 7 },
    { pattern: /index\.(ts|js|tsx|jsx)$/, score: 12 },
    { pattern: /\/test\/|\/tests\/|\.test\.|\.spec\./, score: 6 },
    { pattern: /\/temp\/|\/tmp\/|\.tmp/, score: 0 },
    { pattern: /\/backup\/|\.bak/, score: 0 }
  ]
};

function calculateFilePriority(filePath: string, stats: fs.Stats): number {
  let priority = 5; // Base priority
  
  // Extension bonus
  const ext = path.extname(filePath);
  const extPriority = PRIORITY_RULES.extensions[ext] ?? 0;
  priority += extPriority;
  
  // Pattern bonuses
  for (const rule of PRIORITY_RULES.patterns) {
    if (rule.pattern.test(filePath)) {
      priority += rule.score;
      break; // First match wins
    }
  }
  
  // Recency bonus (newer files get slight preference)
  const daysSinceModified = (Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60 * 24);
  if (daysSinceModified < 7) priority += 2;
  else if (daysSinceModified < 30) priority += 1;
  
  return Math.max(0, priority);
}

export async function scanDuplicates(): Promise<DuplicateAnalysis> {
  console.log("🔍 Culture-Ship Duplicate Analyzer: Scanning files...");
  
  const duplicateMap = new Map<string, DuplicateGroup>();
  let totalFiles = 0;

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
          const stats = fs.statSync(file);
          const buffer = fs.readFileSync(file);
          const hash = crypto.createHash("sha1").update(buffer).digest("hex");
          
          if (!duplicateMap.has(hash)) {
            duplicateMap.set(hash, {
              hash: hash.slice(0, 8),
              size: buffer.length,
              files: []
            });
          }
          
          const priority = calculateFilePriority(file, stats);
          duplicateMap.get(hash)!.files.push({
            path: file,
            size: buffer.length,
            modified: stats.mtime,
            priority
          });
          
          totalFiles++;
        } catch (error) {
          console.warn(`⚠️ Could not process ${file}: ${error}`);
        }
      }
    } catch (error) {
      console.warn(`⚠️ Could not scan ${root}: ${error}`);
    }
  }

  // Filter to only duplicates and generate suggestions
  const duplicates: DuplicateGroup[] = [];
  const suggestions: DuplicateAnalysis["suggestions"] = [];
  
  for (const group of duplicateMap.values()) {
    if (group.files.length > 1) {
      // Sort by priority (highest first)
      group.files.sort((a, b) => b.priority - a.priority);
      duplicates.push(group);
      
      // Generate suggestions based on priority and patterns
      if (group.files.length === 2) {
        const keep = group.files[0];
        const remove = group.files[1];
        if (keep && remove) {
          if (keep.priority > remove.priority + 3) {
            suggestions.push({
              action: "delete",
              files: [remove.path],
              reason: `Lower priority duplicate of ${keep.path}`
            });
          } else {
            suggestions.push({
              action: "review",
              files: [keep.path, remove.path],
              reason: "Similar priority files need manual review"
            });
          }
        }
      } else {
        // Multiple duplicates - suggest keeping highest priority
        const keep = group.files[0];
        if (keep) {
          suggestions.push({
            action: "review",
            files: group.files.map(f => f.path),
            reason: `Multiple duplicates found, review and keep ${keep.path}`
          });
        }
      }
    }
  }

  const analysis: DuplicateAnalysis = {
    totalFiles,
    duplicateGroups: duplicates.length,
    duplicates,
    suggestions,
    timestamp: new Date().toISOString()
  };

  console.log(`📊 Duplicate analysis: ${duplicates.length} groups, ${suggestions.length} suggestions`);
  return analysis;
}

export function generateDuplicateReport(analysis: DuplicateAnalysis): string {
  let report = "# 🔍 Culture-Ship Duplicate Analysis Report\n\n";
  
  report += `**Scan Results:**\n`;
  report += `- Total files: ${analysis.totalFiles}\n`;
  report += `- Duplicate groups: ${analysis.duplicateGroups}\n`;
  report += `- Automated suggestions: ${analysis.suggestions.length}\n\n`;
  
  if (analysis.duplicates.length > 0) {
    report += "## Duplicate Groups\n\n";
    
    for (const group of analysis.duplicates) {
      report += `### Hash: ${group.hash} (${group.size} bytes)\n`;
      for (const file of group.files) {
        const priority = file.priority;
        const indicator = priority >= 10 ? "🔥" : priority >= 5 ? "📄" : "🗑️";
        report += `- ${indicator} \`${file.path}\` (priority: ${priority})\n`;
      }
      report += "\n";
    }
  }
  
  if (analysis.suggestions.length > 0) {
    report += "## Automated Suggestions\n\n";
    
    for (const suggestion of analysis.suggestions) {
      const icon = suggestion.action === "delete" ? "🗑️" : 
                   suggestion.action === "merge" ? "🔗" : "👁️";
      report += `${icon} **${suggestion.action.toUpperCase()}**: ${suggestion.reason}\n`;
      for (const file of suggestion.files) {
        report += `  - \`${file}\`\n`;
      }
      report += "\n";
    }
  }
  
  return report;
}
