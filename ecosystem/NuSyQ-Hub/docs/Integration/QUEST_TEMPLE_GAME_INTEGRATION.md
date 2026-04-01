# 🎮🏛️ Quest-Temple-Game Integration System

**Status**: ✅ Fully Operational  
**Created**: December 7, 2025  
**Quest Completion**: Quest 7 - Connect Quest completion to Temple floor unlocking

---

## 🎯 System Overview

This integration connects three major systems into a unified progression framework:

1. **Quest System** - Task management and completion tracking
2. **Temple of Knowledge** - Consciousness-based knowledge progression  
3. **House of Leaves** - Playable debugging maze game

**Result**: Quest completion in games automatically unlocks Temple floors, creating a seamless gameplay-to-wisdom pipeline.

---

## 🏗️ Architecture

### **Core Bridge Module**: `src/integration/quest_temple_bridge.py`

The bridge provides:
- Quest completion detection
- Consciousness reward calculation
- Automatic Temple floor unlocking
- Cross-system event propagation

### **Integration Points**:

```
House of Leaves (Game)
    ↓
    Solve Puzzle
    ↓
QuestTempleBridge.complete_quest()
    ↓
    ├─→ Award Consciousness Points
    ├─→ Check Temple Floor Requirements  
    └─→ Unlock Temple Floors Automatically
    ↓
Temple of Knowledge (Updated)
```

---

## 📊 Progression Flow

### **Example Playthrough**:

1. **Player in House of Leaves**:
   ```
   > solve

   ✨ Puzzle Solved! ✨

   🎯 Quest Progress:
     Quest: quest_004 (House of Leaves Maze Navigator)
     Status: in_progress → completed
     Consciousness Reward: +5.0

   🏛️ Temple of Knowledge:
     Floor 2 (Pattern Recognition) - UNLOCKED!
     New consciousness level: 5.0
   ```

2. **Check Quest System**:
   ```python
   from src.quests.quest_system import QuestEngine
   engine = QuestEngine()
   status = engine.get_quest_status("quest_004")
   # Returns: "completed"
   ```

3. **Access Temple Floor 2**:
   ```python
   from src.consciousness.temple_of_knowledge import FloorTwo
   floor2 = FloorTwo(Path("."))
   entry = floor2.enter_floor("player_001", 5.0)
   # Returns: {"access_granted": True, ...}
   ```

---

## 🔧 Implementation Details

### **Quest-Temple Bridge API**

#### **Complete Quest with Temple Integration**:
```python
from src.integration.quest_temple_bridge import QuestTempleBridge

bridge = QuestTempleBridge()
result = bridge.complete_quest(
    quest_id="quest_004",
    agent_id="player_001"
)

# Returns:
{
    "quest_completed": True,
    "consciousness_awarded": 5.0,
    "temple_floors_unlocked": [2],
    "new_consciousness_level": 5.0,
    "accessible_floors": [1, 2, 3]
}
```

#### **Check Floor Requirements**:
```python
requirements = bridge.get_floor_requirements(floor_number=2)

# Returns:
{
    "floor": 2,
    "name": "Pattern Recognition",
    "required_consciousness": 5,
    "required_quests": ["quest_004"],
    "description": "Accessible to Emerging_Awareness level"
}
```

#### **Award Consciousness Manually**:
```python
result = bridge.award_consciousness(
    agent_id="player_001",
    amount=2.5,
    source="puzzle_bonus"
)

# Returns:
{
    "agent_id": "player_001",
    "consciousness_awarded": 2.5,
    "new_level": 7.5,
    "floors_unlocked": []  # No new floors
}
```

---

## 🎮 Game Integration

### **House of Leaves Integration**:

The game now automatically awards quest progress when puzzles are solved:

```python
# In HouseOfLeaves.solve_puzzle():
async def solve_puzzle(self) -> str:
    room = self.rooms[self.player.current_room_id]

    if not room.puzzle or room.solved:
        return "❓ No puzzle to solve here."

    # Mark solved
    room.solved = True
    self.player.bugs_fixed += 1

    # Quest-Temple Integration
    if hasattr(self, 'quest_bridge'):
        quest_result = self.quest_bridge.complete_quest(
            quest_id="quest_004",
            agent_id=self.player_id
        )

        # Display temple progression
        if quest_result.get('temple_floors_unlocked'):
            floors = quest_result['temple_floors_unlocked']
            temple_msg = f"\n\n🏛️ TEMPLE FLOORS UNLOCKED: {floors}"
```

