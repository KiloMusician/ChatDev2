import { z } from "zod";

// Resource schemas
export const ResourceTypeSchema = z.enum(["energy", "materials", "components", "research", "population"]);
export type ResourceType = z.infer<typeof ResourceTypeSchema>;

export const ResourceSchema = z.object({
  id: z.string(),
  type: ResourceTypeSchema,
  amount: z.number().min(0),
  capacity: z.number().min(0).optional(),
  rate: z.number().default(0), // per second
  multiplier: z.number().default(1),
});
export type Resource = z.infer<typeof ResourceSchema>;

// Structure schemas
export const StructureTypeSchema = z.enum(["generator", "storage", "converter", "turret", "wall", "research_lab"]);
export type StructureType = z.infer<typeof StructureTypeSchema>;

export const StructureSchema = z.object({
  id: z.string(),
  type: StructureTypeSchema,
  level: z.number().min(1).default(1),
  position: z.object({ x: z.number(), y: z.number() }),
  health: z.number().min(0),
  maxHealth: z.number().min(1),
  cost: z.record(ResourceTypeSchema, z.number()),
  production: z.record(ResourceTypeSchema, z.number()).optional(),
  range: z.number().min(0).default(0),
  damage: z.number().min(0).default(0),
  cooldown: z.number().min(0).default(1000), // milliseconds
  lastFired: z.number().default(0),
});
export type Structure = z.infer<typeof StructureSchema>;

// Enemy schemas
export const EnemyTypeSchema = z.enum(["scout", "warrior", "tank", "swarm", "boss"]);
export type EnemyType = z.infer<typeof EnemyTypeSchema>;

export const EnemySchema = z.object({
  id: z.string(),
  type: EnemyTypeSchema,
  position: z.object({ x: z.number(), y: z.number() }),
  target: z.object({ x: z.number(), y: z.number() }).optional(),
  health: z.number().min(0),
  maxHealth: z.number().min(1),
  speed: z.number().min(0),
  damage: z.number().min(0),
  reward: z.record(ResourceTypeSchema, z.number()),
  lastMove: z.number().default(0),
  path: z.array(z.object({ x: z.number(), y: z.number() })).default([]),
});
export type Enemy = z.infer<typeof EnemySchema>;

// Tier progression schemas
export const TierSchema = z.object({
  tier: z.number().min(1),
  name: z.string(),
  description: z.string(),
  requirements: z.record(ResourceTypeSchema, z.number()),
  unlocks: z.array(z.string()),
  bonuses: z.record(z.string(), z.number()).default({}),
});
export type Tier = z.infer<typeof TierSchema>;

// Wave schemas
export const WaveSchema = z.object({
  wave: z.number().min(1),
  tier: z.number().min(1),
  enemies: z.array(z.object({
    type: EnemyTypeSchema,
    count: z.number().min(1),
    spawn_delay: z.number().min(0), // seconds between spawns
  })),
  duration: z.number().min(1), // seconds
  rewards: z.record(ResourceTypeSchema, z.number()),
});
export type Wave = z.infer<typeof WaveSchema>;

// Game state schemas
export const GameStateSchema = z.object({
  version: z.string().default("1.0.0"),
  created: z.number(),
  lastSaved: z.number(),
  playTime: z.number().default(0), // milliseconds
  currentTier: z.number().min(1).default(1),
  currentWave: z.number().min(0).default(0),
  waveActive: z.boolean().default(false),
  waveStartTime: z.number().optional(),
  resources: z.record(ResourceTypeSchema, ResourceSchema),
  structures: z.array(StructureSchema).default([]),
  enemies: z.array(EnemySchema).default([]),
  unlockedStructures: z.array(StructureTypeSchema).default(["generator"]),
  achievements: z.array(z.string()).default([]),
  settings: z.object({
    autoSave: z.boolean().default(true),
    autoSaveInterval: z.number().default(30000), // 30 seconds
    soundEnabled: z.boolean().default(true),
    difficulty: z.enum(["easy", "normal", "hard"]).default("normal"),
  }).default({}),
});
export type GameState = z.infer<typeof GameStateSchema>;

// Receipt schemas for save/load
export const ReceiptSchema = z.object({
  id: z.string(),
  timestamp: z.number(),
  type: z.string(),
  data: z.record(z.any()),
  gameTime: z.number().optional(),
  wave: z.number().optional(),
});
export type Receipt = z.infer<typeof ReceiptSchema>;

export const SaveDataSchema = z.object({
  gameState: GameStateSchema,
  receipts: z.array(ReceiptSchema).default([]),
  metadata: z.object({
    saveId: z.string(),
    playerName: z.string().optional(),
    achievements: z.number().default(0),
    totalPlayTime: z.number().default(0),
    highestTier: z.number().default(1),
    totalWaves: z.number().default(0),
  }),
});
export type SaveData = z.infer<typeof SaveDataSchema>;