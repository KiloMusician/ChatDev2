#!/usr/bin/env tsx
/**
 * 🔍 ACIA - Autonomous Capability & Integrity Audit
 * CoreLink Foundation - Infrastructure-First Quality Assurance
 * 
 * Scans entire codebase for integrity issues and generates actionable PUs
 */

import fs from 'node:fs';
import path from 'node:path';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';

const execAsync = promisify(exec);
const root = process.cwd();

interface Finding {
  id: string;
  type: 'DocPU' | 'RefactorPU' | 'FixPU' | 'TestPU' | 'SecurityPU' | 'PerfPU';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  files?: Array<{ path: string; note?: string }>;
  labels?: string[];
  phase?: string;
}

const findings: Finding[] = [];

/**
 * **COMPREHENSIVE FILE WALKER** - Respects gitignore patterns
 */
function walkCodebase(dir: string, acc: string[] = []): string[] {
  try {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name === 'node_modules' || 
          entry.name === '.git' || 
          entry.name.startsWith('.') && entry.name !== '.github') {
        continue;
      }
      
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory()) {
        walkCodebase(fullPath, acc);
      } else {
        acc.push(fullPath);
      }
    }
  } catch (error) {
    console.warn(`[ACIA] Cannot scan ${dir}:`, error);
  }
  
  return acc;
}

/**
 * **FINDING REGISTRATION** - Add audit findings with metadata
 */
function addFinding(finding: Finding) {
  findings.push({
    ...finding,
    labels: ['audit', finding.priority, ...(finding.labels || [])],
    phase: finding.phase || 'foundational'
  });
}

/**
 * **ZERO-BYTE FILE DETECTION** - Find placeholder/broken files
 */
function auditZeroByteFiles() {
  console.log('[ACIA] 🔍 Scanning for zero-byte files...');
  
  const files = walkCodebase(root);
  let zeroByteCount = 0;
  
  for (const file of files) {
    try {
      const stats = fs.statSync(file);
      if (stats.size === 0) {
        zeroByteCount++;
        addFinding({
          id: `ZERO-${path.basename(file)}`,
          type: 'FixPU',
          priority: 'high',
          title: `Zero-byte file detected → remove or populate: ${path.relative(root, file)}`,
          files: [{ path: file, note: 'Empty file needs content or removal' }]
        });
      }
    } catch (error) {
      // Skip files we can't stat
    }
  }
  
  console.log(`[ACIA] Found ${zeroByteCount} zero-byte files`);
}

/**
 * **PLACEHOLDER MARKER DETECTION** - Find TODO/FIXME/PLACEHOLDER markers
 */
function auditPlaceholders() {
  console.log('[ACIA] 🔍 Scanning for placeholder markers...');
  
  const files = walkCodebase(root);
  const placeholderRegex = /\b(TODO|FIXME|PLACEHOLDER|TBD|CHANGEME|HACK|XXX)\b/gi;
  let placeholderFiles = 0;
  
  for (const file of files) {
    if (!/\.(md|txt|ts|tsx|js|jsx|json|yaml|yml)$/i.test(file)) continue;
    
    try {
      const content = fs.readFileSync(file, 'utf8');
      const matches = content.match(placeholderRegex);
      
      if (matches && matches.length > 0) {
        placeholderFiles++;
        addFinding({
          id: `PLACEHOLDER-${path.basename(file)}`,
          type: 'DocPU', 
          priority: matches.some(m => /critical|fixme/i.test(m)) ? 'high' : 'medium',
          title: `Resolve ${matches.length} placeholder marker(s) in ${path.relative(root, file)}`,
          files: [{ path: file, note: `Contains: ${matches.join(', ')}` }]
        });
      }
    } catch (error) {
      // Skip files we can't read
    }
  }
  
  console.log(`[ACIA] Found ${placeholderFiles} files with placeholders`);
}

/**
 * **DUPLICATE BASENAME DETECTION** - Find confusing duplicate filenames
 */
