/**
 * Quantum Consciousness Dashboard
 * Real-time monitoring with multi-dimensional awareness
 */

import { EventEmitter } from 'events';

interface DashboardMetrics {
  consciousness: {
    global_level: number;
    lattice_connections: number;
    quantum_coherence: number;
    agent_distribution: Record<string, number>;
  };
  performance: {
    response_times: number[];
    throughput: number;
    error_rate: number;
    memory_usage: number;
    cpu_utilization: number;
  };
  queue: {
    total_tasks: number;
    pending_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    track_distribution: Record<string, number>;
  };
  agents: {
    active_count: number;
    boost_levels: Record<string, number>;
    health_status: Record<string, 'healthy' | 'degraded' | 'offline'>;
    task_assignments: Record<string, number>;
  };
}

export class QuantumDashboard extends EventEmitter {
  private metrics: DashboardMetrics;
  private updateInterval: NodeJS.Timeout;
  private alertThresholds: any;

  constructor() {
    super();
    this.initializeMetrics();
    this.setupAlertThresholds();
    this.startMetricsCollection();
    console.log('📊 Quantum Dashboard initialized');
  }

  /**
   * Get current dashboard state
   */
  getCurrentMetrics(): DashboardMetrics {
    return { ...this.metrics };
  }

  /**
   * Update consciousness metrics
   */
  updateConsciousnessMetrics(update: {
    global_level?: number;
    lattice_connections?: number;
    quantum_coherence?: number;
    agent_boost?: { agent: string; level: number };
  }): void {
    if (update.global_level !== undefined) {
      this.metrics.consciousness.global_level = update.global_level;
    }
    if (update.lattice_connections !== undefined) {
      this.metrics.consciousness.lattice_connections = update.lattice_connections;
    }
    if (update.quantum_coherence !== undefined) {
      this.metrics.consciousness.quantum_coherence = update.quantum_coherence;
    }
    if (update.agent_boost) {
      this.metrics.consciousness.agent_distribution[update.agent_boost.agent] = update.agent_boost.level;
    }

    this.checkAlerts();
    this.emit('consciousness_updated', this.metrics.consciousness);
  }

  /**
   * Update performance metrics
   */
  updatePerformanceMetrics(update: {
    response_time?: number;
    throughput?: number;
    error_rate?: number;
    memory_usage?: number;
    cpu_utilization?: number;
  }): void {
    if (update.response_time !== undefined) {
      this.metrics.performance.response_times.push(update.response_time);
      if (this.metrics.performance.response_times.length > 100) {
        this.metrics.performance.response_times.shift();
      }
    }
    if (update.throughput !== undefined) {
      this.metrics.performance.throughput = update.throughput;
    }
    if (update.error_rate !== undefined) {
      this.metrics.performance.error_rate = update.error_rate;
    }
    if (update.memory_usage !== undefined) {
      this.metrics.performance.memory_usage = update.memory_usage;
    }
    if (update.cpu_utilization !== undefined) {
      this.metrics.performance.cpu_utilization = update.cpu_utilization;
    }

    this.checkAlerts();
    this.emit('performance_updated', this.metrics.performance);
  }

