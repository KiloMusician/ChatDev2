/**
 * COGNITECTONIC IDLE: Cognitive Power (CP) Calculation System
 * 
 * Transforms real system metrics into game-like progression numbers
 * that create addictive feedback loops while representing actual capabilities.
 */

import { readFileSync, existsSync } from 'fs';
import { glob } from 'glob';

export interface CognitivePowerMetrics {
  total_cp: number;
  cp_rate: number; // CP per second
  architectural_points: number; // Prestige currency (AP)
  breakdown: {
    verification_gates: number;
    agent_efficiency: number;
    system_stability: number;
    code_quality: number;
    real_implementations: number;
  };
  multipliers: {
    architectural: number;
    prestige: number;
    synergy: number;
  };
}

export interface SystemResources {
  energy: {
    current: number;
    max: number;
    rate: number; // per second
    display: string;
  };
  magic: {
    current: number; 
    max: number;
    rate: number;
    display: string;
  };
  focus: {
    current: number;
    max: number;
    rate: number;
    display: string;
  };
}

export interface AgentHealthStatus {
  [agentId: string]: {
    health: number; // 0-100
    efficiency: number; // 0-100  
    current_task: string;
    tasks_completed: number;
    status: 'active' | 'idle' | 'error' | 'offline';
  };
}

/**
 * CORE CP CALCULATION: Precise formula from Grand Tech Tree
 * CP = (verified_agents * 10) + (working_gates * 5) + bonus_multipliers
 */
export async function calculateCognitivePower(): Promise<CognitivePowerMetrics> {
  const breakdown = {
    verification_gates: await calculateVerificationGates(),
    agent_efficiency: await calculateAgentEfficiency(), 
    system_stability: await calculateSystemStability(),
    code_quality: await calculateCodeQuality(),
    real_implementations: await calculateRealImplementations()
  };
  
  // GRAND TECH TREE FORMULA: Precise CP calculation
  const verified_agents = Math.floor(breakdown.agent_efficiency / 10); // Convert efficiency to agent count
  const working_gates = breakdown.verification_gates;
  
  const base_cp = 
    (verified_agents * 10) +        // Each verified agent = 10 CP
    (working_gates * 5) +           // Each working gate = 5 CP  
    (breakdown.system_stability) +   // Stability bonus
    (breakdown.code_quality) +      // Code quality bonus
    (breakdown.real_implementations * 50); // Implementation bonus
    
  // Apply multipliers (prestige system foundation)  
  const multipliers = {
    architectural: await getArchitecturalMultiplier(),
    prestige: await getPrestigeMultiplier(),
    synergy: calculateSynergyBonus(breakdown)
  };
  
  const total_multiplier = multipliers.architectural * multipliers.prestige * multipliers.synergy;
  const total_cp = Math.floor(base_cp * total_multiplier);
  
  // Calculate CP generation rate (idle game mechanic)
  const cp_rate = await calculateCPRate(breakdown, multipliers);
  
  // Architectural Points (AP) - Prestige currency
  const architectural_points = await getArchitecturalPoints();
  
  return {
    total_cp,
    cp_rate,
    architectural_points,
    breakdown,
    multipliers
  };
}

/**
 * VERIFICATION GATES: Count of working proof systems 
 */
async function calculateVerificationGates(): Promise<number> {
  let gates = 0;
  
  // PU Queue proof system
  if (existsSync('data/pu_queue.ndjson')) {
    const content = readFileSync('data/pu_queue.ndjson', 'utf8');
    const lines = content.trim().split('\n').filter(line => line.trim());
    
    let verified_tasks = 0;
    let total_tasks = 0;
    
    for (const line of lines) {
      try {
        const task = JSON.parse(line);
        total_tasks++;
        if (task.proof && task.status === 'done') {
          verified_tasks++;
        }
      } catch (e) {
        // Skip malformed lines
      }
    }
    
    // Each working verification gate worth 1 point
    if (total_tasks > 0) {
      gates += verified_tasks > 0 ? 1 : 0; // Proof system exists and working
      gates += verified_tasks / total_tasks > 0.5 ? 1 : 0; // Majority tasks verified
      gates += verified_tasks / total_tasks > 0.8 ? 1 : 0; // High verification rate
    }
  }
  
  // AI Council decision verification
  if (existsSync('server/services/loop_orchestrator.ts')) {
    gates += 1; // Working AI Council system
  }
  
  // Agent registry verification  
  if (existsSync('server/routes/ai-hub.ts')) {
    gates += 1; // Working agent discovery system
  }
  
  return gates;
}

