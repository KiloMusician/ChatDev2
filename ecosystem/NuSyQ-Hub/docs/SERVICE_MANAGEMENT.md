# NuSyQ-Hub Service Management

## 🎯 Overview

This document describes the critical services in NuSyQ-Hub, how to manage them, and how to verify they're working correctly.

## 🚀 Quick Start

### Start All Services

```powershell
python scripts/service_manager.py start --skip-optional
```

### Check Service Status

```powershell
python scripts/service_manager.py status
```

### Stop All Services

```powershell
python scripts/service_manager.py stop
```

### Restart Services

```powershell
python scripts/service_manager.py restart --skip-optional
```

## 📊 Critical Services

### 1. PU Queue Processor
- **Purpose**: Processes Processing Units (PUs) from the unified queue
- **Status**: ✅ Working
- **Log**: `data/service_logs/pu_queue.log`
- **Mode**: Simulated (safe mode, doesn't make actual changes)

### 2. Cross Ecosystem Sync
- **Purpose**: Syncs quest logs across NuSyQ-Hub, SimulatedVerse, and NuSyQ repos
- **Status**: ✅ Working
- **Log**: `data/service_logs/cross_sync.log`
- **Frequency**: Every 5 minutes

### 3. Guild Board Renderer
- **Purpose**: Auto-renders the guild board to `docs/GUILD_BOARD.md`
- **Status**: ⚠️  May need attention (log empty)
- **Log**: `data/service_logs/guild_renderer.log`
- **Frequency**: Every 10 minutes

### 4. Autonomous Monitor (Optional)
- **Purpose**: Monitors repository for changes and triggers audits
- **Status**: Not started by default (use without `--skip-optional`)
- **Log**: `data/service_logs/autonomous_monitor.log`

## 🔧 Fixes Applied

### OpenTelemetry Connection Errors Fixed

**Problem**: Services were trying to connect to OpenTelemetry collector at `localhost:4318` but it wasn't running, causing connection errors.

**Solution**: Service manager now automatically disables OpenTelemetry if no collector is configured:
```python
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["OTEL_TRACES_EXPORTER"] = "none"
```

**Result**: No more connection errors in logs. ✅

### Service Architecture Created

**Problem**: No unified way to start/stop services.

**Solution**: Created `scripts/service_manager.py` that:
- Starts services in separate console windows (Windows)
- Tracks running services in `state/services/services.json`
- Captures logs to `data/service_logs/`
- Provides status checking and clean shutdown

## 📝 Service Logs

All service logs are stored in:
```
data/service_logs/
├── pu_queue.log          # PU processing activity
├── cross_sync.log        # Cross-repo sync activity
├── guild_renderer.log    # Board rendering activity
└── autonomous_monitor.log # Repository monitoring (if enabled)
```

## 🧪 Verification

Run the verification script to test all services:

```powershell
python scripts/verify_services.py
```

This tests:
1. ✅ Terminal routing (messages reach correct terminals)
2. ✅ PU Queue functionality
3. ✅ Cross Ecosystem Sync connectivity
4. ✅ Service status tracking
5. ⚠️  Log file generation

## 🎯 Terminal System

The terminal system is now fully operational:

### Terminal Log Files
- Located in: `data/terminal_logs/`
- Format: JSON lines (NDJSON)
- Watchers: PowerShell scripts in `data/terminal_watchers/`

### Available Terminals
- 🤖 **Claude** - Claude Code agent output
- 🧩 **Copilot** - GitHub Copilot suggestions
- 🧠 **Codex** - OpenAI Codex transformations
- 🏗️ **ChatDev** - Multi-agent team coordination
- 🏛️ **AI Council** - Consensus decisions
- 🔗 **Intermediary** - Cross-agent communication
- 🔥 **Errors** - All error output
- 💡 **Suggestions** - Recommendations
- ✅ **Tasks** - Task execution
- 🧪 **Tests** - Test execution
- 🎯 **Zeta** - Autonomous cycles
- 🤖 **Agents** - General agent coordination
- 📊 **Metrics** - Health and performance
- ⚡ **Anomalies** - Unusual events
- 🔮 **Future** - Planned features
- 🏠 **Main** - General output

### Watch Terminals in VS Code

Use VS Code tasks to watch terminals in real-time:
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Select "Watch All Agent Terminals" or "Watch ALL Terminals (Full System)"

Or run watchers manually:
```powershell
pwsh -NoExit -File data/terminal_watchers/watch_claude_terminal.ps1
pwsh -NoExit -File data/terminal_watchers/watch_tasks_terminal.ps1
# etc...
```

## 📦 Service State

Service state is stored in:
```
state/services/services.json
```

Contains:
- Service PIDs
- Start timestamps
- Log file locations
- Status information

## 🐛 Troubleshooting

### Service Won't Start

1. Check if port/resource is in use
2. Review the service log file
3. Try stopping and restarting:
   ```powershell
   python scripts/service_manager.py restart --skip-optional
   ```

### Service Crashed

1. Check the log file in `data/service_logs/`
2. Look for Python tracebacks or error messages
3. Restart the service

### Terminal Not Showing Output

1. Verify service is running: `python scripts/service_manager.py status`
2. Check terminal log file exists and has content
3. Restart the PowerShell watcher for that terminal

### OpenTelemetry Errors Still Appearing

If you still see OpenTelemetry errors:
1. Set environment variable before running:
   ```powershell
   $env:OTEL_SDK_DISABLED = "true"
   ```
2. Or start a trace collector service at `localhost:4318`

## 🎨 Making Services Write to Terminals

To make your code write to terminals, use the terminal output utilities:

```python
from src.utils.terminal_output import to_tasks, to_zeta, to_claude, to_errors

# Send messages to specific terminals
to_tasks("Processing quest #42...")
to_zeta("Autonomous cycle complete")
to_claude("Analysis finished")
to_errors("ERROR: Connection failed")
```

## 🔮 Future Improvements

1. **Guild Renderer**: Fix empty log issue, ensure it runs successfully
2. **Service Health Checks**: Add periodic health pings
3. **Auto-Restart**: Automatically restart crashed services
4. **Web Dashboard**: Create a web interface for service management
5. **Metrics Collection**: Track service performance metrics
6. **Alert System**: Notify when services fail

## 📚 Related Documentation

- [Terminal System Guide](LIVE_TERMINAL_ROUTING_GUIDE.md)
- [Guild Board Documentation](../config/orchestration_defaults.json)
- [Service Configuration](../config/ecosystem_defaults.json)

## ✅ Success Criteria

Services are working correctly when:
- ✅ All services show "Running" in status
- ✅ Service logs are being written
- ✅ Terminal logs receive messages
- ✅ No OpenTelemetry connection errors
- ✅ Verification script passes 4/5 tests minimum

---

**Last Updated**: 2026-01-14

**Status**: Services operational with OpenTelemetry disabled
