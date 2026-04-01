/* 
OWNERS: team/infra, ai/prime
TAGS: infra, analysis, audit, maximum-depth
STABILITY: beta
INTEGRATIONS: scope/resolver, proof/gate, testing/chamber
*/

import { Router } from "express";
import { resolveScope, type ScopeSelection } from "../lib/scope.js";
import { adminGuard } from '../middleware/auth.js';
import { standardRateLimit } from '../middleware/rate-limit.js';
import fs from "fs";
import path from "path";

const router = Router();

interface AnalysisResult {
  scope: ReturnType<typeof resolveScope>;
  inventory: InventoryResult;
  dependencies: DependencyResult;
  health: HealthResult;
  recommendations: RecommendationItem[];
}

interface InventoryResult {
  total_files: number;
  by_type: Record<string, number>;
  by_directory: Record<string, number>;
  missing_headers: string[];
  orphaned_files: string[];
  potential_duplicates: Array<{files: string[]; similarity: number}>;
}

interface DependencyResult {
  imports: Array<{from: string; to: string; type: string}>;
  circular: string[][];
  external: Record<string, string[]>;
}

interface HealthResult {
  lsp_errors: number;
  test_coverage: number;
  documentation_coverage: number;
  technical_debt_score: number;
}

interface RecommendationItem {
  type: 'fix' | 'refactor' | 'optimize' | 'document';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  files: string[];
  effort: string;
}

// Maximum-depth repository analysis
router.post("/repo-audit", standardRateLimit, adminGuard, async (req, res) => {
  try {
    const scope: ScopeSelection = req.body.scope || { view: "everything" };
    const result = await performMaximumDepthAnalysis(scope);
    
    res.json({
      ok: true,
      analysis: result,
      timestamp: new Date().toISOString(),
      scope_summary: {
        view: result.scope.view,
        files_analyzed: result.scope.files.length,
        analysis_depth: "maximum"
      }
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Analysis failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Quick health check for a scope
router.post("/health-check", standardRateLimit, adminGuard, async (req, res) => {
  try {
    const scope: ScopeSelection = req.body.scope || { view: "everything" };
    const scopeResult = resolveScope(scope);
    
    const health = await analyzeHealth(scopeResult.files);
    
    res.json({
      ok: true,
      health,
      scope: {
        view: scopeResult.view,
        file_count: scopeResult.files.length
      }
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Health check failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Dependency analysis for scope
router.post("/dependencies", standardRateLimit, adminGuard, async (req, res) => {
  try {
    const scope: ScopeSelection = req.body.scope || { view: "everything" };
    const scopeResult = resolveScope(scope);
    
    const deps = await analyzeDependencies(scopeResult.files);
    
    res.json({
      ok: true,
      dependencies: deps,
      scope: {
        view: scopeResult.view,
        file_count: scopeResult.files.length
      }
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Dependency analysis failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

async function performMaximumDepthAnalysis(scope: ScopeSelection): Promise<AnalysisResult> {
  const scopeResult = resolveScope(scope);
  
  const [inventory, dependencies, health] = await Promise.all([
    analyzeInventory(scopeResult.files),
    analyzeDependencies(scopeResult.files),
    analyzeHealth(scopeResult.files)
  ]);
  
  const recommendations = generateRecommendations(inventory, dependencies, health);
  
  return {
    scope: scopeResult,
    inventory,
    dependencies,
    health,
    recommendations
  };
}

async function analyzeInventory(files: string[]): Promise<InventoryResult> {
  const inventory: InventoryResult = {
    total_files: files.length,
    by_type: {},
    by_directory: {},
    missing_headers: [],
    orphaned_files: [],
    potential_duplicates: []
  };

  for (const file of files) {
    // File type analysis
    const ext = path.extname(file) || 'no-ext';
    inventory.by_type[ext] = (inventory.by_type[ext] || 0) + 1;
    
    // Directory analysis
    const dir = path.dirname(file);
    inventory.by_directory[dir] = (inventory.by_directory[dir] || 0) + 1;
    
    // Check for missing Rosetta headers
    if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
      if (!hasRosettaHeader(file)) {
        inventory.missing_headers.push(file);
      }
    }
  }
  
  return inventory;
}

async function analyzeDependencies(files: string[]): Promise<DependencyResult> {
  const dependencies: DependencyResult = {
    imports: [],
    circular: [],
    external: {}
  };
  
  // Basic import analysis (simplified for now)
  for (const file of files.filter(f => ['.ts', '.tsx', '.js', '.jsx'].includes(path.extname(f)))) {
    try {
      const content = fs.readFileSync(file, 'utf8');
      const imports = extractImports(content);
      
      for (const imp of imports) {
        dependencies.imports.push({
          from: file,
          to: imp.path,
          type: imp.type
        });
        
        if (imp.isExternal && imp.package) {
          if (!dependencies.external[imp.package]) {
            dependencies.external[imp.package] = [];
          }
          dependencies.external[imp.package]?.push(file);
        }
      }
    } catch {
      // Skip files that can't be read
    }
  }
  
  return dependencies;
}

async function analyzeHealth(files: string[]): Promise<HealthResult> {
  return {
    lsp_errors: 0, // Would integrate with LSP diagnostics
    test_coverage: 0, // Would integrate with test runner
    documentation_coverage: files.filter(f => f.includes('.md')).length / files.length * 100,
    technical_debt_score: 0 // Would calculate based on various metrics
  };
}

function generateRecommendations(inventory: InventoryResult, dependencies: DependencyResult, health: HealthResult): RecommendationItem[] {
  const recommendations: RecommendationItem[] = [];
  
  if (inventory.missing_headers.length > 0) {
    recommendations.push({
      type: 'fix' as const,
      priority: 'high' as const,
      title: 'Add missing Rosetta headers',
      description: `${inventory.missing_headers.length} files missing OWNERS/TAGS headers`,
      files: inventory.missing_headers.slice(0, 10),
      effort: '1-2 hours'
    });
  }
  
  if (Object.keys(dependencies.external).length > 50) {
    recommendations.push({
      type: 'optimize' as const,
      priority: 'medium' as const,
      title: 'Review external dependencies',
      description: 'Large number of external dependencies may impact performance',
      files: [],
      effort: '4-6 hours'
    });
  }
  
  return recommendations;
}

function hasRosettaHeader(filePath: string): boolean {
  try {
    const content = fs.readFileSync(filePath, "utf8").slice(0, 1024);
    return content.includes("OWNERS:") && content.includes("TAGS:");
  } catch {
    return false;
  }
}

function extractImports(content: string) {
  const imports = [];
  const importRegex = /import\s+.*?\s+from\s+['"]([^'"]+)['"]/g;
  let match;
  
  while ((match = importRegex.exec(content)) !== null) {
    const importPath = match[1];
    if (importPath) {
      const isExternal = !importPath.startsWith('./') && !importPath.startsWith('../') && !importPath.startsWith('@/');
      
      imports.push({
        path: importPath,
        type: isExternal ? 'external' : 'internal',
        isExternal,
        package: isExternal ? importPath.split('/')[0] : null
      });
    }
  }
  
  return imports;
}

export default router;