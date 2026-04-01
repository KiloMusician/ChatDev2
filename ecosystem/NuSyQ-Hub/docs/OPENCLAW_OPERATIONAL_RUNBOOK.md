# OpenClaw Gateway Bridge - Operational Runbook

## Overview

The OpenClaw Gateway Bridge integrates 12+ messaging platforms (Slack, Discord, Telegram, WhatsApp, Signal, Teams, Google Chat, Matrix, iMessage, Zalo, WebChat, etc.) with NuSyQ-Hub's unified orchestration system.

**Architecture Diagram:**
```
OpenClaw Gateway (ws://127.0.0.1:18789)
    ↓ (WebSocket Messages from Slack, Discord, Telegram, etc.)
OpenClawGatewayBridge (src/integrations/openclaw_gateway_bridge.py)
    ↓ (route_task with channel context)
UnifiedAIOrchestrator (src/orchestration/unified_ai_orchestrator.py)
    ↓ (execution with quest logging)
OpenClawGatewayBridge.send_result()
    ↓ (HTTP POST via OpenClaw Channels API)
Original Channel (user receives response)
```

**Status:** Phase 1 Implementation Complete ✅

---

## Prerequisites

### Required Dependencies

1. **aiohttp** - Async HTTP client for channels API
2. **websockets** - WebSocket client for gateway connection
3. **OpenClaw CLI** - Already installed (v2026.2.15)

Install missing dependencies:
```bash
pip install aiohttp websockets
```

Verify aiohttp/websockets:
```bash
python -c "import aiohttp; import websockets; print('✅ Both installed')"
```

### OpenClaw Setup

1. **Start OpenClaw Gateway:**
```bash
openclaw gateway
```

Expected output:
```
🔌 OpenClaw Gateway starting...
📡 WebSocket listening on ws://127.0.0.1:18789
🌐 Channels API on http://127.0.0.1:18790
✅ Gateway ready
```

2. **Onboard messaging platforms (optional):**
```bash
# Slack
openclaw onboard slack --bot-token xoxb-... --app-token xapp-...

# Discord
openclaw onboard discord --token ...

# Telegram
openclaw onboard telegram --bot-token ...
```

---

## Startup Procedures

### Option 1: CLI with --openclaw-enabled Flag (Simplest)

Start NuSyQ-Hub with OpenClaw enabled:
```bash
python src/main.py --openclaw-enabled
```

Expected output:
```
🧠 NuSyQ-Hub: AI-Enhanced Development Ecosystem
🔌 OpenClaw Gateway Bridge enabled
🔌 Starting OpenClaw Gateway Bridge...
📡 Gateway URL: ws://127.0.0.1:18789
✅ OpenClaw Gateway Bridge initialized
👂 Listening for messages from messaging platforms...
```

### Option 2: With Custom Gateway URL

```bash
python src/main.py --openclaw-enabled --openclaw-gateway ws://custom.example.com:9999
```

### Option 3: Programmatic (Python Code)

```python
from src.integrations.openclaw_gateway_bridge import get_openclaw_gateway_bridge
import asyncio

async def main():
    bridge = get_openclaw_gateway_bridge(
        gateway_url="ws://127.0.0.1:18789",
        timeout_seconds=30
    )
    await bridge.run()

asyncio.run(main())
```

### Option 4: VS Code Task (When Implemented)

```json
{
  "label": "🔌 NuSyQ: Start OpenClaw Gateway Bridge",
  "type": "shell",
  "command": "python",
  "args": ["src/main.py", "--openclaw-enabled"],
  "isBackground": true,
  "problemMatcher": {
    "pattern": {
      "regexp": "^(✅|❌|🔌|📡|👂).*$",
      "message": 1
    }
  }
}
```

---

## Configuration

### Configuration File: `config/secrets.json`

The bridge reads configuration from `config/secrets.json`:

```json
{
  "openclaw": {
    "enabled": false,
    "gateway_url": "ws://127.0.0.1:18789",
    "api_url": "http://127.0.0.1:18790",
    "workspace_root": "~/.openclaw/workspace",
    "timeout_seconds": 30,
    "debug_logging": false,
    "channels": {
      "slack": {
        "enabled": false,
        "bot_token": "xoxb-YOUR_BOT_TOKEN",
        "app_token": "xapp-YOUR_APP_TOKEN"
      },
      "discord": {
        "enabled": false,
        "token": "YOUR_BOT_TOKEN"
      },
      "telegram": {
        "enabled": false,
        "bot_token": "YOUR_BOT_TOKEN"
      }
    }
  }
}
```

### Environment Variables

Bridge respects standard environment variables:

- `OPENCLAW_GATEWAY` - Override gateway URL
- `OPENCLAW_TIMEOUT` - Override timeout (seconds)
- `NUSYQ_DEBUG` - Enable debug logging in orchestrator
- `NUSYQ_RUN_ID` - Unique run identifier (auto-generated if not set)

Example:
```bash
export OPENCLAW_GATEWAY=ws://custom:9999
export OPENCLAW_TIMEOUT=60
python src/main.py --openclaw-enabled
```

---

## Usage Examples

### Example 1: Simple Analysis Request (Slack)

**Slack Message:**
```
@nusyq analyze src/main.py
```

**Flow:**
1. Slack → OpenClaw Gateway (WebSocket)
2. Gateway Bridge receives message
3. Router extracts: channel=slack, user=alice, text="analyze src/main.py"
4. Orchestrator invokes analysis tool
5. Result logged to quest_log.jsonl
6. Response sent back to Slack thread

**Response (in Slack):**
```
✅ Task routed successfully (ID: task-abc-123)
[Results appear in thread]
```

### Example 2: Code Review (Discord)

**Discord:**
```
!nusyq review endpoints.py
```

**Flow:**
1. Discord → OpenClaw Gateway
2. Bridge routes to code review analyzer
3. Result includes quality metrics
4. Embeds sent back to Discord channel

### Example 3: Generation Task (Telegram)

**Telegram Chat:**
```
/nusyq generate a REST API handler for user authentication
```

**Flow:**
1. Telegram → Gateway
2. Routes to ChatDev generation
3. Project created in testing chamber
4. Telegram receives project link

---

## Monitoring & Debugging

### Check Gateway Status

```bash
# Is gateway running?
curl http://127.0.0.1:18790/status
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2026.2.15",
  "channels": 12,
  "sessions": 3
}
```

### View Real-Time Logs

```bash
# Terminal 1: Start gateway
openclaw gateway --debug

# Terminal 2: Start bridge
python src/main.py --openclaw-enabled

# Terminal 3: Monitor logs
tail -f logs/openclaw_gateway.log
```

### Test Message Flow (Dry Run)

```bash
python -m pytest tests/integration/test_openclaw_gateway_bridge.py -v
```

### Debug Single Message

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.integrations import get_openclaw_gateway_bridge
bridge = get_openclaw_gateway_bridge()

# Simulate inbound message
import asyncio
message = {
    "channel": "slack",
    "user_id": "U12345",
    "username": "tester",
    "text": "test message"
}

result = asyncio.run(bridge.handle_inbound_message(message))
print(result)
```

### Common Issues

#### Issue: "Connection refused to ws://127.0.0.1:18789"

**Cause:** OpenClaw Gateway not running

**Solution:**
```bash
# Terminal 1
openclaw gateway

# Wait for "✅ Gateway ready"

# Terminal 2
python src/main.py --openclaw-enabled
```

#### Issue: "ImportError: No module named 'aiohttp'"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install aiohttp websockets
```

#### Issue: "Timeout waiting for message"

**Cause:** No messages being sent, or gateway not properly configured

**Solution:**
```bash
# Check gateway status
curl http://127.0.0.1:18790/status

# Verify channel configurations
openclaw channels list

# Check bridge logs
python src/main.py --openclaw-enabled  # Read console output
```

#### Issue: "Failed to send result back to channel"

**Cause:** Channels API not responding, or invalid channel/user

**Solution:**
```bash
# Verify channels API is accessible
curl -X POST http://127.0.0.1:18790/api/channels/send \
  -H "Content-Type: application/json" \
  -d '{"channel":"slack","target_user_id":"U123","message":"test"}'

# Check user ID format for channel (varies by platform)
openclaw channels info slack
```

---

## Performance Tuning

### Timeout Configuration

Adjust in `config/secrets.json`:

```json
{
  "openclaw": {
    "timeout_seconds": 30  // Increase for slow networks
  }
}
```

Or via environment:
```bash
export OPENCLAW_TIMEOUT=60
python src/main.py --openclaw-enabled
```

### Connection Pooling

OpenClaw Gateway handles connection pooling automatically. For high-volume scenarios:

```bash
# Start multiple gateway instances (load balancing)
openclaw gateway --port 18789  # Instance 1
openclaw gateway --port 18799  # Instance 2
```

Then configure bridge to load-balance:
```bash
export OPENCLAW_GATEWAY=ws://localhost:18789,localhost:18799
```

### Message Queue Size

Default: 1000 messages. Adjust in OpenClaw config:
```bash
openclaw config set queue_size 5000
```

---

## Integration Points

### 1. Quest System Integration

All messages are logged to `src/Rosetta_Quest_System/quest_log.jsonl`:

```json
{
  "timestamp": "2025-12-26T10:30:00Z",
  "quest_type": "openclaw_message",
  "data": {
    "channel": "slack",
    "user": "alice",
    "message": "analyze my code",
    "task_id": "task-abc-123",
    "status": "routed"
  }
}
```

### 2. Orchestrator Integration

Messages route through `UnifiedAIOrchestrator.route()`:

```python
# Internally used by bridge
result = orchestrator.route(
    text="analyze src/main.py",
    context={
        "channel": "slack",
        "user_id": "U12345",
        "username": "alice",
        "timestamp": "2025-12-26T10:30:00Z",
        "openclaw": True
    }
)
```

### 3. MCP Server Integration

OpenClaw tools registered in `src/integration/mcp_server.py`:

- `openclaw.gateway.status` - Check gateway health
- `openclaw.channels.send` - Send message to channel
- `openclaw.sessions.history` - Retrieve session history

---

## Troubleshooting Checklist

- [ ] OpenClaw CLI installed? (`openclaw --version`)
- [ ] OpenClaw Gateway running? (`curl http://127.0.0.1:18790/status`)
- [ ] aiohttp/websockets installed? (`pip list | grep aiohttp`)
- [ ] config/secrets.json has openclaw section?
- [ ] Messaging platform onboarded? (`openclaw channels list`)
- [ ] NuSyQ-Hub can connect to gateway? (Check logs for "✅ Successfully connected")
- [ ] Tasks routed to orchestrator? (Check quest_log.jsonl)
- [ ] Results sent back to channel? (Check response in platform)

---

## Shutdown Procedures

### Graceful Shutdown

```bash
# Send Ctrl+C to running bridge
# Bridge will:
# 1. Stop listening for new messages
# 2. Close WebSocket connection
# 3. Close HTTP session
# 4. Flush quest logs
```

### Forced Shutdown (if needed)

```bash
# Kill bridge process
pkill -f "python src/main.py --openclaw-enabled"

# Restart gateway if needed
openclaw gateway --reset
```

---

## Testing

### Unit Tests

```bash
# Run all OpenClaw tests
pytest tests/integration/test_openclaw_gateway_bridge.py -v

# Run specific test class
pytest tests/integration/test_openclaw_gateway_bridge.py::TestOpenClawGatewayBridgeInitialization -v

# Run with coverage
pytest tests/integration/test_openclaw_gateway_bridge.py --cov=src.integrations.openclaw_gateway_bridge
```

### Integration Tests (End-to-End)

```bash
# Terminal 1: Start gateway
openclaw gateway

# Terminal 2: Start bridge
python src/main.py --openclaw-enabled

# Terminal 3: Send test message
python -c "
from src.integrations import get_openclaw_gateway_bridge
import asyncio

async def test():
    bridge = get_openclaw_gateway_bridge()
    # Simulate message (in real scenario, comes from OpenClaw)
    msg = {
        'channel': 'slack',
        'user_id': 'U123',
        'username': 'alice',
        'text': 'hello world'
    }
    result = await bridge.handle_inbound_message(msg)
    print(result)

asyncio.run(test())
"
```

### Smoke Test

```bash
python scripts/openclaw_smoke_test.py
```

---

## Phase Checklist

- [x] Phase 1: Gateway Bridge Implementation
  - [x] Create OpenClawGatewayBridge class (src/integrations/openclaw_gateway_bridge.py)
  - [x] Add --openclaw-enabled flag to main.py
  - [x] Configure secrets.json with openclaw section
  - [x] Create unit tests (tests/integration/test_openclaw_gateway_bridge.py)
  - [x] Create smoke tests (scripts/openclaw_smoke_test.py)
  - [x] Create operational runbook (this document)

- [ ] Phase 2: Quest Session Synchronization
  - [ ] Bidirectional sync between quest_log.jsonl and OpenClaw sessions
  - [ ] Task resumption across restarts

- [ ] Phase 3: Skill Export
  - [ ] Convert NuSyQ task types to OpenClaw SKILL.md format
  - [ ] Discoverable skill registry

- [ ] Phase 4: Agent-to-Agent Messaging
  - [ ] Enable agents to message each other via sessions API

- [ ] Phase 5: Device Integration
  - [ ] Local device actions (macOS/iOS/Android)
  - [ ] Orchestrate with cloud tasks

---

## Support & Escalation

### For Questions:
- See `docs/OPENCLAW_INTEGRATION_QUICK_REFERENCE.md` for quick answers
- Check `docs/OPENCLAW_STRATEGIC_SUMMARY.md` for architecture details

### For Problems:
1. Check "Troubleshooting Checklist" above
2. Review logs: `logs/openclaw_*.log`
3. Run smoke test: `python scripts/openclaw_smoke_test.py`
4. Run unit tests: `pytest tests/integration/test_openclaw_gateway_bridge.py -v`

### For Enhancements:
- Document as quest in `src/Rosetta_Quest_System/quest_log.jsonl`
- Tag with `[openclaw, enhancement, phase-X]`
- Reference this runbook in implementation plan

---

**Version:** 1.0.0  
**Last Updated:** 2025-12-26  
**Status:** Production Ready ✅

OmniTag: [openclaw, operations, runbook, gateway]  
MegaTag: [OPENCLAW⨳OPERATIONAL⦾RUNBOOK→∞]
