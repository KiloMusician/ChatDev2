// server/db.ts — Database connection (node-postgres + Drizzle ORM)
// Uses standard pg driver — works with local PostgreSQL and any standard PG provider.
// Replaces @neondatabase/serverless (WebSocket driver) which only works with Neon Cloud.
// Gracefully degrades to null when DATABASE_URL is missing/unreachable.
import { drizzle } from 'drizzle-orm/node-postgres';
import pg from 'pg';
import * as schema from "@shared/schema";

const { Pool } = pg;

let _pool: pg.Pool | null = null;
let _db: ReturnType<typeof drizzle<typeof schema>> | null = null;

if (process.env.DATABASE_URL) {
  try {
    _pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      // Short connect timeout so server startup isn't blocked if PG is down
      connectionTimeoutMillis: 3000,
      max: 10,
    });

    // Non-blocking health check — log but don't crash on failure
    _pool.connect().then(client => {
      client.release();
      console.info('[db] ✅ PostgreSQL connected');
    }).catch(err => {
      console.warn('[db] ⚠️  PostgreSQL unavailable — running memory-only:', err.message);
    });

    _db = drizzle(_pool, { schema });
  } catch (err) {
    console.warn('[db] ⚠️  Failed to initialise PostgreSQL pool:', (err as Error).message);
  }
} else {
  console.warn('[db] DATABASE_URL not set — running memory-only (no persistence)');
}

export const pool = _pool;
export const db = _db;
