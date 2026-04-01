import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";
import { fileLifecycleManager } from "../../system/ops/file-lifecycle-manager.js";

const MANIFEST: TAgentManifest = {
  id: "librarian", role: "librarian",
  name: "Librarian",
  description: "Indexes, curates, optimizes, and evolves documentation ecosystem",
  capabilities: ["index","inspect","compose","curate","optimize","evolve"], 
  version: "0.1.0", 
  runner: "in-process", 
  enabled: true
};

export const LibrarianAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready for indexing, curation, and optimization" }; },
  async run(input: TAgentInput) {
    const action = input.ask?.payload?.action || 'index';
    
    if (action === 'curate') {
      return await this.curateExistingFiles(input);
    } else if (action === 'optimize') {
      return await this.optimizeFileSystem(input);
    } else {
      return await this.indexAndEvolve(input);
    }
  },
  
  async indexAndEvolve(input: TAgentInput) {
    // Enhanced indexing with read-analyze-evolve pattern
    const docsRoot = path.resolve("docs");
    const toc: Record<string,string[]> = {};
    let filesOptimized = 0;
    
    if (fs.existsSync(docsRoot)) {
      const dirs = fs.readdirSync(docsRoot);
      for (const d of dirs) {
        const p = path.join(docsRoot, d);
        if (fs.statSync(p).isDirectory()) {
          const mdFiles = fs.readdirSync(p).filter(f => f.endsWith(".md"));
          toc[d] = mdFiles;
          
          // Optimize each markdown file as we index
          for (const mdFile of mdFiles) {
            const filePath = path.join(p, mdFile);
            const result = await fileLifecycleManager.optimizeFileContent(filePath);
            if (result) filesOptimized++;
          }
        }
      }
    }
    
    // Infrastructure-First: read-analyze-evolve for index file
    const outDir = path.resolve("docs");
    fs.mkdirSync(outDir, { recursive: true });
    const out = path.join(outDir, "index.json");
    
    const newContent = JSON.stringify({ 
      toc, 
      t: input.t, 
      utc: input.utc,
      filesOptimized,
      lastCuration: new Date().toISOString()
    }, null, 2);
    
    // Check if content changed before writing
    let contentChanged = true;
    if (fs.existsSync(out)) {
      const existing = fs.readFileSync(out, 'utf8');
      contentChanged = existing !== newContent;
    }
    
    if (contentChanged) {
      fs.writeFileSync(out, newContent);
    }
    
    return { 
      ok: true, 
      effects: { 
        artifactPath: out, 
        stateDelta: { 
          docsIndexed: Object.keys(toc).length,
          filesOptimized,
          contentChanged
        } 
      } 
    };
  },
  
  async curateExistingFiles(input: TAgentInput) {
    // Analyze and curate existing files across the ecosystem
    const health = await fileLifecycleManager.analyzeFileHealth();
    const results = await fileLifecycleManager.applyRetentionPolicies();
    
    const report = {
      analysis: health,
      optimizations: results,
      recommendations: this.generateRecommendations(health)
    };
    
    const reportPath = path.resolve("docs/reports/file-curation-report.md");
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
    
    const reportContent = this.formatCurationReport(report);
    fs.writeFileSync(reportPath, reportContent);
    
    return {
      ok: true,
      effects: {
        artifactPath: reportPath,
        stateDelta: {
          filesAnalyzed: health.totalFiles,
          timestampArtifacts: health.timestampArtifacts,
          filesOptimized: results.length,
          totalSpaceSaved: results.reduce((sum, r) => sum + (r.originalSize - r.optimizedSize), 0)
        }
      }
    };
  },
  
  async optimizeFileSystem(input: TAgentInput) {
    // Focus on optimizing large or problematic files
    const health = await fileLifecycleManager.analyzeFileHealth();
    let optimized = 0;
    
    for (const file of health.oversizedFiles.slice(0, 10)) {
      const result = await fileLifecycleManager.optimizeFileContent(file.path);
      if (result) optimized++;
    }
    
    return {
      ok: true,
      effects: {
        artifactPath: "docs/reports/optimization-report.json",
        stateDelta: { filesOptimized: optimized }
      }
    };
  },
  
  generateRecommendations(health: any) {
    const recs = [];
    if (health.timestampArtifacts > 1000) {
      recs.push("URGENT: Clean up timestamp artifacts");
    }
    if (health.oversizedFiles.length > 10) {
      recs.push("Consider file compression/archival for large files");
    }
    if (health.duplicateContent.length > 5) {
      recs.push("Merge duplicate content files");
    }
    return recs;
  },
  
  formatCurationReport(report: any): string {
    return `# File Curation Report\n\nGenerated: ${new Date().toISOString()}\n\n## Health Analysis\n\n- Total files: ${report.analysis.totalFiles}\n- Timestamp artifacts: ${report.analysis.timestampArtifacts}\n- Oversized files: ${report.analysis.oversizedFiles.length}\n- Duplicate content groups: ${report.analysis.duplicateContent.length}\n\n## Optimizations Applied\n\n${report.optimizations.map((opt: any) => `- ${opt.action}: ${opt.path} (${opt.originalSize} → ${opt.optimizedSize} bytes)`).join('\n')}\n\n## Recommendations\n\n${report.recommendations.map((rec: string) => `- ${rec}`).join('\n')}\n`;
  }
};

export default LibrarianAgent;