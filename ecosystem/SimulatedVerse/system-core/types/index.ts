// [Ω:root:types@core] Shared type primitives - no cross-feature imports

export interface ModuleInfo {
  id: string;
  path: string;
  owner: string;
  deputy: string;
  status: 'experimental' | 'active' | 'stable' | 'deprecated' | 'locked';
  dependencies: string[];
  exports: string[];
}

export interface TierUnlock {
  id: string;
  name: string;
  timeRequirement: number;
  resourceRequirements?: Record<string, number>;
  prerequisites: string[];
  unlocks: string[];
  narrative: string;
}

export interface CouncilApproval {
  role: 'SCP-ENG' | 'SCP-QA' | 'SCP-UX' | 'SCP-OPS' | 'SCP-LORE';
  approved: boolean;
  timestamp: number;
  notes?: string;
}

export interface OmniTag {
  module: string;
  verb: string;
  hint?: string;
  line?: number;
  file?: string;
}

export interface ResourceState {
  energy: number;
  materials: number;
  bio?: number;
  circuits?: number;
  [key: string]: number | undefined;
}