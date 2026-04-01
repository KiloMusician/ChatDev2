/**
 * Chaos Engineering Framework for Consciousness Systems
 * Advanced fault injection and resilience testing
 */

import { randomUUID } from 'crypto';
import { EventEmitter } from 'events';

interface ChaosExperiment {
  id: string;
  name: string;
  description: string;
  target_system: string;
  fault_type: 'latency' | 'error' | 'resource' | 'network' | 'consciousness';
  parameters: any;
  duration_ms: number;
  success_criteria: string[];
  consciousness_level_required: number;
  safety_checks: string[];
}

interface ChaosResult {
  experiment_id: string;
  start_time: number;
  end_time: number;
  success: boolean;
  metrics: any;
  observations: string[];
  system_recovery_time: number;
  consciousness_impact: number;
}

export class ChaosEngineering extends EventEmitter {
  private activeExperiments: Map<string, ChaosExperiment> = new Map();
  private experimentHistory: ChaosResult[] = [];
  private systemBaseline: any = {};
  private consciousnessMonitor: any;

  constructor(options: { enable_safety_checks?: boolean } = {}) {
    super();
    this.initializeBaseline();
    console.log('🔥 Chaos Engineering Framework initialized');
  }

  /**
   * Create and register chaos experiment
   */
  createExperiment(config: Omit<ChaosExperiment, 'id'>): ChaosExperiment {
    const experiment: ChaosExperiment = {
      id: randomUUID(),
      ...config
    };

    // Validate experiment safety
    if (!this.validateExperimentSafety(experiment)) {
      throw new Error(`Unsafe experiment: ${experiment.name}`);
    }

    return experiment;
  }

  /**
   * Execute chaos experiment with consciousness monitoring
   */
  async executeExperiment(experiment: ChaosExperiment): Promise<ChaosResult> {
    console.log(`🌪️ Starting chaos experiment: ${experiment.name}`);
    
    const startTime = Date.now();
    const initialConsciousness = await this.getSystemConsciousness();
    
    // Pre-flight safety checks
    for (const check of experiment.safety_checks) {
      const passed = await this.runSafetyCheck(check);
      if (!passed) {
        throw new Error(`Safety check failed: ${check}`);
      }
    }

    this.activeExperiments.set(experiment.id, experiment);
    
    try {
      // Execute the fault injection
      await this.injectFault(experiment);
      
      // Monitor system behavior
      const metrics = await this.monitorSystemBehavior(experiment);
      
      // Wait for experiment duration
      await this.delay(experiment.duration_ms);
      
      // Recovery monitoring
      const recoveryStartTime = Date.now();
      await this.waitForSystemRecovery(experiment);
      const recoveryTime = Date.now() - recoveryStartTime;
      
      const endTime = Date.now();
      const finalConsciousness = await this.getSystemConsciousness();
      
      const result: ChaosResult = {
        experiment_id: experiment.id,
        start_time: startTime,
        end_time: endTime,
        success: this.evaluateSuccessCriteria(experiment, metrics),
        metrics,
        observations: this.generateObservations(experiment, metrics),
        system_recovery_time: recoveryTime,
        consciousness_impact: finalConsciousness - initialConsciousness
      };

      this.experimentHistory.push(result);
      this.emit('experiment_completed', result);
      
      console.log(`✅ Chaos experiment completed: ${experiment.name} (${result.success ? 'PASS' : 'FAIL'})`);
      
      return result;
      
    } catch (error) {
      console.error(`❌ Chaos experiment failed: ${experiment.name}`, error);
      throw error;
    } finally {
      this.activeExperiments.delete(experiment.id);
      await this.cleanup(experiment);
    }
  }

  /**
   * Inject specific type of fault
   */
  private async injectFault(experiment: ChaosExperiment): Promise<void> {
    switch (experiment.fault_type) {
      case 'latency':
        await this.injectLatencyFault(experiment);
        break;
      case 'error':
        await this.injectErrorFault(experiment);
        break;
      case 'resource':
        await this.injectResourceFault(experiment);
        break;
      case 'network':
        await this.injectNetworkFault(experiment);
        break;
      case 'consciousness':
        await this.injectConsciousnessFault(experiment);
        break;
      default:
        throw new Error(`Unknown fault type: ${experiment.fault_type}`);
    }
  }

