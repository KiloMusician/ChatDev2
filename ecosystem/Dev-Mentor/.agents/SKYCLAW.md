# SkyClaw Scanner — DevMentor Integration Guide

## What SkyClaw Monitors in This Project
SkyClaw is the anomaly detection and filesystem scanner for the Terminal Depths ecosystem.

### Scan Targets
```yaml
scan_targets:
  filesystem:
    - path: "app/game_engine/commands.py"
      check: "no duplicate _cmd_ method definitions"
      alert_on: "duplicate def _cmd_"
    - path: "app/game_engine/filesystem.py"
      check: "VFS entries are valid Python dicts"
    - path: "state/"
      check: "SQLite DB health"
      alert_on: "journal mode WAL corruption"
  
  api_health:
    - endpoint: "http://localhost:5000/api/health"
      expected_status: 200
      check_interval: 30s
    - endpoint: "http://localhost:5000/api/serena/status"
      expected_keys: ["embedding_index_size", "indexed_files"]
  
  game_state:
    - path: "state/agent_memory.db"
      check: "no pending tasks > 100"
      check: "no ghost sessions (stale > 2h)"
```

### Alert Thresholds
```yaml
alerts:
  critical:
    - commands_py_syntax_error: "AST parse fails"
    - server_down: "health endpoint unreachable > 60s"
    - db_corrupt: "SQLite integrity check fails"
  
  warning:
    - large_session_count: "> 50 active sessions"
    - llm_cache_full: "llm_cache table > 10000 rows"
    - stale_story_beats: "session with > 1000 beats (possible corruption)"
  
  info:
    - new_command_added: "git diff shows new _cmd_ method"
    - vfs_expanded: "filesystem.py grew > 100 lines"
    - backlog_progress: "FEATURE_BACKLOG.md [x] count increased"
```

### SkyClaw Integration Endpoints
```bash
# Health check
GET http://localhost:5000/api/health

# Session registry
GET http://localhost:5000/api/admin/status

# Serena index status
GET http://localhost:5000/api/serena/status

# Game metrics (via MCP)
POST http://localhost:5000/mcp
{"method": "tools/call", "params": {"name": "get_story_progress", "arguments": {"session_id": "monitor"}}}
```

### Anomaly Files to Watch (in-game)
The game itself generates anomaly alerts in:
- `/var/anomalies/` — SCP-format anomaly reports
- `/var/log/` — system and agent log files
- `/var/glitch/` — glitch incident reports

SkyClaw can subscribe to these via the Redis pub/sub channel `chimera.alerts` (if Docker stack is running).
