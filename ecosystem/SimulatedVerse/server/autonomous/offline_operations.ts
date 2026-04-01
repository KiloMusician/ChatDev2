// server/autonomous/offline_operations.ts
// Intelligent Offline Operations - Autonomous functioning without LLM services
// Implements self-healing, organizing, consolidating, annealing systems

import { promises as fs } from 'node:fs';
import path from 'node:path';
import { setOfflineMode, isQuotaExceeded } from '../../packages/llm/budget-manager.js';
import { ChatDevIntegration } from './chatdev-integration.js';

interface OfflineTask {
  id: string;
  type: 'self_healing' | 'organizing' | 'consolidating' | 'annealing' | 'cultivation';
  priority: number;
  cost: 'free' | 'low' | 'medium' | 'high';
  description: string;
  action: () => Promise<any>;
  requires_llm: boolean;
  last_run?: number;
  frequency_ms: number;
}

interface SystemHealth {
  timestamp: number;
  file_count: number;
  duplicate_count: number;
  error_count: number;
  repo_size_mb: number;
  receipt_count: number;
  organization_score: number;
}

class OfflineOperationsManager {
  private readonly tasks: Map<string, OfflineTask> = new Map();
  private running = false;
  private councilBus: any = null;
  private lastHealthCheck = 0;
  private systemHealth: SystemHealth | null = null;
  private readonly chatdev: ChatDevIntegration;

  constructor() {
    this.chatdev = new ChatDevIntegration();
    this.registerOfflineTasks();
    console.log('[OfflineOps] ✅ Autonomous improvement system initialized');
  }

  public async initialize(): Promise<void> {
    try {
      await this.detectOfflineMode();
      await this.initializeChatDev();
    } catch (error) {
      console.warn('[OfflineOps] Initialization failed:', error);
    }
  }
  
  private async initializeChatDev() {
    console.log('[OfflineOps] 🤖 Initializing ChatDev autonomous development...');
    await this.chatdev.initialize();
    console.log('[OfflineOps] ✅ ChatDev integration ready for autonomous operation');
  }
  
  public async triggerAutonomousDevelopment(idea: string) {
    console.log(`[OfflineOps] 🚀 Triggering autonomous development: ${idea}`);
    return await this.chatdev.createSoftwareProject(idea);
  }

  public setCouncilBus(bus: any): void {
    this.councilBus = bus;
  }

  public start(): void {
    if (this.running) return;
    
    this.running = true;
    console.log('[OfflineOps] ✅ Starting intelligent autonomous operations - replacing theater with real improvements');
    
    // Start the main loop
    this.mainLoop();
    
    // Start periodic health monitoring - intelligent analysis
    setInterval(() => this.performHealthCheck(), 30000); // Every 30 seconds
    
    // Immediate health check for baseline
    this.performHealthCheck();
  }

  public stop(): void {
    this.running = false;
    console.log('[OfflineOps] Stopping offline operations');
  }

  private async detectOfflineMode(): Promise<void> {
    // Check if we should enable offline mode
    const shouldGoOffline = isQuotaExceeded() || await this.isInternetDown();
    
    if (shouldGoOffline) {
      setOfflineMode(true);
      console.log('[OfflineOps] 🌐 Offline mode detected - enabling autonomous operations');
      this.start();
    }
  }

  private async isInternetDown(): Promise<boolean> {
    try {
      // Quick connectivity test
      const response = await fetch('https://api.github.com', { 
        signal: AbortSignal.timeout(3000) 
      });
      return !response.ok;
    } catch (error) {
      console.warn('[OfflineOps] Internet connectivity check failed:', error);
      return true;
    }
  }

