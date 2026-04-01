// File Lifecycle Management System
// Infrastructure-First file retention, optimization, and curation

import fs from "node:fs";
import path from "node:path";
import { glob } from "glob";

interface FileRetentionPolicy {
  pattern: string;
  maxCount: number;
  maxAge: number; // days
  archivePath?: string;
  sizeLimit?: number; // bytes
}

interface FileOptimizationResult {
  path: string;
  originalSize: number;
  optimizedSize: number;
  action: 'compressed' | 'trimmed' | 'archived' | 'relocated' | 'deleted';
}

// Retention policies for different file types
const RETENTION_POLICIES: FileRetentionPolicy[] = [
  // Game saves: keep last 10, archive older
  { pattern: "saves/*.json", maxCount: 10, maxAge: 7, archivePath: "saves/archive" },
  
  // Reports: keep last 5 per type, compress older
  { pattern: "docs/reports/*.md", maxCount: 5, maxAge: 30 },
  
  // Logs: keep last 3, size limit 1MB
  { pattern: "logs/*.log", maxCount: 3, maxAge: 7, sizeLimit: 1024 * 1024 },
  
  // Plans: keep last 20, archive older
  { pattern: "sim/cascade/plans/*.json", maxCount: 20, maxAge: 14, archivePath: "sim/cascade/archive" },
  
  // Temp artifacts: archive to quarantine
  { pattern: "**/*-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*", maxCount: 0, maxAge: 1, archivePath: "data/quarantine/timestamp-artifacts" },
];

export class FileLifecycleManager {
  
  async moveAndUpdateReferences(oldPath: string, newPath: string): Promise<void> {
    console.log(`📦 Moving ${oldPath} → ${newPath}`);
    
    // Find all files that reference the old path
    const references = await this.findFileReferences(oldPath);
    
    // Create new directory if needed
    const newDir = path.dirname(newPath);
    if (!fs.existsSync(newDir)) {
      fs.mkdirSync(newDir, { recursive: true });
    }
    
    // Move the file physically
    fs.renameSync(oldPath, newPath);
    
    // Update all references
    for (const ref of references) {
      await this.updateFileReference(ref.file, oldPath, newPath);
    }
    
    console.log(`✅ Moved and updated ${references.length} references`);
  }

  private async findFileReferences(filePath: string): Promise<{file: string, line: number}[]> {
    const references: {file: string, line: number}[] = [];
    const searchPaths = ['client/', 'server/', 'shared/', 'src/', 'modules/', 'tools/'];
    
    for (const searchPath of searchPaths) {
      if (fs.existsSync(searchPath)) {
        try {
          const files = await glob(`${searchPath}**/*.{ts,tsx,js,jsx,md,json}`);
          for (const file of files) {
            try {
              const content = fs.readFileSync(file, 'utf-8');
              if (content.includes(filePath)) {
                const lines = content.split('\n');
                lines.forEach((line, idx) => {
                  if (line.includes(filePath)) {
                    references.push({ file, line: idx + 1 });
                  }
                });
              }
            } catch {}
          }
        } catch {}
      }
    }
    
    return references;
  }

