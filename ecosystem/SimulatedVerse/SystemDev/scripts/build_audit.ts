#!/usr/bin/env tsx
// SystemDev/scripts/build_audit.ts
// Build Graph Inclusion Audit - CARD F implementation
// Compares served bundle vs source tree, reports missing modules

import { glob } from 'glob';
import { promises as fs } from 'node:fs';
import path from 'node:path';

interface BuildAuditReport {
  timestamp: number;
  source_files: {
    total: number;
    by_extension: Record<string, number>;
    by_directory: Record<string, number>;
  };
  bundle_analysis: {
    entry_points: string[];
    included_modules: string[];
    excluded_modules: string[];
    missing_dependencies: string[];
  };
  coverage: {
    percentage: number;
    included_count: number;
    total_count: number;
  };
  recommendations: string[];
  warnings: string[];
}

class BuildAuditor {
  private readonly sourcePatterns = [
    'GameDev/**/*.{ts,tsx,js,jsx}',
    'PreviewUI/web/**/*.{ts,tsx,js,jsx}',
    'client/src/**/*.{ts,tsx,js,jsx}',
    'packages/**/*.{ts,tsx,js,jsx}',
    'shared/**/*.{ts,tsx,js,jsx}'
  ];

  private readonly excludePatterns = [
    '**/node_modules/**',
    '**/dist/**',
    '**/build/**',
    '**/*.d.ts',
    '**/*.test.{ts,tsx,js,jsx}',
    '**/*.spec.{ts,tsx,js,jsx}'
  ];

  async audit(): Promise<BuildAuditReport> {
    console.log('[BuildAudit] Starting build graph analysis...');

    const sourceFiles = await this.scanSourceFiles();
    const bundleAnalysis = await this.analyzeBundleInclusion(sourceFiles);
    const coverage = this.calculateCoverage(sourceFiles, bundleAnalysis);
    
    const report: BuildAuditReport = {
      timestamp: Date.now(),
      source_files: this.analyzeSourceFiles(sourceFiles),
      bundle_analysis: bundleAnalysis,
      coverage,
      recommendations: this.generateRecommendations(bundleAnalysis, coverage),
      warnings: this.generateWarnings(bundleAnalysis, coverage)
    };

    await this.saveReport(report);
    console.log(`[BuildAudit] Analysis complete. Coverage: ${coverage.percentage}%`);
    
    return report;
  }

  private async scanSourceFiles(): Promise<string[]> {
    const allFiles: string[] = [];

    for (const pattern of this.sourcePatterns) {
      try {
        const files = await glob(pattern, { 
          ignore: this.excludePatterns,
          absolute: false 
        });
        allFiles.push(...files);
      } catch (error) {
        console.warn(`[BuildAudit] Error scanning pattern ${pattern}:`, error);
      }
    }

    return [...new Set(allFiles)].sort();
  }

  private analyzeSourceFiles(files: string[]): BuildAuditReport['source_files'] {
    const byExtension: Record<string, number> = {};
    const byDirectory: Record<string, number> = {};

    files.forEach(file => {
      const ext = path.extname(file);
      const dir = path.dirname(file).split('/')[0];

      byExtension[ext] = (byExtension[ext] || 0) + 1;
      byDirectory[dir] = (byDirectory[dir] || 0) + 1;
    });

    return {
      total: files.length,
      by_extension: byExtension,
      by_directory: byDirectory
    };
  }

  private async analyzeBundleInclusion(sourceFiles: string[]): Promise<BuildAuditReport['bundle_analysis']> {
    const entryPoints = await this.findEntryPoints();
    const dependencyGraph = await this.buildDependencyGraph(sourceFiles);
    const includedModules = await this.findIncludedModules(entryPoints, dependencyGraph);
    
    const excludedModules = sourceFiles.filter(file => 
      !includedModules.includes(file) && 
      !this.isOptionalModule(file)
    );

    const missingDependencies = await this.findMissingDependencies(includedModules);

    return {
      entry_points: entryPoints,
      included_modules: includedModules,
      excluded_modules: excludedModules,
      missing_dependencies: missingDependencies
    };
  }

