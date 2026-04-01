#!/usr/bin/env tsx
/**
 * Repository Intelligence Scanner using Strategic Packages
 * - ts-morph: Deep TypeScript AST analysis  
 * - madge: Dependency graph analysis
 * - fast-glob: Lightning file pattern scanning
 * - depcheck: Unused dependency detection
 */
import { Project } from "ts-morph";
import madge from "madge";
import glob from "fast-glob";
import depcheck from "depcheck";
import fs from "node:fs";
import path from "node:path";

const reports = "SystemDev/reports";
fs.mkdirSync(reports, { recursive: true });

async function scanRepository() {
  const timestamp = Date.now();
  
  console.log("[🧠] Starting repository intelligence scan...");
  
  // Fast file discovery with patterns
  console.log("[📁] Scanning file patterns...");
  const patterns = await Promise.all([
    glob("**/*.{ts,tsx,js,jsx}", { ignore: ["node_modules/**", ".git/**", "dist/**"] }),
    glob("**/index.{html,htm}", { ignore: ["node_modules/**", ".git/**"] }),
    glob("**/*.{vue,svelte,astro}", { ignore: ["node_modules/**", ".git/**"] }),
    glob("**/package.json", { ignore: ["node_modules/**"] }),
  ]);
  
  const [sourceFiles, indexFiles, frameworkFiles, packageFiles] = patterns;
  
  // TypeScript AST analysis for import patterns
  console.log("[🔍] Analyzing TypeScript imports...");
  const project = new Project();
  const importAnalysis: Record<string, string[]> = {};
  
  for (const file of sourceFiles.slice(0, 100)) { // Limit for performance
    try {
      const sourceFile = project.addSourceFileAtPath(file);
      const imports = sourceFile.getImportDeclarations().map(imp => 
        imp.getModuleSpecifierValue()
      );
      importAnalysis[file] = imports;
    } catch (error) {
      // Skip problematic files
    }
  }
  
  // Dependency graph analysis
  console.log("[📊] Building dependency graph...");
  let dependencyGraph: any = null;
  try {
    dependencyGraph = await madge(".", {
      fileExtensions: ['js', 'ts', 'tsx', 'jsx'],
      excludeRegExp: /node_modules|\.git|dist/
    } as any);
  } catch (error) {
    console.warn("[⚠️] Dependency graph analysis failed:", error);
  }
  
  // Unused dependency detection
  console.log("[🧹] Detecting unused dependencies...");
  let unusedDeps: any = null;
  try {
    unusedDeps = await depcheck(".", {
      ignoreBinPackage: false,
      skipMissing: false,
    } as any);
  } catch (error) {
    console.warn("[⚠️] Depcheck analysis failed:", error);
  }
  
  const intelligence = {
    timestamp: new Date().toISOString(),
    scan_id: timestamp,
    file_patterns: {
      source_files: sourceFiles.length,
      index_files: indexFiles.length,
      framework_files: frameworkFiles.length,
      package_files: packageFiles.length,
      sample_sources: sourceFiles.slice(0, 10),
      all_indices: indexFiles,
    },
    import_analysis: Object.keys(importAnalysis).length > 0 ? {
      files_analyzed: Object.keys(importAnalysis).length,
      most_imported: (() => {
        const counts: Record<string, number> = {};
        Object.values(importAnalysis).flat().forEach(imp => {
          counts[imp] = (counts[imp] || 0) + 1;
        });
        return Object.entries(counts)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 10);
      })(),
      sample_imports: Object.entries(importAnalysis).slice(0, 5)
    } : null,
    dependency_graph: dependencyGraph ? {
      circular_dependencies: dependencyGraph.circular(),
      leaf_files: dependencyGraph.leaves(),
      orphan_files: (dependencyGraph as any).orphans?.() || []
    } : null,
    unused_analysis: unusedDeps ? {
      unused_dependencies: unusedDeps.dependencies,
      unused_dev_dependencies: unusedDeps.devDependencies,
      missing_dependencies: Object.keys(unusedDeps.missing || {})
    } : null,
    consolidation_opportunities: {
      duplicate_indices: indexFiles.length > 1 ? indexFiles : [],
      bloat_indicators: unusedDeps ? Object.keys(unusedDeps.dependencies || {}).length : 0,
      circular_complexity: (dependencyGraph as any)?.circular?.()?.length || 0
    }
  };
  
  const outFile = path.join(reports, `repo_intelligence_${timestamp}.json`);
  fs.writeFileSync(outFile, JSON.stringify(intelligence, null, 2));
  
  console.log(`[✅] Repository intelligence saved: ${outFile}`);
  console.log(`[📈] Analysis: ${sourceFiles.length} sources, ${indexFiles.length} indices, ${unusedDeps?.dependencies ? Object.keys(unusedDeps.dependencies).length : 0} unused deps`);
  
  return intelligence;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  scanRepository().catch(console.error);
}