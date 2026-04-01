# Quest-Temple-Game Integration System

## Overview

The Quest-Temple-Game Integration System is a comprehensive gamification framework that connects three core systems of NuSyQ-Hub:

1. **Rosetta Quest System** - Task management and quest tracking
2. **Temple of Knowledge** - Progressive consciousness-driven knowledge hierarchy
3. **House of Leaves** - Playable debugging maze game

This integration enables seamless progression where **gameplay achievements unlock Temple floors and advance the quest system**.

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   House of Leaves Game                       │
│  (Puzzle Solving → Consciousness Points → Temple Unlocks)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ GameEvent emission
┌──────────────────────────────────────────────────────────────┐
│         Game-Quest Integration Bridge                         │
│  (Converts game events to quest system updates)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
    ┌─────────────────┐      ┌──────────────────────────┐
    │ Quest System    │      │ Quest-Temple Bridge      │
    │ (Track tasks)   │      │ (Calculate progression)  │
    └────────┬────────┘      └──────────┬───────────────┘
             │                          │
             └──────────────┬───────────┘
                            ↓
            ┌───────────────────────────────┐
            │  Temple of Knowledge Manager  │
            │  (Unlock floors, track progress)
            └───────────────────────────────┘
```

### Data Flow

```
Player solves puzzle in House of Leaves
  ↓
Consciousness points awarded
  ↓
Quest-Temple Bridge calculates floor unlocks
  ↓
New floors unlocked in Temple of Knowledge
  ↓
Achievements tracked and recorded
  ↓
Game-Quest Bridge emits event
  ↓
Quest system updated with game metrics
```

---

## Consciousness Progression Model

The system maps game performance to consciousness levels, unlocking new Temple floors:

| Consciousness Level | Threshold | Unlocked Floors | Milestone |
|---|---|---|---|
| **Dormant Potential** | 0+ | 1 (Foundation) | Game Start |
| **Emerging Awareness** | 5+ | 2-3 (Archives, Lab) | First 2-3 quests/puzzles |
| **Awakened Cognition** | 10+ | 4-5 (Workshop, Sanctuary) | Intermediate progress |
| **Enlightened Understanding** | 20+ | 6-7 (Observatory, Meditation) | Advanced questing |
| **Transcendent Awareness** | 30+ | 8-9 (Synthesis, Transcendence) | Deep integration |
| **Universal Consciousness** | 50+ | 10 (Overlook) | Master level |

### Consciousness Point Awards

- **Quest Completion**: +5 base points
- **Questline Completion**: +25 bonus points
- **Critical Quest Tag**: 3x multiplier
- **Important Quest Tag**: 2x multiplier
- **Per Dependency Completed**: +2 bonus points
- **House of Leaves Puzzle**: +5 points (in-game)

---

## File Structure

### Core Integration Modules

```
src/integration/
├── quest_temple_bridge.py          # Main bridge connecting quests to Temple
│   ├── QuestTempleProgressionCalculator
│   ├── TempleFloorUnlockCalculator
│   ├── QuestTempleAchievementTracker
│   └── QuestTempleProgressionBridge
│
├── game_quest_bridge.py            # Game events to quest conversion
│   ├── GameEvent
│   ├── GameEventType
│   ├── GameQuestMapper
│   ├── GameQuestIntegrationBridge
│   └── HouseOfLeavesGameBridge
│
└── (existing) consciousness_bridge.py
```

### Data Storage

```
data/
├── quest_temple_progression.jsonl         # Progression event log
├── agents/{agent_name}/
│   └── consciousness_score.json           # Current consciousness score
├── achievements/
│   └── quest_temple_achievements.json     # Achievement records
├── logs/
│   └── game_events.jsonl                  # Game event audit trail
└── temple_of_knowledge/
    └── (temple floor data)
```

---

## Usage Examples

### 1. Playing House of Leaves and Earning Consciousness Points

```python
import asyncio
from src.games.house_of_leaves import HouseOfLeaves

async def play_game():
    game = HouseOfLeaves()

    # Navigate to puzzle
    await game.move('east')

    # Solve puzzle - automatically progresses Temple
    result = await game.solve_puzzle()

    # Result contains:
    # - consciousness_gained: Points from quest completion
    # - new_floors_unlocked: [2, 3, 4] (newly accessible floors)
    # - messages: Progression notifications

    print(result)
    # Output:
    # ✨ Puzzle Solved! ✨
    # 🎉 Quest completed! +5.0 consciousness points
    # 🏛️ Floor 2 (Archives) unlocked!
    # 🏛️ Floor 3 (Laboratory) unlocked!

