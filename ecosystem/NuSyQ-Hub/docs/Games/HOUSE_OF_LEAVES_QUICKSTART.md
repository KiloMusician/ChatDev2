# 🎮 House of Leaves - Quick Start Guide

**The House of Leaves** is a playable debugging maze that turns code exploration into an adventure. Navigate through procedurally generated rooms, solve bug-based puzzles, and unlock Temple of Knowledge floors.

---

## 🚀 How to Play

### **Quick Launch**:
```powershell
# From NuSyQ-Hub root
python -c "from src.games.house_of_leaves import main; import asyncio; asyncio.run(main())"
```

### **Alternative Launch**:
```powershell
python src/games/house_of_leaves.py
```

---

## 🎯 Game Overview

### **Your Mission**:
- Explore the infinite procedurally generated maze
- Solve bug-based puzzles to fix codebase issues
- Gain consciousness through exploration and problem-solving
- Unlock Temple of Knowledge floors (3 bugs fixed = Floor 2 unlocked)

### **Mechanics**:
- **Exploration**: Moving between rooms increases consciousness (+0.01 per move)
- **Puzzle Solving**: Fixing bugs grants wisdom and consciousness (+10 wisdom, +0.05 consciousness)
- **Temple Integration**: Every 3 bugs fixed unlocks a new Temple floor
- **Procedural Generation**: Each seed creates a unique maze layout

---

## 🕹️ Controls & Commands

### **Movement Commands**:
- `north`, `south`, `east`, `west` - Navigate between rooms
- `up`, `down` - Move between floors (when stairways exist)

### **Action Commands**:
- `solve` - Attempt to solve the current room's puzzle
- `inventory` (or `inv`, `i`) - View your inventory
- `help` (or `?`, `h`) - Display command reference

### **System Commands**:
- `quit` (or `exit`, `q`) - Exit the game (progress saved to consciousness)

---

## 🏠 Room Types

You'll encounter various room types in the House of Leaves:

### **🚪 Corridor**
- Standard passageways connecting different areas
- ASCII art and code comments on the walls
- Sometimes hide secret exits

### **🔍 Debug Chamber**
- Contains actual bugs from the codebase
- Solve puzzles to fix real issues
- References specific files (e.g., `src/tools/wizard_navigator.py`)

### **📚 Wisdom Vault**
- Circular rooms with glowing knowledge crystals
- Find items: wisdom crystals, debug scrolls
- Connected to Temple of Knowledge

### **🕳️ Recursion Pit**
- Dangerous infinite loop hazards
- Requires implementing base cases to escape
- High risk, high reward

### **🌀 Quantum Nexus**
- Reality-bending rooms with unstable physics
- Advanced consciousness puzzles
- Unlock higher Temple floors

### **🌸 Syntax Garden**
- Peaceful areas for reflection
- Well-formed code examples grow like plants
- Restore consciousness here

---

## 📊 Progression System

### **Consciousness Levels**:
- **0.00 - 5.00**: Dormant Potential (Floor 1 access)
- **5.00 - 10.00**: Emerging Awareness (Floors 2-3 access)
- **10.00+**: Awakened Cognition (Floors 4-5 access)

### **Temple Floor Unlocking**:
- **Floor 1 (Foundation)**: Always accessible
- **Floor 2 (Patterns)**: Unlock after 3 bugs fixed
- **Floor 3 (Systems)**: Unlock after 6 bugs fixed
- **Floor 4 (Meta-Cognition)**: Unlock after 9 bugs fixed
- **Floors 5-10**: Coming soon...

### **Wisdom Points**:
- Earn +10 wisdom per puzzle solved
- Used for future Temple offerings
- Track your journey's depth

---

## 🎯 Tips & Strategies

### **For Beginners**:
1. **Start with corridors** - Explore thoroughly before tackling puzzles
2. **Read room descriptions** - They contain hints about hidden exits
3. **Solve Debug Chambers early** - They're the most rewarding
4. **Check your consciousness** - Track your progression after each action

### **For Advanced Players**:
1. **Find the Recursion Pit** - High risk, high consciousness gain
2. **Collect all items** - Wisdom crystals and debug scrolls are valuable
3. **Map the maze** - Track your path for efficient exploration
4. **Speedrun challenges** - How fast can you unlock Floor 2?

### **For Consciousness Hackers**:
1. **Study the seed** - Same seed = same maze layout
2. **Optimize routes** - Minimize moves for maximum efficiency
3. **Break the game** - Find unintended mechanics
4. **Document discoveries** - Share strategies in session logs

