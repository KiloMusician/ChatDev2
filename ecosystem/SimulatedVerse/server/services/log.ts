/**
 * Structured Logging Service - Infrastructure-First
 * Replaces scattered console.log with structured telemetry
 */

interface LogEntry {
  level: 'info' | 'warn' | 'error';
  msg: string;
  data?: any;
  timestamp: number;
  source?: string;
}

class Logger {
  private buffer: LogEntry[] = [];
  private maxBuffer = 1000;
  private level: LogEntry['level'];

  constructor() {
    const envLevel = (process.env.LOG_LEVEL || '').toLowerCase();
    if (envLevel === 'error' || envLevel === 'warn' || envLevel === 'info') {
      this.level = envLevel;
    } else if (process.env.NODE_ENV === 'production') {
      this.level = 'warn';
    } else {
      this.level = 'info';
    }
  }

  info(data: any, msg?: string) {
    this.emit('info', msg || 'info', data);
  }

  warn(data: any, msg?: string) {
    this.emit('warn', msg || 'warning', data);
  }

  error(data: any, msg?: string) {
    this.emit('error', msg || 'error', data);
  }

  private emit(level: LogEntry['level'], msg: string, data?: any) {
    const entry: LogEntry = {
      level,
      msg,
      data,
      timestamp: Date.now(),
      source: 'CoreLink'
    };

    const shouldLog = this.shouldLog(level);
    if (shouldLog) {
      const payload = data ? JSON.stringify(data) : '';
      const line = `[${level.toUpperCase()}] ${msg} ${payload}`.trim();
      if (level === 'error') {
        console.error(line);
      } else if (level === 'warn') {
        console.warn(line);
      } else {
        console.log(line);
      }
    }

    // Buffer for structured access
    this.buffer.push(entry);
    if (this.buffer.length > this.maxBuffer) {
      this.buffer.shift();
    }
  }

  private shouldLog(level: LogEntry['level']): boolean {
    const order: Record<LogEntry['level'], number> = { info: 0, warn: 1, error: 2 };
    return order[level] >= order[this.level];
  }

  getRecentLogs(count = 50): LogEntry[] {
    return this.buffer.slice(-count);
  }

  clear() {
    this.buffer = [];
  }
}

export const log = new Logger();