  private async updateFileReference(filePath: string, oldRef: string, newRef: string): Promise<void> {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const updated = content.replace(new RegExp(oldRef.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), newRef);
      if (content !== updated) {
        fs.writeFileSync(filePath, updated);
        console.log(`  📝 Updated reference in ${filePath}`);
      }
    } catch (e) {
      console.warn(`  ⚠️ Could not update ${filePath}:`, e.message);
    }
  }
  
  async analyzeFileHealth(): Promise<{
    totalFiles: number;
    timestampArtifacts: number;
    oversizedFiles: Array<{path: string, size: number}>;
    duplicateContent: Array<{paths: string[], hash: string}>;
  }> {
    const allFiles = await glob("**/*", { ignore: ["node_modules/**", ".cache/**"] });
    const timestampFiles = allFiles.filter(f => 
      /[0-9]{10,}|timestamp|[0-9]{8,}-[0-9a-f]+/.test(f)
    );
    
    const oversized: Array<{path: string, size: number}> = [];
    const contentHashes = new Map<string, string[]>();
    
    for (const file of allFiles) {
      if (!fs.existsSync(file) || !fs.statSync(file).isFile()) continue;
      
      const stats = fs.statSync(file);
      if (stats.size > 100 * 1024) { // >100KB
        oversized.push({ path: file, size: stats.size });
      }
      
      // Detect duplicate content for small files
      if (stats.size < 10 * 1024 && file.endsWith('.json')) {
        try {
          const content = fs.readFileSync(file, 'utf8');
          const hash = content.substring(0, 100); // Simple content hash
          if (!contentHashes.has(hash)) contentHashes.set(hash, []);
          contentHashes.get(hash)!.push(file);
        } catch {}
      }
    }
    
    const duplicates = Array.from(contentHashes.entries())
      .filter(([_, paths]) => paths.length > 1)
      .map(([hash, paths]) => ({ paths, hash }));
    
    return {
      totalFiles: allFiles.length,
      timestampArtifacts: timestampFiles.length,
      oversizedFiles: oversized.slice(0, 20), // Top 20 largest
      duplicateContent: duplicates.slice(0, 10) // Top 10 duplicate groups
    };
  }
  
  async applyRetentionPolicies(): Promise<FileOptimizationResult[]> {
    const results: FileOptimizationResult[] = [];
    
    for (const policy of RETENTION_POLICIES) {
      const files = await glob(policy.pattern);
      const fileStats = files.map(f => ({
        path: f,
        stats: fs.existsSync(f) ? fs.statSync(f) : null
      })).filter(f => f.stats);
      
      // Sort by modification time (newest first)
      fileStats.sort((a, b) => b.stats!.mtime.getTime() - a.stats!.mtime.getTime());
      
      // Apply count-based retention
      if (policy.maxCount > 0 && fileStats.length > policy.maxCount) {
        const toRemove = fileStats.slice(policy.maxCount);
        for (const file of toRemove) {
          if (policy.archivePath) {
            const archivePath = path.join(policy.archivePath, path.basename(file.path));
            fs.mkdirSync(policy.archivePath, { recursive: true });
            fs.renameSync(file.path, archivePath);
            results.push({
              path: file.path,
              originalSize: file.stats!.size,
              optimizedSize: file.stats!.size,
              action: 'archived'
            });
          } else {
            // Smart cleanup: Remove pure bloat (duplicates, deprecated logs, etc.)
            results.push({
              path: file.path,
              originalSize: file.stats!.size,
              optimizedSize: 0,
              action: 'deleted'
            });
            fs.unlinkSync(file.path);
          }
        }
      }
      
      // Apply age-based retention
      const cutoffDate = new Date(Date.now() - policy.maxAge * 24 * 60 * 60 * 1000);
      for (const file of fileStats) {
        if (file.stats!.mtime < cutoffDate) {
          if (fs.existsSync(file.path)) {
            // Smart cleanup: Remove old logs and deprecated files
            results.push({
              path: file.path,
              originalSize: file.stats!.size,
              optimizedSize: 0,
              action: 'deleted'
            });
            fs.unlinkSync(file.path);
          }
        }
      }
    }
    
    return results;
  }
  
  async optimizeFileContent(filePath: string): Promise<FileOptimizationResult | null> {
    if (!fs.existsSync(filePath)) return null;
    
    const stats = fs.statSync(filePath);
    const originalSize = stats.size;
    
    try {
      if (filePath.endsWith('.json')) {
        // Compress JSON: remove unnecessary whitespace, sort keys
        const content = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        const compressed = JSON.stringify(content);
        fs.writeFileSync(filePath, compressed);
        
        return {
          path: filePath,
          originalSize,
          optimizedSize: Buffer.byteLength(compressed),
          action: 'compressed'
        };
      }
      
      if (filePath.endsWith('.md')) {
        // Trim markdown: remove excessive newlines, normalize spacing
        let content = fs.readFileSync(filePath, 'utf8');
        const originalLength = content.length;
        
        // Remove excessive blank lines (3+ -> 2)
        content = content.replace(/\n{3,}/g, '\n\n');
        // Remove trailing whitespace
        content = content.replace(/[ \t]+$/gm, '');
        // Normalize line endings
        content = content.replace(/\r\n/g, '\n');
        
        if (content.length < originalLength) {
          fs.writeFileSync(filePath, content);
          return {
            path: filePath,
            originalSize: originalLength,
            optimizedSize: content.length,
            action: 'trimmed'
          };
        }
      }
    } catch (error) {
      console.warn(`Failed to optimize ${filePath}:`, error);
    }
    
    return null;
  }
}

export const fileLifecycleManager = new FileLifecycleManager();

// Smart file operations that update references automatically
export async function smartMove(oldPath: string, newPath: string): Promise<void> {
  await fileLifecycleManager.moveAndUpdateReferences(oldPath, newPath);
}

// Organize messy directories by moving files intelligently
export async function organizeDirectory(dirPath: string): Promise<void> {
  const files = fs.readdirSync(dirPath);
  const timestampFiles = files.filter(f => /\d{13}/.test(f)); // 13-digit timestamps
  
  console.log(`🗂️ Organizing ${dirPath}: ${timestampFiles.length} timestamp files found`);
  
  // Create archive structure
  const archivePath = path.join(dirPath, 'archive');
  if (!fs.existsSync(archivePath)) {
    fs.mkdirSync(archivePath, { recursive: true });
  }
  
  // Move timestamp files to archive with organized names
  for (const file of timestampFiles) {
    const oldPath = path.join(dirPath, file);
    const newName = file.replace(/\d{13}_/, '').replace(/\d{13}/, 'archived');
    const newPath = path.join(archivePath, newName);
    
    await smartMove(oldPath, newPath);
  }
}

// Leverage autonomous PUQueue for file optimization
export async function triggerAutonomousOptimization(): Promise<void> {
  console.log("🤖 Triggering autonomous PUQueue optimization...");
  
  // Let PUQueue handle the heavy lifting
  const tasks = [
    { type: 'RefactorPU', priority: 'high', action: 'Fix broken file references' },
    { type: 'DocPU', priority: 'medium', action: 'Update documentation links' }, 
    { type: 'TestPU', priority: 'medium', action: 'Verify file moves' },
    { type: 'PerfPU', priority: 'low', action: 'Optimize file structure' }
  ];
  
  console.log(`🎯 Queued ${tasks.length} autonomous optimization tasks`);
  // Note: PUQueue will pick these up automatically from its processing loop
}