  private registerOfflineTasks(): void {
    // File organization and cleanup tasks
    this.tasks.set('cleanup_receipts', {
      id: 'cleanup_receipts',
      type: 'organizing',
      priority: 3,
      cost: 'free',
      description: 'Archive old receipts and organize by date',
      requires_llm: false,
      frequency_ms: 300000, // 5 minutes
      action: () => this.cleanupReceipts()
    });

    this.tasks.set('consolidate_logs', {
      id: 'consolidate_logs',
      type: 'consolidating',
      priority: 4,
      cost: 'free',
      description: 'Consolidate and compress log files',
      requires_llm: false,
      frequency_ms: 600000, // 10 minutes
      action: () => this.consolidateLogs()
    });

    this.tasks.set('duplicate_detection', {
      id: 'duplicate_detection',
      type: 'annealing',
      priority: 5,
      cost: 'low',
      description: 'Detect and report duplicate files',
      requires_llm: false,
      frequency_ms: 1800000, // 30 minutes
      action: () => this.detectDuplicates()
    });

    this.tasks.set('index_rebuild', {
      id: 'index_rebuild',
      type: 'organizing',
      priority: 6,
      cost: 'low', 
      description: 'Rebuild file indices and reports',
      requires_llm: false,
      frequency_ms: 900000, // 15 minutes
      action: () => this.rebuildIndices()
    });

    this.tasks.set('self_healing_config', {
      id: 'self_healing_config',
      type: 'self_healing',
      priority: 2,
      cost: 'free',
      description: 'Fix corrupted config files and restore defaults',
      requires_llm: false,
      frequency_ms: 180000, // 3 minutes
      action: () => this.healConfigs()
    });

    this.tasks.set('system_cultivation', {
      id: 'system_cultivation',
      type: 'cultivation',
      priority: 7,
      cost: 'low',
      description: 'Systematically improve system organization',
      requires_llm: false,
      frequency_ms: 3600000, // 1 hour
      action: () => this.cultivateSystem()
    });

    this.tasks.set('free_task_harvesting', {
      id: 'free_task_harvesting',
      type: 'cultivation',
      priority: 1,
      cost: 'free',
      description: 'Identify and execute zero-cost improvement tasks',
      requires_llm: false,
      frequency_ms: 120000, // 2 minutes
      action: () => this.harvestFreeTasks()
    });

    console.log(`[OfflineOps] Registered ${this.tasks.size} offline tasks`);
  }

  private async mainLoop(): Promise<void> {
    while (this.running) {
      try {
        // Get tasks that should run now
        const readyTasks = Array.from(this.tasks.values())
          .filter(task => this.shouldRunTask(task))
          .sort((a, b) => a.priority - b.priority); // Higher priority = lower number

        if (readyTasks.length > 0) {
          console.log(`[OfflineOps] Executing ${readyTasks.length} offline tasks`);
          
          for (const task of readyTasks.slice(0, 3)) { // Max 3 concurrent tasks
            await this.executeTask(task);
          }
        }

        // Sleep before next iteration
        await this.sleep(5000); // 5 second intervals
        
      } catch (error) {
        console.error('[OfflineOps] Main loop error:', error);
        await this.sleep(10000); // Longer sleep on error
      }
    }
  }

  private shouldRunTask(task: OfflineTask): boolean {
    const now = Date.now();
    const lastRun = task.last_run || 0;
    const timeSinceLastRun = now - lastRun;
    
    return timeSinceLastRun >= task.frequency_ms;
  }

  private async executeTask(task: OfflineTask): Promise<void> {
    try {
      console.log(`[OfflineOps] Executing: ${task.description}`);
      const result = await task.action();
      
      task.last_run = Date.now();
      
      // Emit to Council Bus if available
      if (this.councilBus) {
        this.councilBus.publish('offline.task.complete', {
          task_id: task.id,
          type: task.type,
          result,
          timestamp: Date.now()
        });
      }

      // Save receipt
      await this.saveTaskReceipt(task, result);
      
    } catch (error) {
      console.error(`[OfflineOps] Task ${task.id} failed:`, error);
    }
  }

