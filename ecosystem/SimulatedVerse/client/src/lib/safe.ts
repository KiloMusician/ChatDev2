// client/src/lib/safe.ts
// Drop-in safe helpers to avoid m.map forever

export function asArray<T = any>(m: T | T[] | null | undefined): T[] {
  if (m == null) return [];
  return Array.isArray(m) ? m : [m];
}

export function safeMap<T, R>(m: T[] | null | undefined, f: (t: T, i: number) => R): R[] {
  return (Array.isArray(m) ? m : []).map(f);
}

export function safePct(v?: number): string {
  return typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—";
}

export function safeNum(v?: number, suffix: string = ""): string {
  return typeof v === "number" ? `${v}${suffix}` : "—";
}

export function safePath<T>(obj: any, path: string, fallback: T): T {
  try {
    return path.split('.').reduce((o, key) => o?.[key], obj) ?? fallback;
  } catch {
    return fallback;
  }
}