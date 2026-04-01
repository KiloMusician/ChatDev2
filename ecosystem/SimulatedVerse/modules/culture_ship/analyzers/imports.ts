/**
 * 🔗 IMPORT ANALYZER - Culture-Ship Health Component
 * Zero-token import resolution validation with fix suggestions
 */

import fs from "node:fs";
import path from "node:path";
import { glob } from "glob";

interface ImportIssue {
  file: string;
  line: number;
  importPath: string;
  issue: "broken" | "ambiguous" | "circular" | "inefficient";
  severity: "critical" | "warning" | "info";
  suggestion?: string;
  attempted?: string[];
}

interface ImportAnalysis {
  totalFiles: number;
  totalImports: number;
  brokenImports: number;
  circularDependencies: string[][];
  issues: ImportIssue[];
  suggestions: Array<{
    action: "fix" | "refactor" | "review";
    files: string[];
    description: string;
  }>;
  timestamp: string;
}

const EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"];
const INDEX_FILES = ["index.ts", "index.tsx", "index.js", "index.jsx", "index.mjs"];

export async function scanImports(): Promise<ImportAnalysis> {
  console.log("🔗 Culture-Ship Import Analyzer: Scanning import statements...");
  
  const files = await glob("**/*.{ts,tsx,js,jsx,mjs,cjs}", { 
    ignore: ["node_modules/**", "dist/**", ".git/**"],
    nodir: true 
  });
  
  let totalImports = 0;
  let brokenImports = 0;
  const issues: ImportIssue[] = [];
  const importGraph = new Map<string, string[]>();
  
  // Phase 1: Scan all imports and build dependency graph
  for (const file of files) {
    try {
      const content = fs.readFileSync(file, "utf8");
      const fileImports: string[] = [];
      
      // Match import statements and require calls
      const importRegex = /(?:import.*from\s+['"`]([^'"`]+)['"`]|require\(['"`]([^'"`]+)['"`]\))/g;
      
      let match;
      while ((match = importRegex.exec(content)) !== null) {
        const importPath = match[1] || match[2];
        totalImports++;
        
        // Skip non-relative imports (npm packages)
        if (!importPath) continue;
        if (!importPath.startsWith(".")) continue;
        
        fileImports.push(importPath);
        const resolved = await resolveImport(file, importPath);
        
        if (!resolved.exists) {
          brokenImports++;
          issues.push({
            file,
            line: getLineNumber(content, match.index),
            importPath,
            issue: "broken",
            severity: "critical",
            suggestion: resolved.suggestion,
            attempted: resolved.attempted
          });
        } else {
          // Check for inefficient imports
          if (resolved.resolved && isInefficient(file, resolved.resolved)) {
            issues.push({
              file,
              line: getLineNumber(content, match.index),
              importPath,
              issue: "inefficient",
              severity: "info",
              suggestion: optimizeImportPath(file, resolved.resolved)
            });
          }
        }
      }
      
      importGraph.set(file, fileImports);
    } catch (error) {
      console.warn(`⚠️ Could not process ${file}: ${error}`);
    }
  }
  
  // Phase 2: Detect circular dependencies
  const circularDependencies = detectCircularDependencies(importGraph);
  
  // Phase 3: Generate suggestions
  const suggestions = generateImportSuggestions(issues, circularDependencies);
  
  const analysis: ImportAnalysis = {
    totalFiles: files.length,
    totalImports,
    brokenImports,
    circularDependencies,
    issues,
    suggestions,
    timestamp: new Date().toISOString()
  };
  
  console.log(`📊 Import analysis: ${brokenImports}/${totalImports} broken, ${circularDependencies.length} circular deps`);
  return analysis;
}

async function resolveImport(fromFile: string, importPath: string) {
  const fromDir = path.dirname(fromFile);
  const basePath = path.resolve(fromDir, importPath);
  
  const attempted: string[] = [];
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
  let suggestion: string | undefined;
  const nearby = await findSimilarFiles(path.basename(basePath));
  const firstMatch = nearby[0];
  if (firstMatch) {
    const relativePath = path.relative(fromDir, firstMatch);
    suggestion = relativePath.startsWith(".") ? relativePath : "./" + relativePath;
  }
  
  return { exists: false, attempted, suggestion };
}

async function findSimilarFiles(targetName: string): Promise<string[]> {
  try {
    const searchPattern = `**/${targetName}*`;
    const matches = await glob(searchPattern, {
      ignore: ["node_modules/**", "dist/**", ".git/**"],
      nodir: true
    });
    return matches.slice(0, 3);
  } catch {
    return [];
  }
}

function isInefficient(fromFile: string, toFile: string): boolean {
  // Check for overly complex relative paths
  const relativePath = path.relative(path.dirname(fromFile), toFile);
  const upLevels = (relativePath.match(/\.\.\//g) || []).length;
  
  // More than 3 levels up is usually inefficient
  return upLevels > 3;
}

function optimizeImportPath(fromFile: string, toFile: string): string {
  // Suggest workspace-relative alias if available
  const relativePath = path.relative(path.dirname(fromFile), toFile);
  
  // Look for common patterns that could use aliases
  if (toFile.includes("/src/")) {
    const srcRelative = toFile.split("/src/")[1];
    if (srcRelative) {
      return `@/${srcRelative.replace(/\.(ts|tsx|js|jsx)$/, "")}`;
    }
  }
  
  if (toFile.includes("/shared/")) {
    const sharedRelative = toFile.split("/shared/")[1];
    if (sharedRelative) {
      return `@shared/${sharedRelative.replace(/\.(ts|tsx|js|jsx)$/, "")}`;
    }
  }
  
  return relativePath;
}

function detectCircularDependencies(importGraph: Map<string, string[]>): string[][] {
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const cycles: string[][] = [];
  
  function dfs(file: string, filePath: string[]): void {
    if (visiting.has(file)) {
      // Found a cycle
      const cycleStart = filePath.indexOf(file);
      if (cycleStart >= 0) {
        cycles.push(filePath.slice(cycleStart).concat([file]));
      }
      return;
    }
    
    if (visited.has(file)) return;
    
    visiting.add(file);
    filePath.push(file);
    
    const imports = importGraph.get(file) || [];
    for (const importPath of imports) {
      // Resolve relative import to absolute path for graph traversal
      if (importPath.startsWith(".")) {
        const resolvedPath = path.resolve(path.dirname(file), importPath);
        // Try to find the actual file
        for (const ext of EXTENSIONS) {
          const candidate = resolvedPath + ext;
          if (importGraph.has(candidate)) {
            dfs(candidate, [...filePath]);
            break;
          }
        }
      }
    }
    
    filePath.pop();
    visiting.delete(file);
    visited.add(file);
  }
  
  for (const file of importGraph.keys()) {
    if (!visited.has(file)) {
      dfs(file, []);
    }
  }
  
  return cycles;
}

function generateImportSuggestions(issues: ImportIssue[], circularDeps: string[][]): ImportAnalysis["suggestions"] {
  const suggestions: ImportAnalysis["suggestions"] = [];
  
  // Group broken imports by file
  const brokenByFile = new Map<string, ImportIssue[]>();
  for (const issue of issues.filter(i => i.issue === "broken")) {
    if (!brokenByFile.has(issue.file)) {
      brokenByFile.set(issue.file, []);
    }
    brokenByFile.get(issue.file)!.push(issue);
  }
  
  // Suggest fixes for files with broken imports
  for (const [file, fileIssues] of brokenByFile) {
    const firstIssue = fileIssues[0];
    if (fileIssues.length === 1 && firstIssue?.suggestion) {
      suggestions.push({
        action: "fix",
        files: [file],
        description: `Auto-fix broken import: ${firstIssue.importPath} → ${firstIssue.suggestion}`
      });
    } else {
      suggestions.push({
        action: "review",
        files: [file],
        description: `Manual review needed for ${fileIssues.length} broken imports`
      });
    }
  }
  
  // Suggest circular dependency fixes
  for (const cycle of circularDeps) {
    suggestions.push({
      action: "refactor",
      files: cycle,
      description: `Circular dependency detected: ${cycle.join(" → ")}`
    });
  }
  
  return suggestions;
}

function getLineNumber(content: string, index: number): number {
  return content.slice(0, index).split('\n').length;
}

export function generateImportReport(analysis: ImportAnalysis): string {
  let report = "# 🔗 Culture-Ship Import Analysis Report\n\n";
  
  report += `**Scan Results:**\n`;
  report += `- Files scanned: ${analysis.totalFiles}\n`;
  report += `- Total imports: ${analysis.totalImports}\n`;
  report += `- Broken imports: ${analysis.brokenImports}\n`;
  report += `- Circular dependencies: ${analysis.circularDependencies.length}\n`;
  report += `- Success rate: ${((analysis.totalImports - analysis.brokenImports) / analysis.totalImports * 100).toFixed(1)}%\n\n`;
  
  if (analysis.issues.length > 0) {
    report += "## Issues Found\n\n";
    
    const criticalIssues = analysis.issues.filter(i => i.severity === "critical");
    const warnings = analysis.issues.filter(i => i.severity === "warning");
    const info = analysis.issues.filter(i => i.severity === "info");
    
    if (criticalIssues.length > 0) {
      report += "### 🚨 Critical Issues\n\n";
      for (const issue of criticalIssues) {
        report += `- **${issue.file}:${issue.line}** - ${issue.issue}\n`;
        report += `  Import: \`${issue.importPath}\`\n`;
        if (issue.suggestion) {
          report += `  💡 Suggestion: \`${issue.suggestion}\`\n`;
        }
        report += "\n";
      }
    }
    
    if (warnings.length > 0) {
      report += "### ⚠️ Warnings\n\n";
      for (const issue of warnings) {
        report += `- **${issue.file}:${issue.line}** - ${issue.issue}: \`${issue.importPath}\`\n`;
      }
      report += "\n";
    }
  }
  
  return report;
}
