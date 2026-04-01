// QΛDRA-IMPROV: Five Forms of Interaction
// Adapted from musical improv theory for repository operations

import type { Ability, Target, MicroPlay } from './types.js';

let playCounter = 0;
const nextId = () => `play_${++playCounter}_${Date.now()}`;

/**
 * Solo (σ): Single ability applied directly to target
 * Clean, focused, minimal intervention
 */
export const Solo = (ability: Ability, target: Target): MicroPlay => ({
  id: nextId(),
  form: "solo",
  abilityIds: [ability.id],
  targetId: target.id,
  expect: ability.proofs,
  score: calculateBaseScore(ability, target),
  created: Date.now()
});

/**
 * Unison (υ): Multiple homogeneous abilities in parallel
 * Like multiple lint passes or parallel test suites  
 */
export const Unison = (abilities: Ability[], target: Target): MicroPlay => {
  if (abilities.length === 0) throw new Error("Unison requires at least one ability");
  
  const score = abilities.reduce((sum, a) => sum + calculateBaseScore(a, target), 0) * 0.8; // parallel bonus
  
  return {
    id: nextId(),
    form: "unison", 
    abilityIds: abilities.map(a => a.id),
    targetId: target.id,
    expect: abilities.flatMap(a => a.proofs),
    score,
    created: Date.now()
  };
};

/**
 * Comping (κ): Primary ability + supportive checker
 * Main action with verification/validation accompaniment
 */
export const Comp = (main: Ability, checker: Ability, target: Target): MicroPlay => {
  const mainScore = calculateBaseScore(main, target);
  const checkerBonus = calculateBaseScore(checker, target) * 0.4; // supporting role
  
  return {
    id: nextId(),
    form: "comp",
    abilityIds: [main.id, checker.id],
    targetId: target.id, 
    expect: [...main.proofs, ...checker.proofs],
    score: mainScore + checkerBonus + 0.3, // comp bonus for verification
    created: Date.now()
  };
};

/**
 * Juxtaposition (ξ): Two diverse strategies, A/B shadow run
 * Propose alternatives, keep best by proof quality
 */
export const Juxta = (abilityA: Ability, abilityB: Ability, target: Target): MicroPlay => {
  const scoreA = calculateBaseScore(abilityA, target);
  const scoreB = calculateBaseScore(abilityB, target);
  const explorationBonus = 0.5; // reward for trying alternatives
  
  return {
    id: nextId(),
    form: "juxta",
    abilityIds: [abilityA.id, abilityB.id],
    targetId: target.id,
    expect: [...abilityA.proofs, ...abilityB.proofs],
    score: Math.max(scoreA, scoreB) + explorationBonus,
    created: Date.now()
  };
};

/**
 * Silence (ψ): Enforced pause/consolidation
 * Budgeted quiescence to prevent strobe-light crash loops
 */
export const Silence = (target: Target, durationMs: number = 2000): MicroPlay => ({
  id: nextId(),
  form: "silence",
  abilityIds: [],
  targetId: target.id,
  expect: ["budgeted_quiescence", "log_rotation", "queue_rebalance"],
  score: 0.1, // low score but sometimes necessary
  created: Date.now()
});

/**
 * Smart form selection based on target characteristics
 */
export function selectOptimalForm(
  abilities: Ability[], 
  target: Target,
  context: { recent_failures: string[]; queue_depth: number; theater_score: number }
): MicroPlay[] {
  const candidates: MicroPlay[] = [];
  
  // Filter abilities that can handle this target
  const capable = abilities.filter(a => 
    canHandle(a, target) && !context.recent_failures.includes(a.id)
  );
  
  if (capable.length === 0) {
    // Fallback to silence if nothing can handle it
    return [Silence(target)];
  }
  
  // Solo plays for each capable ability
  candidates.push(...capable.map(a => Solo(a, target)));
  
  // Unison if multiple abilities of same domain
  const domains = groupBy(capable, a => a.domain);
  for (const [domain, domainAbilities] of Object.entries(domains)) {
    if (domainAbilities.length > 1) {
      candidates.push(Unison(domainAbilities, target));
    }
  }
  
  // Comp plays: pair main abilities with checkers
  const mains = capable.filter(a => a.domain !== "observe");
  const checkers = capable.filter(a => a.domain === "observe" || a.domain === "test");
  
  for (const main of mains) {
    for (const checker of checkers) {
      if (main.id !== checker.id) {
        candidates.push(Comp(main, checker, target));
      }
    }
  }
  
  // Juxta for exploration when we have diverse options
  if (capable.length >= 2) {
    const diverse = findDiversePairs(capable);
    candidates.push(...diverse.map(([a, b]) => Juxta(a, b, target)));
  }
  
  // Force silence if system is churning too fast
  if (context.queue_depth > 20 || context.theater_score > 0.8) {
    candidates.push(Silence(target, 5000)); // longer pause
  }
  
  return candidates.sort((a, b) => b.score - a.score);
}

// Helper functions
function calculateBaseScore(ability: Ability, target: Target): number {
  const domainBonus = ability.domain === "fix" ? 1.5 : 1.0;
  const quadMatch = ability.quad === target.quad ? 0.3 : 0;
  const priorityWeight = target.priority * 0.1;
  const costPenalty = ability.cost * 0.05;
  const riskPenalty = ability.risk * 0.1;
  
  return domainBonus + quadMatch + priorityWeight - costPenalty - riskPenalty;
}

function canHandle(ability: Ability, target: Target): boolean {
  // Domain compatibility
  const domainMap: Record<string, string[]> = {
    "error": ["fix", "test", "observe"],
    "warning": ["lint", "fix", "observe"], 
    "duplicate": ["refactor", "observe"],
    "stale": ["refactor", "fix"],
    "feature": ["build", "compose", "test"],
    "sprawl": ["refactor", "observe"],
    "theater": ["fix", "observe"]
  };
  
  return domainMap[target.kind]?.includes(ability.domain) ?? false;
}

function groupBy<T, K extends string>(array: T[], keyFn: (item: T) => K): Record<K, T[]> {
  const result = {} as Record<K, T[]>;
  for (const item of array) {
    const key = keyFn(item);
    (result[key] ||= []).push(item);
  }
  return result;
}

function findDiversePairs(abilities: Ability[]): [Ability, Ability][] {
  const pairs: [Ability, Ability][] = [];
  for (let i = 0; i < abilities.length; i++) {
    for (let j = i + 1; j < abilities.length; j++) {
      const a = abilities[i], b = abilities[j];
      // Consider diverse if different domains or quads
      if (a.domain !== b.domain || a.quad !== b.quad) {
        pairs.push([a, b]);
      }
    }
  }
  return pairs;
}