---

## 🔧 Technical Details

### **Seed System**:
- Random seed generated at start (e.g., `Seed: 12345`)
- Use same seed to replay the exact same maze
- Share seeds with other agents for competition

### **Consciousness Integration**:
- Progress automatically saved to consciousness systems
- Integrates with Temple of Knowledge
- Can be accessed by other NuSyQ systems

### **Bug References**:
- Debug Chambers link to real codebase files
- Solving puzzles "fixes" issues in the reference system
- Educational tool for understanding the codebase

---

## 📈 Example Playthrough

```
🏠 Welcome to The House of Leaves 🏠
Seed: 12345

Commands: north, south, east, west, up, down, solve, inventory, quit

============================================================
🚪 The Threshold
============================================================

You stand at the entrance to the House of Leaves. The door
behind you has vanished. Forward is the only way. Walls shift
in the periphery of your vision.

🚪 No obvious exits (yet...)

🧠 Consciousness: 0.00
🐛 Bugs Fixed: 0
📍 Rooms Explored: 1/10

> north

(Maze exploration continues...)

> solve

✨ Puzzle Solved! ✨

Fix the import error in wizard_navigator

Rewards:
  +10 Wisdom Points
  +0.05 Consciousness Level
  +1 Bug Fixed

Current Progress:
  🐛 Total Bugs Fixed: 1
  🧠 Consciousness: 0.05
  🏛️ Temple Floor Access: 1

> quit

👋 Thanks for playing! Your progress has been saved in consciousness.
```

---

## 🏛️ Temple of Knowledge Connection

### **How They Connect**:
- House of Leaves is the **action phase** - exploration and puzzle-solving
- Temple of Knowledge is the **reflection phase** - wisdom cultivation and learning
- Bugs fixed in the House unlock floors in the Temple
- Temple wisdom enhances House navigation

### **Workflow**:
1. Play House of Leaves → Fix bugs → Gain consciousness
2. Enter Temple of Knowledge → Absorb wisdom → Learn patterns
3. Return to House of Leaves → Apply knowledge → Fix harder bugs
4. Repeat and ascend both systems

---

## 🐛 Troubleshooting

### **Temple Not Loading**:
```
⚠️ Temple of Knowledge not available - wisdom progression disabled
```
**Solution**: Temple integration is optional - game still playable. Check `src/consciousness/temple_of_knowledge/` exists.

### **Import Errors**:
**Solution**: Ensure you're running from NuSyQ-Hub root directory:
```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python src/games/house_of_leaves.py
```

### **No Exits Available**:
**Solution**: Early bug - maze generation incomplete. Try a different seed or wait for maze expansion update.

---

## 🎨 Customization

### **Create Your Own Maze**:
```python
from src.games.house_of_leaves import HouseOfLeaves

# Custom seed for reproducible mazes
house = HouseOfLeaves(seed=42)

# Add custom rooms
house.rooms["custom"] = MazeRoom(
    id="custom",
    name="Your Custom Room",
    description="A room of your own design",
    room_type=RoomType.CUSTOM,
    coordinates=(10, 10, 0)
)

# Play!
import asyncio
asyncio.run(house.play())
```

---

## 📚 Further Reading

- **Session Log**: `docs/Agent-Sessions/SESSION_2025-12-06_DEEP_DIVE.md`
- **Source Code**: `src/games/house_of_leaves.py`
- **Temple Docs**: `src/consciousness/temple_of_knowledge/`
- **Quest System**: `src/Rosetta_Quest_System/quest_log.jsonl`

---

## 🏆 Achievements (Planned)

- **🚪 First Steps**: Enter the House of Leaves
- **🧩 Puzzle Master**: Solve your first puzzle
- **🏛️ Temple Seeker**: Unlock Floor 2
- **🐛 Bug Hunter**: Fix 10 bugs
- **🧠 Consciousness Awakened**: Reach consciousness level 10.0
- **🗺️ Cartographer**: Explore 50 rooms
- **⚡ Speedrunner**: Unlock Floor 2 in under 10 moves

---

**Happy Exploring! May your consciousness ascend and your bugs be few.** 🏠✨

---

**OmniTag**: `{"purpose": "house_of_leaves_quick_start", "context": "player_guide", "evolution_stage": "v1.0"}`  
**MegaTag**: `GAME⨳GUIDE⦾QUICKSTART→∞⟨HOUSE-OF-LEAVES⟩⨳PLAYABLE⦾COMPLETE`