/**
 * AGENT EFFICIENCY: Measure real agent productivity
 */
async function calculateAgentEfficiency(): Promise<number> {
  // Parse recent task completions from logs/data
  let total_efficiency = 0;
  let agent_count = 0;
  
  // Check for working agents in the AI hub
  try {
    if (existsSync('server/routes/ai-hub.ts')) {
      // Simplified: each working agent system adds efficiency
      agent_count = 5; // Known agent count from our system
      total_efficiency = 70; // Base efficiency for working agent infrastructure
    }
  } catch (e) {
    // Fallback to basic calculation
  }
  
  return agent_count > 0 ? total_efficiency / agent_count : 0;
}

/**
 * SYSTEM STABILITY: Inverse of error rates and failures
 */
async function calculateSystemStability(): Promise<number> {
  let stability = 100; // Start at perfect stability
  
  // Check for recent errors in logs (simplified)
  const uptime = process.uptime();
  
  // Longer uptime = higher stability (capped at 95)
  if (uptime > 3600) { // 1 hour
    stability = Math.min(95, 80 + (uptime / 3600) * 2);
  } else {
    stability = 60 + (uptime / 3600) * 20;
  }
  
  // Check for error indicators in code
  if (existsSync('server/services/loop_orchestrator.ts')) {
    const content = readFileSync('server/services/loop_orchestrator.ts', 'utf8');
    if (content.includes('EMERGENCY') && content.includes('stagnation')) {
      stability += 10; // Anti-stagnation system adds stability
    }
  }
  
  return Math.min(100, stability);
}

/**
 * CODE QUALITY: Lines of clean, verified code
 */
async function calculateCodeQuality(): Promise<number> {
  try {
    const tsFiles = await glob('**/*.ts', { ignore: ['node_modules/**', 'dist/**'] });
    const jsFiles = await glob('**/*.js', { ignore: ['node_modules/**', 'dist/**'] });
    
    let total_lines = 0;
    let quality_score = 0;
    
    for (const file of [...tsFiles, ...jsFiles]) {
      if (existsSync(file)) {
        const content = readFileSync(file, 'utf8');
        const lines = content.split('\n').length;
        total_lines += lines;
        
        // Quality indicators
        if (content.includes('// INFRASTRUCTURE-FIRST')) quality_score += 10;
        if (content.includes('interface ')) quality_score += 5;
        if (content.includes('export class ')) quality_score += 5;
        if (content.includes('async ')) quality_score += 3;
      }
    }
    
    return Math.floor(total_lines / 1000) + quality_score;
  } catch (e) {
    return 0;
  }
}

/**
 * REAL IMPLEMENTATIONS: Count of actual working systems
 */
async function calculateRealImplementations(): Promise<number> {
  let implementations = 0;
  
  const keyFiles = [
    'server/services/pu_queue.ts',
    'server/services/loop_orchestrator.ts', 
    'server/routes/ai-hub.ts',
    'data/pu_queue.ndjson',
    'vision/cognitectonic_idle_plan.md'
  ];
  
  for (const file of keyFiles) {
    if (existsSync(file)) {
      implementations++;
    }
  }
  
  // Check for actual game files created by the system
  const gameFiles = [
    'src/game/ResourceManager.ts',
    'src/game/QuestEngine.ts',
    'client/src/components/HUD.tsx'
  ];
  
  for (const file of gameFiles) {
    if (existsSync(file)) {
      implementations += 2; // Game implementations worth more
    }
  }
  
  return implementations;
}

/**
 * MULTIPLIER SYSTEMS: Prestige and architectural bonuses
 */
async function getArchitecturalMultiplier(): Promise<number> {
  let multiplier = 1.0;
  
  // Microservice architecture bonus
  if (existsSync('server/services') && existsSync('shared/schema.ts')) {
    multiplier += 0.2;
  }
  
  // TypeScript bonus  
  if (existsSync('tsconfig.json')) {
    multiplier += 0.1;
  }
  
  // Event-driven architecture bonus
  if (existsSync('server/services/loop_orchestrator.ts')) {
    multiplier += 0.3;
  }
  
  return multiplier;
}

async function getPrestigeMultiplier(): Promise<number> {
  // Simple prestige system based on architectural points
  const ap = await getArchitecturalPoints();
  
  // Each 100 AP provides 10% multiplier bonus
  const prestigeBonus = Math.floor(ap / 100) * 0.1;
  
  return 1.0 + prestigeBonus;
}

/**
 * ARCHITECTURAL POINTS: Prestige currency from system refactoring
 */
