/**
 * 🛠️ Ops Routes - Infrastructure-First Task Management
 * CoreLink Foundation - Autonomous Development Ecosystem
 */

import { Router } from 'express';
import { puQueue } from '../services/pu_queue.js';
import { createPRsFromPUs } from '../services/git.js';
import { resolveScope, type ScopeSelection } from '../lib/scope.js';
import { getInfrastructureLogLevel, setInfrastructureLogLevel } from '../services/real-infrastructure-monitor.js';
import { smartLogger } from '../utils/smart-logger.js';
import crypto from 'crypto';
import { existsSync, readFileSync } from 'node:fs';

const router = Router();

/**
 * **ENTROPY CALCULATION** - System activity entropy
 */
function generateSystemEntropy(): number {
  const timestamp = Date.now();
  const queueActivity = puQueue.size() > 0 ? 1 : 0;
  const randomSeed = crypto.randomBytes(4).readUInt32BE(0);
  
  // Simple entropy calculation: combine timestamp variance, queue activity, and randomness
  const baseEntropy = (timestamp % 1000) / 1000; // 0-1 based on timestamp
  const activityEntropy = queueActivity * 0.3; // Queue activity contributes
  const randomEntropy = (randomSeed % 100) / 1000; // Small random component
  
  return Math.round((baseEntropy + activityEntropy + randomEntropy) * 100) / 100;
}

/**
 * **ADMIN GUARD** - Require authentication for ops endpoints
 */
function adminGuard(req: any, res: any, next: any) {
  const adminToken = process.env.ADMIN_TOKEN;
  const providedToken = req.headers.authorization?.replace('Bearer ', '');
  
  if (!adminToken || providedToken !== adminToken) {
    return res.status(401).json({ error: 'Admin access required' });
  }
  
  next();
}

function normalizeLogLevel(level: any): 'debug' | 'info' | 'warn' | 'error' | null {
  if (typeof level !== 'string') return null;
  const normalized = level.toLowerCase();
  if (normalized === 'debug' || normalized === 'info' || normalized === 'warn' || normalized === 'error') {
    return normalized;
  }
  return null;
}

function normalizeBooleanFlag(value: any): boolean | null {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (normalized === 'true' || normalized === '1') return true;
    if (normalized === 'false' || normalized === '0') return false;
  }
  return null;
}

/**
 * **QUEUE STATUS** - Get current ops queue state
 */
router.get('/status', (req, res) => {
  try {
    res.json({
      autonomous_system: 'operational',
      queue_size: puQueue.size(),
      processing: puQueue.isProcessing(),
      budget_used: 0, // Real budget tracking (implementing soon)
      budget_remaining: 100,
      infrastructure_first: true,
      entropy: generateSystemEntropy(),
      system_ready: true,
      seeds_complete: true,
      last_ping: Date.now()
    });
  } catch (error: any) {
    res.status(500).json({ 
      error: String(error?.message || error),
      infrastructure_first: false 
    });
  }
});

/**
 * **LOGGING STATUS** - Get current logging configuration
 */
router.get('/logging', (_req, res) => {
  res.json({
    ok: true,
    smart_logger: smartLogger.getConfig(),
    infrastructure_logger: { level: getInfrastructureLogLevel() }
  });
});

/**
 * **LOGGING CONTROL** - Adjust verbosity without editing .env
 */
router.post('/logging', adminGuard, (req, res) => {
  try {
    const body = req.body || {};
    const level = normalizeLogLevel(body.level);
    const smartLevel = normalizeLogLevel(body.smart_level || body.smartLevel || body.level);
    const infraLevel = normalizeLogLevel(body.infra_level || body.infrastructure_level || body.level);

    if (level) {
      process.env.LOG_LEVEL = level;
      process.env.SMART_LOG_LEVEL = level;
    }
    if (smartLevel) {
      smartLogger.setLevel(smartLevel);
    }
    if (infraLevel) {
      setInfrastructureLogLevel(infraLevel);
    }
    if (typeof body.rateLimitMs === 'number') {
      smartLogger.setRateLimitMs(body.rateLimitMs);
    }
    if (typeof body.summaryIntervalMs === 'number') {
      smartLogger.setSummaryIntervalMs(body.summaryIntervalMs);
    }

    res.json({
      ok: true,
      smart_logger: smartLogger.getConfig(),
      infrastructure_logger: { level: getInfrastructureLogLevel() }
    });
  } catch (error: any) {
    res.status(500).json({ error: String(error?.message || error) });
  }
});