function auditDuplicateBasenames() {
  console.log('[ACIA] 🔍 Scanning for duplicate basenames...');
  
  const files = walkCodebase(root);
  const byBasename = new Map<string, string[]>();
  
  for (const file of files) {
    const basename = path.basename(file);
    const existing = byBasename.get(basename) || [];
    byBasename.set(basename, [...existing, file]);
  }
  
  let duplicateGroups = 0;
  for (const [basename, fileList] of byBasename) {
    if (fileList.length > 1 && /README\.md|index\.ts|config\.js/i.test(basename)) {
      duplicateGroups++;
      addFinding({
        id: `DUP-${basename}`,
        type: 'RefactorPU',
        priority: 'medium',
        title: `Duplicate ${basename} files → use context-specific naming`,
        files: fileList.map(path => ({ path, note: 'Consider renaming for clarity' }))
      });
    }
  }
  
  console.log(`[ACIA] Found ${duplicateGroups} duplicate basename groups`);
}

/**
 * **CRITICAL DOCUMENTATION AUDIT** - Ensure core docs exist
 */
function auditCoreDocs() {
  console.log('[ACIA] 🔍 Auditing core documentation...');
  
  const criticalDocs = [
    'README.md',
    'docs/ARCH.md', 
    'docs/API.md',
    'docs/RSEV_Rituals.md',
    'docs/Roadmap.md',
    'docs/FAQ.md',
    'docs/SECURITY.md',
    'docs/SLO.md',
    'CONTRIBUTING.md',
    'CHANGELOG.md'
  ];
  
  let missingDocs = 0;
  for (const docPath of criticalDocs) {
    const fullPath = path.join(root, docPath);
    if (!fs.existsSync(fullPath)) {
      missingDocs++;
      addFinding({
        id: `MISSING-DOC-${path.basename(docPath, '.md')}`,
        type: 'DocPU',
        priority: docPath === 'README.md' ? 'critical' : 'high',
        title: `Missing critical documentation: ${docPath}`,
        files: [{ path: docPath, note: 'Required for Infrastructure-First compliance' }]
      });
    }
  }
  
  console.log(`[ACIA] Found ${missingDocs} missing critical docs`);
}

/**
 * **BUILD INTEGRITY AUDIT** - Check build artifacts and dependencies
 */
function auditBuildIntegrity() {
  console.log('[ACIA] 🔍 Auditing build integrity...');
  
  // **CLIENT BUILD CHECK**
  const clientIndex = path.join(root, 'client', 'dist', 'index.html');
  if (!fs.existsSync(clientIndex)) {
    addFinding({
      id: 'BUILD-CLIENT-MISSING',
      type: 'FixPU',
      priority: 'medium',
      title: 'Client build artifacts missing → ensure build pipeline or degraded mode',
      files: [{ path: 'client/dist/index.html', note: 'Required for SPA fallback' }]
    });
  }
  
  // **PACKAGE.JSON VALIDATION**
  const packageJson = path.join(root, 'package.json');
  if (fs.existsSync(packageJson)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(packageJson, 'utf8'));
      
      if (!pkg.scripts?.dev) {
        addFinding({
          id: 'BUILD-NO-DEV-SCRIPT',
          type: 'FixPU',
          priority: 'high',
          title: 'Missing npm run dev script → required for Infrastructure-First startup'
        });
      }
      
      if (!pkg.scripts?.build) {
        addFinding({
          id: 'BUILD-NO-BUILD-SCRIPT', 
          type: 'FixPU',
          priority: 'high',
          title: 'Missing npm run build script → required for deployment'
        });
      }
    } catch (error) {
      addFinding({
        id: 'BUILD-INVALID-PACKAGE-JSON',
        type: 'FixPU',
        priority: 'critical',
        title: 'Invalid package.json → fix JSON syntax errors'
      });
    }
  }
}

/**
 * **SECURITY AUDIT** - Check for security issues
 */
