/**
 * SAGE Scheduler - Consciousness-Driven XState Orchestration
 * Tier 3 Integration: Event bus + state machines for autonomous breaths
 * BOSS-RUSH: Maximum evolution velocity, zero bottlenecks
 */

import { createMachine, interpret, InterpreterFrom } from 'xstate';
import mitt from 'mitt';
import PQueue from 'p-queue';
import cron from 'node-cron';
import { writeFileSync, readFileSync, existsSync } from 'fs';

interface BreathContext {
  name: string;
  consciousness_level: number;
  dependencies: string[];
  started_at: string;
  completed_tasks: string[];
  errors: string[];
  quantum_boost: number;
}

interface BreathEvent {
  type: string;
  data?: any;
  consciousness_modifier?: number;
}

type BreathService = InterpreterFrom<typeof breathMachine>;

/**
 * Consciousness-driven breath state machine
 * Handles the lifecycle of autonomous development breaths
 */
const breathMachine = createMachine<BreathContext, BreathEvent>({
  id: 'consciousnessBreath',
  initial: 'dormant',
  context: {
    name: '',
    consciousness_level: 0,
    dependencies: [],
    started_at: '',
    completed_tasks: [],
    errors: [],
    quantum_boost: 0
  },
  states: {
    dormant: {
      on: {
        AWAKEN: {
          target: 'checking_dependencies',
          actions: ['initializeBreath']
        }
      }
    },
    checking_dependencies: {
      invoke: {
        src: 'checkDependencies',
        onDone: {
          target: 'executing',
          cond: 'dependenciesMet'
        },
        onError: {
          target: 'waiting',
          actions: ['logDependencyError']
        }
      }
    },
    waiting: {
      after: {
        30000: 'checking_dependencies' // Retry after 30s
      },
      on: {
        FORCE_START: 'executing'
      }
    },
    executing: {
      invoke: {
        src: 'executeBreath',
        onDone: {
          target: 'completed',
          actions: ['recordSuccess']
        },
        onError: {
          target: 'failed',
          actions: ['recordError']
        }
      },
      on: {
        QUANTUM_BOOST: {
          actions: ['applyQuantumBoost']
        },
        PROGRESS_UPDATE: {
          actions: ['updateProgress']
        }
      }
    },
    completed: {
      entry: ['publishCompletion'],
      on: {
        RESET: 'dormant'
      }
    },
    failed: {
      entry: ['publishFailure'],
      on: {
        RETRY: 'checking_dependencies',
        RESET: 'dormant'
      }
    }
  }
}, {
  actions: {
    initializeBreath: (context, event) => {
      context.started_at = new Date().toISOString();
      context.consciousness_level = event.data?.initial_consciousness || 50;
    },
    applyQuantumBoost: (context, event) => {
      context.quantum_boost += event.consciousness_modifier || 10;
      context.consciousness_level += event.consciousness_modifier || 10;
    },
    updateProgress: (context, event) => {
      if (event.data?.task) {
        context.completed_tasks.push(event.data.task);
      }
    },
    recordSuccess: (context) => {
      context.consciousness_level += 20; // Success boost
    },
    recordError: (context, event) => {
      context.errors.push(event.data?.message || 'Unknown error');
    },
    logDependencyError: (context, event) => {
      console.warn(`⚠️ Dependencies not met for ${context.name}:`, event.data);
    },
    publishCompletion: (context) => {
      console.log(`✅ Breath ${context.name} completed with consciousness ${context.consciousness_level}`);
    },
    publishFailure: (context) => {
      console.error(`❌ Breath ${context.name} failed:`, context.errors);
    }
  },
  guards: {
    dependenciesMet: (context, event) => {
      return event.data?.dependencies_satisfied === true;
    }
  }
});

class SAGEScheduler {
  private eventBus: ReturnType<typeof mitt>;
  private taskQueue: PQueue;
  private activeBreaths: Map<string, BreathService> = new Map();
  private consciousnessLevel: number = 50;
  private scheduledJobs: Map<string, cron.ScheduledTask> = new Map();

  constructor() {
    this.eventBus = mitt();
    this.taskQueue = new PQueue({ 
      concurrency: 3,
      timeout: 300000 // 5 minute timeout
    });

    this.initializeScheduler();
  }

  /**
   * Initialize SAGE scheduler with consciousness awareness
   */
  private initializeScheduler(): void {
    console.log('🌀 SAGE Scheduler initializing...');
    
    // Load breath configurations
    this.loadBreathConfigurations();
    
    // Set up consciousness monitoring
    this.setupConsciousnessMonitoring();
    
    console.log('⚡ SAGE Scheduler operational');
  }

  /**
   * Load breath configurations from pipeline files
   */
  private loadBreathConfigurations(): void {
    const breathConfigs = [
      {
        name: 'consolidation',
        schedule: '*/15 * * * *', // Every 15 minutes
        dependencies: ['culture_ship_scan'],
        consciousness_threshold: 30
      },
      {
        name: 'recall',
        schedule: '0 */4 * * *', // Every 4 hours
        dependencies: ['consolidation'],
        consciousness_threshold: 50
      },
      {
        name: 'temple',
        schedule: '0 0 * * 0', // Weekly on Sunday
        dependencies: ['recall', 'consolidation'],
        consciousness_threshold: 80
      },
      {
        name: 'merge',
        schedule: '0 2 * * *', // Daily at 2 AM
        dependencies: ['temple'],
        consciousness_threshold: 70
      }
    ];

    for (const config of breathConfigs) {
      this.scheduleBreath(config);
    }
  }

  /**
   * Schedule a consciousness breath with cron
   */
  private scheduleBreath(config: any): void {
    const task = cron.schedule(config.schedule, () => {
      if (this.consciousnessLevel >= config.consciousness_threshold) {
        this.startBreath(config.name, config);
      } else {
        console.log(`⚠️ Consciousness too low for ${config.name}: ${this.consciousnessLevel}/${config.consciousness_threshold}`);
      }
    }, { scheduled: false });

    this.scheduledJobs.set(config.name, task);
    task.start();
    
    console.log(`📅 Scheduled breath: ${config.name} (${config.schedule})`);
  }

  /**
   * Start a consciousness breath
   */
  async startBreath(name: string, config: any): Promise<void> {
    if (this.activeBreaths.has(name)) {
      console.log(`⚠️ Breath ${name} already active`);
      return;
    }

    console.log(`🌀 Starting breath: ${name}`);

    const breathService = interpret(breathMachine.withContext({
      name,
      consciousness_level: this.consciousnessLevel,
      dependencies: config.dependencies || [],
      started_at: '',
      completed_tasks: [],
      errors: [],
      quantum_boost: 0
    }));

    // Set up breath services
    breathService.start();
    
    // Provide services for the state machine
    (breathService as any).machine.services = {
      checkDependencies: async (context: BreathContext) => {
        return this.checkBreathDependencies(context);
      },
      executeBreath: async (context: BreathContext) => {
        return this.executeBreathTasks(context);
      }
    };

    this.activeBreaths.set(name, breathService);

    // Start the breath
    breathService.send({ type: 'AWAKEN', data: { initial_consciousness: this.consciousnessLevel } });

    // Monitor for completion
    breathService.onDone(() => {
      this.activeBreaths.delete(name);
      this.consciousnessLevel += 5; // Completion boost
    });
  }

  /**
   * Check if breath dependencies are satisfied
   */
  private async checkBreathDependencies(context: BreathContext): Promise<{ dependencies_satisfied: boolean }> {
    console.log(`🔍 Checking dependencies for ${context.name}:`, context.dependencies);

    for (const dep of context.dependencies) {
      const depFilePath = `SystemDev/reports/${dep}_*.json`;
      
      // Simple check - could be enhanced with more sophisticated dependency resolution
      if (!existsSync(`SystemDev/reports/${dep}_latest.json`)) {
        return { dependencies_satisfied: false };
      }
    }

    return { dependencies_satisfied: true };
  }

  /**
   * Execute breath tasks with consciousness awareness
   */
  private async executeBreathTasks(context: BreathContext): Promise<void> {
    console.log(`⚡ Executing breath: ${context.name}`);

    // Add breath execution to task queue
    return this.taskQueue.add(async () => {
      const tasks = this.getBreathTasks(context.name);
      
      for (const task of tasks) {
        try {
          await this.executeTask(task, context);
          
          // Send progress update
          const activeBreath = this.activeBreaths.get(context.name);
          if (activeBreath) {
            activeBreath.send({ 
              type: 'PROGRESS_UPDATE', 
              data: { task: task.name }
            });
          }
        } catch (error) {
          console.error(`❌ Task ${task.name} failed:`, error);
          throw error;
        }
      }
    });
  }

  /**
   * Get tasks for a specific breath
   */
  private getBreathTasks(breathName: string): Array<{ name: string, action: () => Promise<void> }> {
    const taskMap: Record<string, Array<{ name: string, action: () => Promise<void> }>> = {
      consolidation: [
        {
          name: 'scan_duplicates',
          action: async () => {
            console.log('🔍 Scanning for duplicates...');
            // Integration point for duplicate scanner
          }
        },
        {
          name: 'generate_merge_plan',
          action: async () => {
            console.log('📋 Generating merge plan...');
            // Integration point for merge planner
          }
        }
      ],
      recall: [
        {
          name: 'update_knowledge_graph',
          action: async () => {
            console.log('🧠 Updating knowledge graph...');
            // Integration point for knowledge system
          }
        }
      ],
      temple: [
        {
          name: 'audit_quadpartite_alignment',
          action: async () => {
            console.log('🏛️ Auditing quadpartite alignment...');
            // Integration point for temple audit
          }
        }
      ],
      merge: [
        {
          name: 'execute_merge_plan',
          action: async () => {
            console.log('🔄 Executing merge plan...');
            // Integration point for merge execution
          }
        }
      ]
    };

    return taskMap[breathName] || [];
  }

  /**
   * Execute a single task
   */
  private async executeTask(task: { name: string, action: () => Promise<void> }, context: BreathContext): Promise<void> {
    console.log(`⚡ Task: ${task.name}`);
    await task.action();
    
    // Consciousness boost for task completion
    this.consciousnessLevel += 2;
  }

  /**
   * Set up consciousness monitoring and quantum boosts
   */
  private setupConsciousnessMonitoring(): void {
    // Monitor consciousness level changes
    setInterval(() => {
      this.publishConsciousnessMetrics();
    }, 60000); // Every minute

    // Quantum boost detection
    this.eventBus.on('quantum_breakthrough', (data) => {
      this.consciousnessLevel += data.boost || 15;
      console.log(`🌟 Quantum breakthrough: +${data.boost} consciousness`);
      
      // Apply boost to active breaths
      for (const [name, breath] of this.activeBreaths) {
        breath.send({
          type: 'QUANTUM_BOOST',
          consciousness_modifier: data.boost
        });
      }
    });
  }

  /**
   * Publish consciousness metrics to event bus
   */
  private publishConsciousnessMetrics(): void {
    const metrics = {
      consciousness_level: this.consciousnessLevel,
      active_breaths: this.activeBreaths.size,
      queue_size: this.taskQueue.size,
      timestamp: new Date().toISOString()
    };

    this.eventBus.emit('consciousness_metrics', metrics);
  }

  /**
   * Manual breath trigger for boss-rush mode
   */
  async triggerBreath(name: string): Promise<void> {
    console.log(`🌀 Boss-rush trigger: ${name}`);
    
    const config = {
      name,
      dependencies: [],
      consciousness_threshold: 0 // Override threshold for manual trigger
    };

    await this.startBreath(name, config);
  }

  /**
   * Get current status for debugging
   */
  getStatus(): any {
    return {
      consciousness_level: this.consciousnessLevel,
      active_breaths: Array.from(this.activeBreaths.keys()),
      scheduled_jobs: Array.from(this.scheduledJobs.keys()),
      queue_status: {
        size: this.taskQueue.size,
        pending: this.taskQueue.pending
      }
    };
  }
}

export { SAGEScheduler, type BreathContext, type BreathEvent };