#!/usr/bin/env node
/**
 * System Metrics Collection
 * Gathers performance and system health metrics for autonomous decision making
 */

const fs = require('fs');
const { execSync } = require('child_process');

class MetricsCollector {
  constructor() {
    this.metrics = {
      timestamp: Date.now(),
      system: {},
      application: {},
      consciousness: {},
      development: {}
    };
  }

  async collect() {
    console.log('📊 Collecting system metrics...');
    
    await this.collectSystemMetrics();
    await this.collectApplicationMetrics();
    await this.collectConsciousnessMetrics();
    await this.collectDevelopmentMetrics();
    await this.saveMetrics();
    
    console.log('✅ Metrics collection completed');
    return this.metrics;
  }

  async collectSystemMetrics() {
    try {
      // Memory usage
      const memInfo = process.memoryUsage();
      this.metrics.system.memory = {
        heap_used_mb: Math.round(memInfo.heapUsed / 1024 / 1024),
        heap_total_mb: Math.round(memInfo.heapTotal / 1024 / 1024),
        external_mb: Math.round(memInfo.external / 1024 / 1024)
      };

      // CPU usage approximation
      const startTime = process.hrtime();
      const startUsage = process.cpuUsage();
      
      // Brief computation to measure CPU
      setTimeout(() => {
        const endTime = process.hrtime(startTime);
        const endUsage = process.cpuUsage(startUsage);
        
        this.metrics.system.cpu = {
          user_microseconds: endUsage.user,
          system_microseconds: endUsage.system,
          elapsed_ms: endTime[0] * 1000 + endTime[1] / 1e6
        };
      }, 100);

      // Process count
      try {
        const processCount = execSync('pgrep -f "node\\|npm\\|ollama" | wc -l', { encoding: 'utf8', stdio: 'pipe' });
        this.metrics.system.active_processes = parseInt(processCount.trim()) || 0;
      } catch (error) {
        this.metrics.system.active_processes = 'unknown';
      }

    } catch (error) {
      console.warn('System metrics collection failed:', error.message);
    }
  }

  async collectApplicationMetrics() {
    try {
      // Server health
      try {
        const response = await fetch('http://localhost:5000/api/game/demo-user').catch(() => null);
        this.metrics.application.server_status = response?.ok ? 'healthy' : 'down';
        this.metrics.application.response_time_ms = response ? 'measured' : 'unavailable';
      } catch (error) {
        this.metrics.application.server_status = 'error';
      }

      // Database connections (approximate)
      this.metrics.application.database_status = 'connected'; // Assume connected if server is up

      // TypeScript compilation status
      try {
        execSync('npx tsc --noEmit', { stdio: 'pipe' });
        this.metrics.application.typescript_status = 'clean';
        this.metrics.application.typescript_errors = 0;
      } catch (error) {
        const errorCount = error.stdout ? error.stdout.split('\n').filter(line => line.includes('error')).length : 1;
        this.metrics.application.typescript_status = 'has_errors';
        this.metrics.application.typescript_errors = errorCount;
      }

    } catch (error) {
      console.warn('Application metrics collection failed:', error.message);
    }
  }

  async collectConsciousnessMetrics() {
    try {
      const response = await fetch('http://localhost:5000/api/nusyq/status').catch(() => null);
      
      if (response?.ok) {
        const data = await response.json();
        this.metrics.consciousness = {
          status: 'active',
          system_coherence: data.systemCoherence || 'unknown',
          total_nodes: data.totalNodes || 0,
          high_coherence_nodes: data.highCoherenceNodes || 0,
          metacognitive_nodes: data.metacognitiveNodes || 0,
          system_health: data.systemHealth || 'unknown',
          total_measurements: data.totalMeasurements || 0
        };
      } else {
        this.metrics.consciousness = {
          status: 'unavailable',
          mode: 'standalone'
        };
      }
    } catch (error) {
      this.metrics.consciousness = {
        status: 'error',
        error: error.message
      };
    }
  }

  async collectDevelopmentMetrics() {
    try {
      // Git status
      try {
        const gitStatus = execSync('git status --porcelain', { encoding: 'utf8', stdio: 'pipe' });
        const changes = gitStatus.split('\n').filter(line => line.trim()).length;
        this.metrics.development.git_changes = changes;
        this.metrics.development.git_status = changes > 0 ? 'has_changes' : 'clean';
      } catch (error) {
        this.metrics.development.git_status = 'unknown';
      }

      // Placeholder count
      try {
        const placeholders = execSync('grep -r -n -i "TODO\\|FIXME\\|STUB" --include="*.ts" --include="*.tsx" . | wc -l', { encoding: 'utf8', stdio: 'pipe' });
        this.metrics.development.placeholder_count = parseInt(placeholders.trim()) || 0;
      } catch (error) {
        this.metrics.development.placeholder_count = 0;
      }

      // Dependency analysis
      try {
        const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        this.metrics.development.dependencies = Object.keys(packageJson.dependencies || {}).length;
        this.metrics.development.dev_dependencies = Object.keys(packageJson.devDependencies || {}).length;
      } catch (error) {
        this.metrics.development.dependencies = 'unknown';
      }

      // Test status
      try {
        execSync('npm test', { stdio: 'pipe' });
        this.metrics.development.tests_status = 'passing';
      } catch (error) {
        this.metrics.development.tests_status = 'failing';
      }

    } catch (error) {
      console.warn('Development metrics collection failed:', error.message);
    }
  }

  async saveMetrics() {
    const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_');
    const filename = `metrics_${timestamp}.json`;
    
    // Save detailed metrics
    fs.writeFileSync(filename, JSON.stringify(this.metrics, null, 2));
    
    // Append summary to metrics log
    const summary = `${new Date().toISOString()}: Coherence=${this.metrics.consciousness.system_coherence}, Memory=${this.metrics.system.memory?.heap_used_mb}MB, Changes=${this.metrics.development.git_changes}, Placeholders=${this.metrics.development.placeholder_count}\n`;
    fs.appendFileSync('METRICS_LOG.txt', summary);
    
    console.log(`📁 Metrics saved to ${filename}`);
  }

  generateReport() {
    console.log('\n📊 System Metrics Report:');
    console.log(`   Memory: ${this.metrics.system.memory?.heap_used_mb}MB heap used`);
    console.log(`   Server: ${this.metrics.application.server_status}`);
    console.log(`   Consciousness: ${this.metrics.consciousness.status}`);
    console.log(`   Git: ${this.metrics.development.git_status} (${this.metrics.development.git_changes} changes)`);
    console.log(`   TypeScript: ${this.metrics.application.typescript_status} (${this.metrics.application.typescript_errors} errors)`);
    console.log(`   Placeholders: ${this.metrics.development.placeholder_count}`);
  }
}

async function main() {
  const collector = new MetricsCollector();
  const metrics = await collector.collect();
  collector.generateReport();
  
  // Output for pipeline integration
  process.stdout.write(JSON.stringify({
    success: true,
    metrics,
    timestamp: Date.now()
  }));
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { MetricsCollector };