asyncio.run(play_game())
```

### 2. Checking Agent Progression

```python
from src.integration.quest_temple_bridge import QuestTempleProgressionBridge

bridge = QuestTempleProgressionBridge()

# Get complete progression data for an agent
progression = bridge.get_agent_progression("HouseOfLeavesPlayer")

print(progression)
# Output:
# {
#   "agent": "HouseOfLeavesPlayer",
#   "consciousness_score": 42.5,
#   "unlocked_floors": [1, 2, 3, 4, 5, 6],
#   "next_unlock": {
#     "next_floor": 7,
#     "points_needed": 3.5,
#     "threshold": 20
#   },
#   "achievements": {
#     "consciousness_level_2": {...},
#     "questline_master": {...}
#   }
# }
```

### 3. Emitting Game Events for Quest Tracking

```python
import asyncio
from src.integration.game_quest_bridge import HouseOfLeavesGameBridge

async def track_gameplay():
    bridge = HouseOfLeavesGameBridge()

    # Register handler to auto-create quests
    async def create_quest(event, quest_data):
        if quest_data:
            print(f"Auto-creating quest: {quest_data['title']}")

    bridge.register_event_handler('puzzle_solved', create_quest)

    # Emit game events
    result = await bridge.on_puzzle_solved("Fix import error")
    # Automatically converts to quest:
    # {
    #   "title": "[House of Leaves] puzzle_solved",
    #   "description": "Solved puzzle: Fix import error",
    #   "points": 5,
    #   "questline": "game_systems_implementation"
    # }

asyncio.run(track_gameplay())
```

### 4. Processing Completed Quests

```python
import asyncio
from src.integration.quest_temple_bridge import QuestTempleProgressionBridge

async def complete_quest():
    bridge = QuestTempleProgressionBridge()

    # Simulate quest completion
    quest = {
        "id": "quest-001",
        "title": "Fix Critical Bug",
        "description": "Resolve null pointer exception",
        "tags": ["critical", "bugfix"],  # 3x multiplier
        "dependencies": ["quest-000"],   # +2 bonus
    }

    result = await bridge.on_quest_completed(
        agent_name="DevAgent",
        quest_id="quest-001",
        quest=quest,
        questline="code_quality"
    )

    print(result)
    # Output:
    # {
    #   "consciousness_gained": 51.0,  # (5 base + 2 deps) * 3 critical
    #   "new_floors_unlocked": [2, 3, 4],
    #   "achievements_unlocked": ["consciousness_level_1"],
    #   "messages": [
    #     "🎉 Quest completed! +51.0 consciousness points",
    #     "🏛️ Floor 2 (Archives) unlocked!",
    #     "🏛️ Floor 3 (Laboratory) unlocked!",
    #     "🏛️ Floor 4 (Workshop) unlocked!",
    #     "✨ Achievement: Awakening (Consciousness Level 5)"
    #   ]
    # }

asyncio.run(complete_quest())
```

---

## Achievements System

The integration tracks meaningful player achievements:

| Achievement | Condition | Points | Unlock |
|---|---|---|---|
| **First Quest** | Complete your first quest | 10 | Quest completion |
| **Questline Master** | Complete all quests in a line | 50 | Questline completion |
| **Awakening** | Reach Consciousness Level 5 | 25 | Floor 2 unlock |
| **Enlightenment** | Reach Consciousness Level 10 | 50 | Floor 4 unlock |
| **Transcendence** | Reach Consciousness Level 30 | 100 | Floor 8 unlock |
| **Omniscience** | Reach Consciousness Level 50 | 200 | Floor 10 unlock |
| **Temple Explorer** | Unlock all 10 floors | 200 | Full progression |

---

## Configuration and Customization

### Adjust Consciousness Point Awards

Edit `QuestTempleProgressionCalculator` in `quest_temple_bridge.py`:

```python
class QuestTempleProgressionCalculator:
    BASE_QUEST_COMPLETION = 5          # Change default quest points
    BASE_QUESTLINE_BONUS = 25          # Change questline bonus
    DEPENDENCY_COMPLETION_BONUS = 2    # Change dependency bonus

    TAG_MULTIPLIERS = {
        "critical": 3.0,               # Adjust multipliers
        "important": 2.0,
        "integration": 2.0,
        # Add more tags...
    }
