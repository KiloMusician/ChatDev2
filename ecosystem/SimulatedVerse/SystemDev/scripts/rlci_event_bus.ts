#!/usr/bin/env tsx
// SystemDev/scripts/rlci_event_bus.ts
// RLCI Event Bus - Wire into existing Council Bus infrastructure

import type { RLCIEvent, RLCIEnvelope } from '../interfaces/rlci';
import { RLCI_TOPICS } from '../interfaces/rlci';

interface EventSubscription {
  topic: string;
  handler: (event: RLCIEvent) => void | Promise<void>;
  agent?: string;
}

export class RLCIEventBus {
  private subscriptions = new Map<string, EventSubscription[]>();
  private councilBusEndpoint = '/api/council-bus/stream';

  constructor() {
    this.setupDefaultSubscriptions();
  }

  // Subscribe to RLCI events
  subscribe(topic: string, handler: EventSubscription['handler'], agent?: string): void {
    if (!this.subscriptions.has(topic)) {
      this.subscriptions.set(topic, []);
    }

    this.subscriptions.get(topic)!.push({ topic, handler, agent });
    console.log(`📡 RLCI subscribed to ${topic}` + (agent ? ` (${agent})` : ''));
  }

  // Publish RLCI event to Council Bus
  async publish(topic: string, payload: any, envelope?: RLCIEnvelope): Promise<void> {
    const event: RLCIEvent = {
      topic,
      payload,
      timestamp: new Date().toISOString(),
      source: 'rlci_event_bus',
      envelope
    };

    // Publish to local subscribers
    await this.notifySubscribers(event);

    // Publish to Council Bus if available
    await this.publishToCouncilBus(event);
  }

  private async notifySubscribers(event: RLCIEvent): Promise<void> {
    const subscribers = this.subscriptions.get(event.topic) || [];
    
    for (const subscription of subscribers) {
      try {
        await subscription.handler(event);
      } catch (error) {
        console.error(`❌ RLCI event handler error for ${event.topic}:`, error);
      }
    }
  }

  private async publishToCouncilBus(event: RLCIEvent): Promise<void> {
    try {
      // Use existing Council Bus infrastructure
      const response = await fetch('http://localhost:5000/api/council-bus/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: `rlci.${event.topic}`,
          payload: event
        })
      });

      if (!response.ok) {
        console.warn(`⚠️ Failed to publish to Council Bus: ${response.status}`);
      }
    } catch (error) {
      console.warn('⚠️ Council Bus not available:', error.message);
    }
  }

  private setupDefaultSubscriptions(): void {
    // Search overload handler
    this.subscribe(RLCI_TOPICS.SEARCH_OVERLOAD, async (event) => {
      console.log('🔍 Search overload detected, switching to targeted provenance');
      
      const { cwd, pattern, file_count } = event.payload;
      
      // Auto-trigger targeted search
      if (file_count > 5000) {
        await this.publish('action/targeted_search', {
          roots: ['src', 'ChatDev', 'GameDev', 'SystemDev/scripts'],
          max_files: 1000,
          reason: 'search_overload'
        });
      }
    }, 'navigator');

    // Git restriction handler  
    this.subscribe(RLCI_TOPICS.GIT_RESTRICTED, async (event) => {
      console.log('🔒 Git restriction detected, escalating to Git-Steward');
      
      await this.publish('action/git_steward', {
        error: event.payload.error,
        lock_path: event.payload.lock_path,
        suggested_action: 'git gc && rm -f .git/index.lock'
      });
    }, 'janitor');

    // TypeScript error handler
    this.subscribe(RLCI_TOPICS.DIAG_TYPESCRIPT, async (event) => {
      console.log('🔧 TypeScript error detected, suggesting fixes');
      
      const { error_text, file_path } = event.payload;
      
      if (error_text.includes('Cannot find module')) {
        await this.publish('action/import_rewrite', {
          file: file_path,
          reason: 'module_not_found'
        });
      }
    }, 'artificer');

    // Mobile Preview focus handler
    this.subscribe(RLCI_TOPICS.MOBILE_PREVIEW, async (event) => {
      console.log('📱 Mobile Preview focus detected');
      
      await this.publish('action/mobile_debug', {
        device: event.payload.device || 'Samsung S23',
        focus_area: 'PreviewUI'
      });
    }, 'navigator');

    // Execution failure handler
    this.subscribe(RLCI_TOPICS.EXEC_FAILURE, async (event) => {
      const { cmd, exit_code, stderr_excerpt } = event.payload;
      
      // Generate contextual tips based on failure
      if (stderr_excerpt.includes('index.lock')) {
        await this.publish('tip/git_lock', {
          suggestion: 'Run git gc && rm -f .git/index.lock',
          priority: 'high'
        });
      } else if (stderr_excerpt.includes('port') && stderr_excerpt.includes('use')) {
        await this.publish('tip/port_conflict', {
          suggestion: 'Check running processes: ps aux | grep node',
          priority: 'medium'
        });
      }
    }, 'tipsynth');
  }

  // Connect to existing Council Bus stream
  async connectToCouncilBus(): Promise<void> {
    try {
      const eventSource = new EventSource(`http://localhost:5000${this.councilBusEndpoint}`);
      
      eventSource.onopen = () => {
        console.log('🔗 RLCI Event Bus connected to Council Bus');
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Process Council Bus events into RLCI events
          if (data.topic && data.topic.startsWith('rlci.')) {
            const rlciTopic = data.topic.substring(5); // Remove 'rlci.' prefix
            this.notifySubscribers({
              topic: rlciTopic,
              payload: data.payload,
              timestamp: new Date().toISOString(),
              source: 'council_bus'
            });
          }
        } catch (error) {
          console.warn('⚠️ Invalid Council Bus event:', event.data);
        }
      };
      
      eventSource.onerror = () => {
        console.warn('❌ Council Bus connection lost, retrying...');
        setTimeout(() => this.connectToCouncilBus(), 5000);
      };
      
    } catch (error) {
      console.warn('⚠️ Could not connect to Council Bus:', error.message);
    }
  }

  // Get subscription statistics
  getSubscriptionStats(): Record<string, number> {
    const stats: Record<string, number> = {};
    
    for (const [topic, subscriptions] of this.subscriptions.entries()) {
      stats[topic] = subscriptions.length;
    }
    
    return stats;
  }

  // Emit common RLCI events (convenience methods)
  async emitSearchOverload(cwd: string, pattern: string, fileCount: number): Promise<void> {
    await this.publish(RLCI_TOPICS.SEARCH_OVERLOAD, { cwd, pattern, file_count: fileCount });
  }

  async emitGitRestricted(error: string, lockPath?: string): Promise<void> {
    await this.publish(RLCI_TOPICS.GIT_RESTRICTED, { error, lock_path: lockPath });
  }

  async emitTypescriptError(errorText: string, filePath: string): Promise<void> {
    await this.publish(RLCI_TOPICS.DIAG_TYPESCRIPT, { error_text: errorText, file_path: filePath });
  }

  async emitMobilePreviewFocus(device: string = 'Samsung S23'): Promise<void> {
    await this.publish(RLCI_TOPICS.MOBILE_PREVIEW, { device });
  }

  async emitExecFailure(cmd: string, exitCode: number, stderrExcerpt: string): Promise<void> {
    await this.publish(RLCI_TOPICS.EXEC_FAILURE, { cmd, exit_code: exitCode, stderr_excerpt: stderrExcerpt });
  }
}

// Global instance
export const rlciEventBus = new RLCIEventBus();

// Auto-connect to Council Bus if in Node.js environment  
if (typeof process !== 'undefined' && process.env.NODE_ENV !== 'test') {
  rlciEventBus.connectToCouncilBus();
}

export default RLCIEventBus;