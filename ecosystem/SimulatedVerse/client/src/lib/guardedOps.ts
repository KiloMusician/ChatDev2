// client/src/lib/guardedOps.ts
// UI Guards: No-crash array operations to prevent m.map errors forever
import React from 'react';

export function asArray<T = any>(x: T | T[] | null | undefined): T[] {
  if (x == null) return [];
  return Array.isArray(x) ? x : [x];
}

export function safeMap<T, R>(
  x: T[] | null | undefined, 
  f: (t: T, i: number) => R,
  label = "safeMap"
): R[] {
  try {
    const arr = asArray(x);
    return arr.map(f);
  } catch (error) {
    console.warn(`[${label}] Map operation failed:`, error);
    return [];
  }
}

export function safeFilter<T>(
  x: T[] | null | undefined,
  predicate: (t: T, i: number) => boolean,
  label = "safeFilter"
): T[] {
  try {
    const arr = asArray(x);
    return arr.filter(predicate);
  } catch (error) {
    console.warn(`[${label}] Filter operation failed:`, error);
    return [];
  }
}

export function safeFind<T>(
  x: T[] | null | undefined,
  predicate: (t: T, i: number) => boolean,
  label = "safeFind"
): T | undefined {
  try {
    const arr = asArray(x);
    return arr.find(predicate);
  } catch (error) {
    console.warn(`[${label}] Find operation failed:`, error);
    return undefined;
  }
}

export function safePct(v?: number): string {
  return typeof v === "number" && !isNaN(v) ? `${(v * 100).toFixed(1)}%` : "—";
}

export function safeNum(v?: number, suffix: string = ""): string {
  return typeof v === "number" && !isNaN(v) ? `${v}${suffix}` : "—";
}

export function safePath<T>(obj: any, path: string, fallback: T): T {
  try {
    return path.split('.').reduce((o, key) => o?.[key], obj) ?? fallback;
  } catch {
    return fallback;
  }
}

// Enhanced SafeList component to completely eliminate m.map class errors
export function guardedForEach<T>(
  items: T | T[] | null | undefined,
  callback: (item: T, index: number) => void,
  label = "guardedForEach"
): void {
  try {
    const arr = asArray(items);
    arr.forEach(callback);
  } catch (error) {
    console.warn(`[${label}] ForEach operation failed:`, error);
  }
}

// Type guard to check if something is safely mappable
export function isSafelyMappable(x: unknown): x is any[] {
  return Array.isArray(x);
}

// Defensive data normalization
export function normalizeData<T>(data: unknown, fallback: T[] = []): T[] {
  if (data == null) return fallback;
  if (Array.isArray(data)) return data;
  if (typeof data === 'object' && 'length' in data) {
    try {
      return Array.from(data as ArrayLike<T>);
    } catch {
      return fallback;
    }
  }
  return [data as T];
}

// Safe array operations specifically for React components
export function safeRender<T>(
  items: T | T[] | null | undefined,
  renderFn: (item: T, index: number) => React.ReactNode,
  keyFn?: (item: T, index: number) => string | number
): React.ReactNode[] {
  try {
    const arr = asArray(items);
    return arr.map((item, index) => {
      const key = keyFn ? keyFn(item, index) : index;
      return React.createElement(React.Fragment, { key }, renderFn(item, index));
    });
  } catch (error) {
    console.warn("[safeRender] Render operation failed:", error);
    return [];
  }
}