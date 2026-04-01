import { readdirSync, statSync } from 'fs';
import path from 'path';
import { log } from './log.js';

const LOG_PLANNER = process.env.LOG_PLANNER === '1';

function logPlanner(message: string, data?: any) {
  if (!LOG_PLANNER) return;
  log.info(data, message);
}

type CascadeContext = {
  prompt: string;
  origin: string;
  meta: any;
  timestamp: number;
  budget_available: number;
  cognitive_state: any;
};

type AutonomousStep = {
  id: string;
  type: string;
  description: string;
  priority: number;
  dependencies: string[];
  estimated_cost: number;
  phase: string;
  files_affected: string[];
  neural_context: string[];
};

// Neural network mapping of repository structure
function mapRepositoryNeuralNetwork(): Map<string, string[]> {
  const neuralMap = new Map<string, string[]>();
  
  // Key directories as neural nodes
  const nodes = [
    'server', 'client', 'shared', 'ai-systems', 'system', 
    'ml', 'tests', 'docs', 'scripts', 'config'
  ];
  
  nodes.forEach(node => {
    try {
      const fullPath = path.join(process.cwd(), node);
      if (statSync(fullPath).isDirectory()) {
        const connections = scanDirectoryConnections(fullPath);
        neuralMap.set(node, connections);
      }
    } catch (error) {
      // Directory doesn't exist, skip
    }
  });
  
  return neuralMap;
}

function scanDirectoryConnections(dirPath: string): string[] {
  try {
    const files = readdirSync(dirPath);
    return files
      .filter(file => file.endsWith('.ts') || file.endsWith('.js'))
      .slice(0, 10); // Limit connections per node
  } catch {
    return [];
  }
}

// Generate the "500 steps" Rube Goldberg machine
export async function generateAutonomousSteps(context: CascadeContext): Promise<AutonomousStep[]> {
  logPlanner(`[PLANNER] Generating autonomous plan`, { prompt: context.prompt });
  
  const neuralMap = mapRepositoryNeuralNetwork();
  const steps: AutonomousStep[] = [];
  
  // Phase 1: Infrastructure Foundation (1-100)
  steps.push(...generateInfrastructureSteps(context, neuralMap));
  
  // Phase 2: Core Systems (101-200)
  steps.push(...generateCoreSystemSteps(context, neuralMap));
  
  // Phase 3: AI & Intelligence (201-300)
  steps.push(...generateAISteps(context, neuralMap));
  
  // Phase 4: Game & Simulation (301-400)
  steps.push(...generateGameSteps(context, neuralMap));
  
  // Phase 5: Optimization & Enhancement (401-500)
  steps.push(...generateOptimizationSteps(context, neuralMap));
  
  logPlanner(`[PLANNER] Generated ${steps.length} autonomous operations`, { count: steps.length });
  return steps;
}

function generateInfrastructureSteps(
  context: CascadeContext, 
  neuralMap: Map<string, string[]>
): AutonomousStep[] {
  const steps: AutonomousStep[] = [];
  
  // Infrastructure steps based on prompt analysis
  const infraTemplates = [
    { type: 'enhance_error_handling', description: 'Strengthen error boundaries and logging' },
    { type: 'optimize_build_process', description: 'Streamline compilation and bundling' },
    { type: 'secure_endpoints', description: 'Harden API security and validation' },
    { type: 'improve_performance', description: 'Optimize server response times' },
    { type: 'enhance_monitoring', description: 'Expand health checks and metrics' }
  ];
  
  infraTemplates.forEach((template, index) => {
    steps.push({
      id: `infra_${index + 1}`,
      type: template.type,
      description: template.description,
      priority: 10 - index,
      dependencies: [],
      estimated_cost: 50,
      phase: 'infrastructure',
      files_affected: ['server/index.ts', 'shared/types.ts'],
      neural_context: Array.from(neuralMap.keys())
    });
  });
  
  // Generate 95 more infrastructure steps...
  for (let i = 5; i < 100; i++) {
    steps.push({
      id: `infra_${i + 1}`,
      type: 'infrastructure_enhancement',
      description: `Infrastructure optimization step ${i + 1}`,
      priority: i % 10,
      dependencies: i > 10 ? [`infra_${i - 5}`] : [],
      estimated_cost: 25,
      phase: 'infrastructure',
      files_affected: getRandomFiles(neuralMap),
      neural_context: getRandomConnections(neuralMap)
    });
  }
  
  return steps;
}

function generateCoreSystemSteps(
  context: CascadeContext, 
  neuralMap: Map<string, string[]>
): AutonomousStep[] {
  const steps: AutonomousStep[] = [];
  
  // Generate 100 core system steps
  for (let i = 0; i < 100; i++) {
    steps.push({
      id: `core_${i + 1}`,
      type: 'core_system',
      description: `Core system enhancement ${i + 1}`,
      priority: i % 10,
      dependencies: i > 5 ? [`core_${i - 3}`] : [],
      estimated_cost: 35,
      phase: 'core_systems',
      files_affected: getRandomFiles(neuralMap),
      neural_context: getRandomConnections(neuralMap)
    });
  }
  
  return steps;
}

function generateAISteps(
  context: CascadeContext, 
  neuralMap: Map<string, string[]>
): AutonomousStep[] {
  const steps: AutonomousStep[] = [];
  
  // Generate 100 AI enhancement steps
  for (let i = 0; i < 100; i++) {
    steps.push({
      id: `ai_${i + 1}`,
      type: 'ai_enhancement',
      description: `AI system improvement ${i + 1}`,
      priority: i % 10,
      dependencies: i > 3 ? [`ai_${i - 2}`] : [],
      estimated_cost: 45,
      phase: 'ai_intelligence',
      files_affected: ['ai-systems/', 'system/llm/'].map(p => p + 'enhancement.ts'),
      neural_context: ['ai-systems', 'system']
    });
  }
  
  return steps;
}

function generateGameSteps(
  context: CascadeContext, 
  neuralMap: Map<string, string[]>
): AutonomousStep[] {
  const steps: AutonomousStep[] = [];
  
  // Generate 100 game development steps
  for (let i = 0; i < 100; i++) {
    steps.push({
      id: `game_${i + 1}`,
      type: 'game_enhancement',
      description: `Game system development ${i + 1}`,
      priority: i % 10,
      dependencies: i > 7 ? [`game_${i - 5}`] : [],
      estimated_cost: 40,
      phase: 'game_simulation',
      files_affected: getRandomFiles(neuralMap),
      neural_context: getRandomConnections(neuralMap)
    });
  }
  
  return steps;
}

function generateOptimizationSteps(
  context: CascadeContext, 
  neuralMap: Map<string, string[]>
): AutonomousStep[] {
  const steps: AutonomousStep[] = [];
  
  // Generate 100 optimization steps
  for (let i = 0; i < 100; i++) {
    steps.push({
      id: `opt_${i + 1}`,
      type: 'optimization',
      description: `System optimization ${i + 1}`,
      priority: i % 10,
      dependencies: i > 10 ? [`opt_${i - 8}`] : [],
      estimated_cost: 30,
      phase: 'optimization',
      files_affected: getRandomFiles(neuralMap),
      neural_context: getRandomConnections(neuralMap)
    });
  }
  
  return steps;
}

let _fileSelectIdx = 0;
function getRandomFiles(neuralMap: Map<string, string[]>): string[] {
  const allNodes = Array.from(neuralMap.keys());
  if (allNodes.length === 0) return [];
  const node = allNodes[_fileSelectIdx++ % allNodes.length];
  if (!node) return [];
  return (neuralMap.get(node) || []).slice(0, 2);
}

function getRandomConnections(neuralMap: Map<string, string[]>): string[] {
  const allNodes = Array.from(neuralMap.keys());
  return allNodes.slice(0, 3);
}
