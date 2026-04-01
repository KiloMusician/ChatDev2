/**
 * 📊 TELEMETRY & REPORTING - Culture-Ship UI Component
 * Zero-token system status and narrative reporting
 */

interface TelemetryData {
  timestamp: string;
  system_health: number;
  token_usage: { used: number; max: number };
  active_operations: number;
  last_cascade: string;
  temples_unlocked: string[];
}

class TelemetryReporter {
  private history: TelemetryData[] = [];
  
  async banner(message: string): Promise<void> {
    const banner = this.createBanner(message);
    console.log(banner);
    
    // In real implementation, would also emit to UI components
    await this.emit("banner", { message, timestamp: new Date().toISOString() });
  }
  
  async plan(plan: any): Promise<void> {
    console.log("📋 Culture-Ship Plan Generated:");
    console.log(`   ID: ${plan.id}`);
    console.log(`   Health Score: ${Math.round(plan.health_score * 100)}%`);
    console.log(`   Steps: ${plan.steps.length}`);
    console.log(`   Narrative: ${plan.narrative}`);
    
    if (plan.steps.length > 0) {
      console.log("   Top Steps:");
      for (const step of plan.steps.slice(0, 3)) {
        const ratio = (step.benefit / step.cost).toFixed(1);
        console.log(`     - ${step.title} (benefit/cost: ${ratio})`);
      }
    }
    
    await this.emit("plan", plan);
  }
  
  async status(status: TelemetryData): Promise<void> {
    this.history.push(status);
    
    // Keep last 100 entries
    if (this.history.length > 100) {
      this.history = this.history.slice(-100);
    }
    
    const healthPercent = Math.round(status.system_health * 100);
    const budgetPercent = Math.round((status.token_usage.used / status.token_usage.max) * 100);
    
    console.log("📊 Culture-Ship Status:");
    console.log(`   Health: ${healthPercent}% | Budget: ${budgetPercent}% | Operations: ${status.active_operations}`);
    console.log(`   Temples: ${status.temples_unlocked.join(", ")}`);
    
    await this.emit("status", status);
  }
  
  async metric(name: string, value: number, unit?: string): Promise<void> {
    const metric = {
      name,
      value,
      unit: unit || "",
      timestamp: new Date().toISOString()
    };
    
    console.log(`📈 ${name}: ${value}${unit || ""}`);
    await this.emit("metric", metric);
  }
  
  private createBanner(message: string): string {
    const line = "═".repeat(60);
    const padding = " ".repeat(Math.max(0, (60 - message.length) / 2));
    
    return `\n${line}\n${padding}${message}\n${line}\n`;
  }
  
  private async emit(event: string, data: any): Promise<void> {
    // In real implementation, would emit to WebSocket, SSE, or event bus
    // For now, just structure the data for future integration
    const eventData = {
      event,
      data,
      timestamp: new Date().toISOString(),
      source: "culture_ship_telemetry"
    };
    
    // Could write to logs/ship.jsonl for persistent storage
    try {
      const fs = await import("node:fs");
      const logEntry = JSON.stringify(eventData) + "\n";
      fs.appendFileSync("logs/ship.jsonl", logEntry);
    } catch (error) {
      // Fail silently if logging isn't available
    }
  }
  
  getHistory(): TelemetryData[] {
    return [...this.history];
  }
  
  generateReport(): string {
    const latest = this.history[this.history.length - 1];
    if (!latest) {
      return "# 📊 Culture-Ship Telemetry Report\n\nNo data available.\n";
    }
    
    const healthPercent = Math.round(latest.system_health * 100);
    const budgetPercent = Math.round((latest.token_usage.used / latest.token_usage.max) * 100);
    
    let report = "# 📊 Culture-Ship Telemetry Report\n\n";
    report += `**System Status** (${latest.timestamp})\n`;
    report += `- Health: ${healthPercent}%\n`;
    report += `- Token Budget: ${latest.token_usage.used}/${latest.token_usage.max} (${budgetPercent}%)\n`;
    report += `- Active Operations: ${latest.active_operations}\n`;
    report += `- Last Cascade: ${latest.last_cascade}\n`;
    report += `- Temples Unlocked: ${latest.temples_unlocked.length}\n\n`;
    
    if (this.history.length > 1) {
      const previous = this.history[this.history.length - 2];
      if (previous) {
        const healthDelta = latest.system_health - previous.system_health;
        const healthTrend = healthDelta > 0 ? "📈" : healthDelta < 0 ? "📉" : "➡️";
      
        report += `**Trends**\n`;
        report += `- Health: ${healthTrend} ${healthDelta >= 0 ? "+" : ""}${Math.round(healthDelta * 100)}%\n`;
        report += `- History Points: ${this.history.length}\n\n`;
      }
    }
    
    return report;
  }
}

export const report = new TelemetryReporter();
