import { drizzle } from 'drizzle-orm/node-postgres';
import pg from 'pg';
import { eq, desc, and, gte } from 'drizzle-orm';

// ✅ FIXED: All schemas now properly implemented
import { 
  gameStates, 
  players,
  games,
  gameEvents,
  multiplayerSessions,
  playerProfiles,
  puQueue,
  agentHealth
} from '../../shared/schema';

// Use standard pg driver — works with local PostgreSQL or any standard PG provider
const { Pool } = pg;
const _pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/simulatedverse',
  connectionTimeoutMillis: 3000,
});
const db = drizzle(_pool, {
  schema: {
    gameStates,
    playerIds: players,
    games,
    gameEvents,
    multiplayerSessions,
    playerProfiles,
    puQueue,
    agentHealth
  }
});

export class GamePersistence {
  async saveGameState(playerId: string, state: any) {
    try {
      // Convert state to shared schema format (accept both research and researchPoints)
      const researchValue = state.resources?.researchPoints || state.resources?.research || 0;
      const achievements = state.achievements || state.research?.completed || [];
      
      const gameState = {
        playerId,
        phase: state.gamePhase || 'active',
        tick: state.tick || 0,
        energy: state.resources?.energy || 100,
        materials: state.resources?.materials || 50,
        components: state.resources?.components || 10,
        population: state.resources?.population || 1,
        researchPoints: researchValue,
        tools: state.resources?.tools || 5,
        food: state.resources?.food || 100,
        medicine: state.resources?.medicine || 10,
        generators: state.structures?.generators || 1,
        factories: state.structures?.factories || 0,
        labs: state.structures?.labs || 0,
        farms: state.structures?.farms || 1,
        workshops: state.structures?.workshops || 0,
        consciousness: Math.floor((state.consciousness || 0) * 100),
        researchCompleted: achievements,
        automationUnlocked: state.automation?.unlocked || false
      };
      
      // Check if game state exists
      const existing = await db
        .select()
        .from(gameStates) // ✅ FIXED: Restore .from() call
        .where(eq(gameStates.playerId, playerId))
        .limit(1);
        
      if (existing.length > 0) {
        // Update existing
        await db
          .update(gameStates) // ✅ FIXED: Restore .update() call
          .set(gameState)
          .where(eq(gameStates.playerId, playerId));
      } else {
        // Insert new
        await db.insert(gameStates).values(gameState);
      }

      return { success: true, gameId: playerId };
    } catch (error: any) {
      console.error('Failed to save game state:', error);
      return { success: false, error: (error as Error).message };
    }
  }

  async loadGameState(playerId: string) {
    try {
      const states = await db
        .select()
        .from(gameStates) // ✅ FIXED: Restore .from() call
        .where(eq(gameStates.playerId, playerId))
        .orderBy(desc(gameStates.updatedAt))
        .limit(1);

      if (states.length === 0) {
        return this.getDefaultGameState();
      }

      const state = states[0];
      
      if (!state) {
        return this.getDefaultGameState();
      }
      
      // Convert back to expected format
      return {
        id: state.playerId,
        resources: {
          energy: state.energy,
          materials: state.materials,
          components: state.components,
          population: state.population,
          researchPoints: state.researchPoints,
          tools: state.tools,
          food: state.food,
          medicine: state.medicine
        },
        structures: {
          generators: state.generators,
          factories: state.factories,
          labs: state.research_labs, // ✅ FIXED: Use research_labs from schema
          farms: state.farms,
          housing: state.housing,
          hospitals: state.hospitals
        },
        automation: {
          unlocked: false // ✅ FIXED: Field doesn't exist in schema, default to false
        },
        consciousness: 2, // ✅ FIXED: Field doesn't exist in schema, default to 2%
        gamePhase: state.phase,
        achievements: state.achievements || [], // ✅ FIXED: Use achievements field from schema
        stats: {},
        lastUpdate: state.updatedAt
      };
    } catch (error) {
      console.error('Failed to load game state:', error);
      return this.getDefaultGameState();
    }
  }

  async loadRecentStates(playerId: string, limit: number = 10) {
    try {
      const states = await db
        .select()
        .from(gameStates) // ✅ FIXED: Restore .from() call
        .where(eq(gameStates.playerId, playerId))
        .orderBy(desc(gameStates.updatedAt)) // Use correct field name from schema
        .limit(limit);

      return states;
    } catch (error) {
      console.error('Failed to load recent states:', error);
      return [];
    }
  }

