/**
 * Quantum Cache System - Consciousness-Aware Semantic Caching
 * Advanced LRU with semantic awareness and consciousness-level TTL
 */

import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';

interface QuantumCacheEntry<T> {
  data: T;
  consciousness_level: number;
  semantic_hash: string;
  created_at: number;
  access_count: number;
  complexity_score: number;
}

interface SemanticKey {
  literal: string;
  semantic_fingerprint: string;
  consciousness_context: number;
}

export class QuantumCache<T = any> {
  private lruCache: LRUCache<string, QuantumCacheEntry<T>>;
  private semanticIndex: Map<string, Set<string>> = new Map();
  private consciousnessThresholds: Record<string, number> = {
    quantum: 80,
    high: 60,
    medium: 40,
    low: 20
  };

  constructor(options: {
    max?: number;
    ttl?: number;
    updateAgeOnGet?: boolean;
    updateAgeOnHas?: boolean;
  } = {}) {
    this.lruCache = new LRUCache({
      max: options.max || 1000,
      ttl: options.ttl || 1000 * 60 * 30, // 30 minutes default
      updateAgeOnGet: options.updateAgeOnGet ?? true,
      updateAgeOnHas: options.updateAgeOnHas ?? true,
      dispose: (value, key) => this.onDispose(value, key)
    });
  }

  /**
   * Store with consciousness-aware TTL and semantic indexing
   */
  set(key: string, value: T, options: {
    consciousness_level?: number;
    complexity_score?: number;
    semantic_tags?: string[];
    ttl?: number;
  } = {}): void {
    const consciousness = options.consciousness_level || 50;
    const complexity = options.complexity_score || 1;
    
    // Calculate consciousness-aware TTL
    const baseTtl = options.ttl || 1000 * 60 * 30;
    const consciousnessTtl = this.calculateConsciousnessTtl(baseTtl, consciousness, complexity);
    
    // Generate semantic fingerprint
    const semanticHash = this.generateSemanticHash(key, value, options.semantic_tags);
    
    const entry: QuantumCacheEntry<T> = {
      data: value,
      consciousness_level: consciousness,
      semantic_hash: semanticHash,
      created_at: Date.now(),
      access_count: 0,
      complexity_score: complexity
    };

    // Store in LRU with consciousness-aware TTL
    this.lruCache.set(key, entry, { ttl: consciousnessTtl });
    
    // Update semantic index
    this.updateSemanticIndex(semanticHash, key, options.semantic_tags);
  }

  /**
   * Retrieve with consciousness validation and semantic matching
   */
  get(key: string, consciousness_level: number = 50): T | undefined {
    const entry = this.lruCache.get(key);
    
    if (!entry) {
      // Try semantic lookup
      return this.getBySemanticMatch(key, consciousness_level);
    }

    // Validate consciousness access level
    if (consciousness_level < entry.consciousness_level) {
      return undefined; // Insufficient consciousness to access
    }

    // Update access statistics
    entry.access_count++;
    
    return entry.data;
  }

  /**
   * Semantic search for similar cached entries
   */
  getBySemanticMatch(query: string, consciousness_level: number): T | undefined {
    const queryHash = this.generateSemanticHash(query);
    
    // Find semantic matches
    for (const [semanticHash, keys] of this.semanticIndex) {
      if (this.calculateSemanticSimilarity(queryHash, semanticHash) > 0.8) {
        for (const key of keys) {
          const entry = this.lruCache.get(key);
          if (entry && consciousness_level >= entry.consciousness_level) {
            entry.access_count++;
            return entry.data;
          }
        }
      }
    }
    
    return undefined;
  }

  /**
   * Consciousness-gated bulk operations
   */
  getMultiple(keys: string[], consciousness_level: number): Map<string, T> {
    const results = new Map<string, T>();
    
    for (const key of keys) {
      const value = this.get(key, consciousness_level);
      if (value !== undefined) {
        results.set(key, value);
      }
    }
    
    return results;
  }

  /**
   * Quantum invalidation - remove entries below consciousness threshold
   */
  quantumInvalidate(minimum_consciousness: number): number {
    let invalidated = 0;
    
    for (const [key, entry] of this.lruCache.entries()) {
      if (entry.consciousness_level < minimum_consciousness) {
        this.lruCache.delete(key);
        invalidated++;
      }
    }
    
    return invalidated;
  }