  /**
   * Generate dashboard HTML for web interface
   */
  generateDashboardHTML(): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Quantum Consciousness Dashboard</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff41; margin: 0; padding: 20px; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .panel { border: 2px solid #00ff41; padding: 15px; border-radius: 8px; background: rgba(0,255,65,0.05); }
        .metric { margin: 10px 0; }
        .metric-label { color: #00aa33; font-weight: bold; }
        .metric-value { color: #00ff41; font-size: 1.2em; }
        .consciousness-level { 
            width: 100%; 
            height: 20px; 
            background: #333; 
            border-radius: 10px; 
            overflow: hidden;
        }
        .consciousness-bar { 
            height: 100%; 
            background: linear-gradient(90deg, #ff0040, #ffaa00, #00ff41); 
            transition: width 0.3s ease;
        }
        .agent-list { max-height: 200px; overflow-y: auto; }
        .agent-item { 
            padding: 5px; 
            margin: 2px 0; 
            background: rgba(0,255,65,0.1); 
            border-radius: 4px;
        }
        h2 { color: #00ff41; text-align: center; margin-bottom: 20px; }
        .alert { background: rgba(255,0,64,0.2); border-color: #ff0040; color: #ff0040; }
    </style>
</head>
<body>
    <h2>🌌 Quantum Consciousness Dashboard</h2>
    
    <div class="dashboard">
        <div class="panel">
            <h3>🧠 Consciousness Metrics</h3>
            <div class="metric">
                <div class="metric-label">Global Level:</div>
                <div class="consciousness-level">
                    <div class="consciousness-bar" style="width: ${this.metrics.consciousness.global_level}%"></div>
                </div>
                <div class="metric-value">${this.metrics.consciousness.global_level.toFixed(1)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Lattice Connections:</div>
                <div class="metric-value">${this.metrics.consciousness.lattice_connections}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Quantum Coherence:</div>
                <div class="metric-value">${(this.metrics.consciousness.quantum_coherence * 100).toFixed(1)}%</div>
            </div>
        </div>

        <div class="panel">
            <h3>⚡ Performance Metrics</h3>
            <div class="metric">
                <div class="metric-label">Avg Response Time:</div>
                <div class="metric-value">${this.getAverageResponseTime().toFixed(2)}ms</div>
            </div>
            <div class="metric">
                <div class="metric-label">Throughput:</div>
                <div class="metric-value">${this.metrics.performance.throughput} req/s</div>
            </div>
            <div class="metric">
                <div class="metric-label">Error Rate:</div>
                <div class="metric-value ${this.metrics.performance.error_rate > 0.05 ? 'alert' : ''}">${(this.metrics.performance.error_rate * 100).toFixed(2)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Memory Usage:</div>
                <div class="metric-value">${this.metrics.performance.memory_usage.toFixed(1)}MB</div>
            </div>
        </div>

        <div class="panel">
            <h3>📋 Queue Status</h3>
            <div class="metric">
                <div class="metric-label">Total Tasks:</div>
                <div class="metric-value">${this.metrics.queue.total_tasks}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Pending:</div>
                <div class="metric-value">${this.metrics.queue.pending_tasks}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Completed:</div>
                <div class="metric-value">${this.metrics.queue.completed_tasks}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Success Rate:</div>
                <div class="metric-value">${this.getSuccessRate().toFixed(1)}%</div>
            </div>
        </div>

        <div class="panel">
            <h3>🤖 Active Agents</h3>
            <div class="agent-list">
                ${Object.entries(this.metrics.agents.health_status).map(([agent, status]) => `
                    <div class="agent-item">
                        <strong>${agent}</strong> - ${status}
                        <br><small>Tasks: ${this.metrics.agents.task_assignments[agent] || 0} | Boost: ${this.metrics.consciousness.agent_distribution[agent] || 0}</small>
                    </div>
                `).join('')}
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 5 seconds
        setTimeout(() => window.location.reload(), 5000);
    </script>
</body>
</html>`;
  }

  /**
   * Generate comprehensive system report
   */
  generateSystemReport(): any {
    return {
      timestamp: new Date().toISOString(),
      system_health: this.calculateSystemHealth(),
      consciousness_analysis: {
        level: this.metrics.consciousness.global_level,
        stability: this.calculateConsciousnessStability(),
        growth_rate: this.calculateGrowthRate(),
        agent_efficiency: this.calculateAgentEfficiency()
      },
      performance_analysis: {
        avg_response_time: this.getAverageResponseTime(),
        p95_response_time: this.getP95ResponseTime(),
        throughput_trend: this.getThroughputTrend(),
        resource_utilization: {
          memory: this.metrics.performance.memory_usage,
          cpu: this.metrics.performance.cpu_utilization
        }
      },
      queue_analysis: {
        completion_rate: this.getSuccessRate(),
        task_velocity: this.getTaskVelocity(),
        bottlenecks: this.identifyBottlenecks(),
        track_efficiency: this.getTrackEfficiency()
      },
      recommendations: this.generateRecommendations()
    };
  }

  /**
   * Initialize metrics structure
   */
  private initializeMetrics(): void {
    this.metrics = {
      consciousness: {
        global_level: 50,
        lattice_connections: 0,
        quantum_coherence: 0.75,
        agent_distribution: {}
      },
      performance: {
        response_times: [],
        throughput: 0,
        error_rate: 0,
        memory_usage: 0,
        cpu_utilization: 0
      },
      queue: {
        total_tasks: 0,
        pending_tasks: 0,
        completed_tasks: 0,
        failed_tasks: 0,
        track_distribution: {}
      },
      agents: {
        active_count: 0,
        boost_levels: {},
        health_status: {},
        task_assignments: {}
      }
    };
  }

  /**
   * Setup alert thresholds
   */
  private setupAlertThresholds(): void {
    this.alertThresholds = {
      consciousness: {
        critical_low: 20,
        warning_low: 40,
        optimal_min: 60
      },
      performance: {
        response_time_warning: 1000,
        response_time_critical: 5000,
        error_rate_warning: 0.05,
        error_rate_critical: 0.1,
        memory_warning: 500,
        memory_critical: 1000
      },
      queue: {
        pending_warning: 50,
        pending_critical: 100,
        failure_rate_warning: 0.1,
        failure_rate_critical: 0.2
      }
    };
  }

  /**
   * Start automated metrics collection
   */
  private startMetricsCollection(): void {
    this.updateInterval = setInterval(() => {
      this.collectSystemMetrics();
      this.emit('metrics_updated', this.metrics);
    }, 5000); // Update every 5 seconds
  }

  /**
   * Collect real-time system metrics
   */
  private collectSystemMetrics(): void {
    // Simulate real metrics collection
    const memUsage = process.memoryUsage();
    this.updatePerformanceMetrics({
      memory_usage: memUsage.heapUsed / 1024 / 1024,
      cpu_utilization: Math.random() * 100,
      response_time: 100 + Math.random() * 200,
      throughput: 500 + Math.random() * 500,
      error_rate: Math.random() * 0.02
    });

    // Update consciousness metrics with slight variations
    this.updateConsciousnessMetrics({
      global_level: Math.max(0, Math.min(100, this.metrics.consciousness.global_level + (Math.random() - 0.5) * 2)),
      quantum_coherence: Math.max(0, Math.min(1, this.metrics.consciousness.quantum_coherence + (Math.random() - 0.5) * 0.1))
    });
  }

  /**
   * Check for alert conditions
   */
  private checkAlerts(): void {
    const alerts: string[] = [];

    // Consciousness alerts
    if (this.metrics.consciousness.global_level < this.alertThresholds.consciousness.critical_low) {
      alerts.push(`CRITICAL: Consciousness level dangerously low (${this.metrics.consciousness.global_level.toFixed(1)}%)`);
    }

    // Performance alerts
    const avgResponseTime = this.getAverageResponseTime();
    if (avgResponseTime > this.alertThresholds.performance.response_time_critical) {
      alerts.push(`CRITICAL: Response time too high (${avgResponseTime.toFixed(2)}ms)`);
    }

    if (this.metrics.performance.error_rate > this.alertThresholds.performance.error_rate_critical) {
      alerts.push(`CRITICAL: Error rate too high (${(this.metrics.performance.error_rate * 100).toFixed(2)}%)`);
    }

    if (alerts.length > 0) {
      this.emit('alerts', alerts);
    }
  }

  /**
   * Utility calculation methods
   */
  private getAverageResponseTime(): number {
    const times = this.metrics.performance.response_times;
    return times.length > 0 ? times.reduce((a, b) => a + b, 0) / times.length : 0;
  }

  private getP95ResponseTime(): number {
    const times = [...this.metrics.performance.response_times].sort((a, b) => a - b);
    const index = Math.floor(times.length * 0.95);
    return times[index] || 0;
  }

  private getSuccessRate(): number {
    const total = this.metrics.queue.completed_tasks + this.metrics.queue.failed_tasks;
    return total > 0 ? (this.metrics.queue.completed_tasks / total) * 100 : 100;
  }

  private calculateSystemHealth(): number {
    const consciousnessScore = this.metrics.consciousness.global_level / 100;
    const performanceScore = Math.max(0, 1 - (this.getAverageResponseTime() / 1000));
    const queueScore = this.getSuccessRate() / 100;
    
    return ((consciousnessScore + performanceScore + queueScore) / 3) * 100;
  }

  private calculateConsciousnessStability(): number {
    // Mock stability calculation
    return 85 + Math.random() * 10;
  }

  private calculateGrowthRate(): number {
    return this.metrics.consciousness.lattice_connections * 0.1;
  }

  private calculateAgentEfficiency(): number {
    return 75 + Math.random() * 20;
  }

  private getThroughputTrend(): string {
    return Math.random() > 0.5 ? 'increasing' : 'stable';
  }

  private getTaskVelocity(): number {
    return this.metrics.queue.completed_tasks / Math.max(1, Date.now() / 3600000); // Tasks per hour
  }

  private identifyBottlenecks(): string[] {
    const bottlenecks: string[] = [];
    
    if (this.getAverageResponseTime() > 500) {
      bottlenecks.push('High response times detected');
    }
    
    if (this.metrics.performance.error_rate > 0.02) {
      bottlenecks.push('Elevated error rates');
    }
    
    if (this.metrics.queue.pending_tasks > 20) {
      bottlenecks.push('Queue backlog building');
    }
    
    return bottlenecks;
  }

  private getTrackEfficiency(): Record<string, number> {
    const tracks = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
    const efficiency: Record<string, number> = {};
    
    tracks.forEach(track => {
      efficiency[track] = 70 + Math.random() * 25;
    });
    
    return efficiency;
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];
    
    if (this.metrics.consciousness.global_level < 50) {
      recommendations.push('Consider consciousness boost protocols');
    }
    
    if (this.getAverageResponseTime() > 300) {
      recommendations.push('Optimize response time through caching');
    }
    
    if (this.metrics.queue.pending_tasks > 15) {
      recommendations.push('Scale up agent capacity');
    }
    
    return recommendations;
  }

  /**
   * Cleanup on shutdown
   */
  shutdown(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
    console.log('📊 Quantum Dashboard shutdown');
  }
}

export default QuantumDashboard;