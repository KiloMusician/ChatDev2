import { execSync } from "node:child_process";
import { existsSync, statSync } from "node:fs";

export interface HealthStatus {
  timestamp: number;
  overall: "healthy" | "warning" | "critical";
  services: {
    server: "up" | "down";
    ml: "operational" | "degraded" | "offline";
    chatdev: "operational" | "degraded" | "offline";
    database: "connected" | "disconnected" | "unknown";
  };
  resources: {
    memory: number; // MB
    cpu: number;    // percentage
    disk: number;   // MB free
  };
  endpoints: {
    api: boolean;
    ws: boolean;
    static: boolean;
  };
  issues: string[];
}

export class HealthMonitor {
  async checkHealth(): Promise<HealthStatus> {
    const issues: string[] = [];
    const timestamp = Date.now();

    // Check services
    const services = {
      server: this.checkServer(),
      ml: await this.checkML(),
      chatdev: await this.checkChatDev(), 
      database: await this.checkDatabase()
    };

    // Check resources
    const resources = this.checkResources();
    
    // Check endpoints
    const endpoints = await this.checkEndpoints();

    // Determine overall health
    let overall: "healthy" | "warning" | "critical" = "healthy";
    
    if (services.server === "down") {
      overall = "critical";
      issues.push("Server is down");
    }
    
    if (resources.memory > 400) {
      overall = "warning";
      issues.push("High memory usage");
    }
    
    if (resources.cpu > 80) {
      overall = "warning";
      issues.push("High CPU usage");
    }

    if (!endpoints.api || !endpoints.static) {
      overall = "critical";
      issues.push("Critical endpoints failing");
    }

    return {
      timestamp,
      overall,
      services,
      resources,
      endpoints,
      issues
    };
  }

  private checkServer(): "up" | "down" {
    try {
      // Check if server process is running
      const port = process.env.PORT || "5000";
      execSync(`lsof -ti:${port}`, { stdio: 'pipe' });
      return "up";
    } catch {
      return "down";
    }
  }

  private async checkML(): Promise<"operational" | "degraded" | "offline"> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/ml/status`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const status = await response.json();
        return status.model_trained ? "operational" : "degraded";
      }
      return "offline";
    } catch {
      return "offline";
    }
  }

  private async checkChatDev(): Promise<"operational" | "degraded" | "offline"> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/chatdev/status`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const status = await response.json();
        return status.agents > 0 ? "operational" : "degraded";
      }
      return "offline";
    } catch {
      return "offline";
    }
  }

  private async checkDatabase(): Promise<"connected" | "disconnected" | "unknown"> {
    // For now, check if DATABASE_URL exists
    if (process.env.DATABASE_URL) {
      return "connected";
    }
    return "unknown";
  }

  private checkResources() {
    try {
      // Memory usage (rough estimate)
      const memInfo = execSync('cat /proc/meminfo', { encoding: 'utf8' });
      const memTotal = parseInt(memInfo.match(/MemTotal:\s+(\d+)/)?.[1] || "0") / 1024;
      const memFree = parseInt(memInfo.match(/MemAvailable:\s+(\d+)/)?.[1] || "0") / 1024;
      const memUsed = memTotal - memFree;

      // CPU usage (simplified)
      const cpuUsage = parseFloat(
        execSync("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1", 
          { encoding: 'utf8' }).trim()
      ) || 0;

      // Disk space
      const diskInfo = execSync('df -m .', { encoding: 'utf8' });
      const diskFree = parseInt(diskInfo.split('\n')[1]?.split(/\s+/)[3] || "0");

      return {
        memory: Math.round(memUsed),
        cpu: Math.round(cpuUsage),
        disk: diskFree
      };
    } catch {
      return { memory: 0, cpu: 0, disk: 0 };
    }
  }

  private async checkEndpoints() {
    const results = {
      api: false,
      ws: false,
      static: false
    };

    try {
      // API check
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const apiResponse = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/ml/status`, { signal: controller.signal });
      clearTimeout(timeoutId);
      results.api = apiResponse.ok;
    } catch {}

    try {
      // Static file check
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const staticResponse = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/`, { signal: controller.signal });
      clearTimeout(timeoutId);
      results.static = staticResponse.status < 500;
    } catch {}

    // WS check (simplified - assume working if server is up)
    results.ws = results.api;

    return results;
  }
}

export const healthMonitor = new HealthMonitor();