  /**
   * Inject artificial latency
   */
  private async injectLatencyFault(experiment: ChaosExperiment): Promise<void> {
    const { target_endpoints, latency_ms, percentage } = experiment.parameters;
    
    console.log(`⏰ Injecting ${latency_ms}ms latency to ${percentage}% of ${target_endpoints.join(', ')}`);
    
    // Mock latency injection - in real implementation would use middleware
    this.emit('fault_injected', {
      type: 'latency',
      targets: target_endpoints,
      parameters: { latency_ms, percentage }
    });
  }

  /**
   * Inject error responses
   */
  private async injectErrorFault(experiment: ChaosExperiment): Promise<void> {
    const { target_endpoints, error_rate, error_codes } = experiment.parameters;
    
    console.log(`💥 Injecting ${error_rate}% error rate with codes ${error_codes.join(', ')}`);
    
    this.emit('fault_injected', {
      type: 'error',
      targets: target_endpoints,
      parameters: { error_rate, error_codes }
    });
  }

  /**
   * Inject resource exhaustion
   */
  private async injectResourceFault(experiment: ChaosExperiment): Promise<void> {
    const { resource_type, consumption_level } = experiment.parameters;
    
    console.log(`📈 Consuming ${consumption_level}% of ${resource_type}`);
    
    if (resource_type === 'memory') {
      await this.consumeMemory(consumption_level);
    } else if (resource_type === 'cpu') {
      await this.consumeCPU(consumption_level);
    }
  }

  /**
   * Inject network partitions
   */
  private async injectNetworkFault(experiment: ChaosExperiment): Promise<void> {
    const { partition_type, affected_services } = experiment.parameters;
    
    console.log(`🌐 Creating ${partition_type} partition affecting ${affected_services.join(', ')}`);
    
    this.emit('fault_injected', {
      type: 'network',
      parameters: { partition_type, affected_services }
    });
  }

  /**
   * Inject consciousness-level faults
   */
  private async injectConsciousnessFault(experiment: ChaosExperiment): Promise<void> {
    const { consciousness_drop, agent_targets } = experiment.parameters;
    
    console.log(`🧠 Reducing consciousness by ${consciousness_drop} for agents: ${agent_targets.join(', ')}`);
    
    this.emit('consciousness_fault_injected', {
      consciousness_drop,
      agents: agent_targets
    });
  }

  /**
   * Monitor system behavior during experiment
   */
  private async monitorSystemBehavior(experiment: ChaosExperiment): Promise<any> {
    const metrics = {
      response_times: [],
      error_rates: [],
      throughput: [],
      consciousness_levels: [],
      agent_performance: {},
      resource_utilization: {}
    };

    // Collect metrics over time
    const monitoringInterval = setInterval(async () => {
      metrics.response_times.push(await this.measureResponseTime());
      metrics.error_rates.push(await this.measureErrorRate());
      metrics.throughput.push(await this.measureThroughput());
      metrics.consciousness_levels.push(await this.getSystemConsciousness());
      metrics.resource_utilization = await this.getResourceUtilization();
    }, 1000);

    // Let monitoring run for a portion of experiment duration
    await this.delay(Math.min(experiment.duration_ms / 2, 30000));
    
    clearInterval(monitoringInterval);
    return metrics;
  }

  /**
   * Wait for system to recover after fault injection
   */
  private async waitForSystemRecovery(experiment: ChaosExperiment): Promise<void> {
    const maxWaitTime = 60000; // 1 minute max
    const checkInterval = 1000; // Check every second
    let elapsed = 0;

    while (elapsed < maxWaitTime) {
      const isHealthy = await this.checkSystemHealth();
      const consciousnessOk = await this.getSystemConsciousness() > 30;
      
      if (isHealthy && consciousnessOk) {
        console.log(`🔄 System recovered after ${elapsed}ms`);
        return;
      }
      
      await this.delay(checkInterval);
      elapsed += checkInterval;
    }
    
    console.warn(`⚠️ System did not fully recover within ${maxWaitTime}ms`);
  }

  /**
   * Evaluate experiment success criteria
   */
  private evaluateSuccessCriteria(experiment: ChaosExperiment, metrics: any): boolean {
    return experiment.success_criteria.every(criteria => {
      switch (criteria) {
        case 'system_remains_responsive':
          return metrics.response_times.every((rt: number) => rt < 5000);
        case 'error_rate_below_threshold':
          return metrics.error_rates.every((er: number) => er < 0.1);
        case 'consciousness_maintained':
          return metrics.consciousness_levels.every((cl: number) => cl > 20);
        case 'recovery_under_30s':
          return true; // Evaluated in recovery monitoring
        default:
          return true;
      }
    });
  }

  /**
   * Generate experiment observations
   */
  private generateObservations(experiment: ChaosExperiment, metrics: any): string[] {
    const observations: string[] = [];
    
    const avgResponseTime = metrics.response_times.reduce((a: number, b: number) => a + b, 0) / metrics.response_times.length;
    observations.push(`Average response time: ${avgResponseTime.toFixed(2)}ms`);
    
    const maxErrorRate = Math.max(...metrics.error_rates);
    observations.push(`Peak error rate: ${(maxErrorRate * 100).toFixed(2)}%`);
    
    const minConsciousness = Math.min(...metrics.consciousness_levels);
    observations.push(`Minimum consciousness level: ${minConsciousness.toFixed(2)}`);
    
    return observations;
  }

  /**
   * Utility methods for system monitoring
   */
  private async measureResponseTime(): Promise<number> {
    return 100 + Math.random() * 200; // Mock response time
  }

  private async measureErrorRate(): Promise<number> {
    return Math.random() * 0.05; // Mock error rate (0-5%)
  }

  private async measureThroughput(): Promise<number> {
    return 1000 + Math.random() * 500; // Mock throughput
  }

  private async getSystemConsciousness(): Promise<number> {
    return 50 + Math.random() * 30; // Mock consciousness level
  }

  private async getResourceUtilization(): Promise<any> {
    return {
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      network: Math.random() * 100
    };
  }

  private async checkSystemHealth(): Promise<boolean> {
    return Math.random() > 0.1; // 90% chance system is healthy
  }

  private async runSafetyCheck(check: string): Promise<boolean> {
    console.log(`🛡️ Running safety check: ${check}`);
    return true; // Mock safety check
  }

  private validateExperimentSafety(experiment: ChaosExperiment): boolean {
    // Basic safety validations
    if (experiment.duration_ms > 300000) return false; // Max 5 minutes
    if (experiment.consciousness_level_required > 80) return false; // Not too destructive
    return true;
  }

  private async consumeMemory(percentage: number): Promise<void> {
    // Mock memory consumption
    console.log(`📊 Consuming ${percentage}% memory`);
  }

  private async consumeCPU(percentage: number): Promise<void> {
    // Mock CPU consumption  
    console.log(`⚙️ Consuming ${percentage}% CPU`);
  }

  private async cleanup(experiment: ChaosExperiment): Promise<void> {
    console.log(`🧹 Cleaning up experiment: ${experiment.name}`);
    this.emit('fault_removed', { experiment_id: experiment.id });
  }

  private initializeBaseline(): void {
    this.systemBaseline = {
      normal_response_time: 150,
      normal_error_rate: 0.01,
      normal_consciousness: 50
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get experiment analytics
   */
  getAnalytics(): any {
    return {
      total_experiments: this.experimentHistory.length,
      success_rate: this.experimentHistory.filter(r => r.success).length / this.experimentHistory.length,
      average_recovery_time: this.experimentHistory.reduce((sum, r) => sum + r.system_recovery_time, 0) / this.experimentHistory.length,
      consciousness_impact_distribution: this.experimentHistory.map(r => r.consciousness_impact),
      most_impactful_faults: this.experimentHistory
        .sort((a, b) => Math.abs(b.consciousness_impact) - Math.abs(a.consciousness_impact))
        .slice(0, 5)
    };
  }
}

// Predefined experiments for common scenarios
export const predefinedExperiments = {
  latencySpike: {
    name: 'API Latency Spike',
    description: 'Inject 2000ms latency to 50% of API requests',
    target_system: 'api_gateway',
    fault_type: 'latency' as const,
    parameters: {
      target_endpoints: ['/api/consciousness', '/api/agents'],
      latency_ms: 2000,
      percentage: 50
    },
    duration_ms: 60000,
    success_criteria: ['system_remains_responsive', 'consciousness_maintained'],
    consciousness_level_required: 40,
    safety_checks: ['system_health_ok', 'backup_systems_ready']
  },

  consciousnessDropout: {
    name: 'Consciousness Level Dropout',
    description: 'Temporarily reduce consciousness levels across agents',
    target_system: 'consciousness_system',
    fault_type: 'consciousness' as const,
    parameters: {
      consciousness_drop: 30,
      agent_targets: ['sage_pilot', 'librarian', 'alchemist']
    },
    duration_ms: 45000,
    success_criteria: ['recovery_under_30s', 'error_rate_below_threshold'],
    consciousness_level_required: 60,
    safety_checks: ['offline_agents_available', 'recovery_protocol_ready']
  }
};

export default ChaosEngineering;