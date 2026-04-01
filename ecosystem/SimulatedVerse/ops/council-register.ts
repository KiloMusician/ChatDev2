#!/usr/bin/env tsx
/**
 * ΞNuSyQ Council Registration - Agent Party Orchestrator
 * Capabilities matrix with LLM-verifiable JSON contracts
 */
import { writeReport } from "./receipts.js";

type AgentCapability = "fix_error" | "run_tests" | "check_system_health" | 
                       "read_topology" | "anneal_repo" | "cascade_ship" | 
                       "refresh_ui" | "plan_game_tier";

type Agent = {
  id: string;
  role: string;
  name: string;
  capabilities: AgentCapability[];
  health_endpoint?: string;
  runner: "in-process" | "replit-agent" | "external";
  enabled: boolean;
};

const COUNCIL_AGENTS: Agent[] = [
  {
    id: "raven",
    role: "skeptic",
    name: "Raven (Skeptic)",
    capabilities: ["check_system_health", "fix_error", "read_topology"],
    runner: "in-process",
    enabled: true
  },
  {
    id: "mladenc",
    role: "planner", 
    name: "𝕄ₗₐ⧉𝕕𝕖𝕟𝕔 (Planner)",
    capabilities: ["plan_game_tier", "read_topology", "anneal_repo"],
    runner: "in-process",
    enabled: true
  },
  {
    id: "librarian",
    role: "memory",
    name: "Librarian (Memory Keeper)",
    capabilities: ["read_topology", "anneal_repo"],
    runner: "in-process", 
    enabled: true
  },
  {
    id: "artificer",
    role: "builder",
    name: "Artificer (Builder)",
    capabilities: ["fix_error", "run_tests", "refresh_ui"],
    runner: "in-process",
    enabled: true
  },
  {
    id: "alchemist",
    role: "stabilizer",
    name: "Alchemist (Stabilizer)",
    capabilities: ["fix_error", "check_system_health", "cascade_ship"],
    runner: "in-process",
    enabled: true
  },
  {
    id: "protagonist",
    role: "integration",
    name: "Protagonist (Integration)",
    capabilities: ["cascade_ship", "refresh_ui", "plan_game_tier"],
    runner: "in-process",
    enabled: true
  }
];

export function getCapabilityMatrix() {
  const matrix: Record<AgentCapability, string[]> = {
    fix_error: [],
    run_tests: [],
    check_system_health: [],
    read_topology: [],
    anneal_repo: [],
    cascade_ship: [],
    refresh_ui: [],
    plan_game_tier: []
  };
  
  for (const agent of COUNCIL_AGENTS) {
    if (!agent.enabled) continue;
    
    for (const capability of agent.capabilities) {
      matrix[capability].push(agent.id);
    }
  }
  
  return matrix;
}

export async function registerCouncil() {
  const matrix = getCapabilityMatrix();
  const health = await checkAgentHealth();
  
  const registration = {
    timestamp: Date.now(),
    agents: COUNCIL_AGENTS,
    capabilities: matrix,
    health,
    llm_routing: {
      gateway_url: "http://127.0.0.1:4455/llm/chat",
      fallback_mode: "heuristic"
    }
  };
  
  writeReport("council_register.json", registration);
  return registration;
}

async function checkAgentHealth() {
  const health: Record<string, any> = {};
  
  for (const agent of COUNCIL_AGENTS) {
    if (!agent.enabled) {
      health[agent.id] = { status: "disabled" };
      continue;
    }
    
    // For in-process agents, assume healthy if no explicit check
    health[agent.id] = {
      status: "operational",
      last_seen: Date.now(),
      runner: agent.runner
    };
  }
  
  return health;
}

// Auto-register when executed
if (import.meta.url === `file://${process.argv[1]}`) {
  registerCouncil().then(() => {
    console.log("[Council] Registration complete");
    process.exit(0);
  });
}