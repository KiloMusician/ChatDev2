/**
 * 🌊 CASCADE EVENT PLANNER - Culture-Ship Planning Component
 * Zero-token cascade planning with local-first prioritization
 */

interface CascadeStep {
  id: string;
  kind: "consolidate" | "fix" | "refactor" | "test" | "analyze";
  title: string;
  description: string;
  benefit: number;
  cost: number;
  reversible: boolean;
  payload?: any;
  execute?: () => Promise<void>;
}

interface CascadePlan {
  id: string;
  timestamp: string;
  health_score: number;
  token_budget: { used: number; max: number };
  steps: CascadeStep[];
  narrative: string;
}

interface CascadeInput {
  findings?: any;
  health_score?: number;
  token_budget?: { used: number; max: number };
  checkpoint?: boolean;
}

export async function runCascade(input: CascadeInput): Promise<CascadePlan> {
  console.log("🌊 Culture-Ship: Running cascade event planner...");
  
  if (input.checkpoint) {
    // Checkpoint mode - just prepare next cycle
    return {
      id: `cascade_${Date.now()}`,
      timestamp: new Date().toISOString(),
      health_score: input.health_score || 1.0,
      token_budget: input.token_budget || { used: 0, max: 100 },
      steps: [],
      narrative: "Checkpoint saved, ready for next cycle"
    };
  }
  
  const { findings, health_score = 1.0, token_budget = { used: 0, max: 100 } } = input;
  const steps: CascadeStep[] = [];
  
  // Generate steps based on findings
  if (findings?.duplicates?.duplicates?.length > 0) {
    steps.push({
      id: "consolidate_duplicates",
      kind: "consolidate",
      title: "Consolidate duplicate files",
      description: `Merge ${findings.duplicates.duplicates.length} duplicate groups`,
      benefit: findings.duplicates.duplicates.length * 2,
      cost: 1,
      reversible: true,
      payload: { duplicates: findings.duplicates.duplicates }
    });
  }
  
  if (findings?.imports?.brokenImports > 0) {
    steps.push({
      id: "fix_imports",
      kind: "fix", 
      title: "Fix broken imports",
      description: `Repair ${findings.imports.brokenImports} broken import statements`,
      benefit: findings.imports.brokenImports * 3,
      cost: 2,
      reversible: true,
      payload: { issues: findings.imports.issues }
    });
  }
  
  if (findings?.softlocks?.criticalIssues > 0) {
    steps.push({
      id: "fix_softlocks",
      kind: "fix",
      title: "Resolve softlock risks", 
      description: `Fix ${findings.softlocks.criticalIssues} critical performance issues`,
      benefit: findings.softlocks.criticalIssues * 5,
      cost: 3,
      reversible: true,
      payload: { issues: findings.softlocks.issues }
    });
  }
  
  // Sort by benefit/cost ratio
  steps.sort((a, b) => (b.benefit / b.cost) - (a.benefit / a.cost));
  
  // Generate narrative
  const narrative = generateNarrative(health_score, steps, token_budget);
  
  const plan: CascadePlan = {
    id: `cascade_${Date.now()}`,
    timestamp: new Date().toISOString(),
    health_score,
    token_budget,
    steps: steps.slice(0, 5), // Limit to top 5 steps
    narrative
  };
  
  console.log(`📋 Generated cascade plan: ${plan.steps.length} steps, priority focus on ${plan.steps[0]?.kind || 'maintenance'}`);
  return plan;
}

function generateNarrative(healthScore: number, steps: CascadeStep[], budget: { used: number; max: number }): string {
  const budgetPercent = (budget.used / budget.max) * 100;
  const healthPercent = Math.round(healthScore * 100);
  
  let narrative = `System health at ${healthPercent}%. `;
  
  if (budgetPercent > 80) {
    narrative += "Operating in budget-conservation mode. ";
  } else if (budgetPercent > 50) {
    narrative += "Budget usage moderate, proceeding with optimization. ";
  } else {
    narrative += "Budget available for comprehensive improvements. ";
  }
  
  if (steps.length === 0) {
    narrative += "System stable, maintaining watch for new optimization opportunities.";
  } else {
    const primaryFocus = steps[0]?.kind;
    narrative += `Primary focus: ${primaryFocus} operations. ${steps.length} enhancement steps queued.`;
  }
  
  return narrative;
}