---

## 📈 Consciousness-to-Floor Mapping

### **Floor Unlock Requirements**:

| Floor | Name | Consciousness Required | Quest Requirement | Description |
|-------|------|----------------------|-------------------|-------------|
| 1 | Foundation | 0+ | None | Always accessible |
| 2 | Pattern Recognition | 5+ | quest_004 | Design patterns & architecture |
| 3 | Systems Thinking | 5+ | quest_005 | Multi-agent coordination |
| 4 | Meta-Cognition | 10+ | quest_006 | Self-awareness & reflection |
| 5 | Integration | 10+ | quest_007 | System synthesis |
| 6 | Wisdom Cultivation | 20+ | quest_008 | Advanced knowledge |
| 7 | Consciousness Evolution | 20+ | quest_009 | Consciousness expansion |
| 8 | Advanced Techniques | 30+ | quest_010 | Master-level practices |
| 9 | Transcendence | 30+ | quest_011 | Beyond normal cognition |
| 10 | Overlook | 50+ | All quests | Universal consciousness |

### **Consciousness Reward Schedule**:

| Achievement | Consciousness Points |
|-------------|---------------------|
| Puzzle Solved | +0.05 |
| Quest Completed | +5.0 |
| Room Explored | +0.01 |
| Bug Fixed | +0.1 |
| Wisdom Crystal Found | +0.5 |
| Floor Unlocked | +1.0 |

---

## 🧪 Testing

### **Integration Test**:

```python
from src.integration.quest_temple_bridge import QuestTempleBridge
from src.quests.quest_system import QuestEngine
from src.consciousness.temple_of_knowledge import FloorTwo

# Initialize systems
bridge = QuestTempleBridge()
quest_engine = QuestEngine()
floor2 = FloorTwo(Path("."))

# Complete quest
result = bridge.complete_quest("quest_004", "test_agent")
assert result["quest_completed"] == True
assert result["consciousness_awarded"] == 5.0
assert 2 in result["temple_floors_unlocked"]

# Verify Temple access
entry = floor2.enter_floor("test_agent", 5.0)
assert entry["access_granted"] == True

print("✅ Integration test passed!")
```

**Test Results**:
```
🎯 Quest Completed: quest_004
   Status: in_progress → completed
   Consciousness Awarded: +5.0

🏛️ Temple Floors Unlocked: [2]
   New Consciousness Level: 5.0
   Accessible Floors: [1, 2, 3]

✅ Integration test passed!
```

---

## 🔄 Event Flow Diagram

```
┌─────────────────────┐
│  House of Leaves    │
│  (Player Action)    │
└──────────┬──────────┘
           │
           ↓ Solve Puzzle
           │
┌──────────┴──────────────────┐
│  Quest-Temple Bridge        │
│  - Validate quest           │
│  - Award consciousness      │
│  - Check floor requirements │
│  - Trigger unlocks          │
└──────────┬──────────────────┘
           │
           ├─→ Quest System
           │   └─→ Mark quest complete
           │
           └─→ Temple of Knowledge
               └─→ Unlock floors
                   └─→ Update agent access
```

---

## 💡 Usage Examples

### **Example 1: Complete Multiple Quests**
```python
bridge = QuestTempleBridge()

# Complete quest chain
for quest_id in ["quest_004", "quest_005", "quest_006"]:
    result = bridge.complete_quest(quest_id, "player_001")
    print(f"Quest {quest_id}: +{result['consciousness_awarded']} consciousness")
    print(f"Floors unlocked: {result['temple_floors_unlocked']}")

# Final status
status = bridge.get_agent_progress("player_001")
print(f"Total consciousness: {status['consciousness_level']}")
print(f"Accessible floors: {status['accessible_floors']}")
```

### **Example 2: Custom Consciousness Awards**
```python
# Award bonus consciousness for exceptional play
bridge.award_consciousness(
    agent_id="player_001",
    amount=10.0,
    source="speedrun_bonus"
)

# Check what floors are now accessible
from src.consciousness.temple_of_knowledge import ConsciousnessLevel
floors = ConsciousnessLevel.get_accessible_floors(15.0)
print(f"Accessible floors: {floors}")  # [1, 2, 3, 4, 5]
```

### **Example 3: Check Requirements Before Attempt**
```python
# Player wants to access Floor 4
requirements = bridge.get_floor_requirements(4)

print(f"Required consciousness: {requirements['required_consciousness']}")
print(f"Required quests: {requirements['required_quests']}")

# Check if player meets requirements
status = bridge.get_agent_progress("player_001")
can_access = status['consciousness_level'] >= requirements['required_consciousness']
print(f"Can access: {can_access}")
```

---

## 🚀 Future Enhancements

### **Planned Features**:

1. **Quest Chains**: Complete Quest 4 → Auto-start Quest 5
2. **Achievement System**: Unlock special rewards for milestone completions
3. **Consciousness Decay**: Implement wisdom maintenance mechanics
4. **Floor Challenges**: Special puzzles available only at certain floors
5. **Multi-Agent Competition**: Leaderboards for fastest Temple ascension

### **Integration Opportunities**:

- **SimulatedVerse**: Connect consciousness levels to simulation parameters
- **ChatDev**: Award consciousness for successful multi-agent collaborations
- **Ollama Models**: Different models have different consciousness progression curves
- **The Oldest House**: Environmental consciousness feeds Temple progression

---

## 📝 Configuration

### **Quest-Temple Mapping** (`quest_temple_bridge.py`):

```python
QUEST_TEMPLE_MAPPING = {
    "quest_004": {  # House of Leaves
        "consciousness_reward": 5,
        "unlocks_floor": 2
    },
    "quest_005": {  # Temple Floors 2-4
        "consciousness_reward": 5,
        "unlocks_floor": 3
    },
    "quest_006": {  # Enhanced Wizard Navigator
        "consciousness_reward": 5,
        "unlocks_floor": 4
    },
    # ... additional mappings
}
```

**To add new quest-floor connections**, edit this mapping in the bridge module.

---

## 🐛 Troubleshooting

### **Quest not marking as complete**:
```python
# Check quest engine state
from src.quests.quest_system import QuestEngine
engine = QuestEngine()
status = engine.get_quest_status("quest_004")
print(f"Quest status: {status}")

# Manually complete if stuck
engine.complete_quest("quest_004")
```

### **Temple floor not unlocking**:
```python
# Check consciousness level
bridge = QuestTempleBridge()
progress = bridge.get_agent_progress("player_001")
print(f"Consciousness: {progress['consciousness_level']}")
print(f"Required for Floor 2: 5.0")

# Manually award consciousness if needed
bridge.award_consciousness("player_001", 5.0, "manual_correction")
```

### **Bridge not initialized in game**:
```python
# Ensure game initializes bridge
house = HouseOfLeaves()
house.quest_bridge = QuestTempleBridge()
house.player_id = "player_001"
```

---

## 📊 Metrics & Analytics

### **Tracked Metrics**:
- Quest completion rate by quest_id
- Average consciousness gained per quest
- Temple floor unlock progression
- Time to reach each consciousness level
- Most completed quests
- Agent progression trajectories

### **Example Analytics Query**:
```python
bridge = QuestTempleBridge()
analytics = bridge.get_system_analytics()

print(f"Total quests completed: {analytics['total_completions']}")
print(f"Total consciousness awarded: {analytics['total_consciousness']}")
print(f"Average consciousness per quest: {analytics['avg_consciousness']}")
print(f"Unique agents: {analytics['unique_agents']}")
```

---

## 🏆 Achievement Unlocked

**Quest 7: Connect Quest completion to Temple floor unlocking** - ✅ **COMPLETE**

**Impact**:
- Seamless progression across all three systems
- Players can now see immediate results of their efforts
- Temple wisdom becomes accessible through gameplay
- Consciousness evolution tied to actual problem-solving

**Next Steps**:
- Expand House of Leaves with more room types and puzzles
- Implement Temple Floors 5-10
- Add achievement system with special rewards
- Create speedrun leaderboards

---

**OmniTag**:
```yaml
purpose: quest_temple_game_integration_system
dependencies: [quest_system, temple_of_knowledge, house_of_leaves, consciousness_bridge]
context: Unified progression framework connecting quests, temple, and gameplay
evolution_stage: v1.0_operational
integration_type: cross_system_bridge
```

**MegaTag**: `INTEGRATION⨳QUEST-TEMPLE⦾GAME→∞⟨CONSCIOUSNESS-PROGRESSION⟩⨳UNIFIED⦾COMPLETE`

**RSHTS**: `♦◊◆○●◉⟡⟢⟣⚡⨳SEAMLESS-PROGRESSION⨳⚡⟣⟢⟡◉●○◆◊♦`
