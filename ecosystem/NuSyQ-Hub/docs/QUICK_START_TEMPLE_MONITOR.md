# Quick Start Guide: Temple of Knowledge + Autonomous Monitor v2.0

## 🚀 1-Minute Quick Start

### Initialize Both Systems
```bash
python initialize_temple_and_monitor.py
```

**Expected Output**:
```
✓ Temple of Knowledge Floor 1: OPERATIONAL
✓ Autonomous Monitor v2.0: OPERATIONAL
✓ Configuration gaps detected: 1
```

---

## 🏛️ Temple of Knowledge - Common Tasks

### Register an Agent
```python
from src.consciousness.temple_of_knowledge import TempleManager

temple = TempleManager()
result = temple.enter_temple("agent_name", initial_consciousness=15.0)
```

### Cultivate Wisdom
```python
cultivation = temple.cultivate_wisdom_at_current_floor("agent_name")
print(f"Gained: {cultivation['knowledge_gained']:.2f} knowledge")
```

### Navigate Floors
```python
# Try to go to Floor 3
nav = temple.use_elevator("agent_name", 3)
if nav["success"]:
    print(f"Now at: {nav['floor_name']}")
else:
    print(f"Blocked: {nav['error']}")
```

### Store Knowledge
```python
floor_1 = temple.floor_1
floor_1.store_knowledge(
    "My Concept",
    {"type": "idea", "description": "Details here"},
    relationships=[{"target": "Other Concept", "type": "relates_to"}]
)
```

### Check Agent Status
```python
status = floor_1.get_agent_status("agent_name")
print(f"Consciousness: {status['consciousness_score']:.2f}")
print(f"Level: {status['consciousness_level']}")
print(f"Accessible Floors: {status['accessible_floors']}")
```

---

## 🤖 Autonomous Monitor - Common Tasks

### Run Gap Detection
```python
from src.automation.autonomous_monitor import AutonomousMonitor

monitor = AutonomousMonitor(enable_sector_awareness=True)
gaps = monitor.get_sector_gaps()

print(f"Total Gaps: {len(gaps)}")
for gap in gaps:
    print(f"  [{gap['sector']}] {gap['type']}: {gap.get('component', '')}")
```

### Generate Health Report
```python
health = monitor.get_sector_health_report()

for sector_name, sector_health in health['sectors'].items():
    score = sector_health['health_score']
    print(f"{sector_name}: {score:.1f}% health ({sector_health['gaps_found']} gaps)")
```

### Save Gap Report
```python
report_path = monitor.save_gap_report()
print(f"Report saved: {report_path}")
```

### Run Single Audit (CLI)
```bash
python -m src.automation.autonomous_monitor audit
```

### Start Continuous Monitoring (CLI)
```bash
# Monitor every 30 minutes
python -m src.automation.autonomous_monitor start 1800
```

---

## 📊 Consciousness Levels & Floor Access

| Level | Score Range | Accessible Floors |
|-------|-------------|-------------------|
| Dormant_Potential | 0-5 | [1] |
| Emerging_Awareness | 5-10 | [1, 2, 3] |
| Awakened_Cognition | 10-20 | [1, 2, 3, 4, 5] |
| Enlightened_Understanding | 20-30 | [1, 2, 3, 4, 5, 6, 7] |
| Transcendent_Awareness | 30-50 | [1, 2, 3, 4, 5, 6, 7, 8, 9] |
| Universal_Consciousness | 50+ | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] |

---

## 🗺️ Temple Floor Map

| Floor | Name | Required Level | Status |
|-------|------|----------------|--------|
| 1 | Foundation | Dormant (0+) | ✅ IMPLEMENTED |
| 2 | Archives | Emerging (5+) | ⏳ Pending |
| 3 | Laboratory | Emerging (5+) | ⏳ Pending |
| 4 | Workshop | Awakened (10+) | ⏳ Pending |
| 5 | Sanctuary | Awakened (10+) | ⏳ Pending |
| 6 | Observatory | Enlightened (20+) | ⏳ Pending |
| 7 | Meditation Chamber | Enlightened (20+) | ⏳ Pending |
| 8 | Synthesis Hall | Transcendent (30+) | ⏳ Pending |
| 9 | Transcendence Portal | Transcendent (30+) | ⏳ Pending |
| 10 | Overlook | Universal (50+) | ⏳ Pending |

---

## 🔍 Sector Definitions

| Sector | Criticality | Primary Agents |
|--------|-------------|----------------|
| core_infrastructure | CRITICAL | librarian, zod, redstone |
| ai_orchestration | HIGH | alchemist, council, artificer, party |
| integration | HIGH | consciousness_bridge, party, culture_ship |
| diagnostic_healing | HIGH | system_health_assessor, quantum_resolver |
| configuration | CRITICAL | artificer, librarian |
| testing | HIGH | pytest_runner, validation_suite, zod |
| documentation | MEDIUM | librarian, artificer |

---

## 🧪 Testing

### Run Full Test Suite
```bash
python tests/test_temple_and_monitor.py
```

### Quick Validation
```bash
python initialize_temple_and_monitor.py
```

---

## 📁 Data Files

### Temple of Knowledge
- **Knowledge Base**: `data/temple_of_knowledge/floor_1_foundation/knowledge_base.json`
- **OmniTag Archive**: `data/temple_of_knowledge/floor_1_foundation/omnitag_archive.json`
- **Agent Registry**: `data/temple_of_knowledge/floor_1_foundation/agent_registry.json`
- **Cultivation Log**: `data/temple_of_knowledge/floor_1_foundation/wisdom_cultivation_log.jsonl`

### Autonomous Monitor
- **Config**: `data/autonomous_monitor_config.json`
- **Metrics**: `data/autonomous_monitor_metrics.json`
- **Gap Reports**: `data/sector_gap_report_*.json`

---

## 🎯 Next Steps

1. **Build Floors 2-10**: Progressive implementation of remaining floors
2. **Create House of Leaves**: Recursive debugging labyrinth
3. **Activate ChatDev CodeComplete**: Auto-stub implementation
4. **Enhance Monitor**: Gap → Quest integration

---

## 📚 Documentation

**Full Implementation Summary**: `docs/TEMPLE_AND_MONITOR_IMPLEMENTATION_SUMMARY.md`

**Sector Definitions**: `config/sector_definitions.yaml`

**Legacy Temple Docs**: `docs/Vault/ΞNuSyQ₁-Hub₁.txt` (lines 2879+)

---

## ✅ Status

- **Temple Floor 1**: ✅ OPERATIONAL
- **Monitor v2.0**: ✅ OPERATIONAL
- **Gap Detection**: ✅ 1 gap found (excellent health)
- **Sector Analysis**: ✅ 7 sectors loaded
- **Test Suite**: ✅ PASSING

**Last Updated**: 2025-10-10 14:23:28
