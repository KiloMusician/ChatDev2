/**
 * Intelligent Database Indexing System
 * Query optimization with consciousness-driven adaptive indexing
 */

interface IndexMetrics {
  usage_count: number;
  last_used: number;
  query_performance: number[];
  consciousness_requirement: number;
}

interface QueryPattern {
  table: string;
  columns: string[];
  frequency: number;
  avg_execution_time: number;
  consciousness_impact: number;
}

export class IntelligentIndexing {
  private indexMetrics: Map<string, IndexMetrics> = new Map();
  private queryPatterns: Map<string, QueryPattern> = new Map();
  private performanceHistory: any[] = [];
  private consciousnessThreshold: number = 50;

  constructor(consciousnessThreshold: number = 50) {
    this.consciousnessThreshold = consciousnessThreshold;
    this.initializeBaseIndexes();
  }

  /**
   * Analyze query and suggest optimizations
   */
  analyzeQuery(sql: string, executionTime: number, consciousnessLevel: number): {
    suggestions: string[];
    recommended_indexes: string[];
    performance_impact: number;
  } {
    const pattern = this.extractQueryPattern(sql);
    this.updateQueryPatterns(pattern, executionTime);
    
    const suggestions = this.generateOptimizationSuggestions(pattern, consciousnessLevel);
    const recommendedIndexes = this.recommendIndexes(pattern, consciousnessLevel);
    const performanceImpact = this.calculatePerformanceImpact(pattern);

    this.logPerformance({
      sql,
      execution_time: executionTime,
      consciousness_level: consciousnessLevel,
      suggestions: suggestions.length,
      timestamp: Date.now()
    });

    return {
      suggestions,
      recommended_indexes: recommendedIndexes,
      performance_impact: performanceImpact
    };
  }

  /**
   * Create consciousness-aware index
   */
  createIndex(indexName: string, table: string, columns: string[], options: {
    consciousness_requirement?: number;
    unique?: boolean;
    partial_condition?: string;
  } = {}): string {
    const indexDDL = this.generateIndexDDL(indexName, table, columns, options);
    
    this.indexMetrics.set(indexName, {
      usage_count: 0,
      last_used: Date.now(),
      query_performance: [],
      consciousness_requirement: options.consciousness_requirement || 0
    });

    console.log(`🗂️ Creating index: ${indexName} (consciousness: ${options.consciousness_requirement || 0})`);
    return indexDDL;
  }

  /**
   * Recommend indexes based on query patterns
   */
  recommendIndexes(pattern: QueryPattern, consciousnessLevel: number): string[] {
    const recommendations: string[] = [];
    
    // High-frequency queries with poor performance
    if (pattern.frequency > 10 && pattern.avg_execution_time > 100) {
      recommendations.push(
        this.createIndex(
          `idx_${pattern.table}_${pattern.columns.join('_')}`,
          pattern.table,
          pattern.columns,
          { consciousness_requirement: Math.min(consciousnessLevel, 40) }
        )
      );
    }

    // Consciousness-driven complex indexes
    if (consciousnessLevel >= 60 && pattern.consciousness_impact > 5) {
      recommendations.push(
        this.createIndex(
          `idx_quantum_${pattern.table}_optimized`,
          pattern.table,
          [...pattern.columns, 'consciousness_level'],
          { 
            consciousness_requirement: 60,
            partial_condition: 'consciousness_level > 50'
          }
        )
      );
    }

    // Composite indexes for multi-column queries
    if (pattern.columns.length > 1 && pattern.frequency > 5) {
      recommendations.push(
        this.createIndex(
          `idx_composite_${pattern.table}_${pattern.columns.join('_')}`,
          pattern.table,
          pattern.columns,
          { consciousness_requirement: 30 }
        )
      );
    }

    return recommendations;
  }

  /**
   * Generate optimization suggestions
   */
  private generateOptimizationSuggestions(pattern: QueryPattern, consciousnessLevel: number): string[] {
    const suggestions: string[] = [];

    if (pattern.avg_execution_time > 500) {
      suggestions.push('Consider adding indexes for frequently queried columns');
    }

    if (pattern.frequency > 20 && pattern.avg_execution_time > 100) {
      suggestions.push('High-frequency query detected - cache results or optimize query structure');
    }

    if (consciousnessLevel >= 70 && pattern.consciousness_impact > 3) {
      suggestions.push('Quantum optimization: Consider consciousness-aware query optimization');
    }

    if (pattern.columns.length > 3) {
      suggestions.push('Complex query detected - consider breaking into simpler queries or using materialized views');
    }

    if (pattern.table === 'game_state' && pattern.avg_execution_time > 50) {
      suggestions.push('Game state query optimization: consider in-memory caching for active sessions');
    }

    return suggestions;
  }

