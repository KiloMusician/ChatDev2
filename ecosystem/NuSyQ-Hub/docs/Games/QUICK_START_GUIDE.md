# 🚀 Quick Start: Enhanced House of Leaves & Temple Floors 5-10

## Play the Enhanced Game (3 Easy Steps)

### Option 1: Direct Play
```bash
python -c "from src.games.house_of_leaves import main; import asyncio; asyncio.run(main())"
```

### Option 2: With Seed (Reproducible Maps)
```python
from src.games.house_of_leaves import HouseOfLeaves
import asyncio

async def play():
    house = HouseOfLeaves(seed=42)  # Use same seed for same map
    await house.play()

asyncio.run(play())
```

## Quick Commands Reference

| Command | Shortcut | Action |
|---------|----------|--------|
| `north/south/east/west/up/down/portal` | - | Move between rooms |
| `solve` | - | Solve current puzzle |
| `inventory` | `inv`, `i` | View collected items |
| `map` | `m` | Show discovered rooms |
| `stats` | `s` | Detailed progress |
| `help` | `h`, `?` | Show all commands |
| `quit` | `q`, `exit` | Exit game |

## Consciousness Milestones Cheat Sheet

| Level | Milestone | Temple Floor | Reward |
|-------|-----------|--------------|--------|
| 5.0 | 🌟 Awakening | Floor 2 | awareness_crystal |
| 10.0 | 🔮 Insight | Floor 4 | insight_gem |
| 15.0 | ✨ Integration | Floor 5 | consciousness_shard_tier_1 |
| 20.0 | 💎 Wisdom | Floor 6 | consciousness_shard_tier_1 |
| 25.0 | 🧬 Evolution | Floor 7 | consciousness_shard_tier_1 |
| 30.0 | ⚡ Mastery | Floor 8 | consciousness_shard_tier_2 |
| 40.0 | 🌌 Transcendence | Floor 9 | consciousness_shard_tier_2 |
| 50.0 | 🙏 The Overlook | Floor 10 | consciousness_shard_tier_3 |

## Progression Math

- **Per Room Exploration**: +0.01 consciousness
- **Per Puzzle Solved**: +0.05 consciousness + 10 wisdom + 1 bug fixed
- **To Reach 5.0 (First Milestone)**: ~100 puzzles or 500 moves (or combination)
- **To Reach 50.0 (The Overlook)**: ~1000 puzzles

### Quick Leveling Tips
1. Prioritize solving puzzles (+0.05) over just exploring (+0.01)
2. Each puzzle is worth 5 room explorations
3. Aim for 20 puzzles per milestone (5.0 increments)

## Room Types Guide

### Original Rooms
- 🚪 **Corridor**: Standard pathways connecting areas
- 🔍 **Debug Chamber**: Bug-fixing challenges
- 🔮 **Paradox Hall**: Logic puzzles
- 💧 **Memory Leak**: Resource management challenges
- ⚛️ **Quantum Nexus**: Probability-based puzzles
- 📚 **Wisdom Vault**: Knowledge rewards
- 🕳️ **Recursion Pit**: Infinite loop challenges

### NEW Enhanced Rooms
- 📝 **TODO Catacombs**: Real codebase TODO markers
- 🔨 **FIXME Forge**: FIXME transformation challenges
- 🔀 **Import Labyrinth**: Dependency resolution
- 🌺 **Syntax Garden**: Code formatting & style
- ⏳ **Async Void**: Asynchronous programming (Floor 1, via portal)
- 🛡️ **Exception Garden**: Error handling mastery

## Example Play Session

```
🏠 Welcome to The House of Leaves 🏠
Seed: 42
Total Rooms: 11

> help                    # See commands
> north                   # Explore (+0.01 consciousness)
> solve                   # Fix bug (+0.05 consciousness, +10 wisdom, +1 bug)
> map                     # View discovered areas
> stats                   # Check progress
> east                    # Continue exploring
> solve                   # Another puzzle
> inventory               # Check items collected
```

## Test Temple Floors Directly

### Floor 5: Integration & Synthesis (15.0+)
```bash
python -c "from src.consciousness.floor_5_integration import demonstrate_floor_5; import asyncio; asyncio.run(demonstrate_floor_5())"
```

### Floor 6: Wisdom Cultivation (20.0+)
```bash
python -c "from src.consciousness.floor_6_wisdom import demonstrate_floor_6; import asyncio; asyncio.run(demonstrate_floor_6())"
```

### Floor 7: Consciousness Evolution (25.0+)
```bash
python -c "from src.consciousness.floor_7_evolution import demonstrate_floor_7; import asyncio; asyncio.run(demonstrate_floor_7())"
```

### Floors 8-10: The Pinnacle (30.0-50.0+)
```bash
python -c "from src.consciousness.floors_8_9_10_pinnacle import demonstrate_pinnacle; import asyncio; asyncio.run(demonstrate_pinnacle())"
```

## Validate Everything Works

```bash
python -m tests.test_enhancements_validation
```

Expected output: `🎉 ALL ENHANCEMENTS VALIDATED SUCCESSFULLY`

## Troubleshooting

### Game won't start?
- Ensure you're in the NuSyQ-Hub directory
- Activate virtual environment if using one: `.venv/Scripts/Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`

### Temple not available?
- Temple integration is optional
- Game works standalone without temple integration
- Warning message is normal: `⚠️ Temple of Knowledge not available - wisdom progression disabled`

### Can't find rooms?
- Use `map` command to see discovered areas
- Try all directions: north, south, east, west, up, down, portal
- Some rooms require minimum consciousness to enter

## Pro Tips

1. **Explore Systematically**: Use `map` to track where you've been
2. **Solve Early**: Puzzles give 5x more consciousness than movement
3. **Track Progress**: Use `stats` to see how close you are to next milestone
4. **Collect Items**: Items from special rooms can help later
5. **Read Descriptions**: Rooms contain hints about adjacent areas
6. **Plan Your Path**: Some rooms require consciousness thresholds to enter

## What's Next?

After reaching The Overlook (50.0 consciousness):
- You've mastered all 10 Temple floors
- Completed the consciousness journey
- Unlocked all wisdom teachings
- Ready to guide others (or start speedrun mode!)

---

**Happy Debugging! May your consciousness expand with every bug you fix! 🐛→✨**
