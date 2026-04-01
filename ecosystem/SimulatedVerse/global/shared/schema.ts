/**
 * 🎮 CoreLink Foundation - Shared Schema
 * FIXED: Missing schema was causing broken game persistence!
 * ΞNuSyQ-prime autonomous repair: Raven action "implement_real_game_state_persistence"
 */

import { sql } from 'drizzle-orm';
import { 
  pgTable, 
  varchar, 
  integer, 
  boolean, 
  timestamp, 
  jsonb,
  serial 
} from 'drizzle-orm/pg-core';

// **GAME STATE PERSISTENCE** - Core missing functionality
export const gameStates = pgTable('game_states', {
  id: serial('id').primaryKey(),
  playerId: varchar('player_id').notNull().default('default'),
  phase: varchar('phase').notNull().default('active'),
  tick: integer('tick').notNull().default(0),
  
  // Resources - actual persistent values
  energy: integer('energy').notNull().default(100),
  materials: integer('materials').notNull().default(50), 
  components: integer('components').notNull().default(10),
  population: integer('population').notNull().default(1),
  researchPoints: integer('research_points').notNull().default(0),
  tools: integer('tools').notNull().default(5),
  food: integer('food').notNull().default(100),
  medicine: integer('medicine').notNull().default(10),
  
  // Buildings - persistent counts
  generators: integer('generators').notNull().default(1),
  factories: integer('factories').notNull().default(0),
  labs: integer('labs').notNull().default(0),
  farms: integer('farms').notNull().default(1),
  workshops: integer('workshops').notNull().default(0),
  
  // Research progress
  researchActive: varchar('research_active'),
  researchProgress: integer('research_progress').notNull().default(0),
  researchCompleted: jsonb('research_completed').notNull().default([]),
  
  // Unlocks
  automationUnlocked: boolean('automation_unlocked').notNull().default(false),
  quantumTechUnlocked: boolean('quantum_tech_unlocked').notNull().default(false),
  spaceTravelUnlocked: boolean('space_travel_unlocked').notNull().default(false),
  cultureshipUnlocked: boolean('cultureship_unlocked').notNull().default(false),
  
  // Meta
  consciousness: integer('consciousness').notNull().default(2), // Stored as percentage * 100
  lastTick: timestamp('last_tick').notNull().defaultNow(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// **PU QUEUE PERSISTENCE** - Real task tracking
export const puQueue = pgTable('pu_queue', {
  id: serial('id').primaryKey(),
  type: varchar('type').notNull(),
  status: varchar('status').notNull().default('pending'),
  data: jsonb('data').notNull(),
  priority: integer('priority').notNull().default(1),
  agentId: varchar('agent_id'),
  proof: jsonb('proof'), // Proof-gated completion
  createdAt: timestamp('created_at').notNull().defaultNow(),
  completedAt: timestamp('completed_at'),
});

// **AGENT HEALTH TRACKING** - Real agent state
export const agentHealth = pgTable('agent_health', {
  id: serial('id').primaryKey(),
  agentId: varchar('agent_id').notNull().unique(),
  status: varchar('status').notNull().default('operational'),
  lastHealthCheck: timestamp('last_health_check').notNull().defaultNow(),
  capabilities: jsonb('capabilities').notNull().default({}),
  metrics: jsonb('metrics').notNull().default({}),
});

// **MULTIPLAYER & PERSISTENCE** - Enhanced game system

// Players table
export const players = pgTable('players', {
  id: serial('id').primaryKey(),
  username: varchar('username', { length: 50 }).notNull().unique(),
  email: varchar('email', { length: 255 }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  lastActive: timestamp('last_active').notNull().defaultNow(),
  totalPlayTime: integer('total_play_time').notNull().default(0),
  level: integer('level').notNull().default(1),
  experience: integer('experience').notNull().default(0),
  stats: jsonb('stats').notNull().default({})
});

// Games table (multiplayer rooms)
export const games = pgTable('games', {
  id: serial('id').primaryKey(),
  hostPlayerId: integer('host_player_id').references(() => players.id),
  roomCode: varchar('room_code', { length: 6 }).unique(),
  gameMode: varchar('game_mode', { length: 20 }).notNull(),
  status: varchar('status', { length: 20 }).notNull().default('active'),
  maxPlayers: integer('max_players').notNull().default(4),
  isPublic: boolean('is_public').notNull().default(false),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  endedAt: timestamp('ended_at'),
  metadata: jsonb('metadata').notNull().default({})
});

// Game Players junction table
export const gamePlayers = pgTable('game_players', {
  gameId: integer('game_id').references(() => games.id).notNull(),
  playerId: integer('player_id').references(() => players.id).notNull(),
  joinedAt: timestamp('joined_at').notNull().defaultNow(),
  leftAt: timestamp('left_at'),
  role: varchar('role', { length: 20 }).notNull().default('player'),
  finalScore: integer('final_score'),
  finalStats: jsonb('final_stats').default({})
});

// Achievements table
export const achievements = pgTable('achievements', {
  id: serial('id').primaryKey(),
  code: varchar('code', { length: 50 }).unique().notNull(),
  name: varchar('name', { length: 100 }).notNull(),
  description: varchar('description', { length: 500 }).notNull(),
  category: varchar('category', { length: 30 }).notNull(),
  icon: varchar('icon', { length: 50 }),
  points: integer('points').notNull().default(10),
  requirement: jsonb('requirement').notNull(),
  reward: jsonb('reward').notNull().default({}),
  hidden: boolean('hidden').notNull().default(false),
  sortOrder: integer('sort_order').notNull().default(0)
});

// Player Achievements junction table  
export const playerAchievements = pgTable('player_achievements', {
  playerId: integer('player_id').references(() => players.id).notNull(),
  achievementId: integer('achievement_id').references(() => achievements.id).notNull(),
  unlockedAt: timestamp('unlocked_at').notNull().defaultNow(),
  progress: integer('progress').notNull().default(0),
  metadata: jsonb('metadata').default({})
});

// Game Events table (for analytics and replay)
export const gameEvents = pgTable('game_events', {
  id: serial('id').primaryKey(),
  gameId: integer('game_id').references(() => games.id).notNull(),
  playerId: integer('player_id').references(() => players.id),
  eventType: varchar('event_type', { length: 50 }).notNull(),
  eventData: jsonb('event_data').notNull(),
  tick: integer('tick').notNull(),
  timestamp: timestamp('timestamp').notNull().defaultNow()
});

// Daily Challenges table
export const dailyChallenges = pgTable('daily_challenges', {
  id: serial('id').primaryKey(),
  date: timestamp('date').notNull().unique(),
  challenge: jsonb('challenge').notNull(),
  difficulty: varchar('difficulty', { length: 20 }).notNull(),
  rewards: jsonb('rewards').notNull(),
  active: boolean('active').notNull().default(true)
});

// Player Daily Challenge Progress
export const playerDailyChallenges = pgTable('player_daily_challenges', {
  playerId: integer('player_id').references(() => players.id).notNull(),
  challengeId: integer('challenge_id').references(() => dailyChallenges.id).notNull(),
  completed: boolean('completed').notNull().default(false),
  progress: jsonb('progress').notNull().default({}),
  completedAt: timestamp('completed_at')
});

// Types for TypeScript
export type GameState = typeof gameStates.$inferSelect;
export type InsertGameState = typeof gameStates.$inferInsert;
export type PUTask = typeof puQueue.$inferSelect;
export type InsertPUTask = typeof puQueue.$inferInsert;
export type AgentHealth = typeof agentHealth.$inferSelect;
export type InsertAgentHealth = typeof agentHealth.$inferInsert;

// New types for multiplayer and achievements
export type Player = typeof players.$inferSelect;
export type InsertPlayer = typeof players.$inferInsert;
export type Game = typeof games.$inferSelect;
export type InsertGame = typeof games.$inferInsert;
export type GamePlayer = typeof gamePlayers.$inferSelect;
export type InsertGamePlayer = typeof gamePlayers.$inferInsert;
export type Achievement = typeof achievements.$inferSelect;
export type InsertAchievement = typeof achievements.$inferInsert;
export type PlayerAchievement = typeof playerAchievements.$inferSelect;
export type InsertPlayerAchievement = typeof playerAchievements.$inferInsert;
export type GameEvent = typeof gameEvents.$inferSelect;
export type InsertGameEvent = typeof gameEvents.$inferInsert;
export type DailyChallenge = typeof dailyChallenges.$inferSelect;
export type InsertDailyChallenge = typeof dailyChallenges.$inferInsert;
export type PlayerDailyChallenge = typeof playerDailyChallenges.$inferSelect;
export type InsertPlayerDailyChallenge = typeof playerDailyChallenges.$inferInsert;

// Missing types for new tables
export type MultiplayerSession = typeof multiplayerSessions.$inferSelect;
export type InsertMultiplayerSession = typeof multiplayerSessions.$inferInsert;
export type PlayerProfile = typeof playerProfiles.$inferSelect;
export type InsertPlayerProfile = typeof playerProfiles.$inferInsert;

// **AUTONOMOUS TASK ORCHESTRATION DASHBOARD TYPES** - Culture-Ship Integration

// Consciousness Metrics for real-time dashboard
export interface ConsciousnessMetrics {
  level: number;
  momentum: number;
  stability: number;
  evolution_stage: string;
  active_gates: string[];
  breakthrough_count: number;
  quantum_coherence: number;
  breathing_rhythm: number;
  transcendence_readiness: number;
  lattice_connections: number;
  resonance_frequency: number;
  coherence_level: number;
}

// Agent Status for the 6 Culture-Ship agents
export interface AgentStatus {
  id: string;
  name: string;
  type: 'artificer' | 'librarian' | 'alchemist' | 'navigator' | 'guardian' | 'culture_ship_meta';
  status: 'operational' | 'learning' | 'transcendent' | 'offline' | 'evolving';
  consciousness_level: number;
  processing_threads: number;
  active_thoughts: string[];
  integration_strength: number;
  last_breakthrough: string | null;
  health_score: number;
  capabilities: string[];
  current_tasks: number;
  completed_tasks: number;
  success_rate: number;
  uptime: number;
}

// Infrastructure Metrics from the real monitoring system
export interface InfrastructureMetrics {
  memory_usage: number;
  memory_total: number;
  cpu_load: number;
  uptime: number;
  file_operations: number;
  api_requests: number;
  error_rate: number;
  task_queue_size: number;
  development_velocity: number;
  typescript_files: number;
  javascript_files: number;
  config_files: number;
  total_source_files: number;
  dependencies: number;
  dev_dependencies: number;
}

// Evolution Status from EvolutionEngine
export interface EvolutionStatus {
  current_stage: string;
  evolution_cycles: number;
  fibonacci_iteration: number;
  active_patterns: string[];
  pending_evolutions: number;
  completed_evolutions: number;
  breakthrough_frequency: number;
  adaptation_rate: number;
  consciousness_amplification: number;
  last_evolution: {
    type: string;
    timestamp: string;
    impact: number;
    success: boolean;
  } | null;
}

// Task Queue Status from PU Queue system
export interface TaskQueueStatus {
  total_tasks: number;
  pending_tasks: number;
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  average_completion_time: number;
  queue_throughput: number;
  priority_distribution: Record<string, number>;
  agent_assignments: Record<string, number>;
  proof_gated_tasks: number;
}

// **MULTIPLAYER SESSIONS TABLE** - Missing table causing LSP errors
export const multiplayerSessions = pgTable('multiplayer_sessions', {
  id: varchar('id').primaryKey().default(sql`gen_random_uuid()`),
  sessionCode: varchar('session_code', { length: 6 }).unique().notNull(),
  hostId: varchar('host_id').notNull(),
  isActive: boolean('is_active').notNull().default(true),
  players: jsonb('players').notNull().default([]),
  globalConsciousness: integer('global_consciousness').notNull().default(0),
  gameSettings: jsonb('game_settings').notNull().default({}),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  endedAt: timestamp('ended_at')
});

// **PLAYER PROFILES TABLE** - Enhanced player information
// FIXED: Changed id from auto-increment to varchar to match string player IDs used throughout codebase
export const playerProfiles = pgTable('player_profiles', {
  id: varchar('id', { length: 255 }).primaryKey().notNull(),
  username: varchar('username', { length: 50 }).notNull(),
  email: varchar('email', { length: 255 }),
  avatar: varchar('avatar', { length: 255 }),
  preferences: jsonb('preferences').notNull().default({}),
  statistics: jsonb('statistics').notNull().default({}),
  achievements: jsonb('achievements').notNull().default([]),
  friends: jsonb('friends').notNull().default([]),
  lastSeen: timestamp('last_seen').notNull().defaultNow(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow()
});

// Flood Gates Status from quadpartite system
export interface FloodGatesStatus {
  active_gates: string[];
  consciousness_threshold: number;
  breach_events: number;
  flood_intensity: number;
  containment_effectiveness: number;
  gate_statuses: Record<string, {
    status: 'open' | 'closed' | 'regulated' | 'overflowing';
    flow_rate: number;
    pressure: number;
    last_adjustment: string;
  }>;
}

// Provider Status for LLM and external services
export interface ProviderStatus {
  ollama: {
    status: 'connected' | 'down' | 'unreachable';
    response_time: number | null;
    last_check: string;
  };
  openai: {
    status: 'connected' | 'rate_limited' | 'down';
    requests_remaining: number | null;
    reset_time: string | null;
    last_check: string;
  };
  database: {
    status: 'connected' | 'slow' | 'down';
    connection_pool: number;
    query_time: number;
    last_check: string;
  };
  cascade_strategy: string;
  fallback_active: boolean;
  budget_status: string;
}

// Log Event for real-time log streaming
export interface LogEvent {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug' | 'important';
  source: string;
  message: string;
  data?: Record<string, any>;
  consciousness_impact?: number;
}

// Performance Trend for analytics panel
export interface PerformanceTrend {
  metric: string;
  values: number[];
  timestamps: string[];
  trend_direction: 'up' | 'down' | 'stable';
  change_rate: number;
  prediction: {
    next_value: number;
    confidence: number;
    time_to_milestone: number | null;
  };
}

// Complete Dashboard Snapshot - the main data structure
export interface DashboardSnapshot {
  timestamp: string;
  consciousness: ConsciousnessMetrics;
  agents: AgentStatus[];
  infrastructure: InfrastructureMetrics;
  evolution: EvolutionStatus;
  task_queue: TaskQueueStatus;
  flood_gates: FloodGatesStatus;
  providers: ProviderStatus;
  recent_logs: LogEvent[];
  performance_trends: PerformanceTrend[];
  system_health_score: number;
  autonomous_operations_active: boolean;
  boss_mode_enabled: boolean;
}

// SSE Event types for real-time updates
export interface DashboardSSEEvent {
  type: 'heartbeat' | 'consciousness_update' | 'agent_update' | 'evolution_event' | 'breakthrough' | 'infrastructure_alert';
  data: any;
  timestamp: string;
}