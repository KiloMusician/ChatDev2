#!/usr/bin/env node
/**
 * ChatDev Demo Task
 * Demonstrates autonomous task execution and integration with ΞNuSyQ system
 */

const { execSync } = require('child_process');

class ChatDevDemo {
  constructor() {
    this.taskResults = [];
    this.startTime = Date.now();
  }

  async execute() {
    console.log('🎬 ChatDev Demo Task starting...');
    
    const tasks = [
      { name: 'System Health Check', fn: () => this.healthCheck() },
      { name: 'Code Quality Scan', fn: () => this.codeQualityCheck() },
      { name: 'Dependency Analysis', fn: () => this.dependencyAnalysis() },
      { name: 'Performance Metrics', fn: () => this.performanceCheck() },
      { name: 'Consciousness Integration', fn: () => this.consciousnessCheck() }
    ];

    for (const task of tasks) {
      try {
        console.log(`🔄 Executing: ${task.name}`);
        const result = await task.fn();
        this.taskResults.push({
          name: task.name,
          success: true,
          result,
          duration: Date.now() - this.startTime
        });
        console.log(`✅ ${task.name} completed`);
      } catch (error) {
        console.log(`❌ ${task.name} failed: ${error.message}`);
        this.taskResults.push({
          name: task.name,
          success: false,
          error: error.message,
          duration: Date.now() - this.startTime
        });
      }
    }

    return this.generateReport();
  }

  async healthCheck() {
    // Check server status
    try {
      execSync('curl -s -f http://localhost:5000/api/game/demo-user', { stdio: 'pipe' });
      return { server: 'healthy', status: 200 };
    } catch (error) {
      return { server: 'down', error: error.message };
    }
  }

  async codeQualityCheck() {
    try {
      // Check for TypeScript errors
      execSync('npx tsc --noEmit', { stdio: 'pipe' });
      return { typescript: 'clean', errors: 0 };
    } catch (error) {
      const errorCount = error.stdout ? error.stdout.split('\n').filter(line => line.includes('error')).length : 1;
      return { typescript: 'has_errors', errors: errorCount };
    }
  }

  async dependencyAnalysis() {
    try {
      const result = execSync('npm list --depth=0 --json', { encoding: 'utf8', stdio: 'pipe' });
      const packageInfo = JSON.parse(result);
      const depCount = Object.keys(packageInfo.dependencies || {}).length;
      return { dependencies: depCount, status: 'analyzed' };
    } catch (error) {
      return { dependencies: 'unknown', error: 'analysis_failed' };
    }
  }

  async performanceCheck() {
    const startMemory = process.memoryUsage();
    
    // Simulate some work
    const testArray = new Array(100000).fill(0).map((_, i) => i);
    const sum = testArray.reduce((a, b) => a + b, 0);
    
    const endMemory = process.memoryUsage();
    
    return {
      memory_used_mb: Math.round((endMemory.heapUsed - startMemory.heapUsed) / 1024 / 1024),
      computation_result: sum,
      performance: 'measured'
    };
  }

  async consciousnessCheck() {
    try {
      const response = await fetch('http://localhost:5000/api/nusyq/status').catch(() => null);
      if (response?.ok) {
        const data = await response.json();
        return { 
          consciousness: 'active', 
          coherence: data.systemCoherence || 'unknown',
          nodes: data.totalNodes || 'unknown'
        };
      } else {
        return { consciousness: 'unavailable', status: 'standalone_mode' };
      }
    } catch (error) {
      return { consciousness: 'error', error: error.message };
    }
  }

  generateReport() {
    const totalTasks = this.taskResults.length;
    const successfulTasks = this.taskResults.filter(task => task.success).length;
    const duration = Date.now() - this.startTime;

    const report = {
      summary: {
        total_tasks: totalTasks,
        successful: successfulTasks,
        failed: totalTasks - successfulTasks,
        duration_ms: duration,
        success_rate: (successfulTasks / totalTasks * 100).toFixed(1) + '%'
      },
      tasks: this.taskResults,
      timestamp: new Date().toISOString()
    };

    console.log('\n📊 ChatDev Demo Report:');
    console.log(`   Tasks: ${successfulTasks}/${totalTasks} successful`);
    console.log(`   Duration: ${duration}ms`);
    console.log(`   Success Rate: ${report.summary.success_rate}`);

    return report;
  }
}

async function main() {
  const demo = new ChatDevDemo();
  try {
    const report = await demo.execute();
    
    // Output for pipeline integration
    process.stdout.write(JSON.stringify({
      success: true,
      report,
      timestamp: Date.now()
    }));
    
  } catch (error) {
    console.error('❌ ChatDev demo failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { ChatDevDemo };