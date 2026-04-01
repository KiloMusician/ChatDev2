#!/usr/bin/env tsx
/**
 * Repo Graph (imports & Godot scenes) — Deep repository relationship analysis
 * Integrates TypeScript imports with Godot scene dependencies for full quadpartite view
 */
import { Project } from "ts-morph";
// @ts-ignore - Module may not be available
import { XMLParser } from "fast-xml-parser";
import fs from "node:fs";
import path from "node:path";
import pino from "pino";

const logger = pino({ level: 'info' });

// Repository node types for quadpartite analysis
export interface RepoNode {
  path: string;
  type: "typescript" | "javascript" | "godot_scene" | "godot_script" | "json" | "markdown";
  imports: string[];
  exports: string[];
  size: number;
  lastModified: Date;
  quadrant: "SystemDev" | "ChatDev" | "GameDev" | "PreviewUI" | "shared";
  centrality?: number; // Calculated post-analysis
  isOrphan?: boolean;
  isBoss?: boolean; // High-centrality files with failing checks
}

export interface RepoGraph {
  nodes: Map<string, RepoNode>;
  edges: Array<{ from: string; to: string; type: "import" | "scene_ref" | "script_ref" }>;
  metadata: {
    totalNodes: number;
    totalEdges: number;
    quadrantDistribution: Record<string, number>;
    bossNodes: RepoNode[];
    orphanNodes: RepoNode[];
    analysisTimestamp: string;
  };
}

/**
 * Build comprehensive repository graph spanning all quadrants
 */
export async function buildRepoGraph(): Promise<RepoGraph> {
  logger.info("🕸️ Building repository graph...");
  const startTime = Date.now();

  // Discover files across quadrants
  const files = await discoverFiles();
  const nodes = new Map<string, RepoNode>();
  const edges: RepoGraph["edges"] = [];

  // Analyze TypeScript/JavaScript files
  await analyzeSourceFiles(files.source, nodes, edges);
  
  // Analyze Godot scenes and scripts
  await analyzeGodotFiles(files.godot, nodes, edges);
  
  // Analyze configuration and metadata files
  await analyzeConfigFiles(files.config, nodes, edges);

  // Calculate graph metrics
  const { bossNodes, orphanNodes } = calculateGraphMetrics(nodes, edges);

  const graph: RepoGraph = {
    nodes,
    edges,
    metadata: {
      totalNodes: nodes.size,
      totalEdges: edges.length,
      quadrantDistribution: calculateQuadrantDistribution(nodes),
      bossNodes: bossNodes.slice(0, 10), // Top 10 boss nodes
      orphanNodes,
      analysisTimestamp: new Date().toISOString()
    }
  };

  logger.info(`✅ Repository graph built: ${nodes.size} nodes, ${edges.length} edges in ${Date.now() - startTime}ms`);
  
  // Save analysis results
  await saveAnalysisResults(graph);
  
  return graph;
}

/**
 * Discover files across all quadrants with proper categorization
 */
async function discoverFiles() {
  let glob;
  try {
    const fastGlob = await import("fast-glob");
    glob = fastGlob.glob;
  } catch {
    // Fallback file discovery if fast-glob unavailable
    glob = async (patterns: string[]) => {
      const result: string[] = [];
      for (const pattern of patterns) {
        // Simple recursive directory walk as fallback
        if (pattern.includes("**")) {
          const baseDir = pattern.split("**")[0];
          if (fs.existsSync(baseDir)) {
            result.push(...walkDirectory(baseDir));
          }
        }
      }
      return result;
    };
  }

  const [sourceFiles, godotFiles, configFiles] = await Promise.all([
    glob([
      "src/**/*.{ts,tsx,js,jsx}",
      "client/**/*.{ts,tsx,js,jsx}",
      "server/**/*.{ts,tsx,js,jsx}",
      "shared/**/*.{ts,tsx,js,jsx}",
      "SystemDev/**/*.{ts,tsx,js,jsx}",
      "PreviewUI/**/*.{ts,tsx,js,jsx}"
    ], { ignore: ["**/node_modules/**", "**/dist/**", "**/.git/**"] }),
    
    glob([
      "GameDev/**/*.{tscn,tres,gd,cs}",
      "PreviewUI/**/*.{tscn,tres,gd}"
    ], { ignore: ["**/node_modules/**", "**/dist/**"] }),
    
    glob([
      "**/package.json",
      "**/tsconfig.json",
      "**/*.config.{js,ts}",
      "SystemDev/**/*.{json,yml,yaml,md}"
    ], { ignore: ["**/node_modules/**", "**/dist/**"] })
  ]);

  return {
    source: sourceFiles,
    godot: godotFiles,
    config: configFiles
  };
}

