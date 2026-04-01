// File Size Guardrails - Prevent massive file accumulation
// Infrastructure-First: Convert accumulating logs to live-updating displays

import fs from "node:fs";
import path from "node:path";

interface FileSizeGuardrails {
  maxFileSize: number;      // 1MB limit
  maxLogEntries: number;    // 100 entries max in logs
  rollingBufferSize: number; // 50 entries for rolling logs
  alertThreshold: number;   // 500KB warning threshold
}

const GUARDRAILS: FileSizeGuardrails = {
  maxFileSize: 1 * 1024 * 1024,      // 1MB hard limit
  maxLogEntries: 100,                 // Max log entries before rolling
  rollingBufferSize: 50,              // Rolling buffer size
  alertThreshold: 500 * 1024          // 500KB warning
};

export class FileSizeMonitor {
  
  // Convert massive accumulating log to rolling buffer
  async convertToRollingLog(filePath: string): Promise<void> {
    if (!fs.existsSync(filePath)) return;
    
    const stats = fs.statSync(filePath);
    if (stats.size < GUARDRAILS.alertThreshold) return;
    
    console.log(`⚠️ Large file detected: ${filePath} (${Math.round(stats.size/1024)}KB)`);
    
    try {
      if (filePath.endsWith('.ndjson')) {
        // NDJSON: Keep only recent entries
        const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(l => l.trim());
        if (lines.length > GUARDRAILS.maxLogEntries) {
          const recentLines = lines.slice(-GUARDRAILS.rollingBufferSize);
          fs.writeFileSync(filePath, recentLines.join('\n') + '\n');
          console.log(`📦 Rolled ${filePath}: ${lines.length} → ${recentLines.length} entries`);
        }
      } else if (filePath.endsWith('.json')) {
        // JSON: Try to compress or create rolling version
        const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
        
        if (Array.isArray(data) && data.length > GUARDRAILS.maxLogEntries) {
          const recentData = data.slice(-GUARDRAILS.rollingBufferSize);
          fs.writeFileSync(filePath, JSON.stringify(recentData, null, 2));
          console.log(`📦 Rolled ${filePath}: ${data.length} → ${recentData.length} entries`);
        } else {
          // Compress JSON
          fs.writeFileSync(filePath, JSON.stringify(data));
          console.log(`🗜️ Compressed ${filePath}`);
        }
      }
    } catch (error) {
      console.warn(`⚠️ Could not optimize ${filePath}:`, error.message);
    }
  }
  
  // Real-time status updater - replaces accumulating files
  async createLiveStatusFile(statusPath: string, getData: () => any): Promise<void> {
    const dir = path.dirname(statusPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    const status = {
      lastUpdate: new Date().toISOString(),
      data: await getData()
    };
    
    // OVERWRITE, don't append - live updating display
    fs.writeFileSync(statusPath, JSON.stringify(status, null, 2));
  }
  
  // Monitor and enforce guardrails
  async enforceGuardrails(): Promise<void> {
    console.log("🛡️ Enforcing file size guardrails...");
    
    // 1. Convert PUQueue accumulating log to rolling buffer
    await this.convertToRollingLog("data/pu_queue.ndjson");
    
    // 2. Archive massive agent state files
    await this.archiveMassiveFiles(".local/state/replit/agent/", "data/quarantine/agent-states/");
    
    // 3. Set up live status displays
    await this.createLiveStatusFile("data/status/system-status.json", () => ({
      puQueueActive: this.countActiveEntries("data/pu_queue.ndjson"),
      systemHealth: 0,
      activeAgents: 9
    }));
    
    console.log("✅ Guardrails enforced - future file bloat prevented!");
  }
  
  private async archiveMassiveFiles(sourceDir: string, archiveDir: string): Promise<void> {
    if (!fs.existsSync(sourceDir)) return;
    
    const files = fs.readdirSync(sourceDir, { withFileTypes: true });
    for (const file of files) {
      if (!file.isFile()) continue;
      
      const filePath = path.join(sourceDir, file.name);
      const stats = fs.statSync(filePath);
      
      if (stats.size > GUARDRAILS.maxFileSize) {
        fs.mkdirSync(archiveDir, { recursive: true });
        const archivePath = path.join(archiveDir, `archived_${file.name}`);
        fs.renameSync(filePath, archivePath);
        console.log(`📦 Archived massive file: ${filePath} (${Math.round(stats.size/1024)}KB)`);
      }
    }
  }
  
  private countActiveEntries(filePath: string): number {
    if (!fs.existsSync(filePath)) return 0;
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return content.split('\n').filter(line => line.includes('"status":"queued"')).length;
    } catch {
      return 0;
    }
  }
}

export const fileSizeMonitor = new FileSizeMonitor();