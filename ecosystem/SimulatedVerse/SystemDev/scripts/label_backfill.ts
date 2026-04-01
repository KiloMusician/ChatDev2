import path from "path";
import fs from "fs/promises";
import glob from "fast-glob";

interface FileLabel {
  path: string;
  namespace: string;
  intent: string;
  ownership: string;
  status: string;
  risk: string;
  lastModified: number;
  size: number;
}

interface LabelBackfillResult {
  timestamp: number;
  filesProcessed: number;
  labelsAssigned: number;
  namespaceDistribution: Record<string, number>;
  errors: string[];
  recommendations: string[];
}

// Namespace classification rules
const NAMESPACE_PATTERNS = {
  "ours.systemdev": {
    patterns: ["SystemDev/**"],
    intent: "infrastructure_operations",
    risk: "move_with_caution"
  },
  "ours.chatdev": {
    patterns: ["ChatDev/**"],
    intent: "agent_coordination", 
    risk: "move_with_caution"
  },
  "ours.gamedev": {
    patterns: ["GameDev/**"],
    intent: "game_logic_implementation",
    risk: "safe_to_move"
  },
  "ours.previewui": {
    patterns: ["PreviewUI/**"],
    intent: "ui_presentation",
    risk: "safe_to_move"
  },
  "ours.client": {
    patterns: ["client/**"],
    intent: "application_client",
    risk: "safe_to_move"
  },
  "ours.server": {
    patterns: ["server/**"],
    intent: "application_server",
    risk: "move_with_caution"
  },
  "ours.shared": {
    patterns: ["shared/**"],
    intent: "shared_utilities",
    risk: "immutable"
  },
  "pkg.node": {
    patterns: ["node_modules/**", "package*.json"],
    intent: "external_dependency",
    risk: "immutable"
  },
  "build.generated": {
    patterns: ["dist/**", "build/**", ".next/**", ".godot/**"],
    intent: "build_artifact",
    risk: "immutable"
  },
  "tools.development": {
    patterns: [".git/**", ".vscode/**", ".*rc*", "*.config.*"],
    intent: "development_tooling",
    risk: "move_with_caution"
  }
};

// File status classification
function classifyFileStatus(filePath: string, stats: any): string {
  const fileName = path.basename(filePath);
  const ext = path.extname(filePath);
  
  // Check for experimental markers
  if (fileName.includes("experimental") || fileName.includes("wip") || fileName.includes("draft")) {
    return "experimental";
  }
  
  // Check for deprecated markers
  if (fileName.includes("deprecated") || fileName.includes("legacy") || fileName.includes("old")) {
    return "deprecated";
  }
  
  // Check for quarantine markers
  if (filePath.includes("quarantine") || filePath.includes("attic") || filePath.includes("archive")) {
    return "quarantined";
  }
  
  // Check file age (very recent files might be experimental)
  const ageMs = Date.now() - stats.mtime.getTime();
  const ageDays = ageMs / (1000 * 60 * 60 * 24);
  
  if (ageDays < 1 && ext === ".ts" || ext === ".tsx") {
    return "experimental";
  }
  
  return "stable";
}

function classifyFile(filePath: string, stats: any): FileLabel {
  let namespace = "unknown";
  let intent = "unknown";
  let risk = "move_with_caution";
  
  // Find matching namespace pattern
  for (const [ns, config] of Object.entries(NAMESPACE_PATTERNS)) {
    for (const pattern of config.patterns) {
      if (minimatch(filePath, pattern)) {
        namespace = ns;
        intent = config.intent;
        risk = config.risk;
        break;
      }
    }
    if (namespace !== "unknown") break;
  }
  
  const status = classifyFileStatus(filePath, stats);
  
  return {
    path: filePath,
    namespace,
    intent,
    ownership: namespace.startsWith("ours.") ? "internal" : "external",
    status,
    risk,
    lastModified: stats.mtime.getTime(),
    size: stats.size,
  };
}

