/**
 * 🔒 SOFTLOCK ANALYZER - Culture-Ship Health Component
 * Zero-token detection of infinite loops, deadlocks, and performance traps
 */

import fs from "node:fs";
import { glob } from "glob";

interface SoftlockIssue {
  file: string;
  line: number;
  type: "infinite_loop" | "unawaited_async" | "blocking_io" | "unbounded_recursion" | "tight_timer";
  severity: "critical" | "warning" | "info";
  pattern: string;
  suggestion: string;
  context?: string;
}

interface SoftlockAnalysis {
  totalFiles: number;
  criticalIssues: number;
  warnings: number;
  issues: SoftlockIssue[];
  suggestions: Array<{
    action: "fix" | "refactor" | "guard";
    files: string[];
    description: string;
  }>;
  timestamp: string;
}

// Patterns that indicate potential softlock conditions
const SOFTLOCK_PATTERNS = [
  // Infinite loops
  {
    regex: /while\s*\(\s*true\s*\)/g,
    type: "infinite_loop" as const,
    severity: "warning" as const,
    suggestion: "Add break condition or use for...of loop with iterator"
  },
  {
    regex: /for\s*\(\s*;\s*;\s*\)/g,
    type: "infinite_loop" as const,
    severity: "warning" as const,
    suggestion: "Add proper loop conditions"
  },
  
  // Unawaited async operations
  {
    regex: /(?<!await\s+)(?:fetch|setTimeout|setInterval|Promise\.)\w*\([^)]*\)(?!\s*\.catch)/g,
    type: "unawaited_async" as const,
    severity: "warning" as const,
    suggestion: "Add await or .catch() for proper async handling"
  },
  
  // Blocking I/O operations
  {
    regex: /fs\.(readFileSync|writeFileSync|statSync)/g,
    type: "blocking_io" as const,
    severity: "info" as const,
    suggestion: "Consider using async variants (readFile, writeFile, stat)"
  },
  
  // Tight timers (< 16ms, can cause performance issues)
  {
    regex: /setInterval\s*\(\s*[^,]+,\s*([0-9]+)\s*\)/g,
    type: "tight_timer" as const,
    severity: "warning" as const,
    suggestion: "Consider using requestAnimationFrame or longer intervals"
  },
  
  // Recursive patterns without guards
  {
    regex: /function\s+(\w+)[^{}]*\{[^{}]*\1\s*\(/g,
    type: "unbounded_recursion" as const,
    severity: "warning" as const,
    suggestion: "Add recursion depth limit or base case check"
  }
];

// Additional context-aware checks
const CONTEXT_CHECKS = [
  {
    pattern: /catch\s*\([^)]*\)\s*\{\s*\}/g,
    issue: "Empty catch blocks can hide errors",
    suggestion: "Add logging or error handling in catch block"
  },
  {
    pattern: /console\.log\s*\([^)]*\).*setInterval|setTimeout.*console\.log/g,
    issue: "Logging in timer can cause console spam",
    suggestion: "Add rate limiting or use debug levels"
  }
];

export async function scanSoftlocks(): Promise<SoftlockAnalysis> {
  console.log("🔒 Culture-Ship Softlock Analyzer: Scanning for performance traps...");
  
  const files = await glob("**/*.{ts,tsx,js,jsx,mjs,cjs}", { 
    ignore: ["node_modules/**", "dist/**", ".git/**", "*.test.*", "*.spec.*"],
    nodir: true 
  });
  
  const issues: SoftlockIssue[] = [];
  let criticalIssues = 0;
  let warnings = 0;
  
  for (const file of files) {
    try {
      const content = fs.readFileSync(file, "utf8");
      
      // Check each softlock pattern
      for (const pattern of SOFTLOCK_PATTERNS) {
        let match;
        while ((match = pattern.regex.exec(content)) !== null) {
          const line = getLineNumber(content, match.index);
          const context = getLineContext(content, line);
          
          // Special handling for tight timers
          if (pattern.type === "tight_timer") {
            const intervalValue = match[1];
            if (!intervalValue) continue;
            const intervalMs = parseInt(intervalValue, 10);
            if (intervalMs >= 16) continue; // 16ms+ is acceptable
          }
          
          // Skip if pattern appears in comments
          if (isInComment(content, match.index)) continue;
          
          const issue: SoftlockIssue = {
            file,
            line,
            type: pattern.type,
            severity: pattern.severity,
            pattern: match[0],
            suggestion: pattern.suggestion,
            context
          };
          
          issues.push(issue);
          
          if (issue.severity === "critical") criticalIssues++;
          else if (issue.severity === "warning") warnings++;
        }
      }
      
      // Context-aware checks
      for (const check of CONTEXT_CHECKS) {
        let match;
        while ((match = check.pattern.exec(content)) !== null) {
          if (isInComment(content, match.index)) continue;
          
          issues.push({
            file,
            line: getLineNumber(content, match.index),
            type: "blocking_io", // Generic type for context issues
            severity: "info",
            pattern: match[0],
            suggestion: check.suggestion,
            context: check.issue
          });
        }
      }
      
    } catch (error) {
      console.warn(`⚠️ Could not process ${file}: ${error}`);
    }
  }
  
  // Generate suggestions
  const suggestions = generateSoftlockSuggestions(issues);
  
  const analysis: SoftlockAnalysis = {
    totalFiles: files.length,
    criticalIssues,
    warnings,
    issues,
    suggestions,
    timestamp: new Date().toISOString()
  };
  
  console.log(`📊 Softlock analysis: ${criticalIssues} critical, ${warnings} warnings in ${files.length} files`);
  return analysis;
}

