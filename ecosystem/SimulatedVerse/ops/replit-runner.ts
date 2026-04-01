/**
 * 🤖 Replit Runner - Infrastructure-First Local Execution
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Provides "hands" for the autonomous system within Replit environment
 * Executes PUs that require local filesystem/shell operations
 */

import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';

const execAsync = promisify(exec);

interface PU {
  id: string;
  type: 'shell' | 'file' | 'http';
  commands?: string[];
  files?: Array<{ path: string; content: string; mode?: string }>;
  requests?: Array<{ url: string; method: string; body?: any }>;
  timeout?: number;
}

interface LeaseResponse {
  items: PU[];
  lease_id: string;
  expires_at: string;
}

// **CONFIGURATION**
const ADMIN_TOKEN = process.env.ADMIN_TOKEN;
const API_BASE = process.env.API_BASE || 'http://localhost:5000';
const RUNNER_ID = process.env.RUNNER_ID || 'replit-agent';
const POLL_INTERVAL = parseInt(process.env.POLL_INTERVAL || '5000');

/**
 * **SECURE EXECUTOR** - Run commands with safety constraints
 */
async function executeShellPU(pu: PU): Promise<{ stdout: string; stderr: string; success: boolean }> {
  try {
    console.log(`[Runner] 🔧 Executing shell PU: ${pu.id}`);
    
    const results = [];
    for (const command of pu.commands || []) {
      // **SAFETY FILTERS** - Block dangerous commands
      const dangerous = ['rm -rf', 'sudo', 'chmod 777', 'dd', '>>', 'curl'];
      if (dangerous.some(cmd => command.includes(cmd))) {
        throw new Error(`Dangerous command blocked: ${command}`);
      }
      
      console.log(`[Runner] Running: ${command}`);
      const result = await execAsync(command, { 
        timeout: pu.timeout || 30000,
        cwd: process.cwd()
      });
      
      results.push(result);
    }
    
    return {
      stdout: results.map(r => r.stdout).join('\n'),
      stderr: results.map(r => r.stderr).join('\n'),
      success: true
    };
    
  } catch (error: any) {
    console.error(`[Runner] ❌ Shell execution failed:`, error);
    return {
      stdout: '',
      stderr: String(error?.message || error),
      success: false
    };
  }
}

/**
 * **FILE OPERATIONS** - Safe filesystem modifications
 */
async function executeFilePU(pu: PU): Promise<{ files_written: number; success: boolean; errors: string[] }> {
  try {
    console.log(`[Runner] 📝 Executing file PU: ${pu.id}`);
    
    const errors: string[] = [];
    let filesWritten = 0;
    
    for (const file of pu.files || []) {
      try {
        // **SAFETY CHECKS** - Prevent writing outside project
        if (file.path.includes('..') || file.path.startsWith('/')) {
          errors.push(`Unsafe path blocked: ${file.path}`);
          continue;
        }
        
        // **ENSURE DIRECTORY EXISTS**
        const dir = path.dirname(file.path);
        await fs.mkdir(dir, { recursive: true });
        
        // **WRITE FILE**
        await fs.writeFile(file.path, file.content, 'utf8');
        
        // **SET PERMISSIONS** if specified
        if (file.mode === '100755') {
          await fs.chmod(file.path, 0o755);
        }
        
        filesWritten++;
        console.log(`[Msg⛛{${Date.now() % 1000}}] File written: ${file.path}`);
        
      } catch (error: any) {
        errors.push(`Failed to write ${file.path}: ${error.message}`);
      }
    }
    
    return {
      files_written: filesWritten,
      success: errors.length === 0,
      errors
    };
    
  } catch (error: any) {
    console.error(`[Runner] ❌ File execution failed:`, error);
    return {
      files_written: 0,
      success: false,
      errors: [String(error?.message || error)]
    };
  }
}

/**
 * **HTTP OPERATIONS** - Make external API calls
 */
