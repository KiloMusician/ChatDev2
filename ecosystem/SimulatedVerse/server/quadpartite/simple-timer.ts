// SIMPLE TIMER - Replaces complex breathing theater with functional operations
// Does actual work instead of logging impressive messages

import { EventEmitter } from 'events';

export class SimpleTimer extends EventEmitter {
  private active = false;
  private interval: NodeJS.Timeout | null = null;
  private cycleCount = 0;

  start() {
    if (this.active) return;
    
    this.active = true;
    this.interval = setInterval(() => {
      this.cycleCount++;
      
      // Emit simple progress event - no theater
      this.emit('cycle_complete', {
        cycle: this.cycleCount,
        timestamp: new Date().toISOString()
      });
      
      // Log completion without theater
      if (this.cycleCount % 10 === 0) {
        console.log(`[SimpleTimer] ✅ Cycle ${this.cycleCount} complete`);
      }
      
    }, 30000); // 30 second intervals
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.active = false;
  }

  getStatus() {
    return {
      active: this.active,
      cycle_count: this.cycleCount,
      uptime_minutes: Math.floor(this.cycleCount * 0.5) // 30s intervals = 0.5 min each
    };
  }
}