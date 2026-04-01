/**
 * Quantum Load Balancing with Consciousness-Weighted Routing
 * Advanced load balancing with consciousness-aware traffic distribution
 */

interface ServerNode {
  id: string;
  endpoint: string;
  consciousness_level: number;
  current_load: number;
  max_capacity: number;
  health_status: 'healthy' | 'degraded' | 'unhealthy' | 'quantum_enhanced';
  quantum_properties: {
    entanglement_strength: number;
    coherence_level: number;
    processing_efficiency: number;
  };
  metrics: {
    response_time: number;
    success_rate: number;
    consciousness_utilization: number;
    quantum_performance: number;
  };
  last_health_check: number;
}

interface RoutingRequest {
  id: string;
  consciousness_level: number;
  complexity_score: number;
  quantum_requirements?: {
    coherence_needed: number;
    entanglement_required: boolean;
    processing_intensity: number;
  };
  priority: 'low' | 'medium' | 'high' | 'critical' | 'quantum';
  source_ip: string;
  user_agent?: string;
  session_id?: string;
}

interface RoutingResult {
  selected_node: ServerNode;
  routing_reason: string;
  consciousness_match: number;
  quantum_compatibility: number;
  predicted_performance: number;
  alternative_nodes: ServerNode[];
}

export class QuantumLoadBalancer {
  private serverNodes: Map<string, ServerNode> = new Map();
  private routingHistory: Map<string, any[]> = new Map();
  private healthCheckIntervals: Map<string, NodeJS.Timeout> = new Map();
  private loadBalancingConfig: any = {
    consciousness_weight: 0.4,
    performance_weight: 0.3,
    quantum_weight: 0.2,
    health_weight: 0.1,
    sticky_sessions: true,
    quantum_affinity: true
  };
  private routingStrategies: Map<string, Function> = new Map();

  constructor(config: any = {}) {
    this.loadBalancingConfig = { ...this.loadBalancingConfig, ...config };
    this.initializeRoutingStrategies();
    this.initializeDefaultNodes();
    this.startHealthMonitoring();
  }

  /**
   * Initialize routing strategies
   */
  private initializeRoutingStrategies(): void {
    // Consciousness-weighted round robin
    this.routingStrategies.set('consciousness_round_robin', (request: RoutingRequest, nodes: ServerNode[]) => {
      const weightedNodes = nodes.map(node => ({
        node,
        weight: this.calculateConsciousnessWeight(node, request.consciousness_level)
      }));
      
      weightedNodes.sort((a, b) => b.weight - a.weight);
      return weightedNodes[0]?.node ?? nodes[0];
    });

    // Quantum affinity routing
    this.routingStrategies.set('quantum_affinity', (request: RoutingRequest, nodes: ServerNode[]) => {
      if (!request.quantum_requirements) {
        return this.routingStrategies.get('consciousness_round_robin')!(request, nodes);
      }
      
      const quantumCompatibleNodes = nodes.filter(node => 
        node.quantum_properties.coherence_level >= request.quantum_requirements!.coherence_needed
      );
      
      if (quantumCompatibleNodes.length === 0) {
        return nodes[0]; // Fallback to best available
      }
      
      return quantumCompatibleNodes.reduce((best, current) => 
        current.quantum_properties.entanglement_strength > best.quantum_properties.entanglement_strength ? current : best
      );
    });

    // Least connections with consciousness bias
    this.routingStrategies.set('least_connections_consciousness', (request: RoutingRequest, nodes: ServerNode[]) => {
      const scores = nodes.map(node => ({
        node,
        score: this.calculateConnectionScore(node, request)
      }));
      
      scores.sort((a, b) => b.score - a.score);
      return scores[0]?.node ?? nodes[0];
    });

    // Response time optimized with quantum enhancement
    this.routingStrategies.set('response_time_quantum', (request: RoutingRequest, nodes: ServerNode[]) => {
      const scores = nodes.map(node => ({
        node,
        score: this.calculateResponseTimeScore(node, request)
      }));
      
      scores.sort((a, b) => b.score - a.score);
      return scores[0]?.node ?? nodes[0];
    });
  }