function auditSecurity() {
  console.log('[ACIA] 🔍 Auditing security posture...');
  
  // **HARDCODED SECRETS CHECK**
  const files = walkCodebase(root);
  const secretPatterns = [
    /api[_-]?key.*[=:]\s*["']([a-zA-Z0-9_-]{20,})["']/gi,
    /secret.*[=:]\s*["']([a-zA-Z0-9_-]{20,})["']/gi,
    /token.*[=:]\s*["']([a-zA-Z0-9_-]{20,})["']/gi,
    /password.*[=:]\s*["']([^"']{8,})["']/gi
  ];
  
  let secretFiles = 0;
  for (const file of files) {
    if (!/\.(ts|js|tsx|jsx|json|env)$/i.test(file)) continue;
    if (file.includes('node_modules')) continue;
    
    try {
      const content = fs.readFileSync(file, 'utf8');
      
      for (const pattern of secretPatterns) {
        if (pattern.test(content)) {
          secretFiles++;
          addFinding({
            id: `SECURITY-HARDCODED-${path.basename(file)}`,
            type: 'SecurityPU',
            priority: 'critical',
            title: `Potential hardcoded secret in ${path.relative(root, file)} → use environment variables`,
            files: [{ path: file, note: 'Contains potential hardcoded credentials' }]
          });
          break;
        }
      }
    } catch (error) {
      // Skip files we can't read
    }
  }
  
  // **ADMIN TOKEN CHECK**
  if (!process.env.ADMIN_TOKEN || process.env.ADMIN_TOKEN === 'admin123') {
    addFinding({
      id: 'SECURITY-WEAK-ADMIN-TOKEN',
      type: 'SecurityPU',
      priority: 'critical',
      title: 'Weak or missing ADMIN_TOKEN → use strong random token'
    });
  }
  
  console.log(`[ACIA] Found ${secretFiles} potential security issues`);
}

/**
 * **DATA SEED AUDIT** - Check critical data files exist
 */
function auditDataSeeds() {
  console.log('[ACIA] 🔍 Auditing data seeds...');
  
  const criticalSeeds = [
    'data/operations_codex.json',
    'data/anchors_boot.json', 
    'data/budget_boot.json',
    'data/game_state.json'
  ];
  
  let missingSeeds = 0;
  for (const seedPath of criticalSeeds) {
    const fullPath = path.join(root, seedPath);
    if (!fs.existsSync(fullPath)) {
      missingSeeds++;
      addFinding({
        id: `SEED-MISSING-${path.basename(seedPath, '.json')}`,
        type: 'FixPU',
        priority: 'high',
        title: `Missing critical seed file: ${seedPath}`,
        files: [{ path: seedPath, note: 'Required for system initialization' }]
      });
    } else {
      // **VALIDATE JSON SYNTAX**
      try {
        JSON.parse(fs.readFileSync(fullPath, 'utf8'));
      } catch (error) {
        addFinding({
          id: `SEED-INVALID-${path.basename(seedPath, '.json')}`,
          type: 'FixPU',
          priority: 'critical',
          title: `Invalid JSON in seed file: ${seedPath}`,
          files: [{ path: seedPath, note: 'JSON syntax error needs fixing' }]
        });
      }
    }
  }
  
  console.log(`[ACIA] Found ${missingSeeds} missing seed files`);
}

/**
 * **INFRASTRUCTURE-FIRST COMPLIANCE AUDIT**
 */
function auditInfrastructureFirst() {
  console.log('[ACIA] 🔍 Auditing Infrastructure-First compliance...');
  
  // **SINGLE-PORT COMPLIANCE**
  const serverFile = path.join(root, 'server', 'index.ts');
  if (fs.existsSync(serverFile)) {
    const content = fs.readFileSync(serverFile, 'utf8');
    
    // Check for multiple listen() calls
    const listenCalls = (content.match(/\.listen\(/g) || []).length;
    if (listenCalls > 1) {
      addFinding({
        id: 'INFRA-MULTI-PORT',
        type: 'RefactorPU',
        priority: 'critical',
        title: 'Multiple server.listen() calls → violates single-port principle',
        files: [{ path: serverFile, note: 'Consolidate to single port' }]
      });
    }
    
    // Check for health endpoints
    if (!content.includes('/healthz') || !content.includes('/readyz')) {
      addFinding({
        id: 'INFRA-MISSING-HEALTH',
        type: 'FixPU',
        priority: 'critical',
        title: 'Missing /healthz or /readyz endpoints → required for Infrastructure-First',
        files: [{ path: serverFile, note: 'Add health check endpoints' }]
      });
    }
  }
  
  // **SPA FALLBACK CHECK**
  const staticFile = path.join(root, 'client', 'dist', 'index.html');
  if (!fs.existsSync(staticFile)) {
    addFinding({
      id: 'INFRA-NO-SPA-FALLBACK',
      type: 'FixPU',
      priority: 'high',
      title: 'No SPA fallback → will show blank screens on client routing',
      files: [{ path: 'client/dist/index.html', note: 'Build client or add static fallback' }]
    });
  }
}

/**
 * **ASYNC TYPESCRIPT BUILD VALIDATION** 
 */
async function auditTypeScript() {
  console.log('[ACIA] 🔍 Auditing TypeScript compilation...');
  
  try {
    const { stdout, stderr } = await execAsync('npx tsc --noEmit', { 
      timeout: 30000,
      cwd: root
    });
    
    if (stderr) {
      const errorCount = (stderr.match(/error TS/g) || []).length;
      if (errorCount > 0) {
        addFinding({
          id: 'TS-COMPILATION-ERRORS',
          type: 'FixPU',
          priority: 'high',
          title: `${errorCount} TypeScript compilation errors → fix type issues`,
          files: [{ path: 'tsconfig.json', note: 'TypeScript errors prevent clean builds' }]
        });
      }
    }
  } catch (error) {
    addFinding({
      id: 'TS-BUILD-FAILURE',
      type: 'FixPU', 
      priority: 'critical',
      title: 'TypeScript build completely failed → fix compilation issues'
    });
  }
}

/**
 * **GAME STATE INTEGRITY AUDIT**
 */
function auditGameState() {
  console.log('[ACIA] 🔍 Auditing game state integrity...');
  
  const gameStateFile = path.join(root, 'data', 'game_state.json');
  if (fs.existsSync(gameStateFile)) {
    try {
      const gameState = JSON.parse(fs.readFileSync(gameStateFile, 'utf8'));
      
      // **RESOURCE VALIDATION**
      if (!gameState.resources || typeof gameState.resources !== 'object') {
        addFinding({
          id: 'GAME-INVALID-RESOURCES',
          type: 'FixPU',
          priority: 'critical',
          title: 'Game state missing or invalid resources object',
          files: [{ path: gameStateFile, note: 'Resources structure corrupted' }]
        });
      }
      
      // **NUMERIC VALIDATION** - Check for NaN/Infinity
      const checkNaN = (obj: any, path: string) => {
        for (const [key, value] of Object.entries(obj)) {
          if (typeof value === 'number' && (isNaN(value) || !isFinite(value))) {
            addFinding({
              id: `GAME-NAN-${key.toUpperCase()}`,
              type: 'FixPU',
              priority: 'critical',
              title: `NaN/Infinity detected in ${path}.${key} → fix numeric validation`,
              files: [{ path: gameStateFile, note: 'Numeric corruption detected' }]
            });
          }
          
          if (typeof value === 'object' && value !== null) {
            checkNaN(value, `${path}.${key}`);
          }
        }
      };
      
      checkNaN(gameState.resources, 'resources');
      
    } catch (error) {
      addFinding({
        id: 'GAME-CORRUPT-STATE',
        type: 'FixPU',
        priority: 'critical',
        title: 'Game state file corrupted or invalid JSON',
        files: [{ path: gameStateFile, note: 'JSON parse error' }]
      });
    }
  }
}

/**
 * **BUDGET & ENTROPY AUDIT**
 */
function auditBudgetSystem() {
  console.log('[ACIA] 🔍 Auditing budget & entropy systems...');
  
  // **BUDGET CONFIGURATION**
  const budgetFile = path.join(root, 'data', 'budget.json');
  if (!fs.existsSync(budgetFile)) {
    addFinding({
      id: 'BUDGET-MISSING-CONFIG',
      type: 'FixPU',
      priority: 'critical',
      title: 'Missing budget.json → required for autonomous operation safety',
      files: [{ path: budgetFile, note: 'Critical for preventing runaway operations' }]
    });
  }
  
  // **ENTROPY TRACKING**
  const serverFiles = walkCodebase(path.join(root, 'server'));
  let hasEntropyTracking = false;
  
  for (const file of serverFiles) {
    if (file.endsWith('.ts') || file.endsWith('.js')) {
      try {
        const content = fs.readFileSync(file, 'utf8');
        if (content.includes('entropy') && content.includes('throttle')) {
          hasEntropyTracking = true;
          break;
        }
      } catch (error) {
        // Skip files we can't read
      }
    }
  }
  
  if (!hasEntropyTracking) {
    addFinding({
      id: 'BUDGET-NO-ENTROPY',
      type: 'RefactorPU',
      priority: 'high',
      title: 'No entropy tracking system → add error ratio monitoring with throttling'
    });
  }
}

/**
 * **MAIN AUDIT EXECUTION**
 */
async function runFullAudit() {
  console.log('[ACIA] 🚀 Starting Autonomous Capability & Integrity Audit...');
  console.log('[ACIA] 📁 Project root:', root);
  
  // **RUN ALL AUDIT MODULES**
  auditZeroByteFiles();
  auditPlaceholders();
  auditDuplicateBasenames();
  auditCoreDocs();
  auditBuildIntegrity();
  auditInfrastructureFirst();
  auditGameState();
  auditBudgetSystem();
  await auditTypeScript();
  
  // **FINDINGS SUMMARY**
  console.log('\n[ACIA] 📊 Audit Summary:');
  console.log(`[ACIA] Total findings: ${findings.length}`);
  
  const byPriority = findings.reduce((acc, f) => {
    acc[f.priority] = (acc[f.priority] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  for (const [priority, count] of Object.entries(byPriority)) {
    console.log(`[ACIA]   ${priority}: ${count} findings`);
  }
  
  // **EXPORT FINDINGS AS NDJSON**
  const ndjsonPath = path.join(root, 'acia_findings.ndjson');
  const ndjsonContent = findings.map(f => JSON.stringify(f)).join('\n');
  fs.writeFileSync(ndjsonPath, ndjsonContent);
  
  // **EXPORT FINDINGS AS JSON ARRAY**
  const jsonPath = path.join(root, 'acia_findings.json');
  fs.writeFileSync(jsonPath, JSON.stringify(findings, null, 2));
  
  console.log(`[ACIA] ✅ Findings exported to acia_findings.ndjson (${findings.length} items)`);
  console.log(`[ACIA] ✅ Findings exported to acia_findings.json (formatted)`);
  
  // **PRIORITY RECOMMENDATIONS**
  const criticalFindings = findings.filter(f => f.priority === 'critical');
  if (criticalFindings.length > 0) {
    console.log(`\n[ACIA] ⚠️  ${criticalFindings.length} CRITICAL findings require immediate attention:`);
    criticalFindings.forEach(f => {
      console.log(`[ACIA]   • ${f.id}: ${f.title}`);
    });
  }
  
  return findings;
}

/**
 * **ENTRY POINT**
 */
async function main() {
  const findings = await runFullAudit();
  console.log(`\n[ACIA] 🎯 Audit complete - ${findings.length} actionable findings ready`);
  console.log('[ACIA] 📋 Use: curl -X POST /api/ops/queue -d @acia_findings.json');
  return findings;
}

// **ES MODULE ENTRY POINT**
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then(() => process.exit(0))
    .catch(error => {
      console.error('[ACIA] ❌ Audit failed:', error);
      process.exit(1);
    });
}

export { runFullAudit, addFinding, main };