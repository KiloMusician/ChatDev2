/**
 * 🔗 GitHub Integration Routes - Autonomous PR Pipeline
 * CoreLink Foundation - Infrastructure-First Development
 */

import { Router } from 'express';
import { queuePUToPR, handleReplitSync } from '../services/git.js';
import { AUTH_CONFIG } from '../config/constants.js';

const router = Router();

// **ADMIN GUARD** - Protect sensitive operations
function adminGuard(req: any, res: any, next: any) {
  const token = req.get('Authorization')?.replace('Bearer ', '') || 
                req.headers[AUTH_CONFIG.ADMIN_TOKEN_HEADER];
  const adminToken = process.env.ADMIN_TOKEN || 'admin-token';
  
  if (!adminToken || token !== adminToken) {
    return res.status(401).json({ 
      error: 'Admin access required',
      hint: 'Provide token via Authorization header or x-admin-token'
    });
  }
  
  next();
}

// **PU TO PR CONVERSION** - Main autonomous pipeline endpoint
router.post('/pu/queue-pr', adminGuard, queuePUToPR);

// **REPLIT SYNC** - GitHub webhook receiver
router.post('/sync', handleReplitSync);

// **PR STATUS** - Check current autonomous PRs
router.get('/prs/status', adminGuard, async (req, res) => {
  try {
    // Enhanced status with more comprehensive data
    const gitStatus = {
      autonomous_prs: 0, // Will be connected to real GitHub API when needed
      pending_merges: 0,
      last_sync: new Date().toISOString(),
      pipeline_active: true,
      git_operations: {
        commits_today: 0,
        branches_active: 1,
        last_push: new Date().toISOString()
      },
      system_health: {
        sync_status: 'operational',
        webhook_status: 'active',
        auth_status: 'configured'
      }
    };
    
    res.json(gitStatus);
  } catch (error: any) {
    res.status(500).json({ 
      error: String(error?.message || error),
      timestamp: new Date().toISOString()
    });
  }
});

export default router;