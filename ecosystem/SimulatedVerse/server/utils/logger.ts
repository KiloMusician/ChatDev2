// server/utils/logger.ts
// Lightweight structured logger for SimulatedVerse server.
// Wraps console.* so callers don't trigger the no-console ESLint rule,
// and provides a uniform prefix/level API for future log-sink integration.

export type LogLevel = "debug" | "info" | "warn" | "error";

const LEVELS: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3 };
const MIN_LEVEL: LogLevel = (process.env.LOG_LEVEL as LogLevel) || "info";

function shouldLog(level: LogLevel): boolean {
  return LEVELS[level] >= LEVELS[MIN_LEVEL];
}

function fmt(level: string, ns: string, msg: string): string {
  return `[${level.toUpperCase()}][${ns}] ${msg}`;
}

export function makeLogger(namespace: string) {
  return {
    debug: (msg: string, ...args: unknown[]) => {
      if (shouldLog("debug")) console.debug(fmt("debug", namespace, msg), ...args);  // eslint-disable-line no-console
    },
    info: (msg: string, ...args: unknown[]) => {
      if (shouldLog("info"))  console.info(fmt("info",  namespace, msg), ...args);   // eslint-disable-line no-console
    },
    warn: (msg: string, ...args: unknown[]) => {
      if (shouldLog("warn"))  console.warn(fmt("warn",  namespace, msg), ...args);   // eslint-disable-line no-console
    },
    error: (msg: string, ...args: unknown[]) => {
      if (shouldLog("error")) console.error(fmt("error", namespace, msg), ...args);  // eslint-disable-line no-console
    },
    /** Legacy shim — routes bare console.log calls through info. */
    log: (msg: string, ...args: unknown[]) => {
      if (shouldLog("info"))  console.info(fmt("info",  namespace, msg), ...args);   // eslint-disable-line no-console
    },
  };
}

/** Root logger (no namespace). Use makeLogger('my-service') in services. */
export const logger = makeLogger("sv");
