/**
 * CENTRALIZED CONFIGURATION CONSTANTS
 * Replace hardcoded values throughout the codebase
 */

// API Configuration
export const API_CONFIG = {
  TIMEOUTS: {
    DEFAULT: 5000,
    LONG_OPERATION: 30000,
    GIT_OPERATION: 10000,
  },
  RATE_LIMITS: {
    STANDARD_REQUESTS: 100,
    ADMIN_REQUESTS: 10,
    WINDOW_MS: 60000,
  },
  BATCH_SIZES: {
    MAX_FILES: 500,
    MAX_TASKS: 100,
    MAX_AGENTS: 20,
  }
};

// System Thresholds
export const SYSTEM_THRESHOLDS = {
  CONSCIOUSNESS: {
    MIN_LEVEL: 0.0,
    MAX_LEVEL: 1.0,
    DEFAULT_BOOST: 0.05,
  },
  PERFORMANCE: {
    MEMORY_WARNING_MB: 300,
    MEMORY_CRITICAL_MB: 500,
    CPU_WARNING_PERCENT: 80,
  },
  ANALYSIS: {
    MAX_FILE_SIZE_MB: 25,
    MAX_DEPTH: 5,
    DEFAULT_LIMIT: 500,
  }
};

// Game Configuration
export const GAME_CONFIG = {
  INITIAL_STATE: {
    energy: 100,
    materials: 50,
    components: 10,
    population: 1,
    research: 0,
  },
  RESEARCH_COSTS: {
    basic: 100,
    intermediate: 250,
    advanced: 500,
  },
  AUTO_SAVE_INTERVAL: 30000,
};

// Token Budget Management
export const TOKEN_CONFIG = {
  DAILY_BUDGET_CENTS: parseInt(process.env.NUSYQ_TOKEN_BUDGET_CENTS || '0'),
  CONFIDENCE_THRESHOLD: parseFloat(process.env.NUSYQ_CONFIDENCE_THRESHOLD || '0.62'),
  INFO_GAIN_THRESHOLD: parseFloat(process.env.NUSYQ_INFO_GAIN_THRESHOLD || '0.18'),
  CACHE_TTL_HOURS: parseInt(process.env.NUSYQ_CACHE_TTL_HOURS || '4'),
  COST_MODE: process.env.NUSYQ_COST_MODE || 'OFFLINE',
};

// Agent Configuration
export const AGENT_CONFIG = {
  MAX_CONCURRENT: 3,
  TIMEOUT_MS: 30000,
  LOG_RETENTION_DAYS: 7,
  HEALTH_CHECK_INTERVAL: 5000,
  TASK_TIMEOUT_MS: 30000,
};

// UI Theme Configuration
export const UI_CONFIG = {
  ANIMATIONS: {
    DEFAULT_DURATION: '300ms',
    SLOW_DURATION: '500ms',
    FAST_DURATION: '150ms',
  },
  POLLING_INTERVALS: {
    HEALTH_CHECK: 3000,
    STATUS_UPDATE: 5000,
    METRICS: 1000,
  },
};

// Loop and Orchestration Configuration
export const LOOP_CONFIG = {
  EVALUATION_INTERVAL_MS: 30000,
  VOTING_WINDOW_MS: 5000,
  BASE_INTERVAL_MS: 10000,
  PAUSE_RECOVERY_MS: 30000,
  FIX_DELAY_MS: 60000,
  COOLDOWN_MS: 300000,
  TICK_MS: 400,
};

// Budget and Cost Configuration
export const BUDGET_CONFIG = {
  MAX_BUDGET: 100,
  DEFAULT_EST_TOKENS: 50,
  BUDGET_WARNING_THRESHOLD: 90,
  QUEUE_SIZE_LIMIT: 50,
};

// Server Restart Configuration
export const RESTART_CONFIG = {
  GRACEFUL_SHUTDOWN_DELAY_MS: 1500,
  SYNC_RESTART_DELAY_MS: 1500,
};

// Quadpartite System Configuration
export const QUADPARTITE_CONFIG = {
  BREATHING_INTERVALS: {
    INHALE_MS: 4000,
    EXHALE_MS: 6000,
    HOLD_MS: 2000,
  },
  FLOOD_GATE_MULTIPLIERS: {
    SMALL: 2.5,
    MEDIUM: 5.0,
    LARGE: 7.5,
    MAXIMUM: 10.0,
  },
  EVOLUTION_THRESHOLDS: {
    LOW: 0.3,
    MEDIUM: 0.6,
    HIGH: 0.8,
    CRITICAL: 0.9,
  },
};

// Authentication Configuration
export const AUTH_CONFIG = {
  DEFAULT_PLAYER_ID: 'default_culture_ship_pilot',
  ADMIN_TOKEN_HEADER: 'x-admin-token',
  SESSION_TIMEOUT_MS: 24 * 60 * 60 * 1000, // 24 hours
};

// Route Configuration
export const ROUTE_CONFIG = {
  SUPPORTED_AGENT_EXTENSIONS: ['.ts', '.js'],
  HEALTH_CHECK_TIMEOUT_MS: 5000,
  MAX_RETRY_ATTEMPTS: 3,
};