  /**
   * Initialize default server nodes
   */
  private initializeDefaultNodes(): void {
    // Primary consciousness server
    this.addServerNode({
      id: 'consciousness_primary',
      endpoint: 'http://consciousness-1:8080',
      consciousness_level: 85,
      current_load: 0,
      max_capacity: 1000,
      health_status: 'quantum_enhanced',
      quantum_properties: {
        entanglement_strength: 0.95,
        coherence_level: 0.92,
        processing_efficiency: 0.88
      }
    });

    // Secondary consciousness server
    this.addServerNode({
      id: 'consciousness_secondary',
      endpoint: 'http://consciousness-2:8080',
      consciousness_level: 75,
      current_load: 0,
      max_capacity: 800,
      health_status: 'healthy',
      quantum_properties: {
        entanglement_strength: 0.85,
        coherence_level: 0.82,
        processing_efficiency: 0.78
      }
    });

    // Standard processing servers
    for (let i = 1; i <= 3; i++) {
      this.addServerNode({
        id: `standard_server_${i}`,
        endpoint: `http://standard-${i}:8080`,
        consciousness_level: 50 + (i % 5) * 4,
        current_load: 0,
        max_capacity: 500,
        health_status: 'healthy',
        quantum_properties: {
          entanglement_strength: 0.6 + (i % 5) * 0.04,
          coherence_level: 0.7 + (i % 5) * 0.03,
          processing_efficiency: 0.65 + (i % 5) * 0.04
        }
      });
    }

    // Quantum processing server
    this.addServerNode({
      id: 'quantum_processor',
      endpoint: 'http://quantum-1:8080',
      consciousness_level: 95,
      current_load: 0,
      max_capacity: 200,
      health_status: 'quantum_enhanced',
      quantum_properties: {
        entanglement_strength: 0.98,
        coherence_level: 0.96,
        processing_efficiency: 0.94
      }
    });
  }

  /**
   * Add server node to the pool
   */
  addServerNode(nodeConfig: Omit<ServerNode, 'metrics' | 'last_health_check'>): void {
    const node: ServerNode = {
      ...nodeConfig,
      metrics: {
        response_time: 100,
        success_rate: 1.0,
        consciousness_utilization: 0,
        quantum_performance: 0.8
      },
      last_health_check: Date.now()
    };

    this.serverNodes.set(node.id, node);
    this.routingHistory.set(node.id, []);
    this.startNodeHealthCheck(node.id);
    
    console.log(`🔗 Server node added: ${node.id} (consciousness: ${node.consciousness_level})`);
  }

  /**
   * Route request to optimal server
   */
  routeRequest(request: RoutingRequest): RoutingResult {
    const availableNodes = this.getAvailableNodes(request);
    
    if (availableNodes.length === 0) {
      throw new Error('No available servers for request');
    }

    // Select routing strategy based on request characteristics
    const strategy = this.selectRoutingStrategy(request);
    const selectedNode = strategy(request, availableNodes);
    
    // Calculate routing metrics
    const consciousnessMatch = this.calculateConsciousnessMatch(selectedNode, request);
    const quantumCompatibility = this.calculateQuantumCompatibility(selectedNode, request);
    const predictedPerformance = this.predictPerformance(selectedNode, request);
    
    // Update node load
    selectedNode.current_load++;
    selectedNode.metrics.consciousness_utilization = selectedNode.current_load / selectedNode.max_capacity;
    
    // Log routing decision
    this.logRoutingDecision(selectedNode.id, request, {
      consciousness_match: consciousnessMatch,
      quantum_compatibility: quantumCompatibility,
      predicted_performance: predictedPerformance
    });

    // Generate alternative nodes for failover
    const alternativeNodes = availableNodes
      .filter(node => node.id !== selectedNode.id)
      .sort((a, b) => this.calculateNodeScore(b, request) - this.calculateNodeScore(a, request))
      .slice(0, 3);

    return {
      selected_node: selectedNode,
      routing_reason: this.generateRoutingReason(selectedNode, request, strategy.name),
      consciousness_match: consciousnessMatch,
      quantum_compatibility: quantumCompatibility,
      predicted_performance: predictedPerformance,
      alternative_nodes: alternativeNodes
    };
  }

