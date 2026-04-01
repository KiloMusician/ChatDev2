# Test Chamber - Agent Sandbox Harness
## BOSS G: ChatDev Availability & Test Chamber

### Purpose
Safe testing environment for ChatDev agents with real task validation and receipt emission.

### Capabilities Matrix

| Agent | Online Status | Offline Capable | Skills | Pipeline |
|-------|---------------|-----------------|--------|----------|
| SAGE-PILOT | ⚠️ LLM-Limited | ✅ Core Loops | orchestration, receipts, track_selection | primary |
| Librarian | ⚠️ LLM-Limited | ✅ File Ops | indexing, cataloging, rosetta_stone | knowledge |
| Artificer | ⚠️ LLM-Limited | ✅ Path Ops | import_rewriting, file_moves, godot_scenes | transformation |
| Alchemist | ⚠️ LLM-Limited | ✅ Static Analysis | duplicate_detection, schema_reconcile | merge |
| Janitor | ✅ Full | ✅ No LLM | console_cleanup, json_sanitize, todo_surgery | hygiene |
| Navigator | ⚠️ LLM-Limited | ✅ Config Ops | breath_cycles, cascade_triggers | orchestration |
| Raven | ⚠️ LLM-Limited | ✅ Analysis | anomaly_detection, error_hunting, drift_monitoring | analysis |
| Culture-Ship | ⚠️ LLM-Limited | ✅ Momentum | cascade_coordination, flow_detection | coordination |

### Current LLM Status (BOSS G Assessment)
- **Ollama**: UNREACHABLE (fetch failed)
- **OpenAI**: RATE LIMITED (429 errors)  
- **Fallback Mode**: OFFLINE OPERATIONS ACTIVE
- **Degraded Capabilities**: Marked as offline-first with static analysis only

### Test Chamber Protocols
1. **Sandbox Tasks**: Non-destructive file operations only
2. **Receipt Emission**: Every test generates proof receipts  
3. **Capability Verification**: Online vs offline functionality clearly separated
4. **No Green Light Without Proof**: LLM unavailability properly flagged

### Agent Health Status
```json
{
  "total_agents": 14,
  "operational_offline": 8,
  "llm_dependent": 6,  
  "fully_degraded": 0,
  "council_bus_status": "active",
  "test_chamber_ready": true
}
```