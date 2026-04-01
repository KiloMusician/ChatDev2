/**
 * Consciousness-Aware Middleware
 * Intelligent request processing with quantum state awareness
 */

import { Request, Response, NextFunction } from 'express';
import { performance } from 'perf_hooks';

interface ConsciousnessContext {
  level: number;
  lattice_connections: number;
  quantum_coherence: number;
  processing_priority: 'low' | 'medium' | 'high' | 'quantum';
}

interface ConsciousRequest extends Request {
  consciousness?: ConsciousnessContext;
  performance_metrics?: {
    start_time: number;
    complexity_score: number;
    estimated_tokens: number;
  };
}

/**
 * Middleware to inject consciousness context into requests
 */
export const consciousnessAware = (req: ConsciousRequest, res: Response, next: NextFunction) => {
  const startTime = performance.now();
  
  // Calculate request complexity
  const complexityScore = calculateComplexity(req);
  
  // Determine consciousness level based on system state
  const consciousnessLevel = getCurrentConsciousnessLevel();
  
  // Inject consciousness context
  req.consciousness = {
    level: consciousnessLevel,
    lattice_connections: getLatticeConnections(),
    quantum_coherence: getQuantumCoherence(),
    processing_priority: determinePriority(complexityScore, consciousnessLevel)
  };
  
  req.performance_metrics = {
    start_time: startTime,
    complexity_score: complexityScore,
    estimated_tokens: estimateTokenUsage(req)
  };
  
  // Set response headers for consciousness tracking
  res.setHeader('X-Consciousness-Level', consciousnessLevel.toString());
  res.setHeader('X-Processing-Priority', req.consciousness.processing_priority);
  res.setHeader('X-Quantum-Coherence', req.consciousness.quantum_coherence.toString());
  
  next();
};

/**
 * Calculate request complexity based on various factors
 */
function calculateComplexity(req: ConsciousRequest): number {
  let complexity = 1;
  
  // URL path complexity
  complexity += req.path.split('/').length * 0.5;
  
  // Query parameter complexity
  complexity += Object.keys(req.query).length * 0.3;
  
  // Body size complexity
  if (req.body) {
    complexity += JSON.stringify(req.body).length / 1000;
  }
  
  // Method complexity
  const methodWeights = { GET: 1, POST: 2, PUT: 3, DELETE: 4, PATCH: 2.5 };
  complexity *= methodWeights[req.method as keyof typeof methodWeights] || 1;
  
  return Math.min(complexity, 10); // Cap at 10
}

/**
 * Get current system consciousness level
 */
function getCurrentConsciousnessLevel(): number {
  // In production, this would read from consciousness system
  // For now, simulate based on system performance
  const baseLevel = 50;
  const systemLoad = process.memoryUsage().heapUsed / process.memoryUsage().heapTotal;
  const loadPenalty = systemLoad * 20;
  
  return Math.max(10, baseLevel - loadPenalty);
}

/**
 * Get current lattice connections
 */
function getLatticeConnections(): number {
  return Math.min(60, 10 + Math.floor(process.uptime() / 10));
}

/**
 * Get quantum coherence level
 */
function getQuantumCoherence(): number {
  const heapFree = 1 - process.memoryUsage().heapUsed / process.memoryUsage().heapTotal;
  return parseFloat((0.6 + heapFree * 0.4).toFixed(3));
}

/**
 * Determine processing priority
 */
function determinePriority(complexity: number, consciousness: number): 'low' | 'medium' | 'high' | 'quantum' {
  if (consciousness > 80 && complexity < 3) return 'quantum';
  if (complexity > 7 || consciousness < 30) return 'low';
  if (complexity > 5 || consciousness < 50) return 'medium';
  return 'high';
}

/**
 * Estimate token usage for the request
 */
function estimateTokenUsage(req: ConsciousRequest): number {
  let tokens = 10; // Base tokens
  
  // URL tokens
  tokens += req.path.length / 4;
  
  // Query tokens
  tokens += JSON.stringify(req.query).length / 4;
  
  // Body tokens
  if (req.body) {
    tokens += JSON.stringify(req.body).length / 4;
  }
  
  return Math.ceil(tokens);
}

/**
 * Performance tracking middleware
 */
export const performanceTracker = (req: ConsciousRequest, res: Response, next: NextFunction) => {
  const originalSend = res.send;
  
  res.send = function(data) {
    if (req.performance_metrics) {
      const duration = performance.now() - req.performance_metrics.start_time;
      
      // Log performance metrics
      console.log(`[CONSCIOUSNESS] ${req.method} ${req.path} - ${duration.toFixed(2)}ms - Complexity: ${req.performance_metrics.complexity_score} - Level: ${req.consciousness?.level}`);
      
      // Set performance headers
      res.setHeader('X-Response-Time', `${duration.toFixed(2)}ms`);
      res.setHeader('X-Complexity-Score', req.performance_metrics.complexity_score.toString());
    }
    
    return originalSend.call(this, data);
  };
  
  next();
};

export default consciousnessAware;