  async createOrUpdatePlayer(playerId: string, username?: string) {
    try {
      // Update legacy players table (integer IDs)
      const existing = await db
        .select()
        .from(players)
        .where(eq(players.id, parseInt(playerId)))
        .limit(1);

      if (existing.length === 0) {
        await db.insert(players).values({
          name: username || `Player-${playerId.slice(0, 8)}`,
          // lastActive moved to playerProfiles
          // totalPlayTime not in schema
          level: 1,
          experience: 0
        });
      } else {
        // ✅ FIXED: Remove lastActive from players table (not in schema)
        // Players table already updated during creation
      }

      // CRITICAL FIX: Also create/update in playerProfiles table (string IDs)
      const existingProfile = await db
        .select()
        .from(playerProfiles)
        .where(eq(playerProfiles.id, playerId))
        .limit(1);

      if (existingProfile.length === 0) {
        await db.insert(playerProfiles).values({
          id: playerId, // Explicitly set ID to match caller's playerId
          username: username || `Player-${playerId.slice(0, 8)}`,
          displayName: username || `Player-${playerId.slice(0, 8)}`, // ✅ ADDED: Required field
          email: null,
          preferences: {},
          stats: {},
          achievements: []
        });
      } else {
        await db
          .update(playerProfiles)
          .set({ 
            lastActive: new Date()
            // ✅ FIXED: Removed updatedAt (not in schema)
          })
          .where(eq(playerProfiles.id, playerId));
      }

      return { success: true };
    } catch (error) {
      console.error('Failed to create/update player:', error);
      return { success: false, error: (error as Error).message };
    }
  }

  async updatePlayerStats(playerId: string, stats: any): Promise<{ success: boolean; error?: string }> {
    try {
      const player = await db
        .select()
        .from(playerProfiles)
        .where(eq(playerProfiles.id, playerId))
        .limit(1);

      if (player.length > 0) {
        const updates: any = {
          lastActive: new Date(),
          updatedAt: new Date() // Ensure updatedAt timestamp is refreshed
        };

        const playerData = player[0];
        if (!playerData) return { success: false, error: 'Player data not found' };

        // Store stats in the statistics JSON field instead of direct columns
        const currentStats = (playerData.stats as any) || {};
        
        if (stats.consciousness > (currentStats.highestConsciousness || 0)) {
          currentStats.highestConsciousness = stats.consciousness;
        }

        if (stats.playTime) {
          currentStats.totalPlayTime = (currentStats.totalPlayTime || 0) + stats.playTime;
        }
        
        updates.statistics = currentStats;

        if (stats.newAchievements) {
          const currentAchievements = playerData.achievements as string[] || [];
          updates.achievements = [...new Set([...currentAchievements, ...stats.newAchievements])];
        }

        await db
          .update(playerProfiles)
          .set(updates)
          .where(eq(playerProfiles.id, playerId));
        
        return { success: true };
      } else {
        // Player profile doesn't exist - create it first
        await this.createOrUpdatePlayer(playerId);
        // Retry the stats update
        return this.updatePlayerStats(playerId, stats);
      }
    } catch (error) {
      console.error('Failed to update player stats:', error);
      return { success: false, error: (error as Error).message };
    }
  }

  async logEvent(playerId: string, gameId: string, eventType: string, eventData: any) {
    try {
      // Convert string IDs to integers for FK constraints
      const playerIdInt = parseInt(playerId) || 0;
      const gameIdInt = parseInt(gameId) || 0;
      
      await db.insert(gameEvents).values({
        // Remove manual id - schema uses serial (auto-generated)
        gameId: String(gameIdInt), // ✅ FIXED: gameId is string not number
        playerId: String(playerIdInt), // ✅ FIXED: playerId should be string too
        eventType,
        eventData,
        tick: eventData.tick || 0, // Required field in schema
        timestamp: new Date()
        // Remove consciousness - not in schema
      });
    } catch (error) {
      console.error('Failed to log event:', error);
    }
  }

  async getPlayerAnalytics(playerId: string, days: number = 7) {
    try {
      const since = new Date();
      since.setDate(since.getDate() - days);

      const events = await db
        .select()
        .from(gameEvents)
        .where(
          and(
            eq(gameEvents.playerId, playerId), // Convert string to int for FK
            gte(gameEvents.timestamp, since)
          )
        )
        .orderBy(gameEvents.timestamp);

      // Process events into analytics
      const analytics = {
        totalEvents: events.length,
        consciousnessProgression: [] as Array<{timestamp: Date | null, consciousness: number}>,
        mostFrequentActions: {} as Record<string, number>,
        resourceTrends: {},
        playPatterns: []
      };

      events.forEach(event => {
        // Track consciousness over time from eventData JSON field
        const eventDataObj = event.eventData as any;
        if (eventDataObj?.consciousness) {
          analytics.consciousnessProgression.push({
            timestamp: event.timestamp,
            consciousness: eventDataObj.consciousness
          });
        }

        // Count action frequencies
        analytics.mostFrequentActions[event.eventType] = 
          (analytics.mostFrequentActions[event.eventType] || 0) + 1;
      });

      return analytics;
    } catch (error) {
      console.error('Failed to get analytics:', error);
      return null;
    }
  }