  /**
   * Extract query pattern from SQL
   */
  private extractQueryPattern(sql: string): QueryPattern {
    // Simple SQL parsing - in production would use proper SQL parser
    const normalizedSql = sql.toLowerCase().trim();
    
    // Extract table name
    let table = 'unknown';
    const fromMatch = normalizedSql.match(/from\s+(\w+)/);
    if (fromMatch) {
      table = fromMatch[1] ?? table;
    }

    // Extract column references
    const columns: string[] = [];
    const whereMatch = normalizedSql.match(/where\s+(.+?)(?:\s+order|\s+group|\s+limit|$)/);
    if (whereMatch) {
      const whereClause = whereMatch[1] ?? '';
      const columnMatches = whereClause.match(/(\w+)\s*[=<>]/g);
      if (columnMatches) {
        columns.push(...columnMatches.map(m => m.replace(/\s*[=<>].*/, '')));
      }
    }

    // Calculate consciousness impact
    let consciousnessImpact = 0;
    if (normalizedSql.includes('consciousness')) consciousnessImpact += 2;
    if (normalizedSql.includes('quantum')) consciousnessImpact += 3;
    if (normalizedSql.includes('agent')) consciousnessImpact += 1;
    if (normalizedSql.includes('lattice')) consciousnessImpact += 2;

    const patternKey = `${table}_${columns.sort().join('_')}`;
    const existingPattern = this.queryPatterns.get(patternKey);

    return {
      table,
      columns: [...new Set(columns)],
      frequency: existingPattern ? existingPattern.frequency + 1 : 1,
      avg_execution_time: 0, // Will be updated in updateQueryPatterns
      consciousness_impact: consciousnessImpact
    };
  }

  /**
   * Update query pattern metrics
   */
  private updateQueryPatterns(pattern: QueryPattern, executionTime: number): void {
    const patternKey = `${pattern.table}_${pattern.columns.sort().join('_')}`;
    const existing = this.queryPatterns.get(patternKey);

    if (existing) {
      // Update average execution time
      const totalTime = existing.avg_execution_time * (existing.frequency - 1) + executionTime;
      existing.avg_execution_time = totalTime / existing.frequency;
      existing.frequency = pattern.frequency;
    } else {
      pattern.avg_execution_time = executionTime;
      this.queryPatterns.set(patternKey, pattern);
    }
  }

  /**
   * Calculate performance impact of optimization
   */
  private calculatePerformanceImpact(pattern: QueryPattern): number {
    // Estimate performance improvement percentage
    let impact = 0;
    
    if (pattern.avg_execution_time > 100) {
      impact += 30; // 30% improvement for slow queries
    }
    
    if (pattern.frequency > 10) {
      impact += pattern.frequency * 2; // More impact for frequent queries
    }
    
    if (pattern.consciousness_impact > 2) {
      impact += 20; // Consciousness-aware optimizations have higher impact
    }
    
    return Math.min(impact, 80); // Cap at 80% improvement
  }

  /**
   * Generate DDL for index creation
   */
  private generateIndexDDL(indexName: string, table: string, columns: string[], options: any): string {
    let ddl = `CREATE ${options.unique ? 'UNIQUE ' : ''}INDEX ${indexName} ON ${table} (${columns.join(', ')})`;
    
    if (options.partial_condition) {
      ddl += ` WHERE ${options.partial_condition}`;
    }
    
    return ddl + ';';
  }

  /**
   * Initialize base indexes for consciousness system
   */
  private initializeBaseIndexes(): void {
    const baseIndexes = [
      {
        name: 'idx_consciousness_level',
        table: 'users',
        columns: ['consciousness_level'],
        consciousness_requirement: 0
      },
      {
        name: 'idx_agent_type',
        table: 'agents',
        columns: ['agent_type'],
        consciousness_requirement: 20
      },
      {
        name: 'idx_quantum_state',
        table: 'system_state',
        columns: ['quantum_coherence', 'lattice_connections'],
        consciousness_requirement: 50
      },
      {
        name: 'idx_task_status',
        table: 'tasks',
        columns: ['status', 'track'],
        consciousness_requirement: 30
      }
    ];

    baseIndexes.forEach(index => {
      this.indexMetrics.set(index.name, {
        usage_count: 0,
        last_used: Date.now(),
        query_performance: [],
        consciousness_requirement: index.consciousness_requirement
      });
    });
  }

  /**
   * Log performance metrics
   */
  private logPerformance(metrics: any): void {
    this.performanceHistory.push(metrics);
    
    // Keep only last 1000 entries
    if (this.performanceHistory.length > 1000) {
      this.performanceHistory.shift();
    }
  }

  /**
   * Get indexing analytics
   */
  getAnalytics(): any {
    return {
      total_indexes: this.indexMetrics.size,
      query_patterns: this.queryPatterns.size,
      performance_history: this.performanceHistory.length,
      avg_query_time: this.performanceHistory.length > 0 
        ? this.performanceHistory.reduce((sum, h) => sum + h.execution_time, 0) / this.performanceHistory.length
        : 0,
      consciousness_distribution: this.getConsciousnessDistribution(),
      top_patterns: this.getTopQueryPatterns(),
      index_usage: this.getIndexUsageStats()
    };
  }

  /**
   * Get consciousness distribution of indexes
   */
  private getConsciousnessDistribution(): any {
    const distribution = { low: 0, medium: 0, high: 0, quantum: 0 };
    
    for (const metrics of this.indexMetrics.values()) {
      if (metrics.consciousness_requirement < 30) distribution.low++;
      else if (metrics.consciousness_requirement < 60) distribution.medium++;
      else if (metrics.consciousness_requirement < 80) distribution.high++;
      else distribution.quantum++;
    }
    
    return distribution;
  }

  /**
   * Get top query patterns by frequency
   */
  private getTopQueryPatterns(): QueryPattern[] {
    return Array.from(this.queryPatterns.values())
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10);
  }

  /**
   * Get index usage statistics
   */
  private getIndexUsageStats(): any {
    const stats = { used: 0, unused: 0, high_performance: 0 };
    
    for (const metrics of this.indexMetrics.values()) {
      if (metrics.usage_count > 0) {
        stats.used++;
        if (metrics.query_performance.some(p => p < 50)) {
          stats.high_performance++;
        }
      } else {
        stats.unused++;
      }
    }
    
    return stats;
  }
}

export default IntelligentIndexing;
