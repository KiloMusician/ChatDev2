/**
 * Repository Philosopher's Stone - Self-Updating Codebase Map
 * 
 * "The philosopher's stone was the key to understanding the true nature
 * of all matter and energy in the universe." - Medieval Alchemists
 * 
 * This creates a living, breathing map of our entire codebase that
 * automatically updates when files change, revealing patterns,
 * connections, and the hidden architecture of our ecosystem.
 */

import { readdir, stat, readFile, watch } from 'fs/promises';
import { writeFileSync, existsSync } from 'fs';
import { join, relative, extname, dirname, basename } from 'path';
import { createHash } from 'crypto';

interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size: number;
  lastModified: number;
  hash?: string;
  extension?: string;
  lines?: number;
  imports?: string[];
  exports?: string[];
  dependencies?: string[];
  tags?: string[];
  purpose?: string;
  connections?: string[];
}

interface RepositorySnapshot {
  timestamp: number;
  totalFiles: number;
  totalDirectories: number;
  totalLinesOfCode: number;
  filesByType: Record<string, number>;
  keyDirectories: string[];
  architecturalLayers: Record<string, string[]>;
  dependencyGraph: Record<string, string[]>;
  hotspots: FileNode[];
  recentChanges: FileNode[];
  tree: FileNode;
  insights: string[];
}

export class RepositoryPhilosophersStone {
  private rootPath: string;
  private snapshotPath: string;
  private currentSnapshot: RepositorySnapshot | null = null;
  private watchHandlers: Map<string, any> = new Map();
  private isWatching = false;

  constructor(rootPath = '.', snapshotPath = 'tools/repository-snapshot.json') {
    this.rootPath = rootPath;
    this.snapshotPath = snapshotPath;
  }

  /**
   * Create a comprehensive snapshot of the entire repository
   */
  async createSnapshot(): Promise<RepositorySnapshot> {
    console.log('🔮 Repository Philosopher\'s Stone - Beginning Deep Analysis...\n');
    
    const startTime = Date.now();
    const tree = await this.scanDirectory(this.rootPath);
    
    // Flatten tree for analysis
    const allFiles = this.flattenTree(tree);
    const files = allFiles.filter(f => f.type === 'file');
    const directories = allFiles.filter(f => f.type === 'directory');

    // Analyze file types
    const filesByType: Record<string, number> = {};
    let totalLinesOfCode = 0;
    
    for (const file of files) {
      const ext = file.extension || 'no-extension';
      filesByType[ext] = (filesByType[ext] || 0) + 1;
      totalLinesOfCode += file.lines || 0;
    }

    // Identify key architectural layers
    const architecturalLayers = this.identifyArchitecturalLayers(directories);
    
    // Build dependency graph
    const dependencyGraph = await this.buildDependencyGraph(files);
    
    // Find hotspots (large, frequently changing, or highly connected files)
    const hotspots = this.identifyHotspots(files, dependencyGraph);
    
    // Recent changes (last 24 hours)
    const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
    const recentChanges = files
      .filter(f => f.lastModified > oneDayAgo)
      .sort((a, b) => b.lastModified - a.lastModified)
      .slice(0, 20);

    // Generate insights
    const insights = this.generateInsights(files, directories, dependencyGraph, architecturalLayers);

    this.currentSnapshot = {
      timestamp: Date.now(),
      totalFiles: files.length,
      totalDirectories: directories.length,
      totalLinesOfCode,
      filesByType,
      keyDirectories: Object.keys(architecturalLayers),
      architecturalLayers,
      dependencyGraph,
      hotspots: hotspots.slice(0, 10),
      recentChanges,
      tree,
      insights
    };

    // Save snapshot
    this.saveSnapshot();
    
    const elapsed = Date.now() - startTime;
    console.log(`🎯 Repository Analysis Complete in ${elapsed}ms`);
    console.log(`📊 Discovered: ${files.length} files, ${directories.length} directories`);
    console.log(`📝 Total Lines: ${totalLinesOfCode.toLocaleString()}`);
    console.log(`🔥 Hotspots: ${hotspots.length}`);
    console.log(`⚡ Recent Changes: ${recentChanges.length}`);
    
    return this.currentSnapshot;
  }

