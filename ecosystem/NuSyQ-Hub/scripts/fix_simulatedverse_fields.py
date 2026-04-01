#!/usr/bin/env python3
"""SimulatedVerse Database Field Mismatch Auto-Fixer
Fixes 20+ field name errors in game-persistence.ts after schema implementation.

Fixes:
- players → playerIds (JSONB array)
- sessionCode → sessionId
- isActive → sessionState
- statistics → stats
- lastSeen → lastActive
- Remove avatar field (not in schema)
- gameId type conversions

Run: python fix_simulatedverse_fields.py
"""

import re
from pathlib import Path


def fix_game_persistence():
    """Fix all field name mismatches in game-persistence.ts."""
    file_path = Path("c:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/server/storage/game-persistence.ts")

    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")
    original_content = content

    # Fix 1: username field doesn't exist in players table (integer ID table)
    # Remove username from players insert
    content = re.sub(
        r"await db\.insert\(players\)\.values\(\{\s*username: username \|\| `Player-\$\{playerId\.slice\(0, 8\)\}`,",
        "await db.insert(players).values({\n          name: username || `Player-${playerId.slice(0, 8)}`,",
        content,
    )

    # Fix 2: lastActive doesn't exist in players table
    content = content.replace("lastActive: new Date(),", "// lastActive moved to playerProfiles")
    content = content.replace("totalPlayTime: 0,", "// totalPlayTime not in schema")

    # Fix 3: lastSeen → lastActive in playerProfiles updates
    content = content.replace("lastSeen: new Date(),", "lastActive: new Date(),")

    # Fix 4: Remove avatar field from playerProfiles (not in schema)
    content = re.sub(r",\s*avatar: null,?", ",", content)
    content = re.sub(r"avatar: null,\s*", "", content)

    # Fix 5: statistics → stats in playerProfiles
    content = content.replace("statistics: {},", "stats: {},")
    content = content.replace("playerData.statistics", "playerData.stats")

    # Fix 6: Remove friends field (not in schema)
    content = re.sub(r",\s*friends: \[\],?", "", content)
    content = re.sub(r"friends: \[\],\s*", "", content)

    # Fix 7: session.players → session.playerIds (JSONB)
    content = content.replace("session.players as any[]", "session.playerIds as any[]")
    content = content.replace(".set({ players })", ".set({ playerIds: players })")
    content = content.replace("players,", "playerIds: players,")

    # Fix 8: multiplayerSessions.sessionCode → .sessionId
    content = content.replace("multiplayerSessions.sessionCode", "multiplayerSessions.sessionId")

    # Fix 9: multiplayerSessions.isActive doesn't exist (use sessionState)
    content = content.replace(
        "eq(multiplayerSessions.isActive, true)",
        'eq(multiplayerSessions.sessionState, "active")',
    )
    content = content.replace("isActive: false,", 'sessionState: "inactive",')

    # Fix 10: Convert string sessionId to number for multiplayerSessions.id comparisons
    content = re.sub(
        r"eq\(multiplayerSessions\.id, sessionId\)",
        "eq(multiplayerSessions.id, parseInt(sessionId) || 0)",
        content,
    )

    # Fix 11: gameId should be string for gameEvents
    content = content.replace("gameId: gameIdInt,", "gameId: String(gameIdInt),")

    # Fix 12: playerId in gameEvents is string, not int
    content = content.replace(
        "eq(gameEvents.playerId, parseInt(playerId) || 0)",
        "eq(gameEvents.playerId, playerId)",
    )

    # Fix 13: Add displayName to playerProfiles insert (required field)
    content = re.sub(
        r"(id: playerId,\s*username: username \|\| `Player-\$\{playerId\.slice\(0, 8\)\}`,)",
        r"\\1\n          displayName: username || `Player-${playerId.slice(0, 8)}`,",
        content,
    )

    # Fix 14: Remove 'id' from multiplayerSessions insert (auto-generated)
    content = re.sub(r"id,\s*sessionId:", "sessionId:", content)

    if content == original_content:
        return

    # Count fixes
    sum(1 for a, b in zip(original_content, content, strict=False) if a != b)

    # Backup original
    backup_path = file_path.with_suffix(".ts.backup")
    backup_path.write_text(original_content, encoding="utf-8")

    # Write fixed version
    file_path.write_text(content, encoding="utf-8")


def fix_tsconfig_deprecation():
    """Fix TypeScript baseUrl deprecation warning."""
    file_path = Path("c:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/tsconfig.json")

    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")

    # Add ignoreDeprecations before baseUrl
    if "ignoreDeprecations" not in content:
        content = content.replace('"baseUrl": ".",', '"baseUrl": ".",\n    "ignoreDeprecations": "6.0",')

        file_path.write_text(content, encoding="utf-8")
    else:
        pass


def main():
    fix_game_persistence()
    fix_tsconfig_deprecation()


if __name__ == "__main__":
    main()
