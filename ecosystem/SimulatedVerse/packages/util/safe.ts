/**
 * Safe Mapping Utilities - Eliminate ".map is not a function" errors
 * 
 * Core utilities for the tripartite CognitoWeave ecosystem to handle
 * arrays, objects, and undefined values safely across System/Game/Simulation layers.
 */

export const asArray = <T>(m: T[] | ReadonlyArray<T> | T | null | undefined): T[] =>
  Array.isArray(m) ? [...m] : (m == null ? [] : [m as T]);

export const isListish = (value: unknown): value is unknown[] => Array.isArray(value);

export function safeMap<T, R>(
  m: T[] | T | null | undefined,
  fn: (x: T, i: number) => R
): R[] {
  const arr = asArray(m);
  const out: R[] = [];
  arr.forEach((value, i) => {
    out.push(fn(value, i));
  });
  return out;
}

export function safeFilter<T>(
  m: T[] | T | null | undefined,
  predicate: (x: T, i: number) => boolean
): T[] {
  const arr = asArray(m);
  const out: T[] = [];
  arr.forEach((value, i) => {
    if (predicate(value, i)) {
      out.push(value);
    }
  });
  return out;
}

export function safeFind<T>(
  m: T[] | T | null | undefined,
  predicate: (x: T, i: number) => boolean
): T | undefined {
  const arr = asArray(m);
  for (let i = 0; i < arr.length; i++) {
    const value = arr[i];
    if (value !== undefined && predicate(value, i)) {
      return value;
    }
  }
  return undefined;
}

export function safeReduce<T, R>(
  m: T[] | T | null | undefined,
  reducer: (acc: R, current: T, i: number) => R,
  initialValue: R
): R {
  const arr = asArray(m);
  let acc = initialValue;
  arr.forEach((value, i) => {
    acc = reducer(acc, value, i);
  });
  return acc;
}

// Safe object access utilities
export function safeGet<T>(obj: any, path: string, defaultValue?: T): T | undefined {
  if (!obj || typeof obj !== 'object') return defaultValue;
  
  const keys = path.split('.');
  let current = obj;
  
  for (const key of keys) {
    if (current == null || typeof current !== 'object' || !(key in current)) {
      return defaultValue;
    }
    current = current[key];
  }
  
  return current ?? defaultValue;
}

// Safe async operations
export async function safeAsync<T>(
  operation: () => Promise<T>,
  fallback: T
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    console.warn('Safe async operation failed:', error);
    return fallback;
  }
}

// Safe JSON operations
export function safeJsonParse<T>(jsonString: string, fallback: T): T {
  try {
    return JSON.parse(jsonString) ?? fallback;
  } catch {
    return fallback;
  }
}

export function safeJsonStringify(obj: any, fallback = '{}'): string {
  try {
    return JSON.stringify(obj) ?? fallback;
  } catch {
    return fallback;
  }
}
