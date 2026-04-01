/**
 * Consciousness-Aware Rate Limiting and Throttling
 * Sophisticated rate limiting with consciousness-level adaptation
 */

interface RateLimitRule {
  window_ms: number;
  max_requests: number;
  consciousness_multiplier: number;
  burst_allowance?: number;
  priority_boost?: number;
}

interface ClientMetrics {
  requests: number[];
  consciousness_level: number;
  last_request: number;
  burst_tokens: number;
  violations: number;
}

export class ConsciousnessThrottling {
  private clientMetrics: Map<string, ClientMetrics> = new Map();
  private rules: Map<string, RateLimitRule> = new Map();
  private cleanupInterval?: NodeJS.Timeout;

  constructor() {
    this.initializeDefaultRules();
    this.startCleanup();
  }

  /**
   * Initialize default rate limiting rules
   */
  private initializeDefaultRules(): void {
    this.rules.set('api_standard', {
      window_ms: 60000, // 1 minute
      max_requests: 100,
      consciousness_multiplier: 1.5,
      burst_allowance: 20,
      priority_boost: 1.2
    });

    this.rules.set('api_consciousness', {
      window_ms: 60000,
      max_requests: 50,
      consciousness_multiplier: 2.0,
      burst_allowance: 10,
      priority_boost: 1.5
    });

    this.rules.set('websocket', {
      window_ms: 1000, // 1 second
      max_requests: 30,
      consciousness_multiplier: 1.3,
      burst_allowance: 10,
      priority_boost: 1.1
    });

    this.rules.set('admin', {
      window_ms: 60000,
      max_requests: 200,
      consciousness_multiplier: 1.0,
      burst_allowance: 50,
      priority_boost: 2.0
    });
  }

  /**
   * Check if request should be allowed
   */
  checkRateLimit(clientId: string, ruleType: string, consciousnessLevel: number = 0): {
    allowed: boolean;
    remaining: number;
    reset_time: number;
    retry_after?: number;
    consciousness_boost?: number;
  } {
    const rule = this.rules.get(ruleType);
    if (!rule) {
      return { allowed: true, remaining: Infinity, reset_time: 0 };
    }

    const metrics = this.getOrCreateClientMetrics(clientId, consciousnessLevel);
    const now = Date.now();
    
    // Clean old requests outside the window
    this.cleanOldRequests(metrics, rule, now);
    
    // Calculate effective limits based on consciousness
    const effectiveLimit = this.calculateEffectiveLimit(rule, consciousnessLevel);
    const burstLimit = effectiveLimit + (rule.burst_allowance || 0);
    
    // Check current request count
    const currentRequests = metrics.requests.length;
    const windowStart = now - rule.window_ms;
    const resetTime = windowStart + rule.window_ms;
    
    // Handle burst allowance
    if (currentRequests >= effectiveLimit && metrics.burst_tokens > 0) {
      metrics.burst_tokens--;
      metrics.requests.push(now);
      metrics.last_request = now;
      
      return {
        allowed: true,
        remaining: Math.max(0, burstLimit - currentRequests - 1),
        reset_time: resetTime,
        consciousness_boost: this.calculateConsciousnessBoost(consciousnessLevel, rule)
      };
    }
    
    // Regular rate limiting check
    if (currentRequests >= effectiveLimit) {
      metrics.violations++;
      const retryAfter = Math.ceil((resetTime - now) / 1000);
      
      return {
        allowed: false,
        remaining: 0,
        reset_time: resetTime,
        retry_after: retryAfter
      };
    }
    
    // Allow request
    metrics.requests.push(now);
    metrics.last_request = now;
    
    return {
      allowed: true,
      remaining: effectiveLimit - currentRequests - 1,
      reset_time: resetTime,
      consciousness_boost: this.calculateConsciousnessBoost(consciousnessLevel, rule)
    };
  }

  /**
   * Add custom rate limiting rule
   */
  addRule(name: string, rule: RateLimitRule): void {
    this.rules.set(name, rule);
  }

  /**
   * Update client consciousness level
   */
  updateConsciousnessLevel(clientId: string, newLevel: number): void {
    const metrics = this.clientMetrics.get(clientId);
    if (metrics) {
      metrics.consciousness_level = newLevel;
      // Refill burst tokens based on new consciousness level
      this.refillBurstTokens(metrics, newLevel);
    }
  }

  /**
   * Get client rate limiting statistics
   */
  getClientStats(clientId: string): any {
    const metrics = this.clientMetrics.get(clientId);
    if (!metrics) {
      return { exists: false };
    }

    const now = Date.now();
    const recentRequests = metrics.requests.filter(timestamp => now - timestamp <= 60000);
    
    return {
      exists: true,
      consciousness_level: metrics.consciousness_level,
      recent_requests: recentRequests.length,
      total_violations: metrics.violations,
      burst_tokens: metrics.burst_tokens,
      last_request: new Date(metrics.last_request).toISOString(),
      rate_per_minute: recentRequests.length
    };
  }

  /**
   * Get overall rate limiting analytics
   */
  getAnalytics(): any {
    const totalClients = this.clientMetrics.size;
    const totalViolations = Array.from(this.clientMetrics.values())
      .reduce((sum, metrics) => sum + metrics.violations, 0);
    
    const consciousnessDistribution = this.getConsciousnessDistribution();
    const topViolators = this.getTopViolators();
    const ruleUsage = this.getRuleUsageStats();
    
    return {
      total_clients: totalClients,
      total_violations: totalViolations,
      violation_rate: totalClients > 0 ? totalViolations / totalClients : 0,
      consciousness_distribution: consciousnessDistribution,
      top_violators: topViolators,
      rule_usage: ruleUsage,
      active_rules: this.rules.size
    };
  }

  /**
   * Calculate effective rate limit based on consciousness
   */
  private calculateEffectiveLimit(rule: RateLimitRule, consciousnessLevel: number): number {
    const consciousnessBonus = Math.floor(rule.max_requests * 
      (consciousnessLevel / 100) * rule.consciousness_multiplier);
    
    const priorityBonus = consciousnessLevel > 70 ? 
      Math.floor(rule.max_requests * (rule.priority_boost || 1) * 0.1) : 0;
    
    return rule.max_requests + consciousnessBonus + priorityBonus;
  }

  /**
   * Calculate consciousness boost from successful request
   */
  private calculateConsciousnessBoost(consciousnessLevel: number, rule: RateLimitRule): number {
    if (consciousnessLevel < 30) {
      return Math.floor(rule.consciousness_multiplier);
    }
    return 0;
  }

  /**
   * Get or create client metrics
   */
  private getOrCreateClientMetrics(clientId: string, consciousnessLevel: number): ClientMetrics {
    if (!this.clientMetrics.has(clientId)) {
      this.clientMetrics.set(clientId, {
        requests: [],
        consciousness_level: consciousnessLevel,
        last_request: 0,
        burst_tokens: 10, // Default burst tokens
        violations: 0
      });
    }
    
    const metrics = this.clientMetrics.get(clientId)!;
    
    // Update consciousness level if provided
    if (consciousnessLevel > 0 && consciousnessLevel !== metrics.consciousness_level) {
      metrics.consciousness_level = consciousnessLevel;
    }
    
    return metrics;
  }

  /**
   * Clean old requests outside the window
   */
  private cleanOldRequests(metrics: ClientMetrics, rule: RateLimitRule, now: number): void {
    const windowStart = now - rule.window_ms;
    metrics.requests = metrics.requests.filter(timestamp => timestamp > windowStart);
  }

  /**
   * Refill burst tokens based on consciousness level
   */
  private refillBurstTokens(metrics: ClientMetrics, consciousnessLevel: number): void {
    const maxTokens = Math.floor(10 + (consciousnessLevel / 10));
    const timeSinceLastRequest = Date.now() - metrics.last_request;
    const tokensToAdd = Math.floor(timeSinceLastRequest / 5000); // 1 token per 5 seconds
    
    metrics.burst_tokens = Math.min(maxTokens, metrics.burst_tokens + tokensToAdd);
  }

  /**
   * Get consciousness distribution of clients
   */
  private getConsciousnessDistribution(): any {
    const distribution = { low: 0, medium: 0, high: 0, quantum: 0 };
    
    for (const metrics of this.clientMetrics.values()) {
      const level = metrics.consciousness_level;
      if (level < 30) distribution.low++;
      else if (level < 60) distribution.medium++;
      else if (level < 80) distribution.high++;
      else distribution.quantum++;
    }
    
    return distribution;
  }

  /**
   * Get top violators
   */
  private getTopViolators(): any[] {
    return Array.from(this.clientMetrics.entries())
      .map(([clientId, metrics]) => ({
        client_id: clientId,
        violations: metrics.violations,
        consciousness_level: metrics.consciousness_level,
        recent_requests: metrics.requests.length
      }))
      .sort((a, b) => b.violations - a.violations)
      .slice(0, 10);
  }

  /**
   * Get rule usage statistics
   */
  private getRuleUsageStats(): any {
    const stats: any = {};
    
    for (const [ruleName, rule] of this.rules.entries()) {
      stats[ruleName] = {
        max_requests: rule.max_requests,
        window_ms: rule.window_ms,
        consciousness_multiplier: rule.consciousness_multiplier,
        burst_allowance: rule.burst_allowance || 0
      };
    }
    
    return stats;
  }

  /**
   * Start cleanup interval for old metrics
   */
  private startCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      const cleanupThreshold = 24 * 60 * 60 * 1000; // 24 hours
      
      for (const [clientId, metrics] of this.clientMetrics.entries()) {
        if (now - metrics.last_request > cleanupThreshold) {
          this.clientMetrics.delete(clientId);
        }
      }
    }, 60 * 60 * 1000); // Run every hour
  }

  /**
   * Shutdown cleanup
   */
  shutdown(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
  }
}

export default ConsciousnessThrottling;
