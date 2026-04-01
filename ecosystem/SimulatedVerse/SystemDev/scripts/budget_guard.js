#!/usr/bin/env node
/**
 * 💰 Budget Guard - Infrastructure-First Budget Enforcement
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Prevents runaway autonomous operations by enforcing budget constraints
 */

const fs = require('fs');
const path = require('path');

// **BUDGET CONFIGURATION**
const BUDGET_LIMITS = {
  daily_max: 100,           // Maximum daily operations
  entropy_threshold: 0.7,   // Stop auto-operations if entropy too high
  file_change_limit: 50,    // Max files changed per PR
  pr_size_limit: 10000,     // Max lines changed per PR
  concurrent_prs: 5         // Max open autonomous PRs
};

// **BUDGET TRACKING**
function getBudgetStatus() {
  const budgetFile = path.join(process.cwd(), 'data', 'budget.json');
  
  try {
    if (fs.existsSync(budgetFile)) {
      return JSON.parse(fs.readFileSync(budgetFile, 'utf8'));
    }
  } catch (error) {
    console.warn('[Budget] Could not read budget file:', error.message);
  }
  
  // **DEFAULT BUDGET STATE**
  return {
    daily_used: 0,
    entropy_score: 0,
    last_reset: new Date().toISOString().split('T')[0],
    operations_today: 0,
    status: 'healthy'
  };
}

// **ENTROPY CALCULATION** - Based on recent failures, complexity
function calculateEntropy() {
  // Check for recent errors, failed tests, merge conflicts
  let entropy = 0;
  
  // Add entropy for various risk factors
  const errorLogs = process.env.ERROR_COUNT || '0';
  entropy += Math.min(parseInt(errorLogs) * 0.1, 0.3);
  
  // Add entropy for system complexity
  const puQueueSize = process.env.PU_QUEUE_SIZE || '0';
  entropy += Math.min(parseInt(puQueueSize) * 0.01, 0.2);
  
  return Math.min(entropy, 1.0);
}

// **MAIN BUDGET CHECK**
function main() {
  console.log('[Budget] 💰 Running Infrastructure-First budget validation...');
  
  const budget = getBudgetStatus();
  const entropy = calculateEntropy();
  
  console.log(`[Budget] Daily usage: ${budget.daily_used}/${BUDGET_LIMITS.daily_max}`);
  console.log(`[Budget] Entropy score: ${entropy.toFixed(3)}`);
  console.log(`[Budget] Operations today: ${budget.operations_today}`);
  
  // **HARD LIMITS** - Fail CI if exceeded
  if (budget.daily_used > BUDGET_LIMITS.daily_max) {
    console.error('[Budget] ❌ HARD LIMIT: Daily budget exceeded');
    console.error('[Budget] 🛑 Blocking autonomous operations');
    process.exit(1);
  }
  
  if (entropy > BUDGET_LIMITS.entropy_threshold) {
    console.error('[Budget] ❌ ENTROPY LIMIT: System too unstable for auto-merge');
    console.error('[Budget] 🛑 Manual review required');
    process.exit(1);
  }
  
  // **SOFT WARNINGS** - Log but don't fail
  if (budget.daily_used > BUDGET_LIMITS.daily_max * 0.8) {
    console.warn('[Budget] ⚠️  SOFT WARNING: 80% of daily budget used');
    console.warn('[Budget] 🔄 Consider throttling autonomous operations');
  }
  
  console.log('[Budget] ✅ Budget validation passed');
  console.log('[Budget] 🚀 Autonomous operations approved');
  
  // **UPDATE BUDGET** - Increment usage
  budget.operations_today += 1;
  budget.daily_used += 1;
  budget.entropy_score = entropy;
  budget.last_check = new Date().toISOString();
  
  // Save updated budget (best effort)
  try {
    const budgetDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(budgetDir)) {
      fs.mkdirSync(budgetDir, { recursive: true });
    }
    fs.writeFileSync(
      path.join(budgetDir, 'budget.json'), 
      JSON.stringify(budget, null, 2)
    );
  } catch (error) {
    console.warn('[Budget] Could not save budget file:', error.message);
  }
  
  process.exit(0);
}

// **ENTRY POINT**
if (require.main === module) {
  main();
}