export async function runLabelBackfill(): Promise<LabelBackfillResult> {
  const result: LabelBackfillResult = {
    timestamp: Date.now(),
    filesProcessed: 0,
    labelsAssigned: 0,
    namespaceDistribution: {},
    errors: [],
    recommendations: [],
  };
  
  try {
    console.log("[LABEL_BACKFILL] Starting file classification...");
    
    // Get all files excluding obvious noise
    const files = await glob([
      "**/*",
      "!node_modules/**",
      "!.git/**", 
      "!dist/**",
      "!build/**",
      "!.next/**",
      "!.godot/**",
      "!**/*.log",
      "!**/*.tmp",
    ], {
      dot: true,
      onlyFiles: true,
    });
    
    const labels: FileLabel[] = [];
    
    for (const filePath of files) {
      try {
        const stats = await fs.stat(filePath);
        const label = classifyFile(filePath, stats);
        labels.push(label);
        
        // Update distribution
        result.namespaceDistribution[label.namespace] = 
          (result.namespaceDistribution[label.namespace] || 0) + 1;
        
        result.filesProcessed++;
        
        if (label.namespace !== "unknown") {
          result.labelsAssigned++;
        }
        
      } catch (error) {
        result.errors.push(`Failed to process ${filePath}: ${error}`);
      }
    }
    
    // Save labels index
    const labelsIndexPath = "SystemDev/reports/labels.index.json";
    await fs.writeFile(labelsIndexPath, JSON.stringify({
      generated: result.timestamp,
      total_files: labels.length,
      namespace_distribution: result.namespaceDistribution,
      labels: labels.reduce((acc, label) => {
        acc[label.path] = {
          namespace: label.namespace,
          intent: label.intent,
          ownership: label.ownership,
          status: label.status,
          risk: label.risk,
          lastModified: label.lastModified,
          size: label.size,
        };
        return acc;
      }, {} as Record<string, any>),
    }, null, 2));
    
    console.log(`[LABEL_BACKFILL] Labels index saved to ${labelsIndexPath}`);
    
    // Generate recommendations
    const unknownFiles = labels.filter(l => l.namespace === "unknown").length;
    if (unknownFiles > 0) {
      result.recommendations.push(`${unknownFiles} files need manual namespace classification`);
    }
    
    const experimentalFiles = labels.filter(l => l.status === "experimental").length;
    if (experimentalFiles > 10) {
      result.recommendations.push(`${experimentalFiles} experimental files - consider stability review`);
    }
    
    const riskyFiles = labels.filter(l => l.risk === "move_with_caution").length;
    result.recommendations.push(`${riskyFiles} files require caution for moves - use Artificer`);
    
    console.log(`[LABEL_BACKFILL] Processed ${result.filesProcessed} files, assigned ${result.labelsAssigned} labels`);
    
  } catch (error) {
    result.errors.push(`Label backfill failed: ${error}`);
  }
  
  return result;
}

export function generateLabelBackfillReceipt(result: LabelBackfillResult) {
  return {
    timestamp: result.timestamp,
    operation: "label_backfill",
    files_processed: result.filesProcessed,
    labels_assigned: result.labelsAssigned,
    coverage_percentage: Math.round((result.labelsAssigned / result.filesProcessed) * 100),
    namespace_distribution: result.namespaceDistribution,
    errors: result.errors,
    recommendations: result.recommendations,
    labels_index_location: "SystemDev/reports/labels.index.json",
    status: result.errors.length === 0 ? "successful" : "completed_with_errors",
  };
}

// CLI interface for ES modules
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  (async () => {
    console.log("[LABEL_BACKFILL] Starting immutable label assignment...");
    const result = await runLabelBackfill();
    
    console.log("\n=== LABEL BACKFILL REPORT ===");
    console.log(`Status: ${result.errors.length === 0 ? "✅ SUCCESS" : "⚠️ COMPLETED WITH ERRORS"}`);
    console.log(`Files Processed: ${result.filesProcessed}`);
    console.log(`Labels Assigned: ${result.labelsAssigned}`);
    console.log(`Coverage: ${Math.round((result.labelsAssigned / result.filesProcessed) * 100)}%`);
    
    console.log("\nNamespace Distribution:");
    for (const [namespace, count] of Object.entries(result.namespaceDistribution)) {
      console.log(`  ${namespace}: ${count} files`);
    }
    
    if (result.errors.length > 0) {
      console.log("\nErrors:");
      result.errors.forEach(error => console.log(`  🔥 ${error}`));
    }
    
    if (result.recommendations.length > 0) {
      console.log("\nRecommendations:");
      result.recommendations.forEach(rec => console.log(`  💡 ${rec}`));
    }
    
    process.exit(result.errors.length === 0 ? 0 : 1);
  })();
}

// Import minimatch for pattern matching
const minimatch = (filePath: string, pattern: string): boolean => {
  // Simple glob pattern matching - replace with actual minimatch if needed
  const regex = pattern
    .replace(/\*\*/g, ".*")
    .replace(/\*/g, "[^/]*")
    .replace(/\?/g, "[^/]");
  return new RegExp(`^${regex}$`).test(filePath);
};