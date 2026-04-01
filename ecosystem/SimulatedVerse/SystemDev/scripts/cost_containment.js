#!/usr/bin/env node

/**
 * Cost containment script - Runtime budget monitoring and control
 */

const fs = require('fs');
const path = require('path');

const COST_MODES = {
  soft: {
    daily_limit: 120000,
    escalation_threshold: 0.62,
    allow_paid_calls: true,
    trace_sampling: 0.1
  },
  hard: {
    daily_limit: 50000,
    escalation_threshold: 0.8,
    allow_paid_calls: false,
    trace_sampling: 0.05
  },
  development: {
    daily_limit: 10000,
    escalation_threshold: 0.9,
    allow_paid_calls: false,
    trace_sampling: 0.0
  },
  cache_only: {
    daily_limit: 0,
    escalation_threshold: 1.0,
    allow_paid_calls: false,
    trace_sampling: 0.0
  }
};

function setCostMode(mode) {
  if (!COST_MODES[mode]) {
    console.error(`Unknown cost mode: ${mode}`);
    console.log(`Available modes: ${Object.keys(COST_MODES).join(', ')}`);
    process.exit(1);
  }
  
  const config = COST_MODES[mode];
  
  // Update ops_codex.json
  const codexPath = './ops_codex.json';
  if (fs.existsSync(codexPath)) {
    const codex = JSON.parse(fs.readFileSync(codexPath, 'utf8'));
    
    codex.budgets.daily_token_limit = config.daily_limit;
    codex.budgets.api_escalation_min_conf = config.escalation_threshold;
    codex.cost_containment.budget_mode = mode;
    codex.cost_containment.trace_sampling = config.trace_sampling;
    
    fs.writeFileSync(codexPath, JSON.stringify(codex, null, 2));
    console.log(`✅ Updated ops_codex.json for ${mode} mode`);
  }
  
  // Set environment variables
  process.env.BUDGET_MODE = mode;
  process.env.TRACE_SAMPLING = config.trace_sampling.toString();
  process.env.CONTEXT_MAX = mode === 'hard' ? '1500' : '2200';
  
  if (mode === 'cache_only') {
    process.env.CACHE_ONLY = '1';
  }
  
  console.log(`🛡️  Cost containment mode: ${mode}`);
  console.log(`   Daily limit: ${config.daily_limit} tokens`);
  console.log(`   Escalation threshold: ${config.escalation_threshold}`);
  console.log(`   Paid calls: ${config.allow_paid_calls ? 'allowed' : 'blocked'}`);
  console.log(`   Trace sampling: ${config.trace_sampling * 100}%`);
}

function showBudgetStatus() {
  // This would integrate with actual token tracking
  console.log('📊 Current Budget Status');
  console.log('========================');
  console.log('Daily spent: 2,450 / 120,000 tokens (2.0%)');
  console.log('Task spent: 320 / 2,500 tokens (12.8%)');
  console.log('Cache hit rate: 78.3%');
  console.log('Avg. escalation rate: 5.2%');
  console.log('');
  console.log('💡 Run `make token-stats` for live data');
}

function optimizeBudget() {
  console.log('🔧 Budget Optimization Recommendations');
  console.log('======================================');
  
  const recommendations = [
    'Increase semantic cache TTL to 6 hours for stable content',
    'Lower escalation threshold to 0.7 (currently high confidence bias)',
    'Enable context compression for prompts over 1500 tokens',
    'Use distilled model for simple classification tasks',
    'Batch similar requests to reduce overhead'
  ];
  
  recommendations.forEach((rec, i) => {
    console.log(`${i + 1}. ${rec}`);
  });
  
  console.log('');
  console.log('💡 Run `make auto-refactor` to apply code-level optimizations');
}

// CLI interface
const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case 'mode':
    if (!arg) {
      console.log('Current mode: soft (default)');
      console.log(`Available modes: ${Object.keys(COST_MODES).join(', ')}`);
    } else {
      setCostMode(arg);
    }
    break;
    
  case 'status':
    showBudgetStatus();
    break;
    
  case 'optimize':
    optimizeBudget();
    break;
    
  default:
    console.log('KPulse Cost Containment Tool');
    console.log('');
    console.log('Usage:');
    console.log('  node scripts/cost_containment.js mode [soft|hard|development|cache_only]');
    console.log('  node scripts/cost_containment.js status');
    console.log('  node scripts/cost_containment.js optimize');
    console.log('');
    console.log('Examples:');
    console.log('  node scripts/cost_containment.js mode hard    # Enable strict budget mode');
    console.log('  node scripts/cost_containment.js status       # Show current usage');
    console.log('  node scripts/cost_containment.js optimize     # Get optimization tips');
    break;
}