function getLineNumber(content: string, index: number): number {
  return content.slice(0, index).split('\n').length;
}

function getLineContext(content: string, lineNumber: number): string {
  const lines = content.split('\n');
  const contextStart = Math.max(0, lineNumber - 2);
  const contextEnd = Math.min(lines.length, lineNumber + 1);
  
  return lines.slice(contextStart, contextEnd)
    .map((line, i) => {
      const actualLineNum = contextStart + i + 1;
      const marker = actualLineNum === lineNumber ? ">>> " : "    ";
      return `${marker}${actualLineNum}: ${line}`;
    })
    .join('\n');
}

function isInComment(content: string, index: number): boolean {
  const beforeIndex = content.slice(0, index);
  const lastLineStart = beforeIndex.lastIndexOf('\n');
  const currentLine = content.slice(lastLineStart + 1, content.indexOf('\n', index));
  
  // Check for single-line comments
  const commentIndex = currentLine.indexOf('//');
  if (commentIndex >= 0 && commentIndex < (index - lastLineStart - 1)) {
    return true;
  }
  
  // Simple check for block comments (not perfect, but good enough)
  const lastBlockCommentStart = beforeIndex.lastIndexOf('/*');
  const lastBlockCommentEnd = beforeIndex.lastIndexOf('*/');
  
  return lastBlockCommentStart > lastBlockCommentEnd;
}

function generateSoftlockSuggestions(issues: SoftlockIssue[]): SoftlockAnalysis["suggestions"] {
  const suggestions: SoftlockAnalysis["suggestions"] = [];
  
  // Group issues by type
  const issuesByType = new Map<string, SoftlockIssue[]>();
  for (const issue of issues) {
    if (!issuesByType.has(issue.type)) {
      issuesByType.set(issue.type, []);
    }
    issuesByType.get(issue.type)!.push(issue);
  }
  
  // Generate type-specific suggestions
  for (const [type, typeIssues] of issuesByType) {
    const files = [...new Set(typeIssues.map(i => i.file))];
    
    switch (type) {
      case "infinite_loop":
        suggestions.push({
          action: "guard",
          files,
          description: `Add break conditions to ${typeIssues.length} potential infinite loops`
        });
        break;
        
      case "unawaited_async":
        suggestions.push({
          action: "fix",
          files,
          description: `Add await/catch to ${typeIssues.length} async operations`
        });
        break;
        
      case "blocking_io":
        suggestions.push({
          action: "refactor",
          files,
          description: `Convert ${typeIssues.length} blocking I/O operations to async`
        });
        break;
        
      case "tight_timer":
        suggestions.push({
          action: "fix",
          files,
          description: `Optimize ${typeIssues.length} high-frequency timers`
        });
        break;
        
      case "unbounded_recursion":
        suggestions.push({
          action: "guard",
          files,
          description: `Add recursion guards to ${typeIssues.length} recursive functions`
        });
        break;
    }
  }
  
  return suggestions;
}

export function generateSoftlockReport(analysis: SoftlockAnalysis): string {
  let report = "# 🔒 Culture-Ship Softlock Analysis Report\n\n";
  
  report += `**Scan Results:**\n`;
  report += `- Files scanned: ${analysis.totalFiles}\n`;
  report += `- Critical issues: ${analysis.criticalIssues}\n`;
  report += `- Warnings: ${analysis.warnings}\n`;
  report += `- Total issues: ${analysis.issues.length}\n\n`;
  
  if (analysis.issues.length > 0) {
    const criticalIssues = analysis.issues.filter(i => i.severity === "critical");
    const warnings = analysis.issues.filter(i => i.severity === "warning");
    const info = analysis.issues.filter(i => i.severity === "info");
    
    if (criticalIssues.length > 0) {
      report += "## 🚨 Critical Softlock Risks\n\n";
      for (const issue of criticalIssues) {
        report += `### ${issue.file}:${issue.line} - ${issue.type}\n`;
        report += `**Pattern:** \`${issue.pattern}\`\n`;
        report += `**Suggestion:** ${issue.suggestion}\n\n`;
        if (issue.context) {
          report += "```\n" + issue.context + "\n```\n\n";
        }
      }
    }
    
    if (warnings.length > 0) {
      report += "## ⚠️ Performance Warnings\n\n";
      for (const issue of warnings.slice(0, 10)) { // Limit to top 10
        report += `- **${issue.file}:${issue.line}** - ${issue.type}\n`;
        report += `  Pattern: \`${issue.pattern}\`\n`;
        report += `  💡 ${issue.suggestion}\n\n`;
      }
      
      if (warnings.length > 10) {
        report += `*... and ${warnings.length - 10} more warnings*\n\n`;
      }
    }
  }
  
  if (analysis.suggestions.length > 0) {
    report += "## 🛠️ Automated Suggestions\n\n";
    for (const suggestion of analysis.suggestions) {
      const icon = suggestion.action === "fix" ? "🔧" : 
                   suggestion.action === "guard" ? "🛡️" : "🔄";
      report += `${icon} **${suggestion.action.toUpperCase()}**: ${suggestion.description}\n`;
      report += `  Files: ${suggestion.files.join(", ")}\n\n`;
    }
  }
  
  return report;
}