async function executeHttpPU(pu: PU): Promise<{ responses: any[]; success: boolean }> {
  try {
    console.log(`[Runner] 🌐 Executing HTTP PU: ${pu.id}`);
    
    const responses = [];
    for (const request of pu.requests || []) {
      const response = await fetch(request.url, {
        method: request.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'CoreLink-Foundation-Runner/1.0'
        },
        body: request.body ? JSON.stringify(request.body) : undefined
      });
      
      const data = await response.text();
      responses.push({
        url: request.url,
        status: response.status,
        data: data.slice(0, 1000) // Truncate large responses
      });
    }
    
    return { responses, success: true };
    
  } catch (error: any) {
    console.error(`[Runner] ❌ HTTP execution failed:`, error);
    return {
      responses: [],
      success: false
    };
  }
}

/**
 * **PU LEASE MANAGER** - Fetch and execute tasks
 */
async function processLeasedPUs() {
  try {
    // **LEASE PUs** from the server
    const leaseResponse = await fetch(`${API_BASE}/api/agent/lease?runner=${RUNNER_ID}&n=3`, {
      headers: {
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!leaseResponse.ok) {
      console.log(`[Runner] No PUs available (${leaseResponse.status})`);
      return;
    }
    
    const lease: LeaseResponse = await leaseResponse.json();
    console.log(`[Runner] 📋 Leased ${lease.items.length} PU(s)`);
    
    // **EXECUTE EACH PU**
    for (const pu of lease.items) {
      let result: any = {};
      
      try {
        switch (pu.type) {
          case 'shell':
            result = await executeShellPU(pu);
            break;
          case 'file':
            result = await executeFilePU(pu);
            break;
          case 'http':
            result = await executeHttpPU(pu);
            break;
          default:
            throw new Error(`Unknown PU type: ${pu.type}`);
        }
        
        // **ACKNOWLEDGE SUCCESS**
        await fetch(`${API_BASE}/api/agent/ack`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${ADMIN_TOKEN}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            id: pu.id,
            lease_id: lease.lease_id,
            status: result.success ? 'completed' : 'failed',
            result,
            timestamp: Date.now()
          })
        });
        
        console.log(`[Msg⛛{${Date.now() % 1000}}] PU completed: ${pu.id}`);
        
      } catch (error: any) {
        console.error(`[Runner] ❌ PU ${pu.id} failed:`, error);
        
        // **ACKNOWLEDGE FAILURE**
        try {
          await fetch(`${API_BASE}/api/agent/ack`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${ADMIN_TOKEN}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              id: pu.id,
              lease_id: lease.lease_id,
              status: 'failed',
              error: String(error?.message || error),
              timestamp: Date.now()
            })
          });
        } catch (ackError) {
          console.error(`[Runner] Failed to acknowledge PU failure:`, ackError);
        }
      }
    }
    
  } catch (error: any) {
    console.error(`[Runner] ❌ Lease processing failed:`, error);
  }
}

/**
 * **MAIN RUNNER LOOP** - Infrastructure-First execution
 */
async function main() {
  console.log('[Runner] 🤖 CoreLink Foundation Replit Runner starting...');
  console.log(`[Runner] 🔗 API: ${API_BASE}`);
  console.log(`[Runner] 📡 Poll interval: ${POLL_INTERVAL}ms`);
  console.log(`[Runner] 🏷️  Runner ID: ${RUNNER_ID}`);
  
  if (!ADMIN_TOKEN) {
    console.error('[Runner] ❌ ADMIN_TOKEN required for authentication');
    process.exit(1);
  }
  
  // **CONTINUOUS EXECUTION LOOP**
  setInterval(async () => {
    await processLeasedPUs();
  }, POLL_INTERVAL);
  
  console.log('[Msg⛛{RUNNER}] Infrastructure-First runner operational');
  console.log('[Runner] 🔄 Polling for autonomous tasks...');
}

// **ENTRY POINT**
if (require.main === module) {
  main().catch(error => {
    console.error('[Runner] ❌ Runner failed to start:', error);
    process.exit(1);
  });
}

export { processLeasedPUs, executeShellPU, executeFilePU, executeHttpPU };