router.post('/logging/verbosity', adminGuard, (req, res) => {
  try {
    const body = req.body || {};
    const shouldClear = Boolean(body.clear);
    const sourceValue = body.verbose ?? body.enabled ?? body.mode;
    const normalized = normalizeBooleanFlag(sourceValue);

    if (shouldClear) {
      smartLogger.setVerboseMode(null);
    } else if (normalized === null) {
      return res.status(400).json({ error: 'Provide a boolean verbose flag or set clear=true' });
    } else {
      smartLogger.setVerboseMode(normalized);
    }

    res.json({
      ok: true,
      verbose_mode: smartLogger.getVerboseMode(),
      smart_logger: smartLogger.getConfig()
    });
  } catch (error: any) {
    res.status(500).json({ error: String(error?.message || error) });
  }
});

router.get('/logging/verbosity', adminGuard, (_req, res) => {
  res.json({
    ok: true,
    verbose_mode: smartLogger.getVerboseMode(),
    smart_logger: smartLogger.getConfig()
  });
});

/**
 * **NDJSON QUEUE INGESTION** - Accept Infrastructure-First task batches
 */
router.post('/queue', (req, res) => {
  try {
    let enqueuedCount = 0;
    
    console.log('[Ops] 📋 Processing Infrastructure-First task batch...');
    console.log('[Ops] Content-Type:', req.headers['content-type']);
    console.log('[Ops] Body type:', typeof req.body);
    
    // **DIRECT NDJSON PROCESSING** - Parse as text
    if (req.headers['content-type'] === 'application/x-ndjson' && typeof req.body === 'string') {
      const lines = req.body.trim().split('\n').filter(Boolean);
      console.log(`[Ops] Processing ${lines.length} NDJSON lines...`);
      
      for (const line of lines) {
        try {
          const task = JSON.parse(line);
          
          // **CONVERT ZI TASK TO PU FORMAT**
          const pu = puQueue.enqueue({
            kind: (task.type || 'FixPU') as any, // Map to valid PU type
            summary: task.title,
            cost: mapPriorityToCost(task.priority),
            payload: {
              phase: task.phase,
              zi_id: task.id,
              infrastructure_first: true,
              original_task: task
            }
          });
          
          enqueuedCount++;
          console.log(`[Ops] ✅ Enqueued ${task.id}: ${task.title.slice(0, 50)}...`);
          
        } catch (parseError) {
          console.warn('[Ops] ⚠️ Skipped invalid NDJSON line:', line.slice(0, 100));
        }
      }
      
    } else if (Array.isArray(req.body)) {
      // **JSON ARRAY PROCESSING**
      for (const task of req.body) {
        const pu = puQueue.enqueue({
          kind: mapTaskTypeToPUKind(task.type) as any,
          summary: task.title,
          cost: mapPriorityToCost(task.priority),
          payload: {
            phase: task.phase,
            zi_id: task.id,
            infrastructure_first: true,
            original_task: task,
            steps: task.plan?.patcher ? [`Execute ${task.plan.patcher}`, "Validate changes", "Emit completion signal"] : undefined
          }
        });
        
        enqueuedCount++;
      }
      
    } else {
      // **SINGLE TASK PROCESSING**
      const task = req.body;
      const pu = puQueue.enqueue({
        kind: mapTaskTypeToPUKind(task.type || 'FeaturePU') as any,
        summary: task.title,
        cost: mapPriorityToCost(task.priority || 'medium'),
        payload: {
          phase: task.phase,
          zi_id: task.id,
          infrastructure_first: true,
          original_task: task,
          steps: [`Execute ${task.plan?.patcher || 'operation'}`, "Validate changes", "Emit completion signal"]
        }
      });
      
      enqueuedCount = 1;
    }
    
    console.log(`[Ops] 📊 Infrastructure-First batch complete: ${enqueuedCount} tasks enqueued`);
    
    res.json({
      ok: true,
      enqueued: enqueuedCount,
      total: puQueue.size(),
      infrastructure_first: true,
      timestamp: Date.now()
    });
    
  } catch (error: any) {
    console.error('[Ops] ❌ Queue ingestion failed:', error);
    res.status(500).json({ 
      error: String(error?.message || error),
      infrastructure_first: false 
    });
  }
});

