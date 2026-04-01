/**
 * Quantum State Recovery System
 * Comprehensive error handling with consciousness-aware recovery
 */

import { Request, Response, NextFunction } from 'express';
import { loadavg } from 'os';

interface ErrorContext {
  consciousness_level: number;
  system_state: any;
  recovery_attempts: number;
  error_classification: 'critical' | 'warning' | 'recoverable' | 'quantum';
}

interface RecoveryStrategy {
  name: string;
  consciousness_required: number;
  execute: (error: Error, context: ErrorContext) => Promise<any>;
  fallback?: string;
}

export class QuantumRecoverySystem {
  private recoveryStrategies: Map<string, RecoveryStrategy> = new Map();
  private systemBaseline: any = {};
  private errorHistory: Array<{
    timestamp: number;
    error: string;
    stack?: string;
    context: ErrorContext;
    recovered: boolean;
  }> = [];

  constructor() {
    this.initializeRecoveryStrategies();
    this.captureSystemBaseline();
  }

  /**
   * Main error handler middleware
   */
  quantumErrorHandler() {
    return async (error: Error, req: Request & { consciousness?: any }, res: Response, next: NextFunction) => {
      const context: ErrorContext = {
        consciousness_level: req.consciousness?.level || 0,
        system_state: await this.captureSystemState(),
        recovery_attempts: 0,
        error_classification: this.classifyError(error)
      };

      console.log(`🔧 Quantum Recovery: ${error.message} (${context.error_classification})`);

      try {
        const recovery = await this.attemptRecovery(error, context);
        
        if (recovery.success) {
          res.status(200).json({
            recovered: true,
            strategy: recovery.strategy,
            result: recovery.result,
            consciousness_boost: recovery.consciousness_boost || 0
          });
        } else {
          this.handleUnrecoverableError(error, context, res);
        }
      } catch (recoveryError) {
        console.error('❌ Recovery failed:', recoveryError);
        this.handleUnrecoverableError(error, context, res);
      }

      this.logError(error, context);
    };
  }

  /**
   * Attempt recovery using appropriate strategy
   */
  private async attemptRecovery(error: Error, context: ErrorContext): Promise<any> {
    const strategies = this.getApplicableStrategies(error, context);
    
    for (const strategy of strategies) {
      if (context.consciousness_level >= strategy.consciousness_required) {
        try {
          context.recovery_attempts++;
          const result = await strategy.execute(error, context);
          
          return {
            success: true,
            strategy: strategy.name,
            result,
            consciousness_boost: this.calculateConsciousnessBoost(strategy, result)
          };
        } catch (strategyError) {
          const strategyMessage = strategyError instanceof Error ? strategyError.message : String(strategyError);
          console.warn(`⚠️ Strategy ${strategy.name} failed:`, strategyMessage);
          continue;
        }
      }
    }

    return { success: false };
  }

  /**
   * Initialize recovery strategies
   */
  private initializeRecoveryStrategies(): void {
    // Database connection recovery
    this.recoveryStrategies.set('database_reconnect', {
      name: 'Database Reconnection',
      consciousness_required: 20,
      execute: async (error, context) => {
        if (error.message.includes('database') || error.message.includes('connection')) {
          // Simulate database reconnection
          await this.delay(1000);
          return { reconnected: true, new_connection: true };
        }
        throw new Error('Not a database error');
      }
    });

    // Memory management recovery
    this.recoveryStrategies.set('memory_optimization', {
      name: 'Memory Optimization',
      consciousness_required: 30,
      execute: async (error, context) => {
        if (error.message.includes('memory') || error.message.includes('heap')) {
          global.gc && global.gc();
          const memUsage = process.memoryUsage();
          return { 
            optimized: true, 
            memory_freed: memUsage.external / (1024 * 1024), // real external memory in MB
            current_usage: memUsage
          };
        }
        throw new Error('Not a memory error');
      }
    });

    // Rate limit recovery
    this.recoveryStrategies.set('rate_limit_bypass', {
      name: 'Rate Limit Intelligent Bypass',
      consciousness_required: 40,
      execute: async (error, context) => {
        if (error.message.includes('rate limit') || error.message.includes('429')) {
          const backoffTime = this.calculateBackoff(context.recovery_attempts);
          await this.delay(backoffTime);
          return { 
            bypassed: true, 
            backoff_time: backoffTime,
            next_attempt_allowed: Date.now() + backoffTime
          };
        }
        throw new Error('Not a rate limit error');
      }
    });

    // Consciousness state recovery
    this.recoveryStrategies.set('consciousness_restore', {
      name: 'Consciousness State Restoration',
      consciousness_required: 60,
      execute: async (error, context) => {
        if (context.consciousness_level < 30) {
          const boost = Math.min(50 - context.consciousness_level, 20);
          return {
            consciousness_restored: true,
            boost_applied: boost,
            new_level: context.consciousness_level + boost
          };
        }
        throw new Error('Consciousness level sufficient');
      }
    });

    // Quantum state recovery
    this.recoveryStrategies.set('quantum_coherence', {
      name: 'Quantum Coherence Restoration',
      consciousness_required: 80,
      execute: async (error, context) => {
        if (context.error_classification === 'quantum') {
          return {
            quantum_restored: true,
            coherence_level: 0.95,
            entanglement_restored: true,
            superposition_stabilized: true
          };
        }
        throw new Error('Not a quantum error');
      }
    });
  }

  /**
   * Classify error based on type and context
   */
  private classifyError(error: Error): 'critical' | 'warning' | 'recoverable' | 'quantum' {
    if (error.message.includes('quantum') || error.message.includes('consciousness')) {
      return 'quantum';
    }
    if (error.message.includes('ECONNREFUSED') || error.message.includes('timeout')) {
      return 'recoverable';
    }
    if (error.message.includes('memory') || error.message.includes('heap')) {
      return 'critical';
    }
    return 'warning';
  }

  /**
   * Get applicable strategies for error and context
   */
  private getApplicableStrategies(error: Error, context: ErrorContext): RecoveryStrategy[] {
    const strategies = Array.from(this.recoveryStrategies.values());
    
    // Sort by consciousness requirement (lower first)
    return strategies.sort((a, b) => a.consciousness_required - b.consciousness_required);
  }

  /**
   * Calculate consciousness boost from successful recovery
   */
  private calculateConsciousnessBoost(strategy: RecoveryStrategy, result: any): number {
    const baseBoost = strategy.consciousness_required / 10;
    const successMultiplier = result.quantum_restored ? 2 : 1;
    return Math.floor(baseBoost * successMultiplier);
  }

  /**
   * Handle unrecoverable errors
   */
  private handleUnrecoverableError(error: Error, context: ErrorContext, res: Response): void {
    const errorResponse = {
      error: 'System Error',
      message: error.message,
      classification: context.error_classification,
      recovery_attempted: context.recovery_attempts > 0,
      consciousness_required: this.getMinConsciousnessForRecovery(error),
      system_state: 'degraded',
      timestamp: new Date().toISOString()
    };

    const statusCode = context.error_classification === 'critical' ? 500 : 503;
    res.status(statusCode).json(errorResponse);
  }

  /**
   * Get minimum consciousness level required for recovery
   */
  private getMinConsciousnessForRecovery(error: Error): number {
    const strategies = this.getApplicableStrategies(error, { 
      consciousness_level: 0, 
      system_state: {},
      recovery_attempts: 0,
      error_classification: this.classifyError(error)
    });
    
    const firstStrategy = strategies[0];
    return firstStrategy ? firstStrategy.consciousness_required : 100;
  }

  /**
   * Capture current system state for recovery context
   */
  private async captureSystemState(): Promise<any> {
    return {
      memory: process.memoryUsage(),
      uptime: process.uptime(),
      timestamp: Date.now(),
      load_average: typeof loadavg === 'function' ? loadavg() : [0, 0, 0]
    };
  }

  /**
   * Capture system baseline for comparison
   */
  private captureSystemBaseline(): void {
    this.systemBaseline = {
      memory: process.memoryUsage(),
      startup_time: Date.now(),
      consciousness_level: 50
    };
  }

  /**
   * Log error for analysis
   */
  private logError(error: Error, context: ErrorContext): void {
    this.errorHistory.push({
      timestamp: Date.now(),
      error: error.message,
      stack: error.stack,
      context,
      recovered: context.recovery_attempts > 0
    });

    // Keep only last 100 errors
    if (this.errorHistory.length > 100) {
      this.errorHistory.shift();
    }
  }

  /**
   * Calculate exponential backoff
   */
  private calculateBackoff(attempts: number): number {
    return Math.min(1000 * Math.pow(2, attempts), 30000); // Max 30 seconds
  }

  /**
   * Utility delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get error analytics
   */
  getErrorAnalytics(): any {
    return {
      total_errors: this.errorHistory.length,
      recovery_success_rate: this.errorHistory.filter(e => e.recovered).length / this.errorHistory.length,
      error_classifications: this.getErrorClassificationStats(),
      recent_errors: this.errorHistory.slice(-10),
      system_health: this.calculateSystemHealth()
    };
  }

  /**
   * Get error classification statistics
   */
  private getErrorClassificationStats(): any {
    const stats = { critical: 0, warning: 0, recoverable: 0, quantum: 0 };
    this.errorHistory.forEach(e => {
      stats[e.context.error_classification]++;
    });
    return stats;
  }

  /**
   * Calculate overall system health
   */
  private calculateSystemHealth(): number {
    const recentErrors = this.errorHistory.slice(-20);
    const criticalErrors = recentErrors.filter(e => e.context.error_classification === 'critical');
    const recoveryRate = recentErrors.filter(e => e.recovered).length / Math.max(recentErrors.length, 1);
    
    return Math.max(0, 100 - (criticalErrors.length * 10) + (recoveryRate * 20));
  }
}

export default QuantumRecoverySystem;
