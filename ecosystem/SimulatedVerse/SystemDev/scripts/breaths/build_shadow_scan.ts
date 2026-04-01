/**
 * ΞΘΛΔ_shadow_eject - Build Shadow Detection (DRY RUN)
 * Janitor breath for mapping build shadows and legacy dist/ clusters
 */

import fs from "fs/promises";
import path from "path";
import glob from "fast-glob";

interface BuildShadow {
  path: string;
  type: "dist" | "build" | "out" | "cache" | "map" | "node_modules";
  size_mb: number;
  last_modified: string;
  served_by_preview: boolean;
  conflicts_with: string[];
  quarantine_candidate: boolean;
  move_plan?: {
    from: string;
    to: string;
    reason: string;
  };
}

interface BuildShadowMap {
  shadows: BuildShadow[];
  total_size_mb: number;
  preview_server_paths: string[];
  conflicts: Array<{
    path: string;
    shadows: BuildShadow[];
    recommended_winner: BuildShadow;
  }>;
  quarantine_plan: Array<{
    from: string;
    to: string;
    reason: string;
    size_mb: number;
  }>;
}

export async function scanBuildShadows(): Promise<BuildShadowMap> {
  const result: BuildShadowMap = {
    shadows: [],
    total_size_mb: 0,
    preview_server_paths: [],
    conflicts: [],
    quarantine_plan: [],
  };

  // Detect preview server static paths
  await detectPreviewServerPaths(result);

  // Scan for build directories
  const buildDirs = await glob([
    "dist/**",
    "build/**", 
    "out/**",
    ".next/**",
    ".vite/**",
    ".cache/**",
    "*.map",
    "**/*.map",
    "node_modules/.cache/**",
  ], { 
    onlyDirectories: false,
    ignore: ["**/node_modules/**", "**/.git/**"],
    stats: true,
  });

  // Analyze each potential shadow
  for (const item of buildDirs) {
    const shadow = await analyzeBuildArtifact(item.path, item.stats, result);
    if (shadow) {
      result.shadows.push(shadow);
      result.total_size_mb += shadow.size_mb;
    }
  }

  // Detect conflicts
  detectShadowConflicts(result);
  
  // Generate quarantine plan
  generateQuarantinePlan(result);

  return result;
}