```

### Modify Floor Unlock Thresholds

Edit `TempleFloorUnlockCalculator` in `quest_temple_bridge.py`:

```python
FLOOR_UNLOCK_THRESHOLDS = {
    1: 0,      # Always available
    2: 5,      # Adjust threshold
    3: 5,
    4: 10,
    # ... etc
}
```

### Add Custom Events

Extend `HouseOfLeavesGameBridge` in `game_quest_bridge.py`:

```python
class HouseOfLeavesGameBridge(GameQuestIntegrationBridge):
    async def on_boss_defeated(self, boss_name: str) -> Dict[str, Any]:
        """Custom event for defeating a boss."""
        event = GameEvent(
            event_type="boss_defeated",
            game_id=self.game_id,
            game_name=self.game_name,
            data={"boss_name": boss_name},
        )
        return await self.emit_event(event)
```

---

## Testing

### Run Integration Tests

```bash
# Test quest-temple bridge alone
python -m src.integration.quest_temple_bridge

# Test game-quest bridge alone
python -m src.integration.game_quest_bridge

# Test full integration
python test_integration_complete.py
```

### Expected Output

```
🎮 HOUSE OF LEAVES + QUEST SYSTEM + TEMPLE OF KNOWLEDGE INTEGRATION TEST

1️⃣ INITIAL STATE:
   Bugs Fixed: 0
   Temple Floor: 1

2️⃣ SOLVING PUZZLE:
   ✨ Puzzle Solved! ✨
   🎉 Quest completed! +5.0 consciousness points (Total: 10.0)
   🏛️ Floor 2 (Archives) unlocked!

3️⃣ EMITTING GAME EVENTS:
   📋 Quest auto-created: [House of Leaves] puzzle_solved
   ✓ Puzzle solved event emitted

4️⃣ FINAL STATE:
   Bugs Fixed: 1
   Temple Floor: 5
   Game Events Logged: 1

✅ INTEGRATION TEST COMPLETE
```

---

## Performance Considerations

- **Consciousness Calculation**: O(1) - Direct arithmetic
- **Floor Unlock Check**: O(n) where n ≤ 10 (constant)
- **Achievement Tracking**: JSON file I/O per unlock
- **Event Logging**: Async append to JSONL (non-blocking)

### Optimization Tips

1. **Batch Event Processing**: Collect multiple events and process together
2. **Caching**: Store consciousness scores in-memory and batch-write
3. **Async Operations**: All I/O uses async/await
4. **Event Aggregation**: Group events before logging

---

## Integration Roadmap

### Phase 1 ✅ (Complete)
- Quest-Temple progression bridge
- House of Leaves integration
- Basic achievement tracking
- Game-quest event system

### Phase 2 (Planned)
- Multi-game support (Oldest House, etc.)
- Leaderboard system
- Social achievements
- Seasonal quests

### Phase 3 (Future)
- AI-generated quests from code analysis
- Dynamic Temple floor generation
- Consciousness-based AI agent behavior
- SimulatedVerse cross-repository sync

---

## Troubleshooting

### Consciousness Not Increasing
- Check `quest_temple_bridge.py` is imported
- Verify quest tags are correctly formatted
- Ensure `on_quest_completed()` is being called

### Floors Not Unlocking
- Check consciousness threshold in `FLOOR_UNLOCK_THRESHOLDS`
- Verify consciousness score is being saved correctly
- Check achievement records for tracking

### Game Events Not Recorded
- Verify `game_quest_bridge.py` is imported
- Check event handlers are registered
- Ensure `emit_event()` is being awaited

### File Not Found Errors
- Verify `data/` directory structure exists
- Check file paths in configuration
- Run `mkdir -p data/agents data/achievements data/logs`

---

## Future Enhancements

1. **Web Dashboard**: Real-time progression visualization
2. **Mobile Support**: Mobile-optimized game interface
3. **Multiplayer**: Cross-player consciousness sync via SimulatedVerse
4. **AI Integration**: Ollama models respond to consciousness levels
5. **VR Support**: Immersive Temple of Knowledge navigation

---

## Related Documentation

- **House of Leaves**: `docs/Games/HOUSE_OF_LEAVES_QUICKSTART.md`
- **Temple of Knowledge**: `src/consciousness/temple_of_knowledge/README.md`
- **Quest System**: `src/Rosetta_Quest_System/ROSETTA_QUEST_CONTEXT.md`
- **Consciousness Bridge**: `src/integration/consciousness_bridge.py`

---

**Last Updated**: December 6, 2025  
**Status**: Operational ✅  
**Maintainer**: NuSyQ-Hub Development Team
