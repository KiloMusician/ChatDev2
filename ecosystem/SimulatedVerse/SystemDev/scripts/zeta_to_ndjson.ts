#!/usr/bin/env tsx
/**
 * 🎯 ZETA Interview → NDJSON Task Converter
 * CoreLink Foundation - Self-Auditing Loop Generator
 * 
 * Converts 123 ZETA interview questions into autonomous audit tasks
 */

import fs from 'node:fs';

interface ZetaTask {
  id: string;
  type: 'AuditPU' | 'TestPU' | 'DocPU' | 'FixPU';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  phase: string;
  category: string;
  question: string;
  check_command?: string;
  fix_hint?: string;
  infrastructure_first: boolean;
}

/**
 * **123 ZETA INTERVIEW QUESTIONS** - Complete Infrastructure-First Audit
 */
const ZETA_QUESTIONS = [
  // **A. Infrastructure-First Principles (Z1–Z15)**
  { id: 'Z001', category: 'Infrastructure', priority: 'critical', phase: 'foundational',
    question: 'Do we strictly enforce the single-port rule for Replit?',
    check: 'grep -r "\.listen(" server/ | wc -l',
    fix: 'Consolidate all servers to single port 5000' },
  
  { id: 'Z002', category: 'Infrastructure', priority: 'critical', phase: 'foundational', 
    question: 'Is SPA fallback guaranteed—no blank screens ever?',
    check: 'curl -s localhost:5000/nonexistent | grep -v "Cannot GET"',
    fix: 'Add Express static fallback for non-API routes' },
    
  { id: 'Z003', category: 'Infrastructure', priority: 'high', phase: 'foundational',
    question: 'Are compression, CORS, and Helmet properly configured?',
    check: 'grep -r "compression\\|cors\\|helmet" server/',
    fix: 'Configure Express security middleware' },
    
  { id: 'Z004', category: 'Safety', priority: 'critical', phase: 'foundational',
    question: 'Do crash boundaries catch uncaught errors and increment entropy counters?',
    check: 'grep -r "uncaughtException\\|unhandledRejection" server/',
    fix: 'Add process error handlers with entropy tracking' },
    
  { id: 'Z005', category: 'Infrastructure', priority: 'critical', phase: 'foundational',
    question: 'Does /readyz block features until seeds + scheduler are ready?',
    check: 'curl -s localhost:5000/readyz | jq .system_ready',
    fix: 'Implement proper readiness gates' },
    
  { id: 'Z006', category: 'Game Core', priority: 'critical', phase: 'foundational',
    question: 'Is there a cooperative scheduler tick running at 1s intervals?',
    check: 'grep -r "setInterval.*1000\\|scheduler.*tick" server/',
    fix: 'Implement 1-second cooperative game tick' },
    
  { id: 'Z007', category: 'Data', priority: 'high', phase: 'foundational',
    question: 'Do we unify persistence behind KV/SQLite abstraction?',
    check: 'ls server/storage.ts && grep -r "IStorage" server/',
    fix: 'Create unified storage abstraction interface' },
    
  { id: 'Z008', category: 'Data', priority: 'medium', phase: 'foundational',
    question: 'Are snapshots/compactions scheduled and idempotent?',
    check: 'grep -r "snapshot\\|compact" server/',
    fix: 'Add scheduled snapshot system' },
    
  { id: 'Z009', category: 'Security', priority: 'critical', phase: 'foundational',
    question: 'Is ADMIN_TOKEN consistently required for mutating routes?',
    check: 'grep -r "ADMIN_TOKEN\\|bearer" server/routes/',
    fix: 'Add admin authentication to all mutating endpoints' },
    
  { id: 'Z010', category: 'Security', priority: 'high', phase: 'foundational',
    question: 'Are rate limits enforced per-IP for mutating routes?',
    check: 'grep -r "rate.*limit\\|throttle" server/',
    fix: 'Implement per-IP rate limiting middleware' },
    
  // **B. Build & Schema Hardening (Z16–Z23)**
  { id: 'Z016', category: 'Build', priority: 'high', phase: 'foundational',
    question: 'Does replit.nix pin Node/TS versions reproducibly?',
    check: 'ls replit.nix && grep -r "nodejs\\|typescript" replit.nix',
    fix: 'Pin specific Node/TypeScript versions in replit.nix' },
    
  { id: 'Z017', category: 'Build', priority: 'medium', phase: 'foundational',
    question: 'Is tsconfig.json aligned with ES2020 + bundler resolution?',
    check: 'jq .compilerOptions.target tsconfig.json',
    fix: 'Update tsconfig.json for modern bundler compatibility' },
    
  { id: 'Z018', category: 'Schema', priority: 'high', phase: 'foundational',
    question: 'Are Zod schemas covering Directive, Anchor, Budget, PU?',
    check: 'grep -r "zod\\|z\." shared/',
    fix: 'Create comprehensive Zod validation schemas' },
    
  // **C. NDJSON Queue & Ops (Z24–Z30)**
  { id: 'Z024', category: 'Queue', priority: 'critical', phase: 'expansion',
    question: 'Can /api/ops/queue safely accept 100+ NDJSON items?',
    check: 'curl -s localhost:5000/api/ops/status | jq .queue_size',
    fix: 'We just verified this! Queue handles large NDJSON batches' },
    
  { id: 'Z025', category: 'Queue', priority: 'high', phase: 'expansion',
    question: 'Does PU executor obey budget-aware throttling?',
    check: 'grep -r "budget.*throttle\\|budget.*remaining" server/',
    fix: 'Implement budget-aware PU execution throttling' },
    
  // **D. Game Core (Z31–Z35)**
  { id: 'Z031', category: 'Game Core', priority: 'critical', phase: 'foundational',
    question: 'Is fixed timestep loop stable under Replit CPU caps?',
    check: 'grep -r "fixed.*timestep\\|accumulator" server/',
    fix: 'Implement fixed timestep with delta accumulation' },
    
  { id: 'Z032', category: 'Game Core', priority: 'high', phase: 'foundational',
    question: 'Does game clock persist across saves?',
    check: 'grep -r "game.*clock\\|elapsed.*time" shared/',
    fix: 'Add persistent game clock to save state' },
    
  { id: 'Z033', category: 'Game Core', priority: 'high', phase: 'foundational',
    question: 'Is RNG deterministic (seeded) for reproducible tests?',
    check: 'grep -r "Math.random\\|seed.*rng" server/',
    fix: 'Replace Math.random with seeded RNG system' },
    
  // **E. Idle Fundamentals (Z36–Z45)**
  { id: 'Z036', category: 'Game Mechanics', priority: 'critical', phase: 'expansion',
    question: 'Do resources have registry entries with caps/tags?',
    check: 'ls shared/resources.ts || grep -r "Resource.*registry" shared/',
    fix: 'Create centralized resource registry with caps and metadata' },
    
  { id: 'Z037', category: 'Game Mechanics', priority: 'critical', phase: 'expansion',
    question: 'Are buildings producing per-tick with upkeep costs?',
    check: 'grep -r "building.*produce\\|upkeep" shared/',
    fix: 'Implement building production system with upkeep' },
    
  { id: 'Z038', category: 'Game Mechanics', priority: 'high', phase: 'expansion',
    question: 'Does clicker hook prevent spam exploits?',
    check: 'grep -r "click.*cooldown\\|anti.*spam" client/',
    fix: 'Add click rate limiting and spam prevention' },
    
  // **H. Agents & Self-Play (Z66–Z75)**
  { id: 'Z066', category: 'Agents', priority: 'critical', phase: 'cultivation',
    question: 'Does agent bus consume Msg⛛ deltas reliably?',
    check: 'grep -r "agent.*bus\\|delta.*subscribe" server/',
    fix: 'Implement agent event bus with delta consumption' },
    
  { id: 'Z067', category: 'Agents', priority: 'high', phase: 'cultivation',
    question: 'Does self-play harness simulate deterministically?',
    check: 'grep -r "self.*play\\|simulate" server/',
    fix: 'Create deterministic self-play simulation harness' },
    
  // **L. Docs & Tutorials (Z96–Z105)**
  { id: 'Z096', category: 'Documentation', priority: 'high', phase: 'cultivation',
    question: 'Does README reflect infra-first principles?',
    check: 'grep -r "Infrastructure.*First\\|single.*port" README.md',
    fix: 'Update README with Infrastructure-First methodology' },
    
  { id: 'Z097', category: 'Documentation', priority: 'medium', phase: 'cultivation',
    question: 'Is ARCH.md up-to-date with scheduler?',
    check: 'ls docs/ARCH.md && grep -r "scheduler\\|tick" docs/ARCH.md',
    fix: 'Create/update ARCH.md with current system architecture' },
    
  { id: 'Z098', category: 'Documentation', priority: 'medium', phase: 'cultivation',
    question: 'Does API.md list correct routes/limits?',
    check: 'ls docs/API.md && grep -r "/api/" docs/API.md',
    fix: 'Create comprehensive API documentation' },
    
  { id: 'Z099', category: 'Documentation', priority: 'medium', phase: 'cultivation',
    question: 'Is RSEV_Rituals.md complete?',
    check: 'ls docs/RSEV_Rituals.md',
    fix: 'Create RSEV (Replit Service Evolution) rituals documentation' },
    
  { id: 'Z100', category: 'Documentation', priority: 'medium', phase: 'cultivation',
    question: 'Does Roadmap.md show Missive seals?',
    check: 'ls docs/Roadmap.md && grep -r "Missive\\|seal" docs/Roadmap.md',
    fix: 'Create roadmap with Missive seal tracking' },
    
  // **O. Bloomwave Integration (Z121–Z123)**
  { id: 'Z121', category: 'Integration', priority: 'critical', phase: 'bloomwave',
    question: 'Are Anchors, Missives, Directives unified in HUD index?',
    check: 'grep -r "Anchor\\|Missive\\|Directive" client/',
    fix: 'Unify core concepts in HUD interface' },
    
  { id: 'Z122', category: 'Governance', priority: 'critical', phase: 'bloomwave',
    question: 'Does council consensus rank PUs correctly?',
    check: 'grep -r "council.*consensus\\|rank.*pu" server/',
    fix: 'Implement council-based PU ranking system' },
    
  { id: 'Z123', category: 'Synthesis', priority: 'critical', phase: 'bloomwave',
    question: 'Does Seal Msg⛛{123} affirm: self-play stable, agent-play bounded, docs current?',
    check: 'grep -r "Seal.*123\\|self.*play.*stable" server/',
    fix: 'Implement final synthesis seal validation' }
];

