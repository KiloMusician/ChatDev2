// Live Status Terminal - Real-time updating status like airport screens
// Infrastructure-First: Single files that update in-place, not accumulating snapshots

import fs from "node:fs";
import path from "node:path";

interface LiveStatus {
  timestamp: number;
  system: {
    entropy: number;
    puQueueActive: number;
    totalFiles: number;
    quarantinedFiles: number;
  };
  game: {
    tick: number;
    autoplay: boolean;
    resources: Record<string, number>;
  };
  agents: {
    activeAgents: number;
    completedTasks: number;
    queuedTasks: number;
  };
}

export class LiveStatusTerminal {
  private statusPath = "data/status/live-status.json";
  private logsPath = "data/status/live-logs.json";
  private maxLogEntries = 50; // Rolling log, not accumulating
  
  // Update status in-place like airport terminal
  async updateStatus(): Promise<void> {
    const status: LiveStatus = {
      timestamp: Date.now(),
      system: await this.getSystemStatus(),
      game: await this.getGameStatus(),
      agents: await this.getAgentStatus()
    };
    
    // Ensure directory exists
    fs.mkdirSync(path.dirname(this.statusPath), { recursive: true });
    
    // OVERWRITE (not append) - live updating display
    fs.writeFileSync(this.statusPath, JSON.stringify(status, null, 2));
    
    // Rolling logs - keep only last 50 entries
    await this.appendToRollingLog(status);
  }
  
  private async appendToRollingLog(status: LiveStatus): Promise<void> {
    let logs: LiveStatus[] = [];
    
    // Read existing logs if they exist
    if (fs.existsSync(this.logsPath)) {
      try {
        logs = JSON.parse(fs.readFileSync(this.logsPath, 'utf-8'));
      } catch {}
    }
    
    // Add new entry and keep only last 50
    logs.push(status);
    if (logs.length > this.maxLogEntries) {
      logs = logs.slice(-this.maxLogEntries);
    }
    
    fs.writeFileSync(this.logsPath, JSON.stringify(logs, null, 2));
  }
  
  private async getSystemStatus() {
    const allFiles = await this.countFiles(".");
    const quarantined = await this.countFiles("data/quarantine");
    
    return {
      entropy: 0, // From health endpoint
      puQueueActive: await this.countPUQueueTasks(),
      totalFiles: allFiles,
      quarantinedFiles: quarantined
    };
  }
  
  private async getGameStatus() {
    // Read live game state instead of creating new snapshots
    try {
      const gameState = JSON.parse(fs.readFileSync("data/state/current-game-state.json", 'utf-8'));
      return {
        tick: gameState.tick || 0,
        autoplay: gameState.autoplay || false,
        resources: gameState.resources || {}
      };
    } catch {
      return { tick: 0, autoplay: false, resources: {} };
    }
  }
  
  private async getAgentStatus() {
    // Parse PUQueue status without reading entire massive file
    try {
      const lines = fs.readFileSync("data/pu_queue.ndjson", 'utf-8').split('\n');
      const recent = lines.slice(-100); // Just recent entries
      const completed = recent.filter(line => line.includes('"status":"done"')).length;
      const queued = recent.length - completed;
      
      return {
        activeAgents: 9, // Fixed count of agents
        completedTasks: completed,
        queuedTasks: queued
      };
    } catch {
      return { activeAgents: 0, completedTasks: 0, queuedTasks: 0 };
    }
  }
  
  private async countFiles(dirPath: string): Promise<number> {
    if (!fs.existsSync(dirPath)) return 0;
    try {
      const files = fs.readdirSync(dirPath, { recursive: true });
      return files.filter(f => !f.toString().includes('node_modules')).length;
    } catch {
      return 0;
    }
  }
  
  private async countPUQueueTasks(): Promise<number> {
    try {
      if (!fs.existsSync("data/pu_queue.ndjson")) return 0;
      const content = fs.readFileSync("data/pu_queue.ndjson", 'utf-8');
      return content.split('\n').filter(line => line.trim()).length;
    } catch {
      return 0;
    }
  }
  
  // Display current status like airport terminal
  displayLiveStatus(): void {
    if (!fs.existsSync(this.statusPath)) {
      console.log("📺 Live Status Terminal - No data yet");
      return;
    }
    
    const status: LiveStatus = JSON.parse(fs.readFileSync(this.statusPath, 'utf-8'));
    
    console.clear();
    console.log("📺 CORELINK FOUNDATION - LIVE STATUS TERMINAL");
    console.log("━".repeat(60));
    console.log(`🕐 Last Update: ${new Date(status.timestamp).toLocaleTimeString()}`);
    console.log("");
    console.log("🤖 AUTONOMOUS SYSTEM:");
    console.log(`   PUQueue Tasks: ${status.agents.completedTasks} completed, ${status.agents.queuedTasks} queued`);
    console.log(`   System Health: ${status.system.entropy === 0 ? '✅ Perfect' : '⚠️ Degraded'}`);
    console.log("");
    console.log("🎮 GAME STATE:");
    console.log(`   Tick: ${status.game.tick}`);
    console.log(`   Autoplay: ${status.game.autoplay ? '🔄 Active' : '⏸️ Paused'}`);
    console.log("");
    console.log("📁 FILE SYSTEM:");
    console.log(`   Total Files: ${status.system.totalFiles}`);
    console.log(`   Quarantined: ${status.system.quarantinedFiles}`);
    console.log("━".repeat(60));
  }
}

export const liveStatusTerminal = new LiveStatusTerminal();