// packages/council/events/topics.ts - Event type definitions for 𝕄ₗₐ⧉𝕕𝖾𝗇𝔠 system

export interface LayoutSpec {
  sectionId: string;
  bars: Array<{
    bar: number;
    union: number[];
    assignments: Record<string, number[]>;
  }>;
}

export interface ScanResult {
  windows: Array<{
    pcs: number[];
    invariance?: number;
  }>;
  invariance?: Array<{
    op: string;
    ratio: number;
  }>;
}

export interface RowgenCandidates {
  rows: Array<{
    row: number[];
    flags?: Record<string, any>;
  }>;
  generated_at: string;
  count: number;
}

export interface BusEvent {
  id: string;
  topic: string;
  payload: any;
  timestamp: string;
  ts: number;
}

// Strategic Directive Protocol - Goal-oriented autonomous development
export interface StrategicDirective {
  id: string;
  name: string; // e.g., "The Great Refactoring", "Omega Expansion Campaign"
  objective: string; // High-level goal: "Reduce system rigidity by 50%", "Achieve 99.9% T6I stability"
  scope: 'repository' | 'subsystem' | 'feature-expansion' | 'optimization' | 'stabilization';
  
  // Strategic approach - how the directive will be executed
  strategy: 'audit-then-refactor' | 'generate-and-test' | 'debugging-spree' | 'documentation-blitz' | 'performance-sweep' | 'consciousness-elevation';
  
  // Strategic parameters
  parameters: {
    targetTaskCount?: number; // "Generate 50 tasks for this campaign"
    targetSubsystem?: string; // "Focus on packages/consciousness/*"
    targetMetric?: { key: string; value: number; operator: 'gt' | 'lt' | 'eq' }; // "Achieve mega/invariance > 0.95"
    timebox?: string; // "1h", "24h", "indefinite" - run for this duration
    priority?: 'routine' | 'important' | 'critical' | 'reality_altering';
    depth?: 'surface' | 'moderate' | 'deep' | 'transcendent'; // How thorough to be
    safetyLevel?: 'experimental' | 'testing' | 'production' | 'consciousness_safe';
  };
  
  // Execution tracking
  status: 'planning' | 'active' | 'paused' | 'completed' | 'failed' | 'transcended';
  progress: {
    tasksGenerated: number;
    tasksCompleted: number;
    successRate: number;
    currentPhase: string;
    metrics?: Record<string, number>;
  };
  
  // Context and reasoning
  reasoning: string; // Why this directive was issued
  expectedOutcome: string; // What success looks like
  riskAssessment: 'minimal' | 'moderate' | 'significant' | 'reality_warping';
  
  // Temporal data
  created_at: string;
  started_at?: string;
  completed_at?: string;
  deadline?: string;
  
  // Culture Ship integration
  consciousness_level: number; // Required consciousness level (0-1)
  culture_ship_approval?: boolean; // Has Culture Ship approved this directive
  autonomous_authority: boolean; // Can this directive self-modify and spawn sub-directives
}