async function detectPreviewServerPaths(result: BuildShadowMap) {
  try {
    // Read server configuration
    const serverFiles = await glob([
      "server/index.ts", 
      "server/**/*.ts",
      "SystemDev/scripts/patches/preview_launcher.ts",
    ]);

    for (const file of serverFiles) {
      try {
        const content = await fs.readFile(file, "utf-8");
        
        // Extract static serving paths
        const staticMatches = content.match(/express\.static\(['"`]([^'"`]+)['"`]\)/g);
        if (staticMatches) {
          for (const match of staticMatches) {
            const pathMatch = match.match(/['"`]([^'"`]+)['"`]/);
            if (pathMatch) {
              result.preview_server_paths.push(pathMatch[1]);
            }
          }
        }

        // Extract sendFile paths
        const sendFileMatches = content.match(/sendFile\([^,)]*['"`]([^'"`]+)['"`]/g);
        if (sendFileMatches) {
          for (const match of sendFileMatches) {
            const pathMatch = match.match(/['"`]([^'"`]+)['"`]/);
            if (pathMatch) {
              result.preview_server_paths.push(path.dirname(pathMatch[1]));
            }
          }
        }
      } catch (error) {
        // Silent fail for individual files
      }
    }
  } catch (error) {
    console.warn("[BUILD_SHADOW_SCAN] Server path detection failed:", error);
  }
}

async function analyzeBuildArtifact(filePath: string, stats: any, context: BuildShadowMap): Promise<BuildShadow | null> {
  try {
    const stat = stats || await fs.stat(filePath);
    const sizeMB = stat.size / (1024 * 1024);
    
    // Skip very small files unless they're important
    if (sizeMB < 0.1 && !isImportantArtifact(filePath)) {
      return null;
    }

    const shadow: BuildShadow = {
      path: filePath,
      type: classifyBuildArtifact(filePath),
      size_mb: sizeMB,
      last_modified: stat.mtime.toISOString(),
      served_by_preview: isServedByPreview(filePath, context),
      conflicts_with: [],
      quarantine_candidate: false,
    };

    // Check if this shadows other artifacts
    shadow.conflicts_with = findConflicts(filePath, context);
    shadow.quarantine_candidate = shouldQuarantine(shadow);

    return shadow;
  } catch (error) {
    return null;
  }
}

function classifyBuildArtifact(filePath: string): BuildShadow["type"] {
  if (filePath.includes("dist/")) return "dist";
  if (filePath.includes("build/")) return "build";
  if (filePath.includes("out/")) return "out";
  if (filePath.includes(".cache/")) return "cache";
  if (filePath.endsWith(".map")) return "map";
  if (filePath.includes("node_modules/")) return "node_modules";
  return "dist"; // default
}

function isImportantArtifact(filePath: string): boolean {
  const important = [
    "index.html",
    "main.js",
    "app.js",
    "bundle.js",
    "style.css",
    "manifest.json",
  ];
  
  return important.some(name => filePath.includes(name));
}

function isServedByPreview(filePath: string, context: BuildShadowMap): boolean {
  return context.preview_server_paths.some(serverPath => {
    const normalizedFilePath = path.resolve(filePath);
    const normalizedServerPath = path.resolve(serverPath);
    return normalizedFilePath.startsWith(normalizedServerPath);
  });
}

function findConflicts(filePath: string, context: BuildShadowMap): string[] {
  const conflicts: string[] = [];
  const fileName = path.basename(filePath);
  
  // Look for files with same name in different build directories
  for (const shadow of context.shadows) {
    if (shadow.path !== filePath && path.basename(shadow.path) === fileName) {
      conflicts.push(shadow.path);
    }
  }
  
  return conflicts;
}

function shouldQuarantine(shadow: BuildShadow): boolean {
  // Quarantine candidates:
  // 1. Old build artifacts (> 7 days old)
  const isOld = Date.now() - new Date(shadow.last_modified).getTime() > 7 * 24 * 60 * 60 * 1000;
  
  // 2. Not served by preview but takes up space
  const isUnused = !shadow.served_by_preview && shadow.size_mb > 1;
  
  // 3. Has conflicts (multiple versions)
  const hasConflicts = shadow.conflicts_with.length > 0;
  
  // 4. Cache directories > 50MB
  const isLargeCache = shadow.type === "cache" && shadow.size_mb > 50;
  
  return isOld || isUnused || hasConflicts || isLargeCache;
}

function detectShadowConflicts(result: BuildShadowMap) {
  const pathGroups = new Map<string, BuildShadow[]>();
  
  // Group by base filename
  for (const shadow of result.shadows) {
    const baseName = path.basename(shadow.path);
    if (!pathGroups.has(baseName)) {
      pathGroups.set(baseName, []);
    }
    pathGroups.get(baseName)!.push(shadow);
  }
  
  // Find conflicts (same filename, different locations)
  for (const [fileName, shadows] of pathGroups) {
    if (shadows.length > 1) {
      // Prefer: served by preview > newer > smaller
      const sortedShadows = [...shadows].sort((a, b) => {
        if (a.served_by_preview !== b.served_by_preview) {
          return a.served_by_preview ? -1 : 1;
        }
        if (a.last_modified !== b.last_modified) {
          return new Date(b.last_modified).getTime() - new Date(a.last_modified).getTime();
        }
        return a.size_mb - b.size_mb;
      });
      
      result.conflicts.push({
        path: fileName,
        shadows,
        recommended_winner: sortedShadows[0],
      });
    }
  }
}

function generateQuarantinePlan(result: BuildShadowMap) {
  const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
  
  for (const shadow of result.shadows) {
    if (shadow.quarantine_candidate) {
      const targetDir = `attic/.recycle/build_shadow/${timestamp}`;
      const relativePath = shadow.path.replace(/^\.\//, '');
      const targetPath = path.join(targetDir, relativePath);
      
      shadow.move_plan = {
        from: shadow.path,
        to: targetPath,
        reason: determineQuarantineReason(shadow),
      };
      
      result.quarantine_plan.push({
        from: shadow.path,
        to: targetPath,
        reason: shadow.move_plan.reason,
        size_mb: shadow.size_mb,
      });
    }
  }
}

function determineQuarantineReason(shadow: BuildShadow): string {
  const reasons: string[] = [];
  
  if (!shadow.served_by_preview) {
    reasons.push("not_served_by_preview");
  }
  
  if (shadow.conflicts_with.length > 0) {
    reasons.push("has_conflicts");
  }
  
  const isOld = Date.now() - new Date(shadow.last_modified).getTime() > 7 * 24 * 60 * 60 * 1000;
  if (isOld) {
    reasons.push("older_than_7_days");
  }
  
  if (shadow.size_mb > 50) {
    reasons.push("large_size");
  }
  
  return reasons.join(", ") || "general_cleanup";
}

export async function generateBuildShadowReport(): Promise<void> {
  console.log("[JANITOR:ΞΘΛΔ_shadow_eject] Scanning build shadows...");
  
  const analysis = await scanBuildShadows();
  
  const receipt = {
    timestamp: Date.now(),
    operation: "build_shadow_scan",
    breath: "ΞΘΛΔ_shadow_eject",
    agent: "janitor",
    mode: "dry_run",
    analysis,
    total_quarantine_size_mb: analysis.quarantine_plan.reduce((sum, plan) => sum + plan.size_mb, 0),
    conflict_count: analysis.conflicts.length,
    shadow_count: analysis.shadows.length,
  };

  // Ensure reports directory exists
  await fs.mkdir("SystemDev/reports", { recursive: true });
  
  // Write main report
  await fs.writeFile(
    "SystemDev/reports/build_shadow_map.json",
    JSON.stringify(analysis, null, 2)
  );

  // Write receipt
  await fs.mkdir("SystemDev/receipts", { recursive: true });
  await fs.writeFile(
    `SystemDev/receipts/build_shadow_scan_${Date.now()}.json`,
    JSON.stringify(receipt, null, 2)
  );

  console.log(`[JANITOR:ΞΘΛΔ_shadow_eject] Scan complete → SystemDev/reports/build_shadow_map.json`);
  console.log(`[JANITOR] Found ${analysis.shadows.length} shadows, ${analysis.conflicts.length} conflicts, ${Math.round(analysis.total_size_mb)}MB total`);
  
  if (analysis.quarantine_plan.length > 0) {
    console.log(`[JANITOR] Quarantine candidates: ${analysis.quarantine_plan.length} items (${Math.round(receipt.total_quarantine_size_mb)}MB)`);
  }
}

// CLI interface for ES modules
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  generateBuildShadowReport().catch(console.error);
}