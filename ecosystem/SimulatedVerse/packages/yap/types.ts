// packages/yap/types.ts
export type Level = "debug" | "info" | "warn" | "error";

export interface YapLog {
  ts: number;
  level: Level;
  source: string;         // module/agent name or "console"
  message: string;
  data?: Record<string, any>;
}

export interface YapTag {
  key: string;            // e.g., "invariance/T6I"
  value: any;
}

export interface YapClassification {
  label: string;          // e.g., "invariance_dip"
  score: number;          // 0..1
  tags: YapTag[];
  reasons: string[];
}