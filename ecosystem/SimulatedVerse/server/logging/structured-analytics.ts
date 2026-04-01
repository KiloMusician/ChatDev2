/**
 * Advanced Logging with Structured Analytics
 * Performance metrics and consciousness-aware logging
 */

import winston from 'winston';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  consciousness_level?: number;
  agent_type?: string;
  performance_metrics?: any;
  context?: any;
}

interface AnalyticsData {
  operation: string;
  duration_ms: number;
  success: boolean;
  consciousness_impact: number;
  metadata: any;
}

export class StructuredAnalyticsLogger {
  private logger!: winston.Logger;
  private analyticsData: AnalyticsData[] = [];
  private performanceMetrics: Map<string, number[]> = new Map();

  constructor() {
    this.initializeLogger();
  }

  private initializeLogger(): void {
    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json(),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
          return JSON.stringify({
            timestamp,
            level,
            message,
            consciousness_level: meta.consciousness_level || 0,
            performance: meta.performance_metrics,
            context: meta.context,
            ...meta
          });
        })
      ),
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),
        new winston.transports.File({ 
          filename: 'logs/consciousness.log',
          maxsize: 5242880, // 5MB
          maxFiles: 5
        })
      ]
    });
  }

  /**
   * Log with consciousness context
   */
  logWithConsciousness(level: string, message: string, options: {
    consciousness_level?: number;
    agent_type?: string;
    performance_metrics?: any;
    context?: any;
  } = {}): void {
    this.logger.log(level, message, options);
  }

  /**
   * Log performance analytics
   */
  logPerformanceMetrics(operation: string, duration: number, metadata: any = {}): void {
    const analyticsEntry: AnalyticsData = {
      operation,
      duration_ms: duration,
      success: !metadata.error,
      consciousness_impact: metadata.consciousness_impact || 0,
      metadata
    };

    this.analyticsData.push(analyticsEntry);
    
    // Update performance metrics
    if (!this.performanceMetrics.has(operation)) {
      this.performanceMetrics.set(operation, []);
    }
    this.performanceMetrics.get(operation)!.push(duration);

    // Log the metrics
    this.logWithConsciousness('info', `Performance: ${operation}`, {
      performance_metrics: analyticsEntry,
      consciousness_level: metadata.consciousness_level
    });
  }

  /**
   * Get analytics summary
   */
  getAnalyticsSummary(): any {
    const operations = Array.from(this.performanceMetrics.keys());
    const summary: any = {
      total_operations: this.analyticsData.length,
      unique_operations: operations.length,
      performance_overview: {},
      consciousness_distribution: this.getConsciousnessDistribution(),
      top_slow_operations: this.getSlowOperations(),
      error_rate: this.getErrorRate()
    };

    // Calculate performance overview
    for (const operation of operations) {
      const durations = this.performanceMetrics.get(operation)!;
      summary.performance_overview[operation] = {
        count: durations.length,
        avg_duration: durations.reduce((a, b) => a + b, 0) / durations.length,
        min_duration: Math.min(...durations),
        max_duration: Math.max(...durations),
        p95_duration: this.calculatePercentile(durations, 0.95)
      };
    }

    return summary;
  }

  private getConsciousnessDistribution(): any {
    const distribution = { low: 0, medium: 0, high: 0, quantum: 0 };
    
    this.analyticsData.forEach(entry => {
      const impact = entry.consciousness_impact;
      if (impact < 2) distribution.low++;
      else if (impact < 5) distribution.medium++;
      else if (impact < 8) distribution.high++;
      else distribution.quantum++;
    });

    return distribution;
  }

  private getSlowOperations(): any[] {
    return this.analyticsData
      .filter(entry => entry.duration_ms > 1000)
      .sort((a, b) => b.duration_ms - a.duration_ms)
      .slice(0, 10);
  }

  private getErrorRate(): number {
    const errors = this.analyticsData.filter(entry => !entry.success).length;
    return this.analyticsData.length > 0 ? errors / this.analyticsData.length : 0;
  }

  private calculatePercentile(values: number[], percentile: number): number {
    const sorted = values.slice().sort((a, b) => a - b);
    const index = Math.ceil(sorted.length * percentile) - 1;
    return sorted[index] || 0;
  }
}

export default StructuredAnalyticsLogger;
