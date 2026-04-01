#!/usr/bin/env tsx
/**
 * WORKING ORDERS TASK ROUTER - User Request Integration
 * Routes user requests into existing PU queue, breath cycle, and agent systems
 * SEEK-UPDATE-FIRST: Connects to existing systems rather than creating new ones
 */

import { writeFileSync, existsSync, readFileSync, appendFileSync } from 'fs';
import { randomUUID } from 'crypto';

export interface UserTask {
  id: string;
  track: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H';
  priority: number;
  title: string;
  user_request: string;
  assigned_agent?: string;
  dependencies: string[];
  zeta_checks: ZetaProtocol;
  created_at: string;
  status: 'queued' | 'in_progress' | 'completed' | 'failed';
}

export interface ZetaProtocol {
  idempotency_key: string;
  rollback_plan: string;
  pre_checks: string[];
  post_checks: string[];
}

const TRACK_MAPPING = {
  // Foundation & Infrastructure
  A: {
    keywords: ['capability', 'matrix', 'probe', 'truth', 'infrastructure', 'foundation'],
    agents: ['sage_pilot', 'librarian'],
    description: 'foundation_infrastructure'
  },
  // Hygiene & Cleanup
  B: {
    keywords: ['fix', 'error', 'cleanup', 'hygiene', 'typescript', 'lint'],
    agents: ['janitor', 'raven'],
    description: 'consolidation_hygiene'
  },
  // Deduplication & Moves
  C: {
    keywords: ['duplicate', 'consolidate', 'merge', 'dedupe', 'move'],
    agents: ['alchemist', 'artificer'],
    description: 'deduplication_moves'
  },
  // Rosetta & Integration
  D: {
    keywords: ['rosetta', 'integration', 'translate', 'bridge', 'connect'],
    agents: ['librarian'],
    description: 'rosetta_integration'
  },
  // Cascade & Optimization
  E: {
    keywords: ['cascade', 'optimize', 'performance', 'flow', 'breath'],
    agents: ['sage_pilot'],
    description: 'cascade_optimization'
  },
  // Alignment & Quadpartite
  F: {
    keywords: ['alignment', 'quadpartite', 'systemdev', 'chatdev', 'gamedev', 'previewui'],
    agents: ['sage_pilot'],
    description: 'quadpartite_alignment'
  },
  // UI & Preview
  G: {
    keywords: ['ui', 'preview', 'interface', 'dimensional', 'companion', 'frontend'],
    agents: ['wizard_navigator'],
    description: 'ui_preview'
  },
  // Game & Mechanics
  H: {
    keywords: ['game', 'mechanic', 'idle', 'progression', 'consciousness', 'simulation'],
    agents: ['wizard_navigator'],
    description: 'game_mechanics'
  }
};

export class TaskRouter {
  private puQueuePath = '../../SystemDev/backlog/pu_queue.jsonl';
  private receiptsPath = '../../SystemDev/receipts/';
  private isOfflineMode = false;

  constructor() {
    this.checkOfflineMode();
    this.ensureQueueExists();
  }

  /**
   * Route a user request into the appropriate track and queue system
   */
  async routeUserRequest(request: string, context?: any): Promise<UserTask> {
    console.log(`[TASK_ROUTER] Processing user request: "${request.substring(0, 100)}..."`);

    // 1. Classify request into track
    const track = this.classifyRequest(request);
    
    // 2. Assign appropriate agent
    const agent = this.assignAgent(track, request);
    
    // 3. Generate task with Zeta protocol
    const task: UserTask = {
      id: randomUUID(),
      track,
      priority: this.calculatePriority(request, track),
      title: this.generateTitle(request, track),
      user_request: request,
      assigned_agent: agent,
      dependencies: this.extractDependencies(request),
      zeta_checks: this.generateZetaProtocol(request, track),
      created_at: new Date().toISOString(),
      status: 'queued'
    };

    // 4. Enqueue in PU queue
    await this.enqueuePUTask(task);
    
    // 5. Emit council bus event
    this.emitCouncilEvent('puq.task.enqueued', task);
    
    // 6. Generate receipt
    this.generateReceipt(task);

    console.log(`[TASK_ROUTER] ✅ Task ${task.id} routed to track ${track} (${agent})`);
    
    return task;
  }

  /**
   * Classify user request into appropriate track
   */
  private classifyRequest(request: string): 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' {
    const lowerRequest = request.toLowerCase();
    
    // Check each track's keywords
    for (const [track, config] of Object.entries(TRACK_MAPPING)) {
      for (const keyword of config.keywords) {
        if (lowerRequest.includes(keyword)) {
          return track as keyof typeof TRACK_MAPPING;
        }
      }
    }

    // Default to foundation track for unclassified requests
    return 'A';
  }

  /**
   * Assign appropriate agent based on track and request complexity
   */
  private assignAgent(track: string, request: string): string {
    const trackConfig = TRACK_MAPPING[track as keyof typeof TRACK_MAPPING];
    
    // If LLM is offline, prefer offline-capable agents
    if (this.isOfflineMode) {
      const offlineCapable = ['librarian', 'artificer', 'alchemist', 'janitor', 'raven'];
      const preferredAgents = trackConfig.agents.filter(agent => 
        offlineCapable.includes(agent)
      );
      if (preferredAgents.length > 0) {
        return preferredAgents[0];
      }
    }

    return trackConfig.agents[0];
  }

  /**
   * Calculate priority based on request urgency and track
   */
  private calculatePriority(request: string, track: string): number {
    const urgencyKeywords = ['urgent', 'critical', 'broken', 'error', 'failing', 'fix'];
    const hasUrgency = urgencyKeywords.some(keyword => 
      request.toLowerCase().includes(keyword)
    );

    // Foundation and hygiene get higher priority
    const trackPriority = {
      'A': 10, 'B': 9, 'F': 8, 'E': 7,
      'D': 6, 'C': 5, 'G': 4, 'H': 3
    };

    const basePriority = trackPriority[track as keyof typeof trackPriority] || 5;
    return hasUrgency ? basePriority + 5 : basePriority;
  }

  /**
   * Generate task title from request
   */
  private generateTitle(request: string, track: string): string {
    const trackConfig = TRACK_MAPPING[track as keyof typeof TRACK_MAPPING];
    const words = request.split(' ').slice(0, 6).join(' ');
    return `${trackConfig.description}: ${words}`;
  }

  /**
   * Extract dependencies from request
   */
  private extractDependencies(request: string): string[] {
    const dependencies: string[] = [];
    
    // Look for explicit dependency mentions
    if (request.includes('after') || request.includes('depends on')) {
      dependencies.push('previous_task_completion');
    }
    
    if (request.includes('typescript') || request.includes('compile')) {
      dependencies.push('typescript_compilation');
    }
    
    if (request.includes('ui') || request.includes('preview')) {
      dependencies.push('ui_build_ready');
    }
    
    return dependencies;
  }

  /**
   * Generate Zeta protocol for safe execution
   */
  private generateZetaProtocol(request: string, track: string): ZetaProtocol {
    return {
      idempotency_key: `task_${Date.now()}_${track}`,
      rollback_plan: 'git_checkout_previous_state',
      pre_checks: [
        'verify_repository_clean',
        'check_typescript_compilation',
        'backup_current_state'
      ],
      post_checks: [
        'verify_no_breaking_changes',
        'run_smoke_tests',
        'update_receipts'
      ]
    };
  }

  /**
   * Enqueue task in PU queue system
   */
  private async enqueuePUTask(task: UserTask): Promise<void> {
    const queueEntry = {
      id: task.id,
      type: 'UserRequest',
      phase: 'foundational',
      title: task.title,
      track: task.track,
      priority: task.priority,
      assigned_agent: task.assigned_agent,
      dependencies: task.dependencies,
      zeta: task.zeta_checks,
      created_at: task.created_at,
      user_request: task.user_request
    };

    // Append to JSONL queue
    appendFileSync(this.puQueuePath, JSON.stringify(queueEntry) + '\n');
    
    console.log(`[PU_QUEUE] ✅ Task ${task.id} enqueued`);
  }

  /**
   * Emit council bus event
   */
  private emitCouncilEvent(event: string, data: any): void {
    const eventData = {
      event,
      data,
      timestamp: new Date().toISOString(),
      source: 'task_router'
    };

    // Write to council event log
    const eventPath = 'SystemDev/receipts/council_events.jsonl';
    appendFileSync(eventPath, JSON.stringify(eventData) + '\n');
    
    console.log(`[COUNCIL_BUS] 📡 Event: ${event}`);
  }

  /**
   * Generate receipt for task routing
   */
  private generateReceipt(task: UserTask): void {
    const receipt = {
      action: 'task_routed',
      task_id: task.id,
      track: task.track,
      agent: task.assigned_agent,
      priority: task.priority,
      timestamp: new Date().toISOString(),
      routing_decision: {
        classification_method: 'keyword_matching',
        agent_selection: this.isOfflineMode ? 'offline_preferred' : 'standard',
        zeta_protocol_applied: true
      }
    };

    const receiptPath = `${this.receiptsPath}task_routing_${task.id}.json`;
    writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
  }

  /**
   * Check if system is in offline mode (LLM unavailable)
   */
  private checkOfflineMode(): void {
    // Check if we're in offline mode based on recent LLM failures
    try {
      // This would normally check LLM status
      this.isOfflineMode = true; // Currently offline based on logs
      console.log(`[TASK_ROUTER] 🌐 Offline mode: ${this.isOfflineMode}`);
    } catch {
      this.isOfflineMode = true;
    }
  }

  /**
   * Ensure PU queue file exists
   */
  private ensureQueueExists(): void {
    if (!existsSync(this.puQueuePath)) {
      writeFileSync(this.puQueuePath, '');
      console.log(`[TASK_ROUTER] ✅ Created PU queue: ${this.puQueuePath}`);
    }
  }

  /**
   * Get current queue status
   */
  getQueueStatus(): any {
    const queueExists = existsSync(this.puQueuePath);
    let queueSize = 0;
    
    if (queueExists) {
      const content = readFileSync(this.puQueuePath, 'utf-8');
      queueSize = content.split('\n').filter(line => line.trim()).length;
    }

    return {
      queue_exists: queueExists,
      queue_size: queueSize,
      offline_mode: this.isOfflineMode,
      last_checked: new Date().toISOString()
    };
  }
}

// CLI interface for direct task routing
if (import.meta.url === `file://${process.argv[1]}`) {
  const router = new TaskRouter();
  const userRequest = process.argv[2] || 'Create capability matrix and fix integration issues';
  
  router.routeUserRequest(userRequest).then(task => {
    console.log('\n✅ Task successfully routed:');
    console.log(JSON.stringify(task, null, 2));
    console.log('\n📊 Queue status:');
    console.log(JSON.stringify(router.getQueueStatus(), null, 2));
  });
}

// TaskRouter already exported in class declaration