  private async saveTaskReceipt(task: OfflineTask, result: any): Promise<void> {
    try {
      await fs.mkdir('SystemDev/receipts/offline', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/offline/${task.id}_${Date.now()}.json`,
        JSON.stringify({
          task_id: task.id,
          type: task.type,
          description: task.description,
          result,
          timestamp: Date.now(),
          cost: task.cost,
          offline_mode: true
        }, null, 2)
      );
    } catch (error) {
      console.warn(`[OfflineOps] Could not save receipt for ${task.id}:`, error);
    }
  }

  // Task implementations

  private async cleanupReceipts(): Promise<any> {
    const receiptsDir = 'SystemDev/receipts';
    const files = await fs.readdir(receiptsDir, { withFileTypes: true });
    
    let cleaned = 0;
    let archived = 0;
    
    for (const file of files) {
      if (file.isFile() && file.name.endsWith('.json')) {
        const filePath = path.join(receiptsDir, file.name);
        const stats = await fs.stat(filePath);
        const age = Date.now() - stats.mtime.getTime();
        
        // Archive receipts older than 24 hours
        if (age > 24 * 60 * 60 * 1000) {
          const archiveDir = `${receiptsDir}/archive/${new Date(stats.mtime).toISOString().split('T')[0]}`;
          await fs.mkdir(archiveDir, { recursive: true });
          await fs.rename(filePath, path.join(archiveDir, file.name));
          archived++;
        }
      }
    }

    return { cleaned, archived, timestamp: Date.now() };
  }

  private async consolidateLogs(): Promise<any> {
    const logPaths = ['logger', 'logs', '.logs'];
    let consolidated = 0;
    
    for (const logPath of logPaths) {
      try {
        const exists = await fs.access(logPath).then(() => true).catch(() => false);
        if (!exists) continue;
        
        const files = await fs.readdir(logPath);
        
        // Consolidate logs by date
        for (const file of files) {
          if (file.endsWith('.log') || file.endsWith('.ndjson')) {
            const filePath = path.join(logPath, file);
            const stats = await fs.stat(filePath);
            
            // Compress logs older than 1 hour
            if (Date.now() - stats.mtime.getTime() > 60 * 60 * 1000) {
              // Simple consolidation - move to dated subdirectory
              const dateDir = path.join(logPath, 'archive', new Date(stats.mtime).toISOString().split('T')[0] || 'unknown');
              await fs.mkdir(dateDir, { recursive: true });
              await fs.rename(filePath, path.join(dateDir, file));
              consolidated++;
            }
          }
        }
      } catch (error) {
        console.warn(`[OfflineOps] Could not consolidate logs in ${logPath}:`, error);
      }
    }

    return { consolidated, timestamp: Date.now() };
  }

  private async detectDuplicates(): Promise<any> {
    // Simple duplicate detection based on file size and name patterns
    const fileMap = new Map<string, string[]>();
    let duplicates = 0;
    let statErrors = 0;
    
    try {
      const files = await this.scanDirectoryRecursive('.');
      
      for (const file of files) {
        try {
          const stats = await fs.stat(file);
          const key = `${stats.size}_${path.basename(file)}`;
          
          if (!fileMap.has(key)) {
            fileMap.set(key, []);
          }
          fileMap.get(key)!.push(file);
        } catch (error) {
          statErrors += 1;
          if (statErrors <= 3) {
            console.warn('[OfflineOps] Skipped file during duplicate scan due to stat error:', file, error);
          }
        }
      }

      // Count duplicates
      for (const paths of fileMap.values()) {
        if (paths.length > 1) {
          duplicates += paths.length - 1;
        }
      }

    } catch (error) {
      console.warn('[OfflineOps] Duplicate detection failed:', error);
    }

    if (statErrors > 0) {
      console.warn(`[OfflineOps] Skipped ${statErrors} files during duplicate scan due to stat errors`);
    }

    return { duplicates_found: duplicates, timestamp: Date.now() };
  }

  private async rebuildIndices(): Promise<any> {
    try {
      // Simple index rebuild - create file listings
      const reports = {
        files_by_type: new Map<string, number>(),
        files_by_directory: new Map<string, number>(),
        total_files: 0
      };

      const files = await this.scanDirectoryRecursive('.');
      
      for (const file of files) {
        const ext = path.extname(file);
        const dir = path.dirname(file).split('/')[0];
        
        reports.files_by_type.set(ext || 'no-ext', (reports.files_by_type.get(ext || 'no-ext') || 0) + 1);
        reports.files_by_directory.set(dir || 'root', (reports.files_by_directory.get(dir || 'root') || 0) + 1);
        reports.total_files++;
      }

      // Save index
      await fs.mkdir('SystemDev/reports', { recursive: true });
      await fs.writeFile(
        'SystemDev/reports/offline_index.json',
        JSON.stringify({
          ...reports,
          files_by_type: Object.fromEntries(reports.files_by_type),
          files_by_directory: Object.fromEntries(reports.files_by_directory),
          generated: Date.now()
        }, null, 2)
      );

      return { indexed_files: reports.total_files, timestamp: Date.now() };
    } catch (error) {
      console.warn('[OfflineOps] Index rebuild failed:', error);
      return { error: error instanceof Error ? error.message : String(error), timestamp: Date.now() };
    }
  }

  private async healConfigs(): Promise<any> {
    const configs = [
      'SystemDev/guards/flags.json',
      'package.json',
      'tsconfig.json'
    ];

    let healed = 0;

    for (const config of configs) {
      try {
        const content = await fs.readFile(config, 'utf8');
        JSON.parse(content); // Validate JSON
      } catch (error) {
        try {
          // Try to restore from backup or create minimal config
          if (config.includes('flags.json')) {
            await this.restoreUIFlags();
            healed++;
          }
        } catch (restoreError) {
          console.warn(`[OfflineOps] Could not heal config ${config}:`, restoreError);
        }
      }
    }

    return { configs_healed: healed, timestamp: Date.now() };
  }

  private async restoreUIFlags(): Promise<void> {
    const defaultFlags = {
      active_ui: 'legacy',
      milestones: {
        UI_M0_BOOT: true,
        UI_M1_PANELS: false,
        UI_M2_ADVISOR: false,
        UI_M3_HOLO: false,
        UI_M4_CHATDEV: false,
        UI_M5_COMPOSER: false
      },
      debug: {
        force_ui: null,
        bypass_research: false,
        log_routing: true
      },
      updated: new Date().toISOString(),
      restored_by: 'offline_operations'
    };

    await fs.mkdir('SystemDev/guards', { recursive: true });
    await fs.writeFile('SystemDev/guards/flags.json', JSON.stringify(defaultFlags, null, 2));
  }

  private async cultivateSystem(): Promise<any> {
    // System cultivation - systematic improvements
    const improvements = [];

    // 1. Organize scattered files
    const scatteredFiles = await this.findScatteredFiles();
    if (scatteredFiles.length > 0) {
      improvements.push(`Found ${scatteredFiles.length} scattered files to organize`);
    }

    // 2. Clean empty directories
    const emptyDirs = await this.findEmptyDirectories();
    if (emptyDirs.length > 0) {
      improvements.push(`Found ${emptyDirs.length} empty directories to clean`);
    }

    // 3. Update file permissions if needed
    const permissionIssues = await this.checkFilePermissions();
    if (permissionIssues > 0) {
      improvements.push(`Found ${permissionIssues} files with permission issues`);
    }

    return { improvements, timestamp: Date.now() };
  }

  private async harvestFreeTasks(): Promise<any> {
    const freeTasks = [];

    // 1. Check for obvious file renames needed
    const renameOpportunities = await this.findRenameOpportunities();
    freeTasks.push(...renameOpportunities);

    // 2. Check for files that can be moved to better locations
    const moveOpportunities = await this.findMoveOpportunities();
    freeTasks.push(...moveOpportunities);

    // 3. Check for unnecessary temporary files
    const tempFiles = await this.findTemporaryFiles();
    freeTasks.push(...tempFiles.map(f => `Clean temp file: ${f}`));

    return { free_tasks: freeTasks, count: freeTasks.length, timestamp: Date.now() };
  }

  // Helper methods

  private async scanDirectoryRecursive(dir: string, maxDepth = 5): Promise<string[]> {
    const results: string[] = [];
    const queue: Array<{path: string, depth: number}> = [{path: dir, depth: 0}];
    let readErrors = 0;

    const excludeDirs = new Set(['node_modules', '.git', 'dist', 'build', '.cache']);

    while (queue.length > 0) {
      const {path: currentPath, depth} = queue.shift()!;
      
      if (depth > maxDepth) continue;

      try {
        const entries = await fs.readdir(currentPath, { withFileTypes: true });
        
        for (const entry of entries) {
          const fullPath = path.join(currentPath, entry.name);
          
          if (entry.isDirectory() && !excludeDirs.has(entry.name)) {
            queue.push({path: fullPath, depth: depth + 1});
          } else if (entry.isFile()) {
            results.push(fullPath);
          }
        }
      } catch (error) {
        readErrors += 1;
        if (readErrors <= 3) {
          console.warn('[OfflineOps] Skipped directory during scan due to read error:', currentPath, error);
        }
      }
    }

    if (readErrors > 0) {
      console.warn(`[OfflineOps] Skipped ${readErrors} directories during scan due to read errors`);
    }

    return results;
  }

  private async findScatteredFiles(): Promise<string[]> {
    // Find files that should be in organized directories
    const files = await this.scanDirectoryRecursive('.', 2);
    return files.filter(f => 
      path.dirname(f) === '.' && 
      !['package.json', 'README.md', '.gitignore'].includes(path.basename(f))
    );
  }

  private async findEmptyDirectories(): Promise<string[]> {
    // Implementation would scan for empty directories
    return [];
  }

  private async checkFilePermissions(): Promise<number> {
    // Implementation would check file permissions
    return 0;
  }

  private async findRenameOpportunities(): Promise<string[]> {
    const opportunities = [];
    
    // Look for files with obvious naming issues
    const files = await this.scanDirectoryRecursive('.', 3);
    
    for (const file of files) {
      const basename = path.basename(file);
      
      // Check for common naming issues
      if (basename.includes('untitled') || basename.includes('copy') || basename.includes('temp')) {
        opportunities.push(`Rename file: ${file}`);
      }
    }

    return opportunities;
  }

  private async findMoveOpportunities(): Promise<string[]> {
    const opportunities = [];
    
    // Look for files in wrong directories
    const files = await this.scanDirectoryRecursive('.', 3);
    
    for (const file of files) {
      const ext = path.extname(file);
      const dir = path.dirname(file);
      
      // Suggest moves based on file types
      if (ext === '.md' && !dir.includes('docs')) {
        opportunities.push(`Move documentation: ${file} -> docs/`);
      }
      
      if (ext === '.json' && path.basename(file).includes('config') && !dir.includes('config')) {
        opportunities.push(`Move config: ${file} -> config/`);
      }
    }

    return opportunities;
  }

  private async findTemporaryFiles(): Promise<string[]> {
    const files = await this.scanDirectoryRecursive('.', 3);
    
    return files.filter(f => {
      const basename = path.basename(f);
      return basename.startsWith('.') && (
        basename.includes('tmp') || 
        basename.includes('temp') || 
        basename.endsWith('~') ||
        basename.endsWith('.bak')
      );
    });
  }

  private async performHealthCheck(): Promise<void> {
    try {
      const files = await this.scanDirectoryRecursive('.', 3);
      
      this.systemHealth = {
        timestamp: Date.now(),
        file_count: files.length,
        duplicate_count: 0, // Would be calculated
        error_count: 0, // Would be calculated
        repo_size_mb: 0, // Would be calculated
        receipt_count: await this.countReceipts(),
        organization_score: this.calculateOrganizationScore(files)
      };

      // Generate intelligent contextual insights instead of generic health stats
      const insights = this.generateIntelligentInsights();
      
      if (this.councilBus) {
        this.councilBus.publish('system.intelligence.update', {
          ...this.systemHealth,
          insights: insights,
          who: 'Autonomous Operations Manager',
          what: 'System health analysis completed',
          when: new Date().toISOString(),
          where: 'Server infrastructure layer',
          why: 'Maintaining optimal system performance',
          how: 'Automated file analysis and organization scoring'
        });
      }

      console.log(`[🧠] System Intelligence: ${insights.join(' | ')}`);

    } catch (error) {
      console.warn('[OfflineOps] Health check failed:', error);
    }
  }

  private generateIntelligentInsights(): string[] {
    if (!this.systemHealth) return [];
    
    const insights = [];
    const health = this.systemHealth;
    
    if (health.organization_score > 80) {
      insights.push(`Repository well-organized (${health.organization_score}% score)`);
    } else if (health.organization_score < 50) {
      insights.push(`Repository needs organization - ${100 - health.organization_score}% improvement potential`);
    }
    
    if (health.receipt_count > 50) {
      insights.push(`Rich development history - ${health.receipt_count} receipts available for analysis`);
    } else {
      insights.push(`Early development stage - establishing documentation patterns`);
    }
    
    if (health.file_count > 10000) {
      insights.push(`Large codebase detected - optimization opportunities available`);
    }
    
    return insights.length > 0 ? insights : ['System baseline established - monitoring for improvement opportunities'];
  }

  private async countReceipts(): Promise<number> {
    try {
      const receipts = await fs.readdir('SystemDev/receipts');
      return receipts.filter(f => f.endsWith('.json')).length;
    } catch (error) {
      console.warn('[OfflineOps] Failed to count receipts:', error);
      return 0;
    }
  }

  private calculateOrganizationScore(files: string[]): number {
    // Simple organization score based on file distribution
    const dirCounts = new Map<string, number>();
    
    for (const file of files) {
      const dir = path.dirname(file).split('/')[0] || 'root';
      dirCounts.set(dir, (dirCounts.get(dir) || 0) + 1);
    }

    // Better organization = more even distribution, fewer files in root
    const rootFiles = dirCounts.get('.') || 0;
    const totalFiles = files.length;
    
    return Math.max(0, Math.min(100, 100 - (rootFiles / totalFiles) * 100));
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  public getStatus() {
    return {
      running: this.running,
      tasks_registered: this.tasks.size,
      system_health: this.systemHealth,
      last_health_check: this.lastHealthCheck,
      offline_mode: isQuotaExceeded()
    };
  }
}

// Export singleton instance
export const offlineOpsManager = new OfflineOperationsManager();
void offlineOpsManager.initialize();
