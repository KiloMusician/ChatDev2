// client/src/lib/useProvisionedStateETag.ts
// ETag-aware provisioned fetch (with backoff) - Replit bandwidth-friendly
import { useEffect, useRef, useState } from "react";

type Opts = {
  url?: string;
  minMs?: number;      // min poll interval
  maxMs?: number;      // max backoff
  startMs?: number;    // initial interval
};

function clamp(x: number, lo: number, hi: number) { 
  return Math.max(lo, Math.min(hi, x)); 
}

export function useProvisionedStateETag(opts: Opts = {}) {
  const url = opts.url ?? "/system-status.json";
  const minMs = opts.minMs ?? 3000;
  const maxMs = opts.maxMs ?? 30000;
  const startMs = opts.startMs ?? 5000;

  const [data, setData] = useState<any>(null);
  const [meta, setMeta] = useState<{etag?: string, lastChecked?: number, lastChanged?: number}>({});
  const timer = useRef<any>(null);
  const interval = useRef<number>(startMs);
  const etagRef = useRef<string | undefined>(undefined);
  const mounted = useRef<boolean>(false);

  useEffect(() => {
    mounted.current = true;

    const load = async () => {
      if (!mounted.current) return;

      try {
        const headers: Record<string, string> = {
          'Cache-Control': 'no-cache'
        };
        
        // Add If-None-Match header for ETag support
        if (etagRef.current) {
          headers['If-None-Match'] = etagRef.current;
        }

        const res = await fetch(url, { headers });
        const now = Date.now();

        if (res.status === 304) {
          // Not modified - increase interval (backoff)
          interval.current = clamp(interval.current * 1.2, minMs, maxMs);
          setMeta(prev => ({ ...prev, lastChecked: now }));
          return;
        }

        if (!res.ok) {
          // Error - increase interval (backoff)
          interval.current = clamp(interval.current * 1.5, minMs, maxMs);
          console.warn(`[ProvisionedState] HTTP ${res.status} for ${url}`);
          return;
        }

        const newEtag = res.headers.get('etag');
        const json = await res.json();

        if (mounted.current) {
          setData(json);
          etagRef.current = newEtag || undefined;
          
          // Data changed - reset interval to minimum
          interval.current = minMs;
          
          setMeta({
            etag: newEtag || undefined,
            lastChecked: now,
            lastChanged: now
          });
        }
      } catch (e) {
        // Network error - increase interval (backoff)
        interval.current = clamp(interval.current * 1.5, minMs, maxMs);
        console.warn("[ProvisionedState] fetch failed:", e);
      }

      // Schedule next poll
      if (mounted.current) {
        timer.current = setTimeout(load, interval.current);
      }
    };

    // Initial load
    load();

    return () => {
      mounted.current = false;
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
      }
    };
  }, [url, minMs, maxMs, startMs]);

  return { data, meta }; // always defined shape { data, meta }, never throws
}