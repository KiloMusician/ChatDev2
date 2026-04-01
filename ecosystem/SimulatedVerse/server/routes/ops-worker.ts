/**
 * OWNERS: @team/ops  TAGS: worker, executor, queue  STABILITY: prod
 * DEPENDS: server/services/pu_queue.ts
 * INTEGRATION: {raven, autonomous-loop, ai-council}
 * HEALTH: {worker_heartbeat:true, lock_management:true}
 * NOTES: SOP-03 Worker State Management. BD-03 Always-On Executor.
 */

import { Router } from 'express';

const router = Router();

// **WORKER STATE** - Always-on executor status
let workerState = {
  running: false,
  started_at: null as string | null,
  last_tick_at: null as string | null,
  last_activity_at: null as string | null,
  lanes: {
    infra: { active: false, last_task: null, concurrency: 1 },
    game: { active: false, last_task: null, concurrency: 1 },
    docs: { active: false, last_task: null, concurrency: 1 },
    ops: { active: false, last_task: null, concurrency: 1 },
    repo: { active: false, last_task: null, concurrency: 1 }
  },
  locks: {} as Record<string, { acquired_at: string, task_id: string, expires_at: string }>
};

// **GET WORKER STATE** - SOP-03: Worker transparency
router.get('/state', (req, res) => {
  try {
    const now = Date.now();
    const staleness = workerState.last_tick_at 
      ? now - new Date(workerState.last_tick_at).getTime()
      : null;
    
    res.json({
      ...workerState,
      staleness_ms: staleness,
      is_stale: staleness ? staleness > 30000 : true, // 30s stale threshold
      active_locks: Object.keys(workerState.locks).length,
      health: workerState.running && staleness && staleness < 30000 ? 'healthy' : 'degraded'
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Worker state check failed',
      health: 'failed'
    });
  }
});

// **START WORKER** - BD-03: Boot always-on executor
router.post('/start', (req, res) => {
  try {
    if (workerState.running) {
      return res.json({
        success: true,
        message: 'Worker already running',
        state: workerState
      });
    }
    
    const now = new Date().toISOString();
    workerState.running = true;
    workerState.started_at = now;
    workerState.last_tick_at = now;
    workerState.last_activity_at = now;
    
    console.log('[WORKER] 🚀 Always-on executor started');
    
    res.json({
      success: true,
      message: 'Worker started successfully',
      state: workerState
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Worker start failed'
    });
  }
});

// **STOP WORKER** - Graceful shutdown
router.post('/stop', (req, res) => {
  try {
    workerState.running = false;
    console.log('[WORKER] ⏹️ Always-on executor stopped');
    
    res.json({
      success: true,
      message: 'Worker stopped successfully',
      state: workerState
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Worker stop failed'
    });
  }
});

// **HEARTBEAT** - Keep worker alive
router.post('/heartbeat', (req, res) => {
  try {
    workerState.last_tick_at = new Date().toISOString();
    
    // Update lane activity from request
    const { lane, task_id } = req.body;
    if (lane && workerState.lanes[lane as keyof typeof workerState.lanes]) {
      const targetLane = workerState.lanes[lane as keyof typeof workerState.lanes];
      targetLane.active = true;
      targetLane.last_task = task_id || null;
      workerState.last_activity_at = new Date().toISOString();
    }
    
    res.json({
      success: true,
      timestamp: workerState.last_tick_at,
      lanes_active: Object.values(workerState.lanes).filter(l => l.active).length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Heartbeat failed'
    });
  }
});

// **UNLOCK LOCK** - BD-04: Lock reaper for stuck tasks
router.post('/unlock/:lockId', (req, res) => {
  try {
    const { lockId } = req.params;
    
    if (workerState.locks[lockId]) {
      const lock = workerState.locks[lockId];
      delete workerState.locks[lockId];
      
      console.log(`[WORKER] 🔓 Lock released: ${lockId} (was held by ${lock.task_id})`);
      
      res.json({
        success: true,
        message: `Lock ${lockId} released successfully`,
        lock_info: lock
      });
    } else {
      res.json({
        success: true,
        message: `Lock ${lockId} was not active`,
        lock_info: null
      });
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Lock unlock failed'
    });
  }
});

// **ACQUIRE LOCK** - For coordination between workers
router.post('/lock/:lockId', (req, res) => {
  try {
    const { lockId } = req.params;
    const { task_id, expires_in_ms = 300000 } = req.body; // 5min default
    
    if (workerState.locks[lockId]) {
      const existing = workerState.locks[lockId];
      const expired = new Date() > new Date(existing.expires_at);
      
      if (!expired) {
        return res.status(409).json({
          success: false,
          message: `Lock ${lockId} already held by ${existing.task_id}`,
          lock_info: existing
        });
      }
    }
    
    const now = new Date();
    const expires_at = new Date(now.getTime() + expires_in_ms);
    
    workerState.locks[lockId] = {
      acquired_at: now.toISOString(),
      task_id: task_id || 'unknown',
      expires_at: expires_at.toISOString()
    };
    
    res.json({
      success: true,
      message: `Lock ${lockId} acquired successfully`,
      lock_info: workerState.locks[lockId]
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Lock acquire failed'
    });
  }
});

export default router;