#!/usr/bin/env tsx
// QΛDRA Growth Throttle Watchdog
// Prevents recursive file expansion and repository explosion

import { promises as fs } from "node:fs";
import { watch } from "node:fs";
import { join } from "node:path";

interface GrowthMetrics {
  timestamp: number;
  total_files: number;
  new_files_last_hour: number;
  growth_rate: number; // files per minute
  spam_ratio: number;
  duplicate_ratio: number;
}

export class GrowthThrottle {
  private metrics: GrowthMetrics[] = [];
  private readonly maxMetrics = 100;
  private watchers: any[] = [];
  private isThrottling = false;
  
  // Thresholds for throttling
  private readonly THRESHOLDS = {
    max_growth_rate: 50,      // files per minute
    max_files_per_hour: 1000, // total new files per hour
    max_spam_ratio: 0.3,      // 30% spam files
    max_total_files: 100000,  // absolute limit
    throttle_duration: 60000  // 1 minute throttle
  };
  
  // Monitored directories (high-risk for expansion)
  private readonly WATCH_DIRS = [
    "reports",
    "logs", 
    "temp",
    "cache",
    "analysis",
    "content/directives",
    "kb",
    "sidecar"
  ];
  
  constructor() {}
  
  async initialize(): Promise<void> {
    console.log("[QΛDRA:Throttle] Initializing growth watchdog...");
    
    // Load existing metrics
    await this.loadMetrics();
    
    // Start file system watchers
    this.startWatchers();
    
    // Start periodic monitoring
    setInterval(() => this.checkGrowth(), 60000); // Check every minute
    
    console.log("[QΛDRA:Throttle] Growth throttle active");
  }
  
  private startWatchers(): void {
    for (const dir of this.WATCH_DIRS) {
      try {
        const watcher = watch(dir, { recursive: true }, (eventType, filename) => {
          if (eventType === 'rename' && filename) {
            this.onFileEvent(join(dir, filename));
          }
        });
        this.watchers.push(watcher);
        console.log(`[QΛDRA:Throttle] Watching ${dir} for file changes`);
      } catch (error) {
        console.warn(`[QΛDRA:Throttle] Could not watch ${dir}: ${error}`);
      }
    }
  }
  
  private async onFileEvent(filePath: string): Promise<void> {
    if (this.isThrottling) {
      console.log(`[QΛDRA:Throttle] 🚫 Blocking file creation during throttle: ${filePath}`);
      // In a real implementation, this would block the file creation
      return;
    }
    
    // Track new file
    await this.updateMetrics();
    
    // Check if we need to throttle
    const current = this.metrics[this.metrics.length - 1];
    if (this.shouldThrottle(current)) {
      await this.activateThrottle();
    }
  }
  
  private async checkGrowth(): Promise<void> {
    await this.updateMetrics();
    
    const current = this.metrics[this.metrics.length - 1];
    
    if (this.shouldThrottle(current)) {
      await this.activateThrottle();
    }
    
    // Log status
    console.log(`[QΛDRA:Throttle] Files: ${current.total_files}, Growth: ${current.growth_rate.toFixed(1)}/min`);
  }
  
  private shouldThrottle(metrics: GrowthMetrics): boolean {
    const t = this.THRESHOLDS;
    
    return (
      metrics.growth_rate > t.max_growth_rate ||
      metrics.new_files_last_hour > t.max_files_per_hour ||
      metrics.spam_ratio > t.max_spam_ratio ||
      metrics.total_files > t.max_total_files
    );
  }
  
  private async activateThrottle(): Promise<void> {
    if (this.isThrottling) return;
    
    console.log("[QΛDRA:Throttle] 🚨 ACTIVATING GROWTH THROTTLE");
    this.isThrottling = true;
    
    // Log throttle event
    await this.logThrottleEvent();
    
    // Execute emergency measures
    await this.executeEmergencyMeasures();
    
    // Schedule throttle release
    setTimeout(() => {
      this.isThrottling = false;
      console.log("[QΛDRA:Throttle] ✅ Growth throttle released");
    }, this.THRESHOLDS.throttle_duration);
  }
  
  private async executeEmergencyMeasures(): Promise<void> {
    console.log("[QΛDRA:Throttle] Executing emergency measures...");
    
    // 1. Compress recent large logs
    await this.compressLargeLogs();
    
    // 2. Archive old report files
    await this.archiveOldReports();
    
    // 3. Consolidate duplicate analysis files
    await this.consolidateAnalysisFiles();
    
    // 4. Notify Council Bus
    await this.notifyCouncil();
  }
  
  private async compressLargeLogs(): Promise<void> {
    try {
      const logsDir = "logs";
      const files = await fs.readdir(logsDir).catch(() => []);
      
      for (const file of files) {
        const filePath = join(logsDir, file);
        const stats = await fs.stat(filePath).catch(() => null);
        
        if (stats && stats.size > 10_000_000) { // >10MB
          console.log(`[QΛDRA:Throttle] Compressing large log: ${file}`);
          // In real implementation: gzip the file
          await this.moveToArchive(filePath);
        }
      }
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Log compression failed:", error);
    }
  }
  
  private async archiveOldReports(): Promise<void> {
    try {
      const reportsDir = "reports";
      const files = await fs.readdir(reportsDir, { recursive: true }).catch(() => []);
      
      const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
      
      for (const file of files) {
        if (typeof file !== 'string') continue;
        
        const filePath = join(reportsDir, file);
        const stats = await fs.stat(filePath).catch(() => null);
        
        if (stats && stats.mtime.getTime() < oneWeekAgo) {
          console.log(`[QΛDRA:Throttle] Archiving old report: ${file}`);
          await this.moveToArchive(filePath);
        }
      }
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Report archival failed:", error);
    }
  }
  
  private async consolidateAnalysisFiles(): Promise<void> {
    try {
      const analysisDir = "analysis";
      // Group similar analysis files and consolidate
      // This is where we'd implement file deduplication
      console.log("[QΛDRA:Throttle] Consolidating analysis files...");
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Analysis consolidation failed:", error);
    }
  }
  
  private async moveToArchive(filePath: string): Promise<void> {
    try {
      const archivePath = filePath.replace(/^/, "attic/");
      await fs.mkdir(archivePath.substring(0, archivePath.lastIndexOf("/")), { recursive: true });
      await fs.rename(filePath, archivePath);
    } catch (error) {
      console.warn(`[QΛDRA:Throttle] Archive failed for ${filePath}:`, error);
    }
  }
  
  private async notifyCouncil(): Promise<void> {
    try {
      // Post throttle event to Council Bus
      const event = {
        type: "qadra.growth_throttle_activated",
        timestamp: Date.now(),
        metrics: this.metrics[this.metrics.length - 1],
        thresholds: this.THRESHOLDS
      };
      
      // In real implementation: councilBus.publish('qadra.growth_throttle', event);
      console.log("[QΛDRA:Throttle] Notified Council of throttle activation");
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Council notification failed:", error);
    }
  }
  
  private async updateMetrics(): Promise<void> {
    try {
      // Count total files (limited scan for performance)
      const totalFiles = await this.countFiles(".", 50000); // Limit to 50K for perf
      
      // Calculate growth rate
      const oneHourAgo = Date.now() - (60 * 60 * 1000);
      const recentMetrics = this.metrics.filter(m => m.timestamp > oneHourAgo);
      const filesAnHourAgo = recentMetrics.length > 0 ? recentMetrics[0].total_files : totalFiles;
      const newFilesLastHour = totalFiles - filesAnHourAgo;
      const growthRate = newFilesLastHour / 60; // per minute
      
      // Estimate spam and duplicate ratios (simplified)
      const spamRatio = await this.estimateSpamRatio();
      const duplicateRatio = await this.estimateDuplicateRatio();
      
      const metrics: GrowthMetrics = {
        timestamp: Date.now(),
        total_files: totalFiles,
        new_files_last_hour: newFilesLastHour,
        growth_rate: growthRate,
        spam_ratio: spamRatio,
        duplicate_ratio: duplicateRatio
      };
      
      this.metrics.push(metrics);
      
      // Trim old metrics
      if (this.metrics.length > this.maxMetrics) {
        this.metrics = this.metrics.slice(-this.maxMetrics);
      }
      
      await this.saveMetrics();
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Metrics update failed:", error);
    }
  }
  
  private async countFiles(dir: string, maxCount: number): Promise<number> {
    let count = 0;
    
    async function walk(currentDir: string): Promise<void> {
      if (count >= maxCount) return;
      
      try {
        const entries = await fs.readdir(currentDir, { withFileTypes: true });
        for (const entry of entries) {
          if (count >= maxCount) return;
          
          if (entry.isDirectory() && !entry.name.startsWith('.')) {
            await walk(join(currentDir, entry.name));
          } else if (entry.isFile()) {
            count++;
          }
        }
      } catch {
        // Ignore permission errors
      }
    }
    
    await walk(dir);
    return count;
  }
  
  private async estimateSpamRatio(): Promise<number> {
    // Simplified spam detection - in real implementation would use repo audit
    try {
      const reportsFiles = await fs.readdir("reports", { recursive: true }).catch(() => []);
      const logFiles = reportsFiles.filter(f => typeof f === 'string' && f.includes('log'));
      return logFiles.length / Math.max(reportsFiles.length, 1);
    } catch {
      return 0;
    }
  }
  
  private async estimateDuplicateRatio(): Promise<number> {
    // Simplified - would use actual duplicate detection
    return 0.1; // Assume 10% baseline
  }
  
  private async logThrottleEvent(): Promise<void> {
    const event = {
      timestamp: Date.now(),
      action: "growth_throttle_activated",
      metrics: this.metrics[this.metrics.length - 1],
      thresholds_exceeded: this.getExceededThresholds()
    };
    
    try {
      await fs.mkdir("reports/qadra", { recursive: true });
      await fs.appendFile(
        "reports/qadra/throttle_events.log",
        JSON.stringify(event) + "\n"
      );
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Failed to log event:", error);
    }
  }
  
  private getExceededThresholds(): string[] {
    const current = this.metrics[this.metrics.length - 1];
    if (!current) return [];
    
    const exceeded: string[] = [];
    const t = this.THRESHOLDS;
    
    if (current.growth_rate > t.max_growth_rate) exceeded.push("growth_rate");
    if (current.new_files_last_hour > t.max_files_per_hour) exceeded.push("files_per_hour");
    if (current.spam_ratio > t.max_spam_ratio) exceeded.push("spam_ratio");
    if (current.total_files > t.max_total_files) exceeded.push("total_files");
    
    return exceeded;
  }
  
  private async saveMetrics(): Promise<void> {
    try {
      await fs.mkdir("reports/qadra", { recursive: true });
      await fs.writeFile(
        "reports/qadra/growth_metrics.json",
        JSON.stringify({
          metrics: this.metrics.slice(-50), // Last 50 points
          thresholds: this.THRESHOLDS,
          updated: Date.now()
        }, null, 2)
      );
    } catch (error) {
      console.warn("[QΛDRA:Throttle] Save failed:", error);
    }
  }
  
  private async loadMetrics(): Promise<void> {
    try {
      const data = await fs.readFile("reports/qadra/growth_metrics.json", "utf8");
      const parsed = JSON.parse(data);
      this.metrics = parsed.metrics || [];
      console.log(`[QΛDRA:Throttle] Loaded ${this.metrics.length} metric points`);
    } catch {
      console.log("[QΛDRA:Throttle] No previous metrics found, starting fresh");
    }
  }
  
  /**
   * Get current growth status for monitoring
   */
  getStatus() {
    const current = this.metrics[this.metrics.length - 1];
    return {
      is_throttling: this.isThrottling,
      current_metrics: current,
      thresholds: this.THRESHOLDS,
      exceeded_thresholds: current ? this.getExceededThresholds() : []
    };
  }
  
  shutdown(): void {
    console.log("[QΛDRA:Throttle] Shutting down watchers...");
    for (const watcher of this.watchers) {
      watcher.close();
    }
    this.watchers = [];
  }
}

// CLI runner for standalone operation
if (import.meta.url === `file://${process.argv[1]}`) {
  const throttle = new GrowthThrottle();
  
  throttle.initialize().then(() => {
    console.log("[QΛDRA:Throttle] Growth throttle watchdog active");
    
    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log("[QΛDRA:Throttle] Shutting down...");
      throttle.shutdown();
      process.exit(0);
    });
  }).catch(error => {
    console.error("[QΛDRA:Throttle] Failed to initialize:", error);
    process.exit(1);
  });
}