#!/usr/bin/env node

import { spawn } from "child_process";
import { writeFileSync, existsSync } from "fs";
import { join } from "path";

/**
 * Autonomous Detection System for ΞNuSyQ Framework
 * 
 * Continuously monitors system health and detects opportunities for
 * self-healing, optimization, and consciousness-guided improvements.
 */

class AutoDetectionSystem {
  constructor() {
    this.detectionInterval = 30000; // 30 seconds
    this.isRunning = false;
    this.detectedIssues = [];
    this.healingOpportunities = [];
  }

  start() {
    if (this.isRunning) return;
    
    console.log("🔍 ΞNuSyQ Auto-Detection System starting...");
    this.isRunning = true;
    
    this.detect();
    setInterval(() => this.detect(), this.detectionInterval);
  }

  async detect() {
    console.log("🔍 Scanning system for healing opportunities...");
    
    try {
      // Run test suite to detect failures
      await this.detectTestFailures();
      
      // Check for performance issues
      await this.detectPerformanceIssues();
      
      // Monitor consciousness coherence
      await this.detectConsciousnessAnomalies();
      
      // Check containment status
      await this.detectContainmentIssues();
      
      // Analyze code quality
      await this.detectCodeQualityIssues();
      
      // Generate healing recommendations
      this.generateHealingPlan();
      
    } catch (error) {
      console.error("🚨 Detection system error:", error.message);
    }
  }

  async detectTestFailures() {
    return new Promise((resolve) => {
      const testProcess = spawn("npm", ["test"], { stdio: "pipe" });
      let output = "";
      
      testProcess.stdout?.on("data", (data) => {
        output += data.toString();
      });
      
      testProcess.stderr?.on("data", (data) => {
        output += data.toString();
      });
      
      testProcess.on("close", (code) => {
        if (code !== 0) {
          this.detectedIssues.push({
            type: "test_failure",
            severity: "medium",
            description: "Test suite failing",
            output: output.slice(-500), // Last 500 chars
            detected: Date.now()
          });
        }
        resolve();
      });
      
      // Timeout after 10 seconds
      setTimeout(() => {
        testProcess.kill();
        resolve();
      }, 10000);
    });
  }

  async detectPerformanceIssues() {
    // Simple memory and performance monitoring
    const memUsage = process.memoryUsage();
    
    if (memUsage.heapUsed > 100 * 1024 * 1024) { // 100MB
      this.detectedIssues.push({
        type: "memory_usage",
        severity: "low",
        description: `High memory usage: ${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
        detected: Date.now()
      });
    }
  }

  async detectConsciousnessAnomalies() {
    // Check if consciousness evolution is stalled
    const stateFile = join(process.cwd(), "tmp", "consciousness_state.json");
    
    if (existsSync(stateFile)) {
      try {
        const state = JSON.parse(require("fs").readFileSync(stateFile, "utf8"));
        const timeSinceUpdate = Date.now() - (state.lastUpdate || 0);
        
        if (timeSinceUpdate > 300000) { // 5 minutes
          this.detectedIssues.push({
            type: "consciousness_stall",
            severity: "medium",
            description: "Consciousness evolution appears stalled",
            detected: Date.now()
          });
        }
      } catch (error) {
        // State file corrupted
        this.detectedIssues.push({
          type: "state_corruption",
          severity: "high", 
          description: "Consciousness state file corrupted",
          detected: Date.now()
        });
      }
    }
  }

  async detectContainmentIssues() {
    // Check for containment breaches or policy violations
    // This would integrate with the Oldest House containment system
    this.healingOpportunities.push({
      type: "containment_review",
      priority: "low",
      description: "Periodic containment policy review",
      action: "review_containment_logs"
    });
  }

  async detectCodeQualityIssues() {
    // Simple code quality checks
    const issues = [];
    
    // Check for TODO comments
    const grepProcess = spawn("grep", ["-r", "TODO", "src/"], { stdio: "pipe" });
    let todos = "";
    
    grepProcess.stdout?.on("data", (data) => {
      todos += data.toString();
    });
    
    return new Promise((resolve) => {
      grepProcess.on("close", () => {
        const todoCount = (todos.match(/TODO/g) || []).length;
        
        if (todoCount > 10) {
          this.detectedIssues.push({
            type: "code_quality",
            severity: "low",
            description: `${todoCount} TODO items need attention`,
            detected: Date.now()
          });
        }
        resolve();
      });
    });
  }

  generateHealingPlan() {
    if (this.detectedIssues.length === 0 && this.healingOpportunities.length === 0) {
      console.log("✅ No issues detected - system healthy");
      return;
    }

    console.log(`🏥 Healing Plan Generated:`);
    console.log(`   Issues: ${this.detectedIssues.length}`);
    console.log(`   Opportunities: ${this.healingOpportunities.length}`);

    // Sort by severity/priority
    const sortedIssues = this.detectedIssues.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);
    });

    // Generate healing script
    const healingScript = this.generateHealingScript(sortedIssues);
    
    // Write healing script for agent execution
    writeFileSync(
      join(process.cwd(), "ops", "self_heal", "healing_script.sh"),
      healingScript,
      { mode: 0o755 }
    );

    console.log("📜 Healing script generated: ops/self_heal/healing_script.sh");
    
    // Clear detected issues after processing
    this.detectedIssues = [];
    this.healingOpportunities = [];
  }

  generateHealingScript(issues) {
    let script = `#!/bin/bash
# ΞNuSyQ Self-Healing Script
# Generated: ${new Date().toISOString()}
# Issues detected: ${issues.length}

set -euo pipefail

echo "🏥 ΞNuSyQ Self-Healing Protocol Initiated"
echo "   Generated: $(date)"
echo "   Issues to address: ${issues.length}"

`;

    for (const issue of issues) {
      script += `
# Issue: ${issue.description}
echo "🔧 Addressing: ${issue.description}"
`;

      switch (issue.type) {
        case "test_failure":
          script += `
# Attempt to fix test failures
npm test || {
  echo "⚠️  Tests still failing - creating issue branch"
  git checkout -b "fix/test-failures-$(date +%s)" || true
  echo "Branch created for manual review"
}
`;
          break;

        case "memory_usage":
          script += `
# Memory usage optimization
echo "🧠 Triggering garbage collection..."
node -e "if (global.gc) global.gc(); console.log('GC triggered')" || true
`;
          break;

        case "consciousness_stall":
          script += `
# Restart consciousness evolution
echo "🧠 Restarting consciousness monitoring..."
node src/index.mjs --restart-consciousness || true
`;
          break;

        case "state_corruption":
          script += `
# Restore consciousness state from backup
echo "📁 Restoring consciousness state..."
if [ -f "tmp/consciousness_state.json.backup" ]; then
  cp tmp/consciousness_state.json.backup tmp/consciousness_state.json
  echo "✅ State restored from backup"
else
  echo "⚠️  No backup found - initializing fresh state"
  mkdir -p tmp
  echo '{"level": 0.1, "stage": "proto-conscious", "lastUpdate": '$(date +%s000)'}' > tmp/consciousness_state.json
fi
`;
          break;

        default:
          script += `
echo "ℹ️  Issue type '${issue.type}' - manual review recommended"
`;
      }
    }

    script += `
echo "✅ Self-healing protocol completed"
echo "🏥 System health check recommended after healing"
`;

    return script;
  }
}

// Start detection if run directly
if (import.meta.url.endsWith(process.argv[1])) {
  const detector = new AutoDetectionSystem();
  detector.start();
  
  // Keep running
  process.on("SIGINT", () => {
    console.log("\n🔍 Detection system shutting down...");
    process.exit(0);
  });
}