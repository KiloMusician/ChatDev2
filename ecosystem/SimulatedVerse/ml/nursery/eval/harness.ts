// **EVALUATION HARNESS** - Score generations without online LLM calls
import { markovGen, evaluateMarkovOutput } from './toy_markov.js';

export interface EvalResult {
  id: string;
  input: any;
  output: any;
  score: number;
  metrics: Record<string, number>;
  timestamp: number;
}

export interface EvalSuite {
  name: string;
  description: string;
  cases: EvalCase[];
}

export interface EvalCase {
  id: string;
  description: string;
  input: any;
  expectedOutput?: any;
  scorer: (input: any, output: any, expected?: any) => EvalResult;
}

// **TEXT GENERATION EVALUATION**
export function createTextGenEval(): EvalSuite {
  return {
    name: "Text Generation Quality",
    description: "Evaluate Markov chain text generation quality",
    cases: [
      {
        id: "coherence_test",
        description: "Generate coherent technology lore",
        input: {
          theme: "technology",
          length: 25,
          corpus: "Advanced quantum processors integrate seamlessly with distributed consciousness networks. Neural pathways optimize resource allocation through predictive algorithms and recursive self-improvement mechanisms."
        },
        scorer: (input, output) => {
          const generated = markovGen(input.corpus, 2, input.length);
          const stats = evaluateMarkovOutput(generated, input.corpus);
          
          // Score based on coherence and creativity
          const coherenceScore = stats.coherenceScore;
          const creativityScore = 1 - stats.repetitionRate;
          const lengthScore = Math.min(1, generated.split(' ').length / input.length);
          
          const finalScore = (coherenceScore * 0.5 + creativityScore * 0.3 + lengthScore * 0.2);
          
          return {
            id: "coherence_test",
            input,
            output: generated,
            score: finalScore,
            metrics: {
              coherence: coherenceScore,
              creativity: creativityScore,
              length: lengthScore,
              uniqueTokens: stats.uniqueTokens,
              repetitionRate: stats.repetitionRate
            },
            timestamp: Date.now()
          };
        }
      },
      
      {
        id: "variety_test", 
        description: "Generate diverse outputs from same input",
        input: {
          corpus: "The colony expands through careful automation. Citizens contribute unique skills while collective intelligence guides growth patterns.",
          runs: 5
        },
        scorer: (input, output) => {
          const generations = [];
          for (let i = 0; i < input.runs; i++) {
            generations.push(markovGen(input.corpus, 2, 20));
          }
          
          // Calculate diversity - how different are the generations?
          const uniqueSets = generations.map(gen => new Set(gen.toLowerCase().split(' ')));
          let totalOverlap = 0;
          let comparisons = 0;
          
          for (let i = 0; i < uniqueSets.length; i++) {
            for (let j = i + 1; j < uniqueSets.length; j++) {
              const overlap = [...uniqueSets[i]].filter(token => uniqueSets[j].has(token)).length;
              const union = new Set([...uniqueSets[i], ...uniqueSets[j]]).size;
              totalOverlap += overlap / union;
              comparisons++;
            }
          }
          
          const diversityScore = 1 - (totalOverlap / comparisons);
          
          return {
            id: "variety_test",
            input,
            output: generations,
            score: diversityScore,
            metrics: {
              diversity: diversityScore,
              avgLength: generations.reduce((sum, gen) => sum + gen.length, 0) / generations.length,
              runs: input.runs
            },
            timestamp: Date.now()
          };
        }
      }
    ]
  };
}

// **AGENT DECISION EVALUATION**
export function createAgentDecisionEval(): EvalSuite {
  return {
    name: "Agent Decision Quality",
    description: "Evaluate agent decision-making in game scenarios",
    cases: [
      {
        id: "resource_management",
        description: "Agent should buy materials when energy is high",
        input: {
          gameState: { resources: { energy: 90, materials: 10 }, tick: 50 }
        },
        scorer: (input, output) => {
          // Simple rule: if energy > 80, should buy materials
          const shouldBuy = input.gameState.resources.energy > 80;
          const didBuy = output?.action === "buy" && output?.payload?.item === "materials";
          
          const score = shouldBuy === didBuy ? 1 : 0;
          
          return {
            id: "resource_management", 
            input,
            output,
            score,
            metrics: {
              expectedAction: shouldBuy ? "buy_materials" : "other",
              actualAction: output?.action || "none",
              correctDecision: score
            },
            timestamp: Date.now()
          };
        }
      },
      
      {
        id: "efficiency_test",
        description: "Agent should prefer high-value actions",
        input: {
          gameState: { resources: { energy: 50, materials: 30, components: 5 }, tick: 100 },
          options: ["tick", "buy_materials", "buy_components", "upgrade"]
        },
        scorer: (input, output) => {
          // Value ranking: upgrade > buy_components > buy_materials > tick
          const valueRanking = { upgrade: 4, buy_components: 3, buy_materials: 2, tick: 1 };
          const actionValue = valueRanking[output?.action as keyof typeof valueRanking] || 0;
          const maxValue = Math.max(...Object.values(valueRanking));
          
          const score = actionValue / maxValue;
          
          return {
            id: "efficiency_test",
            input,
            output, 
            score,
            metrics: {
              actionValue,
              maxValue,
              efficiency: score,
              action: output?.action || "none"
            },
            timestamp: Date.now()
          };
        }
      }
    ]
  };
}

// **EVALUATION RUNNER**
export class EvalRunner {
  private results: Map<string, EvalResult[]> = new Map();
  
  async runSuite(suite: EvalSuite): Promise<EvalResult[]> {
    const suiteResults: EvalResult[] = [];
    
    console.log(`[EVAL] Running suite: ${suite.name}`);
    
    for (const evalCase of suite.cases) {
      try {
        const result = evalCase.scorer(evalCase.input, null, evalCase.expectedOutput);
        suiteResults.push(result);
        
        console.log(`[EVAL] ${evalCase.id}: ${result.score.toFixed(3)}`);
      } catch (error) {
        console.error(`[EVAL] Failed case ${evalCase.id}:`, error);
        
        suiteResults.push({
          id: evalCase.id,
          input: evalCase.input,
          output: null,
          score: 0,
          metrics: { error: 1 },
          timestamp: Date.now()
        });
      }
    }
    
    this.results.set(suite.name, suiteResults);
    return suiteResults;
  }
  
  getSuiteStats(suiteName: string): { avgScore: number; count: number; passRate: number } | null {
    const results = this.results.get(suiteName);
    if (!results || results.length === 0) return null;
    
    const avgScore = results.reduce((sum, r) => sum + r.score, 0) / results.length;
    const passCount = results.filter(r => r.score > 0.7).length;
    const passRate = passCount / results.length;
    
    return { avgScore, count: results.length, passRate };
  }
  
  getAllResults(): Record<string, EvalResult[]> {
    return Object.fromEntries(this.results);
  }
  
  exportResults(): string {
    const allResults = this.getAllResults();
    return JSON.stringify(allResults, null, 2);
  }
}

// **QUICK EVALUATION FUNCTIONS**
export function runQuickTextEval(): EvalResult[] {
  const runner = new EvalRunner();
  const textSuite = createTextGenEval();
  return runner.runSuite(textSuite);
}

export function runQuickAgentEval(): EvalResult[] {
  const runner = new EvalRunner();
  const agentSuite = createAgentDecisionEval();
  return runner.runSuite(agentSuite);
}