  private async scanDirectory(dirPath: string, depth = 0): Promise<FileNode> {
    const stats = await stat(dirPath);
    const name = basename(dirPath);
    
    const node: FileNode = {
      path: dirPath,
      name,
      type: 'directory',
      size: 0,
      lastModified: stats.mtime.getTime()
    };

    if (this.shouldSkipDirectory(name) || depth > 10) {
      return node;
    }

    try {
      const entries = await readdir(dirPath);
      const children: FileNode[] = [];

      for (const entry of entries) {
        const fullPath = join(dirPath, entry);
        const childStats = await stat(fullPath);

        if (childStats.isDirectory()) {
          const childNode = await this.scanDirectory(fullPath, depth + 1);
          children.push(childNode);
        } else {
          const fileNode = await this.analyzeFile(fullPath, childStats);
          children.push(fileNode);
        }
      }

      // @ts-ignore - Add children to node
      node.children = children;
      node.size = children.reduce((sum, child) => sum + child.size, 0);
    } catch (error) {
      console.warn(`Could not read directory: ${dirPath}`, error);
    }

    return node;
  }

  private async analyzeFile(filePath: string, stats: any): Promise<FileNode> {
    const name = basename(filePath);
    const extension = extname(filePath).toLowerCase().slice(1);
    
    const node: FileNode = {
      path: filePath,
      name,
      type: 'file',
      size: stats.size,
      lastModified: stats.mtime.getTime(),
      extension: extension || undefined
    };

    // Skip binary files and very large files
    if (this.isBinaryFile(filePath) || stats.size > 1024 * 1024) {
      return node;
    }

    try {
      const content = await readFile(filePath, 'utf8');
      node.hash = createHash('md5').update(content).digest('hex');
      node.lines = content.split('\n').length;
      
      // Extract imports/exports for supported file types
      if (['ts', 'js', 'tsx', 'jsx', 'py', 'go', 'rs'].includes(extension)) {
        const analysis = this.analyzeCodeFile(content, extension);
        node.imports = analysis.imports;
        node.exports = analysis.exports;
        node.purpose = analysis.purpose;
        node.tags = analysis.tags;
      }
    } catch (error) {
      // File couldn't be read as text, that's okay
    }

    return node;
  }

  private analyzeCodeFile(content: string, extension: string) {
    const imports: string[] = [];
    const exports: string[] = [];
    const tags: string[] = [];
    let purpose = '';

    const lines = content.split('\n');
    
    // Extract imports based on language
    if (['ts', 'js', 'tsx', 'jsx'].includes(extension)) {
      for (const line of lines) {
        const importMatch = line.match(/import.*from\s+['"`]([^'"`]+)['"`]/);
        if (importMatch) imports.push(importMatch[1]);
        
        const exportMatch = line.match(/export\s+(class|function|const|let|var)\s+(\w+)/);
        if (exportMatch) exports.push(exportMatch[2]);
      }
    }
    
    if (extension === 'py') {
      for (const line of lines) {
        const importMatch = line.match(/from\s+(\S+)\s+import|import\s+(\S+)/);
        if (importMatch) imports.push(importMatch[1] || importMatch[2]);
      }
    }

    // Infer purpose from filename and content
    const filename = lines[0] || '';
    if (content.includes('interface') || content.includes('type ')) tags.push('types');
    if (content.includes('class ') || content.includes('extends ')) tags.push('class');
    if (content.includes('function ') || content.includes('=> ')) tags.push('functions');
    if (content.includes('test') || content.includes('spec')) tags.push('testing');
    if (content.includes('config') || content.includes('settings')) tags.push('configuration');
    if (content.includes('api') || content.includes('endpoint')) tags.push('api');
    if (content.includes('component') || content.includes('jsx')) tags.push('component');

    return { imports, exports, purpose, tags };
  }

  private shouldSkipDirectory(name: string): boolean {
    const skipDirs = [
      'node_modules', '.git', '.next', 'dist', 'build', 
      '__pycache__', '.pytest_cache', 'coverage', '.coverage',
      '.vscode', '.idea', 'target', 'vendor'
    ];
    return skipDirs.includes(name) || name.startsWith('.');
  }

  private isBinaryFile(filePath: string): boolean {
    const binaryExts = [
      '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
      '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll',
      '.so', '.dylib', '.bin', '.dat'
    ];
    return binaryExts.some(ext => filePath.toLowerCase().endsWith(ext));
  }

  private flattenTree(node: FileNode): FileNode[] {
    const result = [node];
    // @ts-ignore
    if (node.children) {
      // @ts-ignore
      for (const child of node.children) {
        result.push(...this.flattenTree(child));
      }
    }
    return result;
  }

  private identifyArchitecturalLayers(directories: FileNode[]): Record<string, string[]> {
    const layers: Record<string, string[]> = {};
    
    for (const dir of directories) {
      const name = dir.name.toLowerCase();
      const path = dir.path;
      
      if (name.includes('src') || name.includes('source')) {
        layers['Source Code'] = layers['Source Code'] || [];
        layers['Source Code'].push(path);
      }
      if (name.includes('test') || name.includes('spec')) {
        layers['Testing'] = layers['Testing'] || [];
        layers['Testing'].push(path);
      }
      if (name.includes('config') || name.includes('settings')) {
        layers['Configuration'] = layers['Configuration'] || [];
        layers['Configuration'].push(path);
      }
      if (name.includes('api') || name.includes('server')) {
        layers['Backend/API'] = layers['Backend/API'] || [];
        layers['Backend/API'].push(path);
      }
      if (name.includes('client') || name.includes('frontend') || name.includes('ui')) {
        layers['Frontend/UI'] = layers['Frontend/UI'] || [];
        layers['Frontend/UI'].push(path);
      }
      if (name.includes('shared') || name.includes('common') || name.includes('lib')) {
        layers['Shared/Library'] = layers['Shared/Library'] || [];
        layers['Shared/Library'].push(path);
      }
      if (name.includes('agent') || name.includes('ai') || name.includes('bot')) {
        layers['AI/Agents'] = layers['AI/Agents'] || [];
        layers['AI/Agents'].push(path);
      }
    }
    
    return layers;
  }

  private async buildDependencyGraph(files: FileNode[]): Promise<Record<string, string[]>> {
    const graph: Record<string, string[]> = {};
    
    for (const file of files) {
      if (file.imports && file.imports.length > 0) {
        graph[file.path] = file.imports;
      }
    }
    
    return graph;
  }

  private identifyHotspots(files: FileNode[], dependencyGraph: Record<string, string[]>): FileNode[] {
    // Score files based on size, complexity, and connections
    const scored = files.map(file => {
      let score = 0;
      
      // Size factor (larger files are more complex)
      score += Math.log(file.size || 1) * 0.1;
      
      // Line count factor
      score += Math.log(file.lines || 1) * 0.2;
      
      // Import/export factor (highly connected)
      score += (file.imports?.length || 0) * 0.5;
      score += (file.exports?.length || 0) * 0.3;
      
      // Dependency factor (how many files depend on this)
      const dependents = Object.values(dependencyGraph).filter(deps => 
        deps.some(dep => dep.includes(file.name))
      ).length;
      score += dependents * 2;
      
      // Recent modification factor
      const daysSinceModified = (Date.now() - file.lastModified) / (24 * 60 * 60 * 1000);
      if (daysSinceModified < 7) score += (7 - daysSinceModified) * 0.1;
      
      return { ...file, hotspotScore: score };
    });
    
    return scored
      .filter(f => f.hotspotScore > 1)
      .sort((a, b) => (b.hotspotScore || 0) - (a.hotspotScore || 0));
  }

  private generateInsights(
    files: FileNode[], 
    directories: FileNode[], 
    dependencyGraph: Record<string, string[]>,
    architecturalLayers: Record<string, string[]>
  ): string[] {
    const insights: string[] = [];
    
    // File type distribution
    const jstsFiles = files.filter(f => ['js', 'ts', 'jsx', 'tsx'].includes(f.extension || ''));
    const pyFiles = files.filter(f => f.extension === 'py');
    const configFiles = files.filter(f => ['json', 'yml', 'yaml', 'toml'].includes(f.extension || ''));
    
    insights.push(`🔍 Language Distribution: ${jstsFiles.length} JS/TS files, ${pyFiles.length} Python files`);
    insights.push(`⚙️ Configuration: ${configFiles.length} config files detected`);
    
    // Architecture insights
    const layerCount = Object.keys(architecturalLayers).length;
    insights.push(`🏗️ Architecture: ${layerCount} distinct layers identified`);
    
    // Complexity insights
    const totalDependencies = Object.keys(dependencyGraph).length;
    insights.push(`🕸️ Dependency Complexity: ${totalDependencies} files with imports tracked`);
    
    // Size insights
    const largeFiles = files.filter(f => (f.lines || 0) > 500);
    if (largeFiles.length > 0) {
      insights.push(`📏 Code Complexity: ${largeFiles.length} files over 500 lines`);
    }
    
    // Recent activity
    const recentFiles = files.filter(f => f.lastModified > Date.now() - (7 * 24 * 60 * 60 * 1000));
    insights.push(`⚡ Recent Activity: ${recentFiles.length} files modified in last 7 days`);
    
    return insights;
  }

  private saveSnapshot() {
    if (!this.currentSnapshot) return;
    
    try {
      writeFileSync(this.snapshotPath, JSON.stringify(this.currentSnapshot, null, 2));
      console.log(`💾 Snapshot saved to: ${this.snapshotPath}`);
    } catch (error) {
      console.error('Failed to save snapshot:', error);
    }
  }

  /**
   * Start watching for file changes and auto-update snapshot
   */
  async startAutoUpdate(intervalMs = 60000): Promise<void> {
    if (this.isWatching) return;
    
    console.log('👁️ Starting auto-update monitoring...');
    this.isWatching = true;
    
    // Periodic full refresh
    setInterval(async () => {
      if (this.isWatching) {
        console.log('🔄 Auto-refreshing repository snapshot...');
        await this.createSnapshot();
      }
    }, intervalMs);
  }

  stopAutoUpdate(): void {
    console.log('⏹️ Stopping auto-update monitoring...');
    this.isWatching = false;
    
    for (const [path, watcher] of this.watchHandlers) {
      watcher.close();
    }
    this.watchHandlers.clear();
  }

  /**
   * Get the current snapshot or create one if none exists
   */
  async getSnapshot(): Promise<RepositorySnapshot> {
    if (!this.currentSnapshot) {
      await this.createSnapshot();
    }
    return this.currentSnapshot!;
  }

  /**
   * Print a beautiful tree visualization
   */
  printTree(node?: FileNode, prefix = '', depth = 0): string {
    if (!node) node = this.currentSnapshot?.tree;
    if (!node || depth > 4) return '';
    
    let output = '';
    const isLast = true; // Simplified for now
    const connector = isLast ? '└── ' : '├── ';
    
    // Color coding
    let icon = '';
    if (node.type === 'directory') {
      icon = '📁';
    } else {
      switch (node.extension) {
        case 'ts': case 'tsx': icon = '🔷'; break;
        case 'js': case 'jsx': icon = '📜'; break;
        case 'py': icon = '🐍'; break;
        case 'json': icon = '📋'; break;
        case 'md': icon = '📝'; break;
        default: icon = '📄';
      }
    }
    
    output += `${prefix}${connector}${icon} ${node.name}`;
    if (node.type === 'file' && node.lines) {
      output += ` (${node.lines} lines)`;
    }
    output += '\n';
    
    // @ts-ignore
    if (node.children && depth < 3) {
      // @ts-ignore
      for (let i = 0; i < node.children.length; i++) {
        // @ts-ignore
        const child = node.children[i];
        const isChildLast = i === node.children.length - 1;
        const newPrefix = prefix + (isLast ? '    ' : '│   ');
        output += this.printTree(child, newPrefix, depth + 1);
      }
    }
    
    return output;
  }
}

// CLI interface when run directly  
if (import.meta.url === `file://${process.argv[1]}`) {
  const stone = new RepositoryPhilosophersStone();
  
  (async () => {
    const snapshot = await stone.createSnapshot();
    
    console.log('\n🎯 REPOSITORY INSIGHTS:');
    for (const insight of snapshot.insights) {
      console.log(`   ${insight}`);
    }
    
    console.log('\n📊 ARCHITECTURAL LAYERS:');
    for (const [layer, paths] of Object.entries(snapshot.architecturalLayers)) {
      console.log(`   ${layer}: ${paths.length} directories`);
    }
    
    console.log('\n🔥 TOP HOTSPOTS:');
    snapshot.hotspots.slice(0, 5).forEach((file, i) => {
      console.log(`   ${i + 1}. ${file.path} (${file.lines} lines, score: ${file.hotspotScore?.toFixed(1)})`);
    });
    
    if (process.argv.includes('--watch')) {
      await stone.startAutoUpdate();
      console.log('\n👁️ Watching for changes... Press Ctrl+C to stop.');
    }
  })().catch(console.error);
}

export default RepositoryPhilosophersStone;