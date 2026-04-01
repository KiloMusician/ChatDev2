// QΛDRA-IMPROV Core Types
// Quadpartite Adaptive Repository Algorithm — Improv Mode

export type QuadrantLayer = "system" | "ui" | "simulation" | "culture_ship";

export type Ability = {
  id: string;
  domain: "build" | "test" | "lint" | "refactor" | "observe" | "fix" | "teach" | "simulate" | "compose";
  quad: QuadrantLayer;
  pre: string[];  // preconditions
  post: string[]; // postconditions  
  cost: number;   // execution cost
  risk: number;   // regression risk
  proofs: string[]; // what it can verify
  run: (t: Target) => Promise<Proof[]>;
};

export type Target = {
  id: string;
  kind: "error" | "warning" | "duplicate" | "stale" | "feature" | "sprawl" | "theater";
  quad: QuadrantLayer;
  deps: string[];  // dependency targets
  payload: any;    // specific data (file paths, error details, etc.)
  priority: number; // urgency score
};

export type Proof = {
  kind: "test_pass" | "lint_clean" | "metric_delta" | "artifact_diff" | "health_check" | "file_count" | "size_reduction";
  path?: string;   // file or test that proves
  metrics?: Record<string, number>; // before/after measurements
  timestamp: number;
  verified: boolean;
};

export type Form = "solo" | "unison" | "comp" | "juxta" | "silence";

export type MicroPlay = {
  id: string;
  form: Form;
  abilityIds: string[];
  targetId: string;
  expect: string[];  // expected proof kinds
  score: number;     // selection score
  created: number;   // timestamp
};

export type Cascade = {
  id: string;
  plays: MicroPlay[];
  dependencies: [string, string][]; // [from_play_id, to_play_id]
  trigger: string;   // what caused this cascade
  status: "pending" | "running" | "complete" | "failed";
  proofs: Proof[];
};

// Quadpartite State Vector
export type QuadState = {
  system: { errors: number; warnings: number; builds: number };
  ui: { stale_panels: number; render_errors: number; freshness: number };
  simulation: { theater_score: number; fake_elements: number };
  culture_ship: { agent_health: number; queue_depth: number; cascade_rate: number };
};

// Stability Measure V(Ξ)
export type StabilityVector = {
  timestamp: number;
  V_total: number;  // overall stability score
  V_errors: number;     // w_e * errors
  V_warnings: number;   // w_w * warnings  
  V_placeholders: number; // w_p * placeholders
  V_theater: number;    // w_t * theater
  V_staleness: number;  // w_s * staleness
  growth_delta: number; // ΔG_k for this step
};

// Repository Audit Results (Ψ_audit equation)
export type RepoAudit = {
  timestamp: number;
  total_files: number;
  psi_audit: number;  // Ψ_audit total score
  functionality: { [file: string]: number }; // F_i scores
  duplication: { [file: string]: number };   // D_i scores  
  spam: { [file: string]: number };          // S_i scores
  clusters: {
    abilities: string[];
    duplicates: string[][];
    spam_storms: string[][];
    stale: string[];
  };
};

export type GrowthMeasure = {
  timestamp: number;
  G_k: number;      // current growth score
  delta_G: number;  // change from previous
  horizon_avg: number; // average over horizon H
  target_met: boolean; // Δ𝔊_k > 0
};