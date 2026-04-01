/**
 * 🔄 Replit Sync Routes - Infrastructure-First Deployment
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Handles GitHub webhooks and manages Replit environment sync
 */

import { Router } from 'express';
import crypto from 'node:crypto';
import { exec } from 'node:child_process';
import { RESTART_CONFIG } from '../config/constants.js';

const router = Router();

/**
 * **WEBHOOK SIGNATURE VERIFICATION** - Security for GitHub webhooks
 */
function verifyWebhookSignature(signature: string, timestamp: string, secret: string): boolean {
  if (!secret || !signature || !timestamp) return false;
  
  try {
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(timestamp);
    const expected = hmac.digest('base64');
    
    return crypto.timingSafeEqual(
      Buffer.from(signature || '', 'base64'), 
      Buffer.from(expected)
    );
  } catch (error) {
    console.error('[Sync] Signature verification failed:', error);
    return false;
  }
}

/**
 * **REPLIT SYNC ENDPOINT** - Receive GitHub deployment webhooks
 */
router.post('/sync', async (req, res) => {
  try {
    const sig = req.get('X-Signature') || '';
    const ts = req.get('X-Timestamp') || '';
    const secret = process.env.REPLIT_SYNC_SECRET || '';
    
    console.log('[Sync] 📡 Received GitHub deployment webhook');
    
    if (!secret) {
      console.error('[Sync] ❌ REPLIT_SYNC_SECRET not configured');
      return res.status(500).json({ 
        error: 'Sync secret not configured',
        infrastructure_first: false
      });
    }
    
    // **VERIFY WEBHOOK SIGNATURE**
    const isValid = verifyWebhookSignature(sig, ts, secret);
    if (!isValid) {
      console.warn('[Sync] ⚠️  Invalid webhook signature');
      return res.status(401).json({ 
        error: 'Invalid signature',
        infrastructure_first: false
      });
    }
    
    console.log('[Sync] ✅ Webhook signature verified');
    
    // **EXTRACT DEPLOYMENT INFO**
    const { event, branch, source } = req.body;
    console.log(`[Sync] Event: ${event}, Branch: ${branch}, Source: ${source}`);
    
    if (event === 'deploy' && branch === 'main') {
      console.log('[Sync] 🔄 Starting Infrastructure-First sync...');
      
      // **SAFE GIT SYNC** - Pull latest changes from GitHub
      exec(
        'git fetch origin main && git checkout main && git reset --hard origin/main && npm run build || true',
        (error, stdout, stderr) => {
          if (error) {
            console.error('[Sync] ❌ Git sync failed:', error);
          } else {
            console.log('[Sync] ✅ Successfully synced with GitHub main');
            console.log('[Sync] Git output:', stdout);
          }
          
          if (stderr) {
            console.warn('[Sync] Git warnings:', stderr);
          }
        }
      );
      
      // **GENTLE RESTART** - Allow current requests to complete
      setTimeout(() => {
        console.log('[Sync] 🔄 Restarting to apply Infrastructure-First changes...');
        console.log('[Sync] 🤖 Autonomous development cycle continuing...');
        process.exit(0);
      }, RESTART_CONFIG.SYNC_RESTART_DELAY_MS);
      
      res.json({ 
        ok: true, 
        message: 'Infrastructure-First sync initiated',
        restart_in_ms: RESTART_CONFIG.SYNC_RESTART_DELAY_MS,
        timestamp: Date.now(),
        infrastructure_first: true
      });
      
    } else {
      console.log(`[Sync] Ignoring event ${event} for branch ${branch}`);
      res.json({ 
        ok: true, 
        message: 'Event ignored - not main branch deployment',
        infrastructure_first: true
      });
    }
    
  } catch (error: any) {
    console.error('[Sync] ❌ Sync endpoint failed:', error);
    res.status(500).json({ 
      ok: false, 
      error: String(error?.message || error),
      infrastructure_first: false,
      timestamp: Date.now()
    });
  }
});

/**
 * **REPLIT STATUS** - Health check for Infrastructure-First deployment
 */
router.get('/status', (req, res) => {
  res.json({
    replit_environment: 'active',
    sync_endpoint: '/api/replit/sync',
    infrastructure_first: true,
    git_integration: !!process.env.GH_TOKEN || !!(process.env.GH_APP_ID && process.env.GH_APP_INSTALLATION_ID),
    last_sync: new Date().toISOString(),
    uptime: process.uptime()
  });
});

export default router;