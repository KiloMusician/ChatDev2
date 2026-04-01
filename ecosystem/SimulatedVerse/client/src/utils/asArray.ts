/* 
OWNERS: team/infra, ai/prime
TAGS: utils, defensive, anti-crash, type-safe
STABILITY: stable
INTEGRATIONS: ui/views, sim/state, ops/proof
*/

/**
 * ΞNuSyQ-Prime Defensive Array Normalizer
 * Prevents "m.map is not a function" crashes with surgical type safety
 * 
 * @param maybe - Unknown data that should be an array
 * @param label - Debug label for logging contract breaches
 * @returns Safe array ready for .map() operations
 */
export function asArray<T>(maybe: unknown, label = "data"): T[] {
  if (Array.isArray(maybe)) return maybe as T[];
  if (maybe == null) return [];           // soft-fail for null/undefined
  
  if (typeof maybe === "object") {
    // If it's an object with values we likely intended to map, prefer values
    const vals = Object.values(maybe as Record<string, T>);
    if (vals.length > 0) return vals;
  }
  
  // Proof-aware contract breach logging
  if (process.env.NODE_ENV !== "production") {
    console.warn(`[ΞNuSyQ-Prime] Contract breach: Expected array for ${label}, got:`, typeof maybe, maybe);
  }
  
  return []; // Graceful fallback
}

/**
 * Safe string extraction with fallback
 */
export function asString(x: unknown, fallback = "unknown"): string {
  return typeof x === 'string' ? x : String(x ?? fallback);
}

/**
 * Type guard for array validation at boundaries
 */
export function isArrayLike(x: unknown): x is unknown[] {
  return Array.isArray(x) || (x != null && typeof x === 'object' && 'length' in x);
}