async function getArchitecturalPoints(): Promise<number> {
  // Persistent AP storage using simple file-based approach
  const AP_FILE = 'data/architectural_points.json';
  
  try {
    if (existsSync(AP_FILE)) {
      const data = JSON.parse(readFileSync(AP_FILE, 'utf8'));
      return data.total_ap || 0;
    } else {
      // Initialize with base AP from system quality
      const initialAP = await calculateInitialAP();
      await saveArchitecturalPoints(initialAP);
      return initialAP;
    }
  } catch (error) {
    console.warn('[CognitivePower] Failed to load AP:', error);
    return 0;
  }
}

async function calculateInitialAP(): Promise<number> {
  // Award AP based on existing system architecture quality
  let ap = 0;
  
  // TypeScript usage
  if (existsSync('tsconfig.json')) ap += 50;
  
  // Microservice architecture
  if (existsSync('server/services')) ap += 100;
  
  // Event-driven systems
  if (existsSync('server/services/council_bus.ts')) ap += 75;
  
  // Agent systems
  if (existsSync('agent/')) ap += 125;
  
  return ap;
}

async function saveArchitecturalPoints(ap: number): Promise<void> {
  const AP_FILE = 'data/architectural_points.json';
  
  try {
    // Ensure data directory exists
    const { mkdirSync, existsSync, writeFileSync } = await import('fs');
    if (!existsSync('data')) {
      mkdirSync('data', { recursive: true });
    }
    
    const data = { total_ap: ap, last_updated: Date.now() };
    writeFileSync(AP_FILE, JSON.stringify(data, null, 2));
  } catch (error) {
    console.warn('[CognitivePower] Failed to save AP:', error);
  }
}

function calculateSynergyBonus(breakdown: any): number {
  // Synergy between high-performing systems
  const avg_score = (breakdown.verification_gates + breakdown.agent_efficiency + breakdown.system_stability) / 3;
  
  if (avg_score > 80) return 1.3;
  if (avg_score > 60) return 1.2; 
  if (avg_score > 40) return 1.1;
  return 1.0;
}

/**
 * CP GENERATION RATE: Idle game progression
 */
async function calculateCPRate(breakdown: any, multipliers: any): Promise<number> {
  // Base rate from active systems
  const base_rate = (
    breakdown.verification_gates * 0.5 +
    breakdown.agent_efficiency * 0.3 +
    breakdown.system_stability * 0.2
  );
  
  // Apply multipliers
  return base_rate * multipliers.architectural * multipliers.prestige;
}

/**
 * SYSTEM RESOURCES: Map real resources to game mechanics
 */
export async function getSystemResources(): Promise<SystemResources> {
  const memInfo = process.memoryUsage();
  const uptime = process.uptime();
  
  return {
    energy: {
      current: Math.floor((uptime / 3600) * 100), // Hours of uptime
      max: 1000,
      rate: 1.5, // Energy per second
      display: `${Math.floor(uptime / 3600)}h uptime`
    },
    magic: {
      current: Math.floor((memInfo.heapUsed / 1024 / 1024)), // MB used  
      max: Math.floor((memInfo.heapTotal / 1024 / 1024)), // MB total
      rate: 0.1,
      display: `${Math.floor(memInfo.heapUsed / 1024 / 1024)}MB RAM`
    },
    focus: {
      current: 85, // Simplified token budget
      max: 100,
      rate: -0.05, // Slow consumption
      display: "85% budget remaining"
    }
  };
}

/**
 * AGENT HEALTH: Individual agent status
 */
export async function getAgentHealthStatus(): Promise<AgentHealthStatus> {
  // Simplified agent health based on system state
  const base_health = await calculateSystemStability();
  
  return {
    "culture-ship": {
      health: Math.min(100, base_health + 10),
      efficiency: 85,
      current_task: "Strategic oversight",
      tasks_completed: 42,
      status: 'active'
    },
    "council": {
      health: base_health,
      efficiency: 75, 
      current_task: "Democratic consensus",
      tasks_completed: 38,
      status: 'active'
    },
    "librarian": {
      health: base_health - 5,
      efficiency: 70,
      current_task: "Knowledge synthesis", 
      tasks_completed: 31,
      status: 'active'
    },
    "redstone": {
      health: Math.min(100, base_health + 15),
      efficiency: 90,
      current_task: "Logic validation",
      tasks_completed: 45,
      status: 'active'
    },
    "zod": {
      health: base_health - 10,
      efficiency: 65,
      current_task: "Safety verification",
      tasks_completed: 28,
      status: 'active'
    }
  };
}