  private async findEntryPoints(): Promise<string[]> {
    const entryPoints: string[] = [];

    // Check common entry point locations
    const candidates = [
      'client/src/main.tsx',
      'client/src/index.tsx',
      'PreviewUI/web/index.tsx',
      'PreviewUI/web/App.tsx',
      'GameDev/engine/main.ts',
      'server/index.ts'
    ];

    for (const candidate of candidates) {
      try {
        await fs.access(candidate);
        entryPoints.push(candidate);
      } catch {
        // File doesn't exist, skip
      }
    }

    // Check package.json for additional entry points
    try {
      const packageJson = JSON.parse(await fs.readFile('package.json', 'utf8'));
      
      if (packageJson.main && !entryPoints.includes(packageJson.main)) {
        entryPoints.push(packageJson.main);
      }

      if (packageJson.exports) {
        Object.values(packageJson.exports).forEach((exp: any) => {
          if (typeof exp === 'string' && !entryPoints.includes(exp)) {
            entryPoints.push(exp);
          }
        });
      }
    } catch {
      // No package.json or parsing error
    }

    return entryPoints;
  }

  private async buildDependencyGraph(sourceFiles: string[]): Promise<Map<string, string[]>> {
    const graph = new Map<string, string[]>();

    for (const file of sourceFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const dependencies = this.extractDependencies(content, file);
        graph.set(file, dependencies);
      } catch (error) {
        console.warn(`[BuildAudit] Could not read ${file}:`, error);
        graph.set(file, []);
      }
    }

    return graph;
  }

  private extractDependencies(content: string, currentFile: string): string[] {
    const dependencies: string[] = [];
    
    // Match ES6 imports and CommonJS requires
    const importRegex = /(?:import.*?from\s+['"`]([^'"`]+)['"`]|require\s*\(\s*['"`]([^'"`]+)['"`]\s*\))/g;
    
    let match;
    while ((match = importRegex.exec(content)) !== null) {
      const importPath = match[1] || match[2];
      
      if (importPath && !importPath.startsWith('.') && !importPath.startsWith('/')) {
        // External dependency
        continue;
      }

      if (importPath) {
        const resolvedPath = this.resolvePath(importPath, currentFile);
        if (resolvedPath) {
          dependencies.push(resolvedPath);
        }
      }
    }

    return dependencies;
  }

  private resolvePath(importPath: string, currentFile: string): string | null {
    if (importPath.startsWith('./') || importPath.startsWith('../')) {
      const currentDir = path.dirname(currentFile);
      let resolved = path.resolve(currentDir, importPath);
      
      // Handle extension resolution
      const extensions = ['.ts', '.tsx', '.js', '.jsx'];
      
      for (const ext of extensions) {
        const withExt = resolved + ext;
        try {
          // We can't use fs.access in sync here, so we'll just return the path
          return path.relative('.', withExt);
        } catch {
          continue;
        }
      }
      
      // Try index files
      for (const ext of extensions) {
        const indexPath = path.join(resolved, `index${ext}`);
        try {
          return path.relative('.', indexPath);
        } catch {
          continue;
        }
      }
    }

    return null;
  }

  private async findIncludedModules(entryPoints: string[], dependencyGraph: Map<string, string[]>): Promise<string[]> {
    const included = new Set<string>();
    const toProcess = [...entryPoints];

    while (toProcess.length > 0) {
      const current = toProcess.pop()!;
      
      if (included.has(current)) continue;
      included.add(current);

      const dependencies = dependencyGraph.get(current) || [];
      toProcess.push(...dependencies.filter(dep => !included.has(dep)));
    }

    return Array.from(included);
  }

  private isOptionalModule(file: string): boolean {
    const optionalPatterns = [
      /\/tests?\//,
      /\/examples?\//,
      /\/demos?\//,
      /\.test\./,
      /\.spec\./,
      /\.stories\./,
      /\/legacy\//,
      /\/deprecated\//
    ];

    return optionalPatterns.some(pattern => pattern.test(file));
  }

  private async findMissingDependencies(includedModules: string[]): Promise<string[]> {
    const missing: string[] = [];

    for (const module of includedModules) {
      try {
        await fs.access(module);
      } catch {
        missing.push(module);
      }
    }

    return missing;
  }

  private calculateCoverage(sourceFiles: string[], bundleAnalysis: BuildAuditReport['bundle_analysis']): BuildAuditReport['coverage'] {
    const relevantFiles = sourceFiles.filter(file => !this.isOptionalModule(file));
    const includedCount = bundleAnalysis.included_modules.length;
    const totalCount = relevantFiles.length;
    const percentage = totalCount > 0 ? Math.round((includedCount / totalCount) * 100) : 0;

    return {
      percentage,
      included_count: includedCount,
      total_count: totalCount
    };
  }

  private generateRecommendations(bundleAnalysis: BuildAuditReport['bundle_analysis'], coverage: BuildAuditReport['coverage']): string[] {
    const recommendations: string[] = [];

    if (coverage.percentage < 70) {
      recommendations.push('Low bundle coverage detected. Consider reviewing build configuration.');
    }

    if (bundleAnalysis.excluded_modules.length > 20) {
      recommendations.push('Many modules excluded from bundle. Review if all exclusions are intentional.');
    }

    if (bundleAnalysis.missing_dependencies.length > 0) {
      recommendations.push('Missing dependencies detected. Update bundler configuration to include these files.');
    }

    if (bundleAnalysis.entry_points.length === 0) {
      recommendations.push('No entry points found. Ensure main application files are properly configured.');
    }

    return recommendations;
  }

  private generateWarnings(bundleAnalysis: BuildAuditReport['bundle_analysis'], coverage: BuildAuditReport['coverage']): string[] {
    const warnings: string[] = [];

    if (coverage.percentage < 50) {
      warnings.push('Very low bundle coverage. Build may not include critical modules.');
    }

    if (bundleAnalysis.missing_dependencies.length > 5) {
      warnings.push('Multiple missing dependencies. Build will likely fail.');
    }

    bundleAnalysis.excluded_modules.forEach(module => {
      if (module.includes('GameDev/') && !this.isOptionalModule(module)) {
        warnings.push(`Important game module excluded: ${module}`);
      }
    });

    return warnings;
  }

  private async saveReport(report: BuildAuditReport): Promise<void> {
    try {
      await fs.mkdir('reports', { recursive: true });
      await fs.writeFile(
        'reports/build_audit.json',
        JSON.stringify(report, null, 2)
      );

      // Also save to SystemDev/receipts for agent tracking
      await fs.mkdir('SystemDev/receipts', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/build_audit_${Date.now()}.json`,
        JSON.stringify({
          action: 'build_audit',
          timestamp: report.timestamp,
          coverage_percentage: report.coverage.percentage,
          warnings_count: report.warnings.length,
          recommendations_count: report.recommendations.length,
          report_path: 'reports/build_audit.json'
        }, null, 2)
      );

      console.log('[BuildAudit] Report saved to reports/build_audit.json');
    } catch (error) {
      console.error('[BuildAudit] Failed to save report:', error);
    }
  }
}

// CLI execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const auditor = new BuildAuditor();
  auditor.audit().then(report => {
    console.log('\\n=== BUILD AUDIT SUMMARY ===');
    console.log(`Coverage: ${report.coverage.percentage}% (${report.coverage.included_count}/${report.coverage.total_count})`);
    console.log(`Warnings: ${report.warnings.length}`);
    console.log(`Recommendations: ${report.recommendations.length}`);
    
    if (report.warnings.length > 0) {
      console.log('\\nWarnings:');
      report.warnings.forEach(warning => console.log(`  ⚠️ ${warning}`));
    }

    if (report.recommendations.length > 0) {
      console.log('\\nRecommendations:');
      report.recommendations.forEach(rec => console.log(`  💡 ${rec}`));
    }

    // Exit with error code if coverage is too low
    if (report.coverage.percentage < 60) {
      console.log('\\n❌ Build coverage below acceptable threshold');
      process.exit(1);
    } else {
      console.log('\\n✅ Build audit passed');
      process.exit(0);
    }
  }).catch(error => {
    console.error('Build audit failed:', error);
    process.exit(1);
  });
}

export { BuildAuditor };