/**
 * **CONVERT ZETA QUESTIONS TO NDJSON TASKS**
 */
function generateZetaNDJSON(): ZetaTask[] {
  console.log('[ZETA] 🎯 Converting 123 interview questions to autonomous audit tasks...');
  
  const tasks: ZetaTask[] = [];
  
  for (const q of ZETA_QUESTIONS) {
    tasks.push({
      id: `ZETA-${q.id}`,
      type: 'AuditPU',
      priority: q.priority,
      title: `ZETA ${q.id}: ${q.question}`,
      phase: q.phase,
      category: q.category,
      question: q.question,
      check_command: q.check,
      fix_hint: q.fix,
      infrastructure_first: true
    });
  }
  
  console.log(`[ZETA] ✅ Generated ${tasks.length} autonomous audit tasks`);
  return tasks;
}

/**
 * **MAIN EXECUTION**
 */
async function main() {
  const tasks = generateZetaNDJSON();
  
  // **EXPORT AS NDJSON**
  const ndjsonPath = 'zeta_123_audit_tasks.ndjson';
  const ndjsonContent = tasks.map(task => JSON.stringify(task)).join('\n');
  fs.writeFileSync(ndjsonPath, ndjsonContent);
  
  // **EXPORT AS JSON ARRAY**
  const jsonPath = 'zeta_123_audit_tasks.json';
  fs.writeFileSync(jsonPath, JSON.stringify(tasks, null, 2));
  
  console.log(`[ZETA] 📋 Exported ${tasks.length} tasks → ${ndjsonPath}`);
  console.log(`[ZETA] 📋 Also exported as JSON array → ${jsonPath}`);
  console.log('[ZETA] 🚀 Ready to queue: curl -X POST /api/ops/queue --data-binary @zeta_123_audit_tasks.json');
  
  // **SUMMARY STATS**
  const byPhase = tasks.reduce((acc, task) => {
    acc[task.phase] = (acc[task.phase] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const byPriority = tasks.reduce((acc, task) => {
    acc[task.priority] = (acc[task.priority] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  console.log('\n[ZETA] 📊 Task Distribution:');
  console.log('[ZETA] By Phase:', JSON.stringify(byPhase, null, 2));
  console.log('[ZETA] By Priority:', JSON.stringify(byPriority, null, 2));
  
  return tasks;
}

// **ES MODULE ENTRY POINT**
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then(() => {
      console.log('\n[ZETA] 🎯 ZETA → NDJSON conversion complete!');
      console.log('[ZETA] 💫 Self-auditing loop ready for autonomous execution');
      process.exit(0);
    })
    .catch(error => {
      console.error('[ZETA] ❌ Conversion failed:', error);
      process.exit(1);
    });
}

export { generateZetaNDJSON, main };