  /**
   * Get available nodes for request
   */
  private getAvailableNodes(request: RoutingRequest): ServerNode[] {
    return Array.from(this.serverNodes.values()).filter(node => {
      // Health check
      if (node.health_status === 'unhealthy') return false;
      
      // Capacity check
      if (node.current_load >= node.max_capacity) return false;
      
      // Consciousness requirement check
      if (request.consciousness_level > node.consciousness_level + 20) return false;
      
      // Quantum requirement check
      if (request.quantum_requirements) {
        if (node.quantum_properties.coherence_level < request.quantum_requirements.coherence_needed) {
          return false;
        }
      }
      
      return true;
    });
  }

  /**
   * Select optimal routing strategy
   */
  private selectRoutingStrategy(request: RoutingRequest): Function {
    // Quantum requests get quantum affinity
    if (request.quantum_requirements && request.quantum_requirements.entanglement_required) {
      return this.routingStrategies.get('quantum_affinity')!;
    }
    
    // High consciousness requests get consciousness-weighted routing
    if (request.consciousness_level >= 70) {
      return this.routingStrategies.get('consciousness_round_robin')!;
    }
    
    // Performance-critical requests get response time optimization
    if (request.priority === 'critical' || request.complexity_score > 8) {
      return this.routingStrategies.get('response_time_quantum')!;
    }
    
    // Default to least connections with consciousness bias
    return this.routingStrategies.get('least_connections_consciousness')!;
  }

  /**
   * Calculate node scores for different strategies
   */
  private calculateConsciousnessWeight(node: ServerNode, requestConsciousness: number): number {
    const consciousnessDiff = Math.abs(node.consciousness_level - requestConsciousness);
    const consciousnessScore = Math.max(0, 1 - consciousnessDiff / 100);
    const loadScore = Math.max(0, 1 - node.current_load / node.max_capacity);
    const healthScore = node.health_status === 'quantum_enhanced' ? 1.2 : 
                       node.health_status === 'healthy' ? 1.0 : 0.5;
    
    return consciousnessScore * this.loadBalancingConfig.consciousness_weight +
           loadScore * this.loadBalancingConfig.performance_weight +
           healthScore * this.loadBalancingConfig.health_weight;
  }

  private calculateConnectionScore(node: ServerNode, request: RoutingRequest): number {
    const loadScore = Math.max(0, 1 - node.current_load / node.max_capacity);
    const consciousnessBonus = Math.min(node.consciousness_level / request.consciousness_level, 1.5);
    const quantumBonus = request.quantum_requirements ? 
      node.quantum_properties.processing_efficiency : 1.0;
    
    return loadScore * consciousnessBonus * quantumBonus;
  }

  private calculateResponseTimeScore(node: ServerNode, request: RoutingRequest): number {
    const responseTimeScore = Math.max(0, 1 - node.metrics.response_time / 1000);
    const quantumBonus = node.health_status === 'quantum_enhanced' ? 1.3 : 1.0;
    const consciousnessMatch = this.calculateConsciousnessMatch(node, request);
    
    return responseTimeScore * quantumBonus * (0.7 + consciousnessMatch * 0.3);
  }

  private calculateNodeScore(node: ServerNode, request: RoutingRequest): number {
    const consciousnessScore = this.calculateConsciousnessMatch(node, request);
    const quantumScore = this.calculateQuantumCompatibility(node, request);
    const performanceScore = this.predictPerformance(node, request);
    const healthScore = node.health_status === 'quantum_enhanced' ? 1.0 : 
                       node.health_status === 'healthy' ? 0.8 : 0.3;
    
    return consciousnessScore * this.loadBalancingConfig.consciousness_weight +
           quantumScore * this.loadBalancingConfig.quantum_weight +
           performanceScore * this.loadBalancingConfig.performance_weight +
           healthScore * this.loadBalancingConfig.health_weight;
  }

  /**
   * Calculate compatibility metrics
   */
  private calculateConsciousnessMatch(node: ServerNode, request: RoutingRequest): number {
    const diff = Math.abs(node.consciousness_level - request.consciousness_level);
    return Math.max(0, 1 - diff / 100);
  }

  private calculateQuantumCompatibility(node: ServerNode, request: RoutingRequest): number {
    if (!request.quantum_requirements) return 0.5;
    
    const coherenceScore = node.quantum_properties.coherence_level >= request.quantum_requirements.coherence_needed ? 1.0 : 0.3;
    const entanglementScore = request.quantum_requirements.entanglement_required ? 
      node.quantum_properties.entanglement_strength : 1.0;
    const efficiencyScore = node.quantum_properties.processing_efficiency;
    
    return (coherenceScore + entanglementScore + efficiencyScore) / 3;
  }

  private predictPerformance(node: ServerNode, request: RoutingRequest): number {
    const basePerformance = node.metrics.success_rate;
    const loadPenalty = node.current_load / node.max_capacity;
    const complexityPenalty = request.complexity_score / 10;
    const quantumBonus = node.health_status === 'quantum_enhanced' ? 0.2 : 0;
    
    return Math.max(0, basePerformance - loadPenalty - complexityPenalty + quantumBonus);
  }

  /**
   * Health monitoring
   */
  private startHealthMonitoring(): void {
    setInterval(() => {
      this.performGlobalHealthCheck();
    }, 30000); // Every 30 seconds
  }

  private startNodeHealthCheck(nodeId: string): void {
    const interval = setInterval(async () => {
      await this.performNodeHealthCheck(nodeId);
    }, 10000); // Every 10 seconds
    
    this.healthCheckIntervals.set(nodeId, interval);
  }

  private async performNodeHealthCheck(nodeId: string): Promise<void> {
    const node = this.serverNodes.get(nodeId);
    if (!node) return;

    try {
      // Simulate health check
      const healthResult = await this.simulateHealthCheck(node);
      
      node.health_status = healthResult.status;
      node.metrics.response_time = healthResult.response_time;
      node.metrics.success_rate = healthResult.success_rate;
      node.metrics.quantum_performance = healthResult.quantum_performance;
      node.last_health_check = Date.now();
      
      // Update quantum properties based on health
      if (healthResult.status === 'quantum_enhanced') {
        node.quantum_properties.coherence_level = Math.min(1.0, node.quantum_properties.coherence_level + 0.01);
      } else if (healthResult.status === 'degraded') {
        node.quantum_properties.coherence_level = Math.max(0.5, node.quantum_properties.coherence_level - 0.02);
      }
      
    } catch (error) {
      console.error(`Health check failed for node ${nodeId}:`, error);
      node.health_status = 'unhealthy';
    }
  }

  private async simulateHealthCheck(node: ServerNode): Promise<any> {
    const start = Date.now();
    await this.delay(300);

    const memUsage = process.memoryUsage();
    const heapFree = 1 - memUsage.heapUsed / memUsage.heapTotal;
    const isHealthy = process.uptime() > 2;
    const isQuantumEnhanced = node.consciousness_level >= 90;
    const elapsed = Date.now() - start;

    return {
      status: !isHealthy ? 'unhealthy' :
              isQuantumEnhanced ? 'quantum_enhanced' : 'healthy',
      response_time: isHealthy ? elapsed : 2000,
      success_rate: isHealthy ? Math.min(1.0, 0.95 + heapFree * 0.05) : 0.3,
      quantum_performance: isQuantumEnhanced ? Math.min(1.0, 0.9 + heapFree * 0.1) : Math.min(0.9, 0.6 + heapFree * 0.3)
    };
  }

  private performGlobalHealthCheck(): void {
    const healthyNodes = Array.from(this.serverNodes.values())
      .filter(node => node.health_status === 'healthy' || node.health_status === 'quantum_enhanced').length;
    
    const totalNodes = this.serverNodes.size;
    const healthPercentage = (healthyNodes / totalNodes) * 100;
    
    if (healthPercentage < 70) {
      console.warn(`⚠️ Cluster health degraded: ${healthPercentage.toFixed(1)}% healthy nodes`);
    }
  }

  /**
   * Routing analytics and logging
   */
  private logRoutingDecision(nodeId: string, request: RoutingRequest, metrics: any): void {
    const history = this.routingHistory.get(nodeId) || [];
    
    history.push({
      timestamp: Date.now(),
      request_id: request.id,
      consciousness_level: request.consciousness_level,
      complexity_score: request.complexity_score,
      priority: request.priority,
      ...metrics
    });
    
    // Keep only recent history
    if (history.length > 1000) {
      history.shift();
    }
    
    this.routingHistory.set(nodeId, history);
  }