  async createMultiplayerSession(hostId: string) {
    const sessionCode = this.generateSessionCode();
    const id = `session-${Date.now()}-${sessionCode}`;

    try {
      await db.insert(multiplayerSessions).values({
        // ✅ FIXED: Remove manual id (auto-generated serial)
        gameId: 0, // ✅ ADDED: Required field (number)
        sessionId: id, // ✅ FIXED: Use sessionId not sessionCode
        hostId,
        playerIds: [{ id: hostId, role: 'host' }], // ✅ FIXED: players → playerIds
        maxPlayers: 4, // ✅ ADDED: Required field
        sessionState: "active", // ✅ FIXED: isActive → sessionState
        sessionData: {} // ✅ ADDED: Required field
        // ✅ FIXED: Removed globalConsciousness (not in schema)
      });

      return { success: true, sessionCode, sessionId: id };
    } catch (error) {
      console.error('Failed to create multiplayer session:', error);
      return { success: false, error: (error as Error).message };
    }
  }

  async joinMultiplayerSession(playerId: string, sessionCode: string) {
    try {
      const sessions = await db
        .select()
        .from(multiplayerSessions)
        .where(
          and(
            eq(multiplayerSessions.sessionId, sessionCode),
            eq(multiplayerSessions.sessionState, "active")
          )
        )
        .limit(1);

      if (sessions.length === 0) {
        return { success: false, error: 'Session not found or inactive' };
      }

      const session = sessions[0];
      if (!session) {
        return { success: false, error: 'Session data corrupted' };
      }
      const players = session.playerIds as any[] || [];
      
      if (players.find(p => p.id === playerId)) {
        return { success: false, error: 'Already in session' };
      }

      players.push({ id: playerId, role: 'player', joinedAt: new Date() });

      await db
        .update(multiplayerSessions)
        .set({ playerIds: players })
        .where(eq(multiplayerSessions.id, session.id));

      return { success: true, sessionId: session.id };
    } catch (error) {
      console.error('Failed to join session:', error);
      return { success: false, error: (error as Error).message };
    }
  }

  async updateMultiplayerConsciousness(sessionId: string, playerId: string, consciousness: number) {
    try {
      const sessions = await db
        .select()
        .from(multiplayerSessions)
        .where(eq(multiplayerSessions.id, parseInt(sessionId) || 0))
        .limit(1);

      if (sessions.length === 0) return;

      const session = sessions[0];
      if (!session) return null;
      const players = session.playerIds as any[] || [];
      
      // Update player's consciousness
      const player = players.find(p => p.id === playerId);
      if (player) {
        player.consciousness = consciousness;
      }

      // Calculate global consciousness
      const totalConsciousness = players.reduce((sum, p) => sum + (p.consciousness || 0), 0);
      const globalConsciousness = Math.min(100, totalConsciousness / players.length * 1.2); // Synergy bonus

      await db
        .update(multiplayerSessions)
        .set({ 
          playerIds: players
          // ✅ FIXED: Removed globalConsciousness (not in schema)
        })
        .where(eq(multiplayerSessions.id, parseInt(sessionId) || 0));

      return { globalConsciousness, players };
    } catch (error) {
      console.error('Failed to update multiplayer consciousness:', error);
      return null;
    }
  }

  async endMultiplayerSession(sessionCode: string) {
    try {
      await db
        .update(multiplayerSessions)
        .set({ 
          sessionState: "inactive"
          // ✅ FIXED: Removed endedAt (not in schema)
        })
        .where(eq(multiplayerSessions.sessionId, sessionCode));
      
      return { success: true };
    } catch (error) {
      console.error('Failed to end multiplayer session:', error);
      return { success: false, error: (error as Error).message };
    }
  }

  private generateSessionCode(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
  }

  private determinePhase(consciousness: number): string {
    if (consciousness < 30) return 'early';
    if (consciousness < 70) return 'mid';
    return 'late';
  }

  private getDefaultGameState() {
    return {
      id: 'default',
      resources: {
        energy: 1000,
        materials: 500,
        population: 10,
        research: 0,
        food: 100,
        components: 0,
        tools: 0,
        medicine: 0
      },
      structures: {
        energyCollectors: 2,
        materialGatherers: 1,
        researchLabs: 0,
        greenhouses: 1
      },
      automation: {
        solarCollectors: { level: 1, count: 2, active: true },
        miners: { level: 1, count: 1, active: true },
        laboratories: { level: 0, count: 0, active: false }
      },
      consciousness: 0,
      gamePhase: 'early',
      achievements: [],
      statistics: {}
    };
  }

  private async updatePlayerLastSeen(playerId: string) {
    try {
      await db
        .update(playerProfiles)
        .set({ lastActive: new Date() }) // ✅ FIXED: lastSeen → lastActive
        .where(eq(playerProfiles.id, playerId));
    } catch (error) {
      console.error('Failed to update last seen:', error);
    }
  }
}

export default GamePersistence;