/**
 * **RESOLVER → PU QUEUE** - Resolve scope and enqueue per-file PUs
 */
router.post('/queue-from-scope', adminGuard, (req, res) => {
  try {
    const body = req.body || {};
    const scope: ScopeSelection | undefined = body.scope;
    if (!scope) {
      return res.status(400).json({ error: 'scope is required' });
    }

    const scopeSelection: ScopeSelection = {
      ...scope,
      maxFiles: typeof body.maxFiles === 'number' ? body.maxFiles : scope.maxFiles
    };

    const scopeResult = resolveScope(scopeSelection);
    const summaryTemplate = typeof body.summaryTemplate === 'string' && body.summaryTemplate.trim().length
      ? body.summaryTemplate
      : 'Scope task for {file}';
    const kind = (body.kind || 'ScanPU') as any;
    const priority = body.priority || 'medium';

    const queued: Array<{ id: string; file: string }> = [];
    for (const file of scopeResult.files) {
      const summary = summaryTemplate
        .replace('{file}', file)
        .replace('{view}', scopeResult.view.join(','));
      const pu = puQueue.enqueue({
        kind,
        summary,
        cost: mapPriorityToCost(priority),
        payload: {
          scope: scopeResult.view,
          file,
          tags: scopeResult.tags,
          infrastructure_first: true
        }
      });
      queued.push({ id: pu.id, file });
    }

    res.json({
      ok: true,
      enqueued: queued.length,
      total: puQueue.size(),
      scope: {
        view: scopeResult.view,
        file_count: scopeResult.files.length
      },
      queued
    });
  } catch (error: any) {
    console.error('[Ops] ❌ queue-from-scope failed:', error);
    res.status(500).json({ error: String(error?.message || error) });
  }
});

/**
 * **PU QUEUE → PR BRIDGE** - Convert queued PUs with file payloads into PRs
 */
router.post('/queue-pr', adminGuard, async (req, res) => {
  try {
    const body = req.body || {};
    const source = body.source || 'payload';
    const limit = typeof body.limit === 'number' ? body.limit : 25;
    const syncAfter = Boolean(body.sync || body.syncAfter);
    const smokeAfter = Boolean(body.ci || body.smoke || body.smokeAfter);
    let syncPerformed = false;
    let smokePerformed = false;

    let candidates: any[] = [];

    if (source === 'queue') {
      if (existsSync('data/pu_queue.ndjson')) {
        const content = readFileSync('data/pu_queue.ndjson', 'utf8');
        const lines = content.split('\n').filter(Boolean);
        for (const line of lines.slice(0, limit)) {
          try {
            candidates.push(JSON.parse(line));
          } catch {
            // Skip invalid lines
          }
        }
      }
    } else if (Array.isArray(body.pus)) {
      candidates = body.pus;
    } else if (body.pu) {
      candidates = [body.pu];
    }

    const normalized = candidates.map((pu) => ({
      id: pu.id,
      branch: pu.branch,
      base: pu.base,
      title: pu.title || pu.summary,
      phase: pu.phase || pu.payload?.phase,
      labels: pu.labels,
      automerge: pu.automerge,
      draft: pu.draft,
      body: pu.body,
      files: Array.isArray(pu.files)
        ? pu.files
        : Array.isArray(pu.payload?.files)
          ? pu.payload.files
          : []
    }));

    const results = await createPRsFromPUs(normalized);

    const hookResults: Record<string, any> = {};
    if (syncAfter) {
      if (results.length === 0) {
        hookResults.sync = { ok: false, skipped: true, reason: 'no_prs_created' };
      } else {
        syncPerformed = true;
      }
    }
    if (syncPerformed) {
      try {
        const syncResp = await fetch(`http://127.0.0.1:${(process.env.PORT || '5000').trim()}/api/discipline/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        hookResults.sync = syncResp.ok ? await syncResp.json() : { ok: false, status: syncResp.status };
      } catch (error: any) {
        hookResults.sync = { ok: false, error: String(error?.message || error) };
      }
    }
    if (smokeAfter && results.length > 0) {
      smokePerformed = true;
      try {
        const smokeResp = await fetch(`http://127.0.0.1:${(process.env.PORT || '5000').trim()}/api/discipline/smoke`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        hookResults.smoke = smokeResp.ok ? await smokeResp.json() : { ok: false, status: smokeResp.status };
      } catch (error: any) {
        hookResults.smoke = { ok: false, error: String(error?.message || error) };
      }
    } else if (smokeAfter && results.length === 0) {
      hookResults.smoke = { ok: false, skipped: true, reason: 'no_prs_created' };
    }

    res.json({
      ok: true,
      source,
      requested: candidates.length,
      created: results.length,
      results,
      hooks: hookResults,
      status: {
        prs_created: results.length,
        sync_requested: syncAfter,
        sync_performed: syncPerformed,
        smoke_requested: smokeAfter,
        smoke_performed: smokePerformed
      }
    });
  } catch (error: any) {
    console.error('[Ops] ❌ queue-pr failed:', error);
    res.status(500).json({ error: String(error?.message || error) });
  }
});

/**
 * **ERROR REPORTING** - Endpoint for ErrorBoundary reports
 */
router.post('/error-report', (req, res) => {
  try {
    const errorReport = {
      timestamp: Date.now(),
      ...req.body
    };
    
    // Log error for debugging
    console.error('[OPS] Error report received:', errorReport);
    
    // Send error to monitoring service if available
    if (process.env.MONITORING_ENDPOINT) {
      try {
        fetch(process.env.MONITORING_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: 'error_report',
            error: errorReport,
            timestamp: Date.now()
          })
        }).catch(err => console.warn('[Ops] Monitoring unavailable:', err.message));
      } catch (error) {
        // Monitoring service unavailable
      }
    }
    
    // Acknowledge receipt
    res.json({ 
      status: 'received', 
      timestamp: errorReport.timestamp,
      id: `err_${Date.now()}` 
    });
  } catch (e: any) {
    console.error('[OPS] Failed to process error report:', e);
    res.status(500).json({ error: 'Failed to process error report' });
  }
});

/**
 * **QUEUE MANAGEMENT** - Clear, pause, resume operations
 */
router.post('/clear', adminGuard, (req, res) => {
  try {
    const clearedCount = puQueue.size();
    puQueue.clear(); // Clear the queue
    
    console.log(`[Ops] 🧹 Queue cleared: ${clearedCount} items removed`);
    
    res.json({ 
      ok: true, 
      message: `Queue cleared: ${clearedCount} items removed`,
      cleared_count: clearedCount
    });
  } catch (error) {
    res.status(500).json({ ok: false, error: 'Queue clear failed' });
  }
});

router.post('/pause', adminGuard, (req, res) => {
  try {
    // Pause the PU queue processor
    puQueue.pauseProcessor();
    
    console.log('[Ops] ⏸️ Queue processor paused');
    
    res.json({ 
      ok: true, 
      message: 'Queue processor paused successfully',
      queue_size: puQueue.size(),
      timestamp: Date.now()
    });
  } catch (error) {
    console.error('[Ops] Failed to pause queue:', error);
    res.status(500).json({ 
      ok: false, 
      error: 'Queue pause failed',
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

/**
 * **GET QUEUE** - View queued tasks
 */
router.get('/queue', (req, res) => {
  try {
    const allQueued = puQueue.getAllQueued();
    const next = puQueue.peek();
    
    res.json({
      total: puQueue.size(),
      items: allQueued ? allQueued.slice(0, 20).map(pu => ({ // Limit to first 20 for performance
        id: pu.id,
        kind: pu.kind,
        summary: pu.summary ? pu.summary.slice(0, 80) : pu.id,
        status: pu.status,
        cost: pu.cost
      })) : [],
      next: next ? { 
        id: next.id, 
        kind: next.kind, 
        summary: next.summary ? next.summary.slice(0, 80) : next.id
      } : null,
      processing: puQueue.isProcessing(),
      budget: {
        used: 0,
        max: 100, 
        remaining: 100
      }
    });
  } catch (error: any) {
    res.status(500).json({ 
      error: String(error?.message || error),
      processing: false 
    });
  }
});

/**
 * **START PROCESSOR** - Begin autonomous execution
 */
router.post('/start', adminGuard, (req, res) => {
  try {
    puQueue.startProcessor();
    res.json({ 
      ok: true, 
      message: 'Autonomous processor started',
      queue_size: puQueue.size(),
      processing: puQueue.isProcessing()
    });
  } catch (error: any) {
    res.status(500).json({ 
      error: String(error?.message || error),
      processing: false 
    });
  }
});

/**
 * **STOP PROCESSOR** - Pause autonomous execution
 */
router.post('/stop', adminGuard, (req, res) => {
  try {
    puQueue.stopProcessor();
    res.json({ 
      ok: true, 
      message: 'Autonomous processor stopped',
      processing: puQueue.isProcessing()
    });
  } catch (error: any) {
    res.status(500).json({ 
      error: String(error?.message || error) 
    });
  }
});

router.post('/resume', adminGuard, (req, res) => {
  // Alias for start
  try {
    puQueue.startProcessor();
    res.json({ 
      ok: true, 
      message: 'Autonomous processor resumed',
      queue_size: puQueue.size(),
      processing: puQueue.isProcessing()
    });
  } catch (error: any) {
    res.status(500).json({ 
      error: String(error?.message || error) 
    });
  }
});

/**
 * **DEQUEUE NEXT** - Pop next PU without processing
 */
router.post('/dequeue', adminGuard, (req, res) => {
  try {
    const item = puQueue.dequeue();
    res.json({
      ok: true,
      item,
      remaining: puQueue.size()
    });
  } catch (error: any) {
    res.status(500).json({ error: String(error?.message || error) });
  }
});

/**
 * **EXECUTE NEXT** - Run one PU immediately
 */
router.post('/execute-next', adminGuard, async (req, res) => {
  try {
    const result = await puQueue.runNext();
    if (!result) {
      return res.json({ ok: false, reason: 'queue_empty_or_processing' });
    }
    res.json({
      ok: true,
      pu: result.pu,
      proof: result.proof || null
    });
  } catch (error: any) {
    res.status(500).json({ error: String(error?.message || error) });
  }
});

/**
 * **TASK TYPE MAPPING** - Convert ZI task types to PU kinds
 */
function mapTaskTypeToPUKind(type: string): string {
  const mapping: Record<string, string> = {
    'InfraPU': 'RefactorPU',
    'UXPU': 'UXPU', 
    'SafetyPU': 'RefactorPU',
    'SchedulerPU': 'PerfPU',
    'PersistPU': 'RefactorPU',
    'AuthPU': 'RefactorPU',
    'PolicyPU': 'RefactorPU',
    'LogsPU': 'RefactorPU',
    'EntropyPU': 'PerfPU',
    'BudgetPU': 'RefactorPU',
    'EventsPU': 'RefactorPU',
    'BuildPU': 'RefactorPU',
    'SchemaPU': 'RefactorPU',
    'UtilsPU': 'RefactorPU',
    'DataPU': 'RefactorPU',
    'OpsPU': 'RefactorPU',
    'UI-PU': 'UXPU',
    'MsgPU': 'RefactorPU',
    'GamePU': 'GamePU',
    'EconomyPU': 'GamePU',
    'HUDPU': 'UXPU',
    'A11yPU': 'UXPU',
    'PerfPU': 'PerfPU',
    'AgentsPU': 'RefactorPU',
    'CouncilPU': 'RefactorPU',
    'IntegrationPU': 'RefactorPU',
    'HintsPU': 'RefactorPU',
    'MetricsPU': 'PerfPU',
    'AnalyticsPU': 'RefactorPU',
    'TestPU': 'TestPU',
    'ContentPU': 'RefactorPU',
    'NotebooksPU': 'DocPU',
    'DocsPU': 'DocPU',
    'GovernPU': 'DocPU',
    'CI-PU': 'TestPU',
    'ReleasePU': 'RefactorPU',
    'IndexPU': 'RefactorPU',
    'SealPU': 'RefactorPU',
    'SystemPU': 'RefactorPU'
  };
  
  return mapping[type] || 'RefactorPU';
}

/**
 * **PRIORITY MAPPING** - Convert priorities to cost weights
 */
function mapPriorityToCost(priority: string): number {
  const mapping: Record<string, number> = {
    'critical': 10,
    'high': 7,
    'medium': 5,
    'low': 3
  };
  
  return mapping[priority] || 5;
}

export default router;