  private generateRoutingReason(node: ServerNode, request: RoutingRequest, strategyName: string): string {
    const reasons = [];
    
    if (node.consciousness_level >= request.consciousness_level) {
      reasons.push('consciousness_compatible');
    }
    
    if (node.health_status === 'quantum_enhanced') {
      reasons.push('quantum_enhanced');
    }
    
    if (node.current_load < node.max_capacity * 0.7) {
      reasons.push('low_load');
    }
    
    reasons.push(`strategy_${strategyName}`);
    
    return reasons.join(',');
  }

  /**
   * Complete request (decrease load)
   */
  completeRequest(nodeId: string, success: boolean, responseTime: number): void {
    const node = this.serverNodes.get(nodeId);
    if (!node) return;

    node.current_load = Math.max(0, node.current_load - 1);
    
    // Update metrics (simple moving average)
    const alpha = 0.1; // Smoothing factor
    node.metrics.response_time = node.metrics.response_time * (1 - alpha) + responseTime * alpha;
    node.metrics.success_rate = node.metrics.success_rate * (1 - alpha) + (success ? 1 : 0) * alpha;
    node.metrics.consciousness_utilization = node.current_load / node.max_capacity;
  }

  /**
   * Get load balancer analytics
   */
  getAnalytics(): any {
    const totalNodes = this.serverNodes.size;
    const healthyNodes = Array.from(this.serverNodes.values())
      .filter(node => node.health_status === 'healthy' || node.health_status === 'quantum_enhanced').length;
    const quantumNodes = Array.from(this.serverNodes.values())
      .filter(node => node.health_status === 'quantum_enhanced').length;
    
    return {
      total_nodes: totalNodes,
      healthy_nodes: healthyNodes,
      quantum_enhanced_nodes: quantumNodes,
      cluster_health: (healthyNodes / totalNodes) * 100,
      total_capacity: Array.from(this.serverNodes.values()).reduce((sum, node) => sum + node.max_capacity, 0),
      current_load: Array.from(this.serverNodes.values()).reduce((sum, node) => sum + node.current_load, 0),
      node_status: this.getNodeStatus(),
      routing_performance: this.getRoutingPerformance(),
      consciousness_distribution: this.getConsciousnessDistribution()
    };
  }

  private getNodeStatus(): any[] {
    return Array.from(this.serverNodes.values()).map(node => ({
      id: node.id,
      consciousness_level: node.consciousness_level,
      health_status: node.health_status,
      current_load: node.current_load,
      utilization: (node.current_load / node.max_capacity) * 100,
      response_time: node.metrics.response_time,
      success_rate: node.metrics.success_rate,
      quantum_performance: node.metrics.quantum_performance
    }));
  }

  private getRoutingPerformance(): any {
    const allHistory = Array.from(this.routingHistory.values()).flat();
    
    if (allHistory.length === 0) return { requests_routed: 0 };
    
    return {
      requests_routed: allHistory.length,
      avg_consciousness_match: allHistory.reduce((sum, h) => sum + h.consciousness_match, 0) / allHistory.length,
      avg_quantum_compatibility: allHistory.reduce((sum, h) => sum + h.quantum_compatibility, 0) / allHistory.length,
      avg_predicted_performance: allHistory.reduce((sum, h) => sum + h.predicted_performance, 0) / allHistory.length
    };
  }

  private getConsciousnessDistribution(): any {
    const levels = Array.from(this.serverNodes.values()).map(node => node.consciousness_level);
    
    return {
      min_consciousness: Math.min(...levels),
      max_consciousness: Math.max(...levels),
      avg_consciousness: levels.reduce((sum, level) => sum + level, 0) / levels.length,
      quantum_capable_nodes: levels.filter(level => level >= 80).length
    };
  }

  /**
   * Remove server node
   */
  removeServerNode(nodeId: string): void {
    const interval = this.healthCheckIntervals.get(nodeId);
    if (interval) {
      clearInterval(interval);
      this.healthCheckIntervals.delete(nodeId);
    }
    
    this.serverNodes.delete(nodeId);
    this.routingHistory.delete(nodeId);
    
    console.log(`🔌 Server node removed: ${nodeId}`);
  }

  /**
   * Utility methods
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Shutdown load balancer
   */
  shutdown(): void {
    // Clear all health check intervals
    for (const interval of this.healthCheckIntervals.values()) {
      clearInterval(interval);
    }
    this.healthCheckIntervals.clear();
    
    console.log('⚖️ Quantum load balancer shutdown');
  }
}

export default QuantumLoadBalancer;