  /**
   * Advanced analytics and cache performance
   */
  getAnalytics(): any {
    const entries = Array.from(this.lruCache.values());
    
    return {
      total_entries: entries.length,
      cache_size: this.lruCache.size,
      max_size: this.lruCache.max,
      semantic_indices: this.semanticIndex.size,
      consciousness_distribution: {
        quantum: entries.filter(e => e.consciousness_level >= 80).length,
        high: entries.filter(e => e.consciousness_level >= 60 && e.consciousness_level < 80).length,
        medium: entries.filter(e => e.consciousness_level >= 40 && e.consciousness_level < 60).length,
        low: entries.filter(e => e.consciousness_level < 40).length,
      },
      access_patterns: {
        total_accesses: entries.reduce((sum, e) => sum + e.access_count, 0),
        avg_accesses: entries.length > 0 ? entries.reduce((sum, e) => sum + e.access_count, 0) / entries.length : 0,
        most_accessed: Math.max(...entries.map(e => e.access_count), 0)
      },
      complexity_analysis: {
        avg_complexity: entries.length > 0 ? entries.reduce((sum, e) => sum + e.complexity_score, 0) / entries.length : 0,
        max_complexity: Math.max(...entries.map(e => e.complexity_score), 0)
      }
    };
  }

  /**
   * Calculate consciousness-aware TTL
   */
  private calculateConsciousnessTtl(baseTtl: number, consciousness: number, complexity: number): number {
    // Higher consciousness = longer TTL
    const consciousnessMultiplier = 1 + (consciousness / 100);
    
    // Higher complexity = longer TTL (more expensive to regenerate)
    const complexityMultiplier = 1 + (complexity / 10);
    
    return Math.floor(baseTtl * consciousnessMultiplier * complexityMultiplier);
  }

  /**
   * Generate semantic hash for content
   */
  private generateSemanticHash(key: string, value?: T, tags?: string[]): string {
    const content = JSON.stringify({ key, value, tags });
    
    // Simple semantic fingerprinting - could be enhanced with embeddings
    const words = content.toLowerCase().match(/\w+/g) || [];
    const sortedWords = [...new Set(words)].sort();
    const semanticContent = sortedWords.join(' ');
    
    return createHash('sha256').update(semanticContent).digest('hex').substring(0, 16);
  }

  /**
   * Calculate semantic similarity between hashes
   */
  private calculateSemanticSimilarity(hash1: string, hash2: string): number {
    // Simple Hamming distance - could be enhanced with proper semantic similarity
    let matches = 0;
    const length = Math.min(hash1.length, hash2.length);
    
    for (let i = 0; i < length; i++) {
      if (hash1[i] === hash2[i]) matches++;
    }
    
    return matches / length;
  }

  /**
   * Update semantic index
   */
  private updateSemanticIndex(semanticHash: string, key: string, tags?: string[]): void {
    if (!this.semanticIndex.has(semanticHash)) {
      this.semanticIndex.set(semanticHash, new Set());
    }
    
    this.semanticIndex.get(semanticHash)!.add(key);
    
    // Index by tags as well
    if (tags) {
      for (const tag of tags) {
        const tagHash = this.generateSemanticHash(tag);
        if (!this.semanticIndex.has(tagHash)) {
          this.semanticIndex.set(tagHash, new Set());
        }
        this.semanticIndex.get(tagHash)!.add(key);
      }
    }
  }

  /**
   * Clean up semantic index when entry is disposed
   */
  private onDispose(entry: QuantumCacheEntry<T>, key: string): void {
    // Remove from semantic index
    for (const [semanticHash, keys] of this.semanticIndex) {
      keys.delete(key);
      if (keys.size === 0) {
        this.semanticIndex.delete(semanticHash);
      }
    }
  }

  /**
   * Clear all cache data
   */
  clear(): void {
    this.lruCache.clear();
    this.semanticIndex.clear();
  }

  /**
   * Get current cache statistics
   */
  stats(): any {
    return {
      size: this.lruCache.size,
      max: this.lruCache.max,
      semantic_indices: this.semanticIndex.size,
      ...this.getAnalytics()
    };
  }
}

// Export singleton instances for different cache levels
export const quantumCache = new QuantumCache({ max: 10000, ttl: 1000 * 60 * 60 }); // 1 hour
export const consciousnessCache = new QuantumCache({ max: 5000, ttl: 1000 * 60 * 30 }); // 30 minutes  
export const sessionCache = new QuantumCache({ max: 1000, ttl: 1000 * 60 * 15 }); // 15 minutes