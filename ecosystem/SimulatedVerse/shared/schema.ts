// shared/schema.ts
import { z } from "zod";
import { pgTable, serial, text, integer, timestamp, jsonb, varchar, boolean, index } from 'drizzle-orm/pg-core';

// ==================================================================
// DRIZZLE TABLE DEFINITIONS (Actual Database Schema)
// ==================================================================

// 1. Game Events Table - Tracks all in-game events
export const gameEvents = pgTable(
  'game_events',
  {
    id: serial('id').primaryKey(),
    gameId: varchar('game_id', { length: 255 }).notNull(),
    playerId: varchar('player_id', { length: 255 }),
    eventType: varchar('event_type', { length: 100 }).notNull(),
    eventData: jsonb('event_data').notNull(),
    tick: integer('tick').notNull().default(0),
    timestamp: timestamp('timestamp').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for gameEvents
    gameEventsGameIdIdx: index('game_id_idx').on(table.gameId),
    gameEventsPlayerIdIdx: index('player_id_idx').on(table.playerId),
    gameEventsEventTypeIdx: index('event_type_idx').on(table.eventType),
  }),
);

// 2. Game States Table - Stores current game state snapshots
export const gameStates = pgTable(
  'game_states',
  {
    id: serial('id').primaryKey(),
    playerId: varchar('player_id', { length: 255 }).notNull(),
    phase: varchar('phase', { length: 50 }).notNull().default('active'),
    tick: integer('tick').notNull().default(0),
    
    // Resources
    energy: integer('energy').notNull().default(100),
    materials: integer('materials').notNull().default(50),
    components: integer('components').notNull().default(10),
    population: integer('population').notNull().default(1),
    researchPoints: integer('research_points').notNull().default(0),
    tools: integer('tools').notNull().default(5),
    food: integer('food').notNull().default(100),
    medicine: integer('medicine').notNull().default(10),
    
    // Structures
    generators: integer('generators').notNull().default(1),
    factories: integer('factories').notNull().default(0),
    labs: integer('labs').notNull().default(0),
    research_labs: integer('research_labs').notNull().default(0),
    housing: integer('housing').notNull().default(1),
    farms: integer('farms').notNull().default(0),
    hospitals: integer('hospitals').notNull().default(0),
    workshops: integer('workshops').notNull().default(0),

    // Research state
    researchCompleted: jsonb('research_completed').notNull().default('[]'),
    researchActive: varchar('research_active', { length: 255 }),
    researchProgress: integer('research_progress').notNull().default(0),

    // Unlock flags
    automationUnlocked: boolean('automation_unlocked').notNull().default(false),
    quantumTechUnlocked: boolean('quantum_tech_unlocked').notNull().default(false),
    spaceTravelUnlocked: boolean('space_travel_unlocked').notNull().default(false),
    cultureshipUnlocked: boolean('cultureship_unlocked').notNull().default(false),

    // Consciousness (integer 0-100; divide by 100 for float)
    consciousness: integer('consciousness').notNull().default(0),

    // Achievements & Settings
    achievements: jsonb('achievements').notNull().default('[]'),
    gameSettings: jsonb('game_settings').notNull().default('{}'),
    
    // Timestamps
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for gameStates
    gameStatesPlayerIdIdx: index('game_state_player_id_idx').on(table.playerId),
    gameStatesUpdatedAtIdx: index('game_state_updated_at_idx').on(table.updatedAt),
  }),
);

// 3. Players Table (Legacy - Integer IDs)
export const players = pgTable(
  'players',
  {
    id: serial('id').primaryKey(),
    name: varchar('name', { length: 255 }).notNull(),
    level: integer('level').notNull().default(1),
    experience: integer('experience').notNull().default(0),
    inventory: jsonb('inventory').notNull().default('[]'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => ({
    // Index for players
    playersNameIdx: index('player_name_idx').on(table.name),
  }),
);

// 4. Games Table - Tracks individual game sessions
export const games = pgTable(
  'games',
  {
    id: serial('id').primaryKey(),
    name: varchar('name', { length: 255 }).notNull(),
    hostPlayerId: varchar('host_player_id', { length: 255 }).notNull(),
    gameMode: varchar('game_mode', { length: 50 }).notNull().default('single'),
    isActive: boolean('is_active').notNull().default(true),
    maxPlayers: integer('max_players').notNull().default(1),
    currentPlayers: integer('current_players').notNull().default(1),
    gameState: jsonb('game_state').notNull().default('{}'),
    settings: jsonb('settings').notNull().default('{}'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for games
    gamesHostIdx: index('game_host_idx').on(table.hostPlayerId),
    gamesActiveIdx: index('game_active_idx').on(table.isActive),
  }),
);

// 5. Multiplayer Sessions Table - Tracks multiplayer game sessions
export const multiplayerSessions = pgTable(
  'multiplayer_sessions',
  {
    id: serial('id').primaryKey(),
    sessionId: varchar('session_id', { length: 255 }).notNull().unique(),
    gameId: integer('game_id').notNull().references(() => games.id),
    playerIds: jsonb('player_ids').notNull().default('[]'),
    sessionState: varchar('session_state', { length: 50 }).notNull().default('waiting'),
    hostId: varchar('host_id', { length: 255 }).notNull(),
    maxPlayers: integer('max_players').notNull().default(4),
    currentTick: integer('current_tick').notNull().default(0),
    sessionData: jsonb('session_data').notNull().default('{}'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for multiplayerSessions
    multiplayerSessionsSessionIdIdx: index('session_id_idx').on(table.sessionId),
    multiplayerSessionsGameIdIdx: index('multiplayer_game_id_idx').on(table.gameId),
    multiplayerSessionsStateIdx: index('session_state_idx').on(table.sessionState),
  }),
);

// ==================================================================
// DASHBOARD & ORCHESTRATION TYPES (re-exported from global shared schema)
// ==================================================================
export type {
  ConsciousnessMetrics,
  AgentStatus,
  InfrastructureMetrics,
  EvolutionStatus,
  TaskQueueStatus,
  FloodGatesStatus,
  ProviderStatus,
  LogEvent,
  PerformanceTrend,
  DashboardSnapshot,
  DashboardSSEEvent
} from "../global/shared/schema";

// 6. Player Profiles Table (String IDs - Modern)
export const playerProfiles = pgTable(
  'player_profiles',
  {
    id: varchar('id', { length: 255 }).primaryKey(),
    username: varchar('username', { length: 255 }).notNull().unique(),
    displayName: varchar('display_name', { length: 255 }).notNull(),
    email: varchar('email', { length: 255 }),
    level: integer('level').notNull().default(1),
    experience: integer('experience').notNull().default(0),
    totalGamesPlayed: integer('total_games_played').notNull().default(0),
    achievements: jsonb('achievements').notNull().default('[]'),
    preferences: jsonb('preferences').notNull().default('{}'),
    stats: jsonb('stats').notNull().default('{}'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    lastActive: timestamp('last_active').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for playerProfiles
    playerProfilesUsernameIdx: index('profile_username_idx').on(table.username),
    playerProfilesEmailIdx: index('profile_email_idx').on(table.email),
    playerProfilesLastActiveIdx: index('profile_last_active_idx').on(table.lastActive),
  }),
);

// 7. PU Queue Table - Autonomous task queue for agents
export const puQueue = pgTable(
  'pu_queue',
  {
    id: serial('id').primaryKey(),
    puId: varchar('pu_id', { length: 255 }).notNull().unique(),
    priority: integer('priority').notNull().default(5),
    status: varchar('status', { length: 50 }).notNull().default('pending'),
    taskType: varchar('task_type', { length: 100 }).notNull(),
    taskData: jsonb('task_data').notNull().default('{}'),
    assignedAgent: varchar('assigned_agent', { length: 100 }),
    result: jsonb('result'),
    errorMessage: text('error_message'),
    retryCount: integer('retry_count').notNull().default(0),
    maxRetries: integer('max_retries').notNull().default(3),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    startedAt: timestamp('started_at'),
    completedAt: timestamp('completed_at'),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for puQueue
    puQueuePuIdIdx: index('pu_id_idx').on(table.puId),
    puQueueStatusIdx: index('pu_status_idx').on(table.status),
    puQueuePriorityIdx: index('pu_priority_idx').on(table.priority),
    puQueueAssignedAgentIdx: index('pu_assigned_agent_idx').on(table.assignedAgent),
  }),
);

// 8. Agent Health Table - Tracks health and status of autonomous agents
export const agentHealth = pgTable(
  'agent_health',
  {
    id: serial('id').primaryKey(),
    agentId: varchar('agent_id', { length: 100 }).notNull().unique(),
    agentType: varchar('agent_type', { length: 50 }).notNull(),
    status: varchar('status', { length: 50 }).notNull().default('healthy'),
    health: integer('health').notNull().default(100),
    lastHeartbeat: timestamp('last_heartbeat').defaultNow().notNull(),
    errorCount: integer('error_count').notNull().default(0),
    successCount: integer('success_count').notNull().default(0),
    currentTask: varchar('current_task', { length: 255 }),
    metrics: jsonb('metrics').notNull().default('{}'),
    logs: jsonb('logs').notNull().default('[]'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => ({
    // Indexes for agentHealth
    agentHealthAgentIdIdx: index('agent_id_idx').on(table.agentId),
    agentHealthStatusIdx: index('agent_status_idx').on(table.status),
    agentHealthLastHeartbeatIdx: index('agent_last_heartbeat_idx').on(table.lastHeartbeat),
  }),
);

// ==================================================================
// ZOD VALIDATION SCHEMAS (Runtime Type Checking)
// ==================================================================

// Core schema definitions for SimulatedVerse persistence
export const GameStateSchema = z.object({
  id: z.string(),
  name: z.string(),
  state: z.record(z.any()),
  created_at: z.date().optional(),
  updated_at: z.date().optional(),
});

export const PlayerSchema = z.object({
  id: z.string(),
  name: z.string(),
  level: z.number().default(1),
  experience: z.number().default(0),
  inventory: z.array(z.any()).default([]),
});

export const SessionSchema = z.object({
  id: z.string(),
  player_id: z.string(),
  game_state: GameStateSchema,
  timestamp: z.date(),
});

// Consciousness-related schemas
export const ConsciousnessEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.record(z.any()),
  timestamp: z.date(),
});

export const AgentMemorySchema = z.object({
  agent_id: z.string(),
  memory_type: z.enum(['short_term', 'long_term', 'episodic']),
  content: z.string(),
  importance: z.number().min(0).max(1),
  created_at: z.date(),
});

// Export all schemas
export const Schema = {
  GameState: GameStateSchema,
  Player: PlayerSchema,
  Session: SessionSchema,
  ConsciousnessEvent: ConsciousnessEventSchema,
  AgentMemory: AgentMemorySchema,
};

export default Schema;

// ==================================================================
// TYPESCRIPT TYPES (Inferred from Drizzle Tables)
// ==================================================================

export type GameEvent = typeof gameEvents.$inferSelect;
export type NewGameEvent = typeof gameEvents.$inferInsert;

export type GameState = typeof gameStates.$inferSelect;
export type NewGameState = typeof gameStates.$inferInsert;

export type Player = typeof players.$inferSelect;
export type NewPlayer = typeof players.$inferInsert;

export type Game = typeof games.$inferSelect;
export type NewGame = typeof games.$inferInsert;

export type MultiplayerSession = typeof multiplayerSessions.$inferSelect;
export type NewMultiplayerSession = typeof multiplayerSessions.$inferInsert;

export type PlayerProfile = typeof playerProfiles.$inferSelect;
export type NewPlayerProfile = typeof playerProfiles.$inferInsert;

export type PUQueueItem = typeof puQueue.$inferSelect;
export type NewPUQueueItem = typeof puQueue.$inferInsert;

export type AgentHealth = typeof agentHealth.$inferSelect;
export type NewAgentHealth = typeof agentHealth.$inferInsert;
