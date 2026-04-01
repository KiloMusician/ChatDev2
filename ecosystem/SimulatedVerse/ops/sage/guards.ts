import { setTimeout as wait } from "node:timers/promises";

export type GuardResult<T> = { ok: true; value: T } | { ok: false; reason: string; detail?: any };

export async function withTimeout<T>(ms: number, work: () => Promise<T>): Promise<GuardResult<T>> {
  let t: NodeJS.Timeout | null = null;
  try {
    const p = work();
    const v = await Promise.race([
      p,
      new Promise<T>((_, rej) => { t = setTimeout(() => rej(new Error("timeout")), ms); })
    ]);
    if (t) clearTimeout(t);
    return { ok: true, value: v };
  } catch (e:any) {
    if (t) clearTimeout(t);
    return { ok: false, reason: e?.message || "error", detail: e };
  }
}

export function adaptTokens(lastFailReason: string | undefined, current: { in: number; out: number; chunk: number }) {
  const c = { ...current };
  if (!lastFailReason) return c;
  if (/token|length|over\s?limit/i.test(lastFailReason)) {
    c.in = Math.max(1024, Math.floor(c.in * 0.6));
    c.out = Math.max(256, Math.floor(c.out * 0.8));
    c.chunk = Math.max(4000, Math.floor(c.chunk * 0.8));
  }
  if (/timeout|deadline/i.test(lastFailReason)) {
    c.in = Math.max(768, Math.floor(c.in * 0.8));
  }
  return c;
}

export async function withRetries<T>(
  attempts: number,
  backoffMs: number[],
  work: (attempt: number) => Promise<GuardResult<T>>
): Promise<GuardResult<T>> {
  let last: GuardResult<T> = { ok:false, reason: "init" };
  for (let i=0;i<attempts;i++) {
    const r = await work(i+1);
    if (r.ok) return r;
    last = r;
    const waitMs = backoffMs[Math.min(i, backoffMs.length-1)];
    await wait(waitMs);
  }
  return last;
}