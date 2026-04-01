// SystemDev/interfaces/rlci.ts
// RLCI v1 - Replit ↔ Culture-Ship Interface Protocol

export interface RLCIEnvelope {
  rlci: "v1";
  origin: "chat" | "replit" | "agent" | "wizard" | "janitor";
  quad: Array<"SystemDev" | "ChatDev" | "GameDev" | "PreviewUI">;
  loc: {
    cwd: string;
    focus: string[];
    selection?: string[];
  };
  omnitag: {
    mode: "breath_cycle" | "micro_cycle" | "cascade" | "emergency";
    law: "receipts" | "quantum_wink" | "culture_ship";
    colony: "ΞNuSyQ" | string;
    anneal: boolean;
    zeta_checks: boolean;
    anti_theater: boolean;
    tier?: string;
    temple: Array<"SystemDev" | "ChatDev" | "GameDev" | "PreviewUI">;
  };
  intent: {
    task: string;
    priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    limits: {
      edits_max: number;
      lines_max: number;
    };
    safety: string[];
  };
  hints: string[];
}

export interface LocationBeacon {
  entrypoints: string[];
  safe_move_roots: string[];
  ignore: string[];
  preferred_scanners: string[];
  description?: string;
  quadrant: "SystemDev" | "ChatDev" | "GameDev" | "PreviewUI";
}

export interface TipSynthInput {
  error_text: string;
  last_command: string;
  envelope: RLCIEnvelope;
  capabilities: any;
  context?: {
    file_path?: string;
    line_number?: number;
    git_status?: string;
  };
}

export interface TipSynthOutput {
  tips: Array<{
    text: string;
    action?: string;
    priority: "low" | "medium" | "high";
    run_card?: string;
  }>;
  alternative_commands?: string[];
  escalation?: {
    agent: string;
    directive: string;
  };
}

export interface CycleReceipt {
  cycle: number;
  focus: string;
  edits: number;
  lines_changed: number;
  tests_run: number;
  result: "ok" | "partial" | "failed";
  found: string[];
  fixed: string[];
  next_hint: string;
  cascade_ready: boolean;
  rlci_envelope: RLCIEnvelope;
}

export interface RLCIEvent {
  topic: string;
  payload: any;
  timestamp: string;
  source: string;
  envelope?: RLCIEnvelope;
}

// Event topic patterns
export const RLCI_TOPICS = {
  SEARCH_OVERLOAD: 'search/overload',
  GIT_RESTRICTED: 'git/restricted', 
  EXEC_SUCCESS: 'exec/success',
  EXEC_FAILURE: 'exec/failure',
  UI_FOCUS: 'ui/focus',
  DIAG_TYPESCRIPT: 'diag/typescript_error',
  FS_TIMEOUT: 'fs/search_timeout',
  GODOT_IMPORT: 'godot/import_cache_hit',
  MOBILE_PREVIEW: 'ui/mobile_preview_focus'
} as const;

// Standard RLCI factory functions
export function createRLCIEnvelope(
  origin: RLCIEnvelope['origin'],
  task: string,
  options: Partial<RLCIEnvelope> = {}
): RLCIEnvelope {
  return {
    rlci: "v1",
    origin,
    quad: ["SystemDev", "ChatDev", "GameDev", "PreviewUI"],
    loc: {
      cwd: process.cwd(),
      focus: ["src/", "SystemDev/scripts"],
      ...options.loc
    },
    omnitag: {
      mode: "breath_cycle",
      law: "receipts", 
      colony: "ΞNuSyQ",
      anneal: true,
      zeta_checks: true,
      anti_theater: true,
      temple: ["SystemDev", "ChatDev", "GameDev", "PreviewUI"],
      ...options.omnitag
    },
    intent: {
      task,
      priority: "MEDIUM",
      limits: {
        edits_max: 8,
        lines_max: 400
      },
      safety: ["path_safe_moves", "idempotent", "receipt_required"],
      ...options.intent
    },
    hints: [
      "Prefer targeted scans over full-repo globbing",
      "Use capability registry before invoking tools",
      "Surface tips if failure matches a known pattern",
      ...(options.hints || [])
    ]
  };
}

export function createCycleReceipt(
  cycle: number,
  focus: string,
  edits: number,
  envelope: RLCIEnvelope,
  options: Partial<CycleReceipt> = {}
): CycleReceipt {
  return {
    cycle,
    focus,
    edits,
    lines_changed: 0,
    tests_run: 0,
    result: "ok",
    found: [],
    fixed: [],
    next_hint: "",
    cascade_ready: edits >= 6,
    rlci_envelope: envelope,
    ...options
  };
}