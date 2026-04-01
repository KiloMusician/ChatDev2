// **LOW-HANGING FRUIT HINT GENERATOR**
interface Hint {
  id: string;
  title: string;
  kind: "critical" | "high" | "medium" | "low";
  impact: number; // 1-10
  effort: number; // 1-10  
  action?: string;
  path?: string;
}

interface SystemState {
  queue_size: number;
  budget_used: number;
  budget_max: number;
  entropy: number;
  system_ready: boolean;
  seeds_complete: boolean;
}

export function computeHints(state: SystemState): Hint[] {
  const hints: Hint[] = [];
  
  // **Critical Infrastructure Fixes**
  if (!state.system_ready) {
    hints.push({
      id: "H1",
      title: "System not ready - check initialization",
      kind: "critical", 
      impact: 10,
      effort: 2,
      action: "Check /readyz endpoint for specific issues"
    });
  }
  
  if (state.entropy > 0.3) {
    hints.push({
      id: "H2", 
      title: "High entropy detected - system instability",
      kind: "critical",
      impact: 9,
      effort: 3,
      action: "Review error logs and reduce error rate"
    });
  }
  
  // **Budget Management**
  const budgetPct = (state.budget_used / state.budget_max) * 100;
  if (budgetPct > 90) {
    hints.push({
      id: "H3",
      title: "Budget critical - throttling active",
      kind: "critical",
      impact: 8, 
      effort: 1,
      action: "Wait for budget recovery or increase limits"
    });
  } else if (budgetPct > 70) {
    hints.push({
      id: "H4",
      title: "Budget warning - consider lighter tasks",
      kind: "high",
      impact: 6,
      effort: 2,
      action: "Queue smaller PUs or wait for recovery"
    });
  }
  
  // **Queue Optimization**
  if (state.queue_size > 50) {
    hints.push({
      id: "H5",
      title: "Large queue - consider batch processing", 
      kind: "medium",
      impact: 5,
      effort: 4,
      action: "Group similar tasks or increase processing rate"
    });
  }
  
  if (state.queue_size === 0) {
    hints.push({
      id: "H6",
      title: "Empty queue - ready for new tasks",
      kind: "low",
      impact: 3,
      effort: 1,
      action: "Seed new task batches or run ZETA generation"
    });
  }
  
  // **Performance Opportunities**
  hints.push({
    id: "H7",
    title: "Run null-safety sweep on UI components",
    kind: "high",
    impact: 7,
    effort: 3,
    action: "Apply safeNumber/safePercent to all numeric displays"
  });
  
  hints.push({
    id: "H8", 
    title: "Add SPA fallback to prevent white screens",
    kind: "high",
    impact: 8,
    effort: 2,
    action: "Ensure all routes have proper error boundaries"
  });
  
  // **Documentation & Knowledge**
  if (state.seeds_complete) {
    hints.push({
      id: "H9",
      title: "Generate missing API documentation",
      kind: "medium", 
      impact: 4,
      effort: 5,
      action: "Run DocPU generator for undocumented endpoints"
    });
  }
  
  // Sort by impact/effort ratio (highest impact, lowest effort first)
  return hints.sort((a, b) => {
    const scoreA = a.impact / a.effort;
    const scoreB = b.impact / b.effort;
    return scoreB - scoreA;
  });
}