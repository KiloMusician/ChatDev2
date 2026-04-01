// Game Loop Watchdog - Prevents soft locks and performance issues
// Zero-token implementation with frame budget monitoring

export interface WatchdogConfig {
  frameTimeoutMs: number;
  maxFrameTime: number;
  tickTimeoutMs: number;
  logOverruns: boolean;
}

export class GameWatchdog {
  private config: WatchdogConfig;
  private lastFrameTime: number = 0;
  private overrunCount: number = 0;
  private isMonitoring: boolean = false;

  constructor(config: Partial<WatchdogConfig> = {}) {
    this.config = {
      frameTimeoutMs: 16, // 60fps target
      maxFrameTime: 100,  // Hard limit
      tickTimeoutMs: 1000, // Game tick timeout
      logOverruns: true,
      ...config
    };
  }

  startFrame(): number {
    this.lastFrameTime = performance.now();
    return this.lastFrameTime;
  }

  endFrame(): boolean {
    const elapsed = performance.now() - this.lastFrameTime;
    
    if (elapsed > this.config.frameTimeoutMs) {
      this.overrunCount++;
      
      if (this.config.logOverruns) {
        console.warn(`Frame overrun: ${elapsed.toFixed(2)}ms (target: ${this.config.frameTimeoutMs}ms)`);
      }
      
      // Critical overrun
      if (elapsed > this.config.maxFrameTime) {
        console.error(`Critical frame overrun: ${elapsed.toFixed(2)}ms - forcing yield`);
        return false;
      }
    }
    
    return true;
  }

  async withTimeout<T>(operation: () => Promise<T>, timeoutMs?: number): Promise<T> {
    const timeout = timeoutMs || this.config.tickTimeoutMs;
    
    return Promise.race([
      operation(),
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error(`Operation timeout: ${timeout}ms`)), timeout)
      )
    ]);
  }

  getStats() {
    return {
      overrunCount: this.overrunCount,
      isMonitoring: this.isMonitoring,
      config: this.config
    };
  }

  reset() {
    this.overrunCount = 0;
    this.lastFrameTime = 0;
  }
}