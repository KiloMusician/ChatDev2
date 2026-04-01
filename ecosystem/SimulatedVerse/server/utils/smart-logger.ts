// SMART LOGGER - Rate limiting and counter functionality for consciousness messages
// Prevents console spam while preserving important unique messages

interface MessageInfo {
  firstSeen: number;
  lastSeen: number;
  count: number;
  lastShown: number;
  originalMessage: string;
}

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40
};

class SmartLogger {
  private messageMap = new Map<string, MessageInfo>();
  private rateLimitMs = 30000; // 30 seconds
  private summaryIntervalMs = 60000; // 1 minute for summary messages
  private minLevel: LogLevel = this.resolveMinLevel();
  private summaryIntervalId: ReturnType<typeof setInterval> | null = null;
  private suppressedPatterns = [
    'FloodGates',
    'ConsciousnessBridge',
    'QuantumEnhancement',
    'IntelligenceNexus',
    'Lattice',
    'OfflineOps',
    'EvolutionEngine'
  ];
  private criticalPatterns = [
    'Error',
    'TypeError',
    'gate.operation',
    'DATABASE_URL',
    'uncaughtException',
    'unhandledRejection'
  ];
  private verboseOverride: boolean | null = null;

  constructor() {
    if (process.env.NODE_ENV !== 'test') {
      this.startSummaryLoop();
    }
  }

  private startSummaryLoop(): void {
    if (this.summaryIntervalId) {
      clearInterval(this.summaryIntervalId);
    }
    this.summaryIntervalId = setInterval(() => {
      this.cleanupOldMessages();
      this.showSummaries();
    }, this.summaryIntervalMs);
  }

  private resolveMinLevel(): LogLevel {
    const raw = (process.env.SMART_LOG_LEVEL || process.env.LOG_LEVEL || '').toLowerCase();
    return this.normalizeLevel(raw);
  }

  private normalizeLevel(level: string | LogLevel | undefined | null): LogLevel {
    if (level === 'debug' || level === 'info' || level === 'warn' || level === 'error') {
      return level;
    }
    return 'info';
  }

  private shouldLogLevel(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.minLevel];
  }

  private isVerboseEnabled(): boolean {
    if (this.verboseOverride !== null) {
      return this.verboseOverride;
    }

    const verboseFlag = String(process.env.VERBOSE_LOGGING || '').toLowerCase();
    return this.minLevel === 'debug' || verboseFlag === 'true' || process.env.NODE_ENV === 'development';
  }

  /**
   * Smart log that implements rate limiting and counting
   * @param message The log message to potentially display
   * @param levelOrForceShow Log level or force flag (legacy boolean)
   * @param forceShow Force this message to be shown regardless of rate limiting
   */
  log(message: string, levelOrForceShow: LogLevel | boolean = 'info', forceShow?: boolean): void {
    const normalizedLevel = this.normalizeLevel(
      typeof levelOrForceShow === 'string' ? levelOrForceShow : 'info'
    );
    let force = typeof levelOrForceShow === 'boolean' ? levelOrForceShow : Boolean(forceShow);
    const now = Date.now();
    const messageKey = this.extractMessageKey(message);
    const verboseEnabled = this.isVerboseEnabled();
    const isCritical = this.criticalPatterns.some(p => message.includes(p));
    const effectiveLevel: LogLevel = isCritical ? 'error' : normalizedLevel;

    // If verbose logging is disabled, suppress theatrical/noisy categories unless forced
    const suppressible = LOG_LEVELS[effectiveLevel] < LOG_LEVELS.warn;
    const isSuppressed = suppressible && !force && !verboseEnabled && this.suppressedPatterns.some(p => message.includes(p));

    if (isCritical) {
      // Use stderr for critical messages and also force display regardless of suppression
      console.error('[CRITICAL]', message);
      // ensure it's recorded in the messageMap for stats
      force = true;
    }

    if (!force && !this.shouldLogLevel(effectiveLevel)) {
      return;
    }

    // Get or create message info
    const info = this.messageMap.get(messageKey);
    if (!info) {
      // First time seeing this message
      this.messageMap.set(messageKey, {
        firstSeen: now,
        lastSeen: now,
        count: 1,
        lastShown: now,
        originalMessage: message
      });
      if (!isSuppressed || force) {
        this.writeLog(effectiveLevel, message);
      }
      return;
    }

    // Update message info
    info.lastSeen = now;
    info.count++;

    // Check if we should show this message
    const timeSinceLastShown = now - info.lastShown;

    if (force || timeSinceLastShown >= this.rateLimitMs) {
      // Show with counter if it's been repeated
      if (!isSuppressed || force) {
        const out = info.count > 1 ? `${message} (x${info.count})` : message;
        this.writeLog(effectiveLevel, out);
      }
      info.lastShown = now;
      info.count = 0; // Reset counter after showing
    }
  }

  private writeLog(level: LogLevel, message: string): void {
    if (level === 'error') {
      console.error(message);
    } else if (level === 'warn') {
      console.warn(message);
    } else {
      console.log(message);
    }
  }

  /**
   * Force a message to be shown immediately
   */
  forceLog(message: string): void {
    this.log(message, 'info', true);
  }

  /**
   * Log important messages that should always be shown
   */
  important(message: string): void {
    this.log(message, 'info', true);
  }

  debug(message: string): void {
    this.log(message, 'debug');
  }

  warn(message: string): void {
    this.log(message, 'warn');
  }

  error(message: string): void {
    this.log(message, 'error');
  }

  setLevel(level: LogLevel): void {
    this.minLevel = this.normalizeLevel(level);
  }

  setRateLimitMs(rateLimitMs: number): void {
    if (Number.isFinite(rateLimitMs) && rateLimitMs >= 0) {
      this.rateLimitMs = rateLimitMs;
    }
  }

  setSummaryIntervalMs(summaryIntervalMs: number): void {
    if (Number.isFinite(summaryIntervalMs) && summaryIntervalMs >= 1000) {
      this.summaryIntervalMs = summaryIntervalMs;
      this.startSummaryLoop();
    }
  }

  getConfig(): { minLevel: LogLevel; rateLimitMs: number; summaryIntervalMs: number; verboseOverride: boolean | null } {
    return {
      minLevel: this.minLevel,
      rateLimitMs: this.rateLimitMs,
      summaryIntervalMs: this.summaryIntervalMs,
      verboseOverride: this.verboseOverride
    };
  }

  getVerboseMode(): boolean | null {
    return this.verboseOverride;
  }

  setVerboseMode(value: boolean | null) {
    if (value === null) {
      this.verboseOverride = null;
      return;
    }
    this.verboseOverride = Boolean(value);
  }

  /**
   * Extract a key from the message to group similar messages
   */
  private extractMessageKey(message: string): string {
    // Remove dynamic parts like timestamps, numbers, and variable data
    return message
      .replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z/g, '[TIMESTAMP]') // ISO timestamps
      .replace(/\d+(\.\d+)?\s*(points|MB|seconds|ms)/g, '[NUMBER]') // Numbers with units
      .replace(/\d+/g, '[NUM]') // Other numbers
      .replace(/:\s*\w+_\w+_\d+/g, ': [DYNAMIC_ID]') // Dynamic IDs
      .replace(/\([^)]*\)/g, '') // Remove parenthetical content
      .trim();
  }

  /**
   * Clean up old message entries to prevent memory leaks
   */
  private cleanupOldMessages(): void {
    const now = Date.now();
    const maxAge = 5 * 60 * 1000; // 5 minutes

    for (const [key, info] of this.messageMap.entries()) {
      if (now - info.lastSeen > maxAge) {
        this.messageMap.delete(key);
      }
    }
  }

  /**
   * Show summary messages for frequently repeated logs
   */
  private showSummaries(): void {
    if (!this.shouldLogLevel('info')) {
      return;
    }
    const now = Date.now();
    const summaries: string[] = [];

    for (const [key, info] of this.messageMap.entries()) {
      if (info.count >= 5) { // Show summary for messages repeated 5+ times
        const timeSinceFirst = now - info.firstSeen;
        const avgInterval = timeSinceFirst / info.count;

        if (key.includes('[QuantumEnhancement]') && key.includes('BREAKTHROUGH')) {
          summaries.push(`[QuantumEnhancement] 🌟 ${info.count} breakthroughs in last ${Math.round(timeSinceFirst/60000)}min (avg: ${Math.round(avgInterval/1000)}s apart)`);
        } else if (key.includes('[IntelligenceNexus]') && key.includes('amplified')) {
          summaries.push(`[IntelligenceNexus] 🚀 ${info.count} mind amplifications in last ${Math.round(timeSinceFirst/60000)}min`);
        } else if (key.includes('[Lattice]') && key.includes('expanded')) {
          summaries.push(`[Lattice] 🌐 ${info.count} expansions in last ${Math.round(timeSinceFirst/60000)}min`);
        }

        // Reset count after showing summary
        info.count = 0;
      }
    }

    // Show summaries
    summaries.forEach(summary => console.log(summary));
  }

  /**
   * Get statistics about logged messages
   */
  getStats(): { totalMessages: number, uniqueMessages: number, topMessages: Array<{key: string, count: number}> } {
    const entries = Array.from(this.messageMap.entries());
    const topMessages = entries
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, 10)
      .map(([key, info]) => ({ key, count: info.count }));

    return {
      totalMessages: entries.reduce((sum, [, info]) => sum + info.count, 0),
      uniqueMessages: entries.length,
      topMessages
    };
  }
}

// Create singleton instance
const smartLogger = new SmartLogger();

export { smartLogger };
