# OpenClaw Integration Quick Reference

**Purpose:** Fast lookup for how OpenClaw capabilities map to NuSyQ's existing infrastructure  
**Audience:** Developers implementing integration  
**Last Updated:** February 16, 2026

---

## 1. Architecture Alignment (At a Glance)

### Current NuSyQ Flow
```
User Input (Agent conversation)
    ↓
agent_task_router.py: route_task()
    ↓
UnifiedAIOrchestrator.execute_task()
    ├─ Ollama (local LLM)
    ├─ ChatDev (multi-agent development)
    ├─ Consciousness Bridge (semantic awareness)
    └─ Quantum Resolver (self-healing)
    ↓
quest_log.jsonl (persistent result)
```

### With OpenClaw Bridge
```
Message from Slack/Discord/Telegram
    ↓ [OpenClaw Gateway]
openclaw_gateway_bridge.py: handle_inbound_message()
    ↓
route_task() [same as above]
    ↓
quest_log.jsonl + Channel response
```

---

## 2. File Mapping: NuSyQ ↔ OpenClaw

| NuSyQ File | Purpose | OpenClaw Equivalent | Integration File |
|------------|---------|-------------------|-----------------|
| `src/tools/agent_task_router.py` | Natural language → task routing | Gateway RPC methods | `src/integrations/openclaw_gateway_bridge.py` |
| `src/orchestration/unified_ai_orchestrator.py` | Multi-AI dispatch | Session + tool execution | (same bridge) |
| `src/Rosetta_Quest_System/quest_engine.py` | Task persistence + queuing | Sessions + history | `src/integrations/quest_session_bridge.py` |
| `src/integration/consciousness_bridge.py` | Semantic memory | SOUL.md + AGENTS.md | (personality bridge) |
| `src/integration/mcp_server.py` | MCP tool registry | Gateway tools registration | (extend MCPServer) |
| `src/system/enhanced_terminal_ecosystem.py` | Terminal channels (internal) | Message queues | (logging sink) |
| `config/secrets.json` | Configuration secrets | ~/.openclaw/openclaw.json | (secrets sync layer) |
| `src/Rosetta_Quest_System/quest_log.jsonl` | Audit trail + results | sessions_history() | (bidirectional sync) |

---

## 3. Key Integration Classes to Create

### 3.1 OpenClaw Gateway Bridge

**File:** `src/integrations/openclaw_gateway_bridge.py`

```python
import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Optional

import aiohttp

from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
from src.Rosetta_Quest_System.quest_manager import QuestManager
from src.tools.agent_task_router import AgentTaskRouter


class OpenClawGatewayBridge:
    """
    Bridges OpenClaw Gateway to NuSyQ orchestration.
    
    - WebSocket connection to OpenClaw Gateway (ws://host:port)
    - Listens for inbound messages from channels
    - Routes to agent_task_router (UnifiedAIOrchestrator)
    - Sends results back through original channel
    - Logs all interactions to quest_log.jsonl
    """
    
    def __init__(
        self,
        gateway_url: str = "ws://127.0.0.1:18789",
        orchestrator: Optional[UnifiedAIOrchestrator] = None,
        quest_manager: Optional[QuestManager] = None,
    ):
        self.gateway_url = gateway_url
        self.orchestrator = orchestrator or UnifiedAIOrchestrator()
        self.quest_manager = quest_manager or QuestManager()
        self.task_router = AgentTaskRouter()
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
    
    async def connect(self) -> None:
        """Establish WebSocket connection to OpenClaw Gateway."""
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(self.gateway_url)
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
    
    async def listen_for_messages(self) -> None:
        """
        Main loop: listen for inbound messages from OpenClaw Gateway.
        
        Expected message format:
        {
            "type": "message",
            "channel": "slack",
            "sender": "@alice",
            "text": "Analyze my Python code with Ollama",
            "metadata": {
                "timestamp": "2026-02-16T12:30:00Z",
                "channel_id": "C1234567"
            }
        }
        """
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("type") == "message":
                        await self.handle_inbound_message(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket error: {self.ws.exception()}")
                    break
        except Exception as e:
            print(f"Listen error: {e}")
            raise
    
    async def handle_inbound_message(self, message: dict[str, Any]) -> None:
        """
        Route inbound message from channel to UnifiedAIOrchestrator.
        
        Steps:
        1. Extract text + metadata
        2. Call route_task() with auto-detection
        3. Log to quest_log.jsonl
        4. Send result back through channel
        5. Update message status in OpenClaw
        """
        channel = message.get("channel")  # "slack", "discord", "telegram"
        sender = message.get("sender")
        text = message.get("text")
        
        # Create quest entry for tracking
        quest_id = f"openclaw_{channel}_{int(datetime.now().timestamp())}"
        
        try:
            # Route through existing agent_task_router
            # This intelligently detects task type + target system
            result = await self.task_router.route_task(
                task_type="analyze",  # or detected from text
                description=text,
                context={
                    "source": "openclaw",
                    "channel": channel,
                    "sender": sender,
                    "external_id": message.get("id", "unknown"),
                },
                target_system="auto",  # Let orchestrator decide
            )
            
            # Log successful execution
            quest_entry = {
                "quest_id": quest_id,
                "type": "openclaw_message",
                "title": f"{channel} message from {sender}",
                "description": text,
                "status": "completed",
                "source": "openclaw_gateway",
                "channel": channel,
                "sender": sender,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
            self.quest_manager.add_quest(quest_entry)
            
            # Send result back through channel
            response_text = result.get("text", json.dumps(result))
            await self.send_result(channel, sender, response_text)
            
        except Exception as e:
            # Log failure
            quest_entry = {
                "quest_id": quest_id,
                "type": "openclaw_message",
                "title": f"{channel} message from {sender} (FAILED)",
                "description": text,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.quest_manager.add_quest(quest_entry)
            
            # Send error back through channel
            await self.send_result(
                channel,
                sender,
                f"Error processing request: {str(e)}",
            )
    
    async def send_result(
        self,
        channel: str,
        target_user: str,
        result_text: str,
    ) -> None:
        """
        Send orchestrator result back through original channel.
        
        Uses OpenClaw message.send RPC method.
        """
        if not self.ws:
            return
        
        message = {
            "method": "message.send",
            "params": {
                "channel": channel,
                "to": target_user,
                "text": result_text,
            },
        }
        
        await self.ws.send_json(message)
    
    async def run(self) -> None:
        """Start listening for messages (blocking)."""
        await self.connect()
        try:
            await self.listen_for_messages()
        finally:
            await self.disconnect()


# Singleton instance
_bridge_instance: Optional[OpenClawGatewayBridge] = None


def get_openclaw_gateway_bridge() -> OpenClawGatewayBridge:
    """Get or create singleton bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = OpenClawGatewayBridge()
    return _bridge_instance


async def start_openclaw_bridge(
    gateway_url: str = "ws://127.0.0.1:18789",
) -> None:
    """Start the OpenClaw Gateway bridge."""
    bridge = OpenClawGatewayBridge(gateway_url=gateway_url)
    await bridge.run()
```

---

### 3.2 Quest ↔ Session Sync Bridge

**File:** `src/integrations/quest_session_bridge.py`

```python
import json
from datetime import datetime
from typing import Any, Optional

from src.Rosetta_Quest_System.quest_manager import QuestManager


class QuestSessionBridge:
    """
    Synchronizes NuSyQ quests ↔ OpenClaw sessions.
    
    - Maps quest_log.jsonl entries ↔ OpenClaw session history
    - Syncs multi-agent assignments
    - Tracks results bidirectionally
    """
    
    def __init__(self, quest_manager: Optional[QuestManager] = None):
        self.quest_manager = quest_manager or QuestManager()
    
    async def quest_to_session_metadata(
        self,
        quest_id: str,
    ) -> dict[str, Any]:
        """
        Convert NuSyQ quest → OpenClaw session metadata.
        
        Quest:
        {
            "quest_id": "analyze_2025_12",
            "title": "Analyze NLP Model",
            "assigned_to": ["Ollama", "Consciousness"],
            "status": "completed",
            "results": {...}
        }
        
        Returns metadata suitable for sessions.patch():
        {
            "thinkingLevel": "high",
            "model": "qwen2.5-coder",
            "metadata": {
                "quest_id": "analyze_2025_12",
                "nusyq_workload": "analysis"
            }
        }
        """
        quests = self.quest_manager.list_quests()
        quest = next(
            (q for q in quests if q.get("quest_id") == quest_id),
            None,
        )
        
        if not quest:
            return {}
        
        return {
            "metadata": {
                "quest_id": quest_id,
                "nusyq_source": True,
                "title": quest.get("title", ""),
                "assigned_to": quest.get("assigned_to", []),
                "status": quest.get("status", "unknown"),
                "created_at": quest.get("created_at", ""),
            },
        }
    
    async def session_to_quest(
        self,
        session_id: str,
        session_data: dict[str, Any],
    ) -> str:
        """
        Convert OpenClaw session → NuSyQ quest.
        
        Session data from sessions_history():
        {
            "id": "session-abc123",
            "model": "claude-opus-4-6",
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "metadata": {...}
        }
        
        Returns: created quest_id
        """
        quest_id = f"openclaw_session_{session_id}_{int(datetime.now().timestamp())}"
        
        quest_entry = {
            "quest_id": quest_id,
            "type": "openclaw_session_import",
            "title": f"OpenClaw Session: {session_id}",
            "description": "Imported from OpenClaw session history",
            "status": "completed",
            "source": "openclaw",
            "session_id": session_id,
            "model": session_data.get("model", "unknown"),
            "message_count": len(session_data.get("messages", [])),
            "metadata": session_data.get("metadata", {}),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add to quest log
        quest_id_result = self.quest_manager.add_quest(quest_entry)
        return quest_id_result or quest_id


# Singleton
_bridge_instance: Optional[QuestSessionBridge] = None


def get_quest_session_bridge() -> QuestSessionBridge:
    """Get or create singleton quest/session bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = QuestSessionBridge()
    return _bridge_instance
```

---

## 4. Configuration Integration

### 4.1 Add to `config/secrets.json`

```json
{
  "openclaw": {
    "enabled": false,
    "gateway_url": "ws://127.0.0.1:18789",
    "workspace_root": "~/.openclaw/workspace",
    "timeout_seconds": 30,
    "debug": false,
    "channels": {
      "slack": {
        "enabled": false,
        "bot_token": "xoxb-YOUR-TOKEN",
        "app_token": "xapp-YOUR-TOKEN"
      },
      "discord": {
        "enabled": false,
        "token": "YOUR-TOKEN"
      },
      "telegram": {
        "enabled": false,
        "bot_token": "YOUR-TOKEN"
      }
    }
  }
}
```

### 4.2 Extend `src/main.py`

```python
import argparse
import asyncio
from typing import Optional

async def main() -> int:
    parser = argparse.ArgumentParser(description="NuSyQ Hub")
    
    # ... existing args ...
    
    parser.add_argument(
        "--openclaw-enabled",
        action="store_true",
        help="Enable OpenClaw Gateway bridge",
    )
    parser.add_argument(
        "--openclaw-gateway",
        default="ws://127.0.0.1:18789",
        help="OpenClaw Gateway URL",
    )
    
    args = parser.parse_args()
    
    # ... existing setup ...
    
    # Start OpenClaw bridge if enabled
    if args.openclaw_enabled:
        from src.integrations.openclaw_gateway_bridge import (
            get_openclaw_gateway_bridge,
        )
        
        bridge = get_openclaw_gateway_bridge()
        # Run in background task
        asyncio.create_task(bridge.run())
        print("✓ OpenClaw Gateway bridge started")
    
    # ... rest of main ...
```

---

## 5. Example: Message Flow

### Scenario: User sends Slack message

```
Slack: "@openclaw analyze this repo for code quality issues"

↓ [OpenClaw receives]

{
  "type": "message",
  "channel": "slack",
  "sender": "@alice",
  "text": "analyze this repo for code quality issues",
  "metadata": {"timestamp": "2026-02-16T12:30:00Z"}
}

↓ [Gateway Bridge receives via WS]

openclaw_gateway_bridge.handle_inbound_message()
  ├─ Extract: task="analyze", description="code quality issues"
  ├─ Call: route_task(task_type="analyze", description=..., target="auto")
  │
  │  ↓ [Orchestrator routes to appropriate system]
  │
  │  UnifiedAIOrchestrator.execute_task()
  │   └─ Detects: code quality → route to Ollama
  │   └─ Calls: Ollama with ruff/black/mypy analysis
  │   └─ Returns: {
  │       "text": "Code quality analysis...",
  │       "issues": 12,
  │       "critical": 2
  │     }
  │
  ├─ Log quest to quest_log.jsonl
  │  {
  │    "quest_id": "openclaw_slack_1234567890",
  │    "title": "slack message from @alice",
  │    "description": "analyze this repo for code quality issues",
  │    "status": "completed",
  │    "result": {...}
  │  }
  │
  └─ Send result: message.send(channel="slack", to="@alice", text="...")

↓ [Slack receives response]

Slack: "@alice Your repo has 12 quality issues, 2 critical..."
```

---

## 6. Testing OpenClaw Integration

### 6.1 Unit Test Template

```python
# tests/integration/test_openclaw_gateway_bridge.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.integrations.openclaw_gateway_bridge import OpenClawGatewayBridge


@pytest.mark.asyncio
async def test_gateway_bridge_initialization():
    """Test bridge initialization."""
    bridge = OpenClawGatewayBridge(
        gateway_url="ws://localhost:18789"
    )
    assert bridge.gateway_url == "ws://localhost:18789"
    assert bridge.orchestrator is not None


@pytest.mark.asyncio
async def test_handle_inbound_message():
    """Test inbound message handling."""
    bridge = OpenClawGatewayBridge()
    
    message = {
        "type": "message",
        "channel": "slack",
        "sender": "@test",
        "text": "analyze my code",
        "id": "msg123",
    }
    
    # Mock the task router to return a result
    bridge.task_router.route_task = AsyncMock(
        return_value={"text": "Analysis complete"}
    )
    
    # Mock send_result
    bridge.send_result = AsyncMock()
    
    # Handle the message
    await bridge.handle_inbound_message(message)
    
    # Verify route_task was called
    bridge.task_router.route_task.assert_called_once()
    
    # Verify result was sent
    bridge.send_result.assert_called_once()
```

### 6.2 Manual Test (Local)

```bash
# Terminal 1: Start OpenClaw Gateway
npx -p openclaw@latest openclaw gateway --port 18789 --verbose

# Terminal 2: Start NuSyQ with OpenClaw bridge
python -m src.main --openclaw-enabled --openclaw-gateway ws://127.0.0.1:18789

# Terminal 3: Test with a message
python -c "
import asyncio
import aiohttp
import json

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('ws://127.0.0.1:18789') as ws:
            msg = {
                'type': 'message',
                'channel': 'test',
                'sender': 'alice',
                'text': 'say hello'
            }
            await ws.send_json(msg)
            
            response = await ws.receive_json()
            print(json.dumps(response, indent=2))

asyncio.run(test())
"
```

---

## 7. Terminal Commands Quick Reference

```bash
# Start OpenClaw (requires npm/Node)
npm install -g openclaw@latest
openclaw onboard --install-daemon
openclaw gateway --port 18789 --verbose

# Check gateway health
curl http://localhost:18789/health

# List available skills
curl http://localhost:18789/skills

# Start NuSyQ with bridge
python -m src.main --openclaw-enabled

# View quest log (all interactions)
tail -f src/Rosetta_Quest_System/quest_log.jsonl

# Search quest log for OpenClaw messages
grep '"source": "openclaw"' src/Rosetta_Quest_System/quest_log.jsonl
```

---

## 8. Debugging Tips

### WebSocket Connection Issues

```python
# Check if gateway is running
python -c "
import socket
s = socket.socket()
try:
    s.connect(('127.0.0.1', 18789))
    print('✓ Gateway responding')
except:
    print('✗ Gateway not running')
"
```

### Message Routing Not Working

1. Check `quest_log.jsonl` for errors
   ```bash
   grep '"status": "failed"' quest_log.jsonl | tail -5
   ```

2. Enable debug logging
   ```python
   bridge = OpenClawGatewayBridge(debug=True)
   ```

3. Verify route_task is being called
   ```python
   # Add breakpoint in agent_task_router.py
   ```

### Channel Auth Issues

- Slack: verify bot token has `chat:write` permission
- Discord: verify token has permissions + server access
- Telegram: verify bot token is valid with @BotFather

---

## 9. References

- **OpenClaw Docs:** https://docs.openclaw.ai/
- **Gateway Protocol:** https://docs.openclaw.ai/concepts/architecture
- **NuSyQ Code:**
  - Orchestrator: `src/orchestration/unified_ai_orchestrator.py`
  - Task Router: `src/tools/agent_task_router.py`
  - Quest System: `src/Rosetta_Quest_System/quest_engine.py`

---

**Quick Reference Complete**  
*For deeper details, see OPENCLAW_INTEGRATION_INVESTIGATION.md*