/**
 * Analyze TypeScript/JavaScript source files
 */
async function analyzeSourceFiles(files: string[], nodes: Map<string, RepoNode>, edges: RepoGraph["edges"]) {
  logger.info(`🔍 Analyzing ${files.length} source files...`);
  
  const project = new Project({ 
    skipFileDependencyResolution: true,
    useInMemoryFileSystem: true // Performance optimization
  });

  // Add files to project in batches for performance
  const batchSize = 100;
  for (let i = 0; i < files.length; i += batchSize) {
    const batch = files.slice(i, i + batchSize);
    batch.forEach(file => {
      try {
        project.addSourceFileAtPath(file);
      } catch (error) {
        logger.warn(`Skipping problematic file: ${file}`, error);
      }
    });
  }

  // Analyze each source file
  for (const sourceFile of project.getSourceFiles()) {
    const filePath = sourceFile.getFilePath();
    const stats = fs.statSync(filePath);
    
    // Extract imports
    const imports = sourceFile.getImportDeclarations().map(imp => 
      imp.getModuleSpecifierValue()
    );
    
    // Extract exports
    const exports = sourceFile.getExportDeclarations().map(exp => 
      exp.getModuleSpecifier()?.getLiteralValue() || ""
    ).filter(Boolean);

    const node: RepoNode = {
      path: filePath,
      type: filePath.endsWith('.ts') || filePath.endsWith('.tsx') ? "typescript" : "javascript",
      imports,
      exports,
      size: stats.size,
      lastModified: stats.mtime,
      quadrant: determineQuadrant(filePath)
    };

    nodes.set(filePath, node);

    // Create edges for imports
    imports.forEach(importPath => {
      edges.push({
        from: filePath,
        to: resolveImportPath(importPath, filePath),
        type: "import"
      });
    });
  }
}

/**
 * Analyze Godot scene and script files
 */
async function analyzeGodotFiles(files: string[], nodes: Map<string, RepoNode>, edges: RepoGraph["edges"]) {
  logger.info(`🎮 Analyzing ${files.length} Godot files...`);
  
  const parser = new XMLParser();

  for (const file of files) {
    try {
      const stats = fs.statSync(file);
      const content = fs.readFileSync(file, 'utf8');
      
      let imports: string[] = [];
      let type: RepoNode["type"] = "godot_scene";

      if (file.endsWith('.gd')) {
        // GDScript file - parse script dependencies
        type = "godot_script";
        imports = extractGDScriptDependencies(content);
      } else if (file.endsWith('.tscn') || file.endsWith('.tres')) {
        // Godot scene/resource file - parse XML structure
        const parsed = parser.parse(content);
        imports = extractSceneDependencies(parsed);
      }

      const node: RepoNode = {
        path: file,
        type,
        imports,
        exports: [], // Godot files don't have explicit exports like JS/TS
        size: stats.size,
        lastModified: stats.mtime,
        quadrant: "GameDev"
      };

      nodes.set(file, node);

      // Create edges for scene/script references
      imports.forEach(dep => {
        edges.push({
          from: file,
          to: dep,
          type: file.endsWith('.gd') ? "script_ref" : "scene_ref"
        });
      });

    } catch (error) {
      logger.warn(`Failed to analyze Godot file ${file}:`, error);
    }
  }
}

/**
 * Analyze configuration and metadata files
 */
async function analyzeConfigFiles(files: string[], nodes: Map<string, RepoNode>, edges: RepoGraph["edges"]) {
  logger.info(`⚙️ Analyzing ${files.length} config files...`);
  
  for (const file of files) {
    try {
      const stats = fs.statSync(file);
      const content = fs.readFileSync(file, 'utf8');
      
      let imports: string[] = [];
      
      if (file.endsWith('package.json')) {
        const pkg = JSON.parse(content);
        imports = [
          ...Object.keys(pkg.dependencies || {}),
          ...Object.keys(pkg.devDependencies || {})
        ];
      } else if (file.endsWith('tsconfig.json')) {
        const tsconfig = JSON.parse(content);
        imports = tsconfig.extends ? [tsconfig.extends] : [];
      }

      const node: RepoNode = {
        path: file,
        type: "json",
        imports,
        exports: [],
        size: stats.size,
        lastModified: stats.mtime,
        quadrant: determineQuadrant(file)
      };

      nodes.set(file, node);

    } catch (error) {
      logger.warn(`Failed to analyze config file ${file}:`, error);
    }
  }
}

/**
 * Calculate graph metrics including boss nodes and orphans
 */
function calculateGraphMetrics(nodes: Map<string, RepoNode>, edges: RepoGraph["edges"]) {
  // Calculate centrality scores
  const inDegree = new Map<string, number>();
  const outDegree = new Map<string, number>();
  
  edges.forEach(edge => {
    inDegree.set(edge.to, (inDegree.get(edge.to) || 0) + 1);
    outDegree.set(edge.from, (outDegree.get(edge.from) || 0) + 1);
  });

  // Update nodes with centrality and classification
  const bossNodes: RepoNode[] = [];
  const orphanNodes: RepoNode[] = [];

  nodes.forEach((node, path) => {
    const inDeg = inDegree.get(path) || 0;
    const outDeg = outDegree.get(path) || 0;
    node.centrality = inDeg + outDeg;
    
    // Classify as boss (high centrality) or orphan (no connections)
    if (node.centrality >= 10) {
      node.isBoss = true;
      bossNodes.push(node);
    } else if (node.centrality === 0) {
      node.isOrphan = true;
      orphanNodes.push(node);
    }
  });

  // Sort boss nodes by centrality
  bossNodes.sort((a, b) => (b.centrality || 0) - (a.centrality || 0));

  return { bossNodes, orphanNodes };
}

/**
 * Helper functions
 */
function determineQuadrant(filePath: string): RepoNode["quadrant"] {
  if (filePath.includes("SystemDev")) return "SystemDev";
  if (filePath.includes("GameDev")) return "GameDev";
  if (filePath.includes("PreviewUI")) return "PreviewUI";
  if (filePath.includes("shared")) return "shared";
  return "ChatDev"; // Default for src/, client/, server/
}

function resolveImportPath(importPath: string, fromFile: string): string {
  // Simple import resolution - in production would use proper module resolution
  if (importPath.startsWith('.')) {
    return path.resolve(path.dirname(fromFile), importPath);
  }
  return importPath; // External dependency
}

function extractGDScriptDependencies(content: string): string[] {
  const deps: string[] = [];
  const lines = content.split('\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('extends ')) {
      deps.push(trimmed.split(' ')[1]);
    }
    if (trimmed.includes('preload(') || trimmed.includes('load(')) {
      const match = trimmed.match(/(?:preload|load)\("([^"]+)"\)/);
      if (match) deps.push(match[1]);
    }
  }
  
  return deps;
}

function extractSceneDependencies(parsed: any): string[] {
  const deps: string[] = [];
  
  // Extract external resource paths
  if (parsed.resource?.ext_resource) {
    const resources = Array.isArray(parsed.resource.ext_resource) 
      ? parsed.resource.ext_resource 
      : [parsed.resource.ext_resource];
    
    resources.forEach((res: any) => {
      if (res?.path) deps.push(res.path);
    });
  }
  
  return deps;
}

function calculateQuadrantDistribution(nodes: Map<string, RepoNode>): Record<string, number> {
  const distribution: Record<string, number> = {
    SystemDev: 0,
    ChatDev: 0,
    GameDev: 0,
    PreviewUI: 0,
    shared: 0
  };
  
  nodes.forEach(node => {
    distribution[node.quadrant]++;
  });
  
  return distribution;
}

function walkDirectory(dir: string): string[] {
  const result: string[] = [];
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory() && !['node_modules', '.git', 'dist'].includes(entry.name)) {
        result.push(...walkDirectory(fullPath));
      } else if (entry.isFile()) {
        result.push(fullPath);
      }
    }
  } catch (error) {
    // Ignore permission errors
  }
  return result;
}

async function saveAnalysisResults(graph: RepoGraph): Promise<void> {
  const reportsDir = "SystemDev/reports";
  fs.mkdirSync(reportsDir, { recursive: true });
  
  const timestamp = Date.now();
  const analysisPath = path.join(reportsDir, `repo_graph_${timestamp}.json`);
  
  // Serialize graph data
  const serializable = {
    nodes: Array.from(graph.nodes.entries()).map(([filePath, node]) => ({ filePath, ...node })),
    edges: graph.edges,
    metadata: graph.metadata
  };
  
  fs.writeFileSync(analysisPath, JSON.stringify(serializable, null, 2));
  logger.info(`📊 Analysis saved: ${analysisPath}`);
}

// CLI execution
if (import.meta.url === `file://${process.argv[1]}`) {
  buildRepoGraph().catch(console.error);
}