#!/usr/bin/env tsx
// SystemDev/scripts/case_clash_audit.ts
// Case-sensitive path clash detection for mobile compatibility

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

interface FileEntry {
  path: string;
  normalizedPath: string;
  hash: string;
}

interface ClashGroup {
  normalizedPath: string;
  files: string[];
  severity: 'low' | 'medium' | 'high';
}

class CaseClashAuditor {
  private fileMap = new Map<string, FileEntry[]>();
  private excludePatterns = [
    /node_modules/,
    /\.git/,
    /\.godot/,
    /dist\/assets/,
    /\.map$/,
    /\.cache/,
    /\.venv/,
    /__pycache__/
  ];

  async auditDirectory(rootPath: string): Promise<ClashGroup[]> {
    console.log(`🔍 Starting case-clash audit for: ${rootPath}`);
    
    await this.scanDirectory(rootPath);
    const clashes = this.findClashes();
    
    console.log(`📊 Audit complete: ${clashes.length} potential clashes found`);
    return clashes;
  }

  private async scanDirectory(dirPath: string): Promise<void> {
    try {
      const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        
        // Skip excluded patterns
        if (this.excludePatterns.some(pattern => pattern.test(fullPath))) {
          continue;
        }
        
        if (entry.isDirectory()) {
          await this.scanDirectory(fullPath);
        } else {
          this.recordFile(fullPath);
        }
      }
    } catch (error) {
      console.warn(`⚠️ Cannot read directory: ${dirPath}`);
    }
  }

  private recordFile(filePath: string): void {
    const normalizedPath = filePath.toLowerCase();
    const hash = crypto.createHash('md5').update(normalizedPath).digest('hex');
    
    const entry: FileEntry = {
      path: filePath,
      normalizedPath,
      hash
    };
    
    if (!this.fileMap.has(normalizedPath)) {
      this.fileMap.set(normalizedPath, []);
    }
    
    this.fileMap.get(normalizedPath)!.push(entry);
  }

  private findClashes(): ClashGroup[] {
    const clashes: ClashGroup[] = [];
    
    for (const [normalizedPath, entries] of this.fileMap.entries()) {
      if (entries.length > 1) {
        // Multiple files with same case-insensitive path
        const severity = this.assessSeverity(entries);
        
        clashes.push({
          normalizedPath,
          files: entries.map(e => e.path),
          severity
        });
      }
    }
    
    return clashes.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }

  private assessSeverity(entries: FileEntry[]): 'low' | 'medium' | 'high' {
    const paths = entries.map(e => e.path);
    
    // High severity: Different extensions or critical paths
    if (paths.some(p => p.includes('src/') || p.includes('client/') || p.includes('server/'))) {
      return 'high';
    }
    
    // Medium severity: Assets or configuration files
    if (paths.some(p => p.includes('assets/') || p.includes('public/') || p.includes('config/'))) {
      return 'medium';
    }
    
    return 'low';
  }

  async generateReport(clashes: ClashGroup[]): Promise<void> {
    const timestamp = new Date().toISOString();
    const report = {
      timestamp,
      total_clashes: clashes.length,
      severity_breakdown: {
        high: clashes.filter(c => c.severity === 'high').length,
        medium: clashes.filter(c => c.severity === 'medium').length,
        low: clashes.filter(c => c.severity === 'low').length
      },
      clashes: clashes.map(clash => ({
        normalized_path: clash.normalizedPath,
        severity: clash.severity,
        conflicting_files: clash.files,
        recommendation: this.getRecommendation(clash)
      })),
      mobile_impact: {
        android_webview: "Case-sensitive filesystem will cause 404s",
        samsung_s23: "Native browser may fail to load resources",
        replit_preview: "Mobile preview tunnel sensitive to case mismatches"
      },
      next_actions: clashes.length > 0 ? [
        "Review high-severity clashes first",
        "Standardize naming convention (lowercase preferred)",
        "Use path normalization middleware",
        "Test on actual Android device"
      ] : [
        "No case clashes detected",
        "Mobile preview should work correctly",
        "Maintain consistent naming conventions"
      ]
    };

    const reportPath = 'SystemDev/reports/case_clash.json';
    await fs.promises.mkdir(path.dirname(reportPath), { recursive: true });
    await fs.promises.writeFile(reportPath, JSON.stringify(report, null, 2));
    
    console.log(`📋 Report generated: ${reportPath}`);
    
    // Also generate a run card if clashes found
    if (clashes.length > 0) {
      await this.generateRunCard(clashes);
    }
  }

  private getRecommendation(clash: ClashGroup): string {
    switch (clash.severity) {
      case 'high':
        return `URGENT: Rename files to avoid case conflicts. Affects core functionality.`;
      case 'medium':
        return `MODERATE: Standardize case for asset files. May cause mobile loading issues.`;
      case 'low':
        return `LOW: Consider renaming for consistency. Minor mobile impact.`;
    }
  }

  private async generateRunCard(clashes: ClashGroup[]): Promise<void> {
    const runCard = `# Path Fix Run Card

## Case Clash Resolution Plan

**Generated**: ${new Date().toISOString()}
**Priority**: ${clashes.some(c => c.severity === 'high') ? 'HIGH' : 'MEDIUM'}

### Issues Found

${clashes.map(clash => `
**${clash.severity.toUpperCase()}**: \`${clash.normalizedPath}\`
- Files: ${clash.files.map(f => `\`${f}\``).join(', ')}
- Action: ${this.getRecommendation(clash)}
`).join('\n')}

### Recommended Actions

1. **Immediate**: Fix high-severity clashes
2. **Short-term**: Standardize medium-severity paths
3. **Long-term**: Implement naming convention enforcement

### Implementation Steps

\`\`\`bash
# 1. Backup current state
git add -A && git commit -m "Backup before case-clash fixes"

# 2. Rename conflicting files (example)
# git mv src/Components/Header.tsx src/components/header.tsx

# 3. Update import statements
# Use import rewriter or find/replace in IDE

# 4. Test on mobile device
# curl -I http://localhost:5000/preview/preview_probe.html
\`\`\`

### Mobile Testing Checklist

- [ ] Samsung S23 Preview loads correctly
- [ ] All assets load without 404s
- [ ] No console errors related to missing files
- [ ] Touch navigation works properly
`;

    const runCardPath = 'SystemDev/backlog/next_up/path_fix_run_card.md';
    await fs.promises.mkdir(path.dirname(runCardPath), { recursive: true });
    await fs.promises.writeFile(runCardPath, runCard);
    
    console.log(`📝 Run card generated: ${runCardPath}`);
  }
}

// Main execution
async function main() {
  const auditor = new CaseClashAuditor();
  
  console.log('🔧 Case-Clash Audit Tool');
  console.log('========================');
  
  const clashes = await auditor.auditDirectory('.');
  await auditor.generateReport(clashes);
  
  if (clashes.length === 0) {
    console.log('✅ No case clashes detected - mobile preview ready!');
  } else {
    console.log(`⚠️ Found ${clashes.length} case clashes - see report for details`);
  }
}

if (import.meta.url.endsWith(process.argv[1])) {
  main().catch(console.error);
}

export { CaseClashAuditor };