# NuSyQ Cross-Repository Integration Proposal
<!-- cSpell:ignore timedelta simulatedverse sandboxing sandboxed omnitag getenv SIMULATEDVERSE -->

**Status**: Active baseline with follow-on wiring
**Risk Level**: Low (non-blocking, additive)
**Effort**: 1-2 hours (proposal + integration stubs)
**Goal**: Define MCP tool contract & integration points for the tripartite NuSyQ ecosystem

---

## Executive Summary

The NuSyQ ecosystem consists of three independent repositories:

| Repo | Role | Location | Current State |
|------|------|----------|----------------|
| **NuSyQ** (this) | Agent orchestration & routing | `/c/Users/keath/NuSyQ` | ✅ Standalone, fully functional |
| **NuSyQ-Hub** | Knowledge base, orchestration, Nogic, GitNexus | `/c/Users/keath/Desktop/Legacy/NuSyQ-Hub` | ✅ Active APIs and coordination surfaces |
| **SimulatedVerse** | World simulation & agent environments | `/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse` | ✅ Runtime-integrated, service-driven |

**Current State**: Cross-repo paths are defined in [nusyq.manifest.yaml](nusyq.manifest.yaml#L9-L15) and [.env](.env#L69-L79), and live surfaces now exist through NuSyQ-Hub GitNexus plus the Nogic bridges.

**Proposal**: Define a lightweight **MCP Tool Contract** that allows:
- NuSyQ to query knowledge bases in NuSyQ-Hub
- NuSyQ to spawn agents into SimulatedVerse environments
- Bidirectional logging of agent performance across repos

**Benefit**: Enables data-driven agent optimization (routing decisions informed by past performance across all repos).

## Current Live Surfaces

- `NuSyQ-Hub GitNexus`
  - `/api/gitnexus/health`
  - `/api/gitnexus/matrix`
  - `/api/gitnexus/repos/{repo_id}`
- `NuSyQ-Hub Nogic`
  - `src/integrations/nogic_bridge.py`
  - `src/integrations/nogic_vscode_bridge.py`
- `CONCEPT / Keeper`
  - PowerShell bridge/MCP for deterministic machine-state preflight

## Current Operating Rule

Treat the live deterministic surfaces as the control plane:

1. `Keeper` for machine-health and safe-start decisions
2. `GitNexus` for cross-repo git truth
3. `Nogic` for topology/architecture context
4. `Rosetta bootstrap` for distributed control-plane truth
5. `RosettaStone` for durable normalized artifacts

Do not start by rediscovering repo state or runtime topology through broad
analysis if one of those surfaces already answers the question.

## Distributed Rosetta Bundle

The current contract is distributed, not monolithic.

Preferred read order for humans, scripts, agents, and cockpits:

1. `state/boot/rosetta_bootstrap.json`
2. `state/registry.json`
3. `state/reports/control_plane_snapshot.json`
4. focused feed artifacts
5. docs fallback

Culture Ship is intentionally dual-authority:

- `runtime_owner: simulatedverse`
- `control_owner: nusyq_hub`

---

## Part A: Integration Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    VS Code / GitHub Copilot                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
            ┌─────────────────────┐
            │   NuSyQ (Main)      │ ← MCP Server on port 8765
            │  - Router           │
            │  - Rosetta Pipeline │
            │  - Orchestrator     │
            └─────────┬───────────┘
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ↓             ↓              ↓
   [MCP Tool]  [HTTP Call]   [File Sync]
        │             │              │
        ├──→ [NuSyQ-Hub]        [SimulatedVerse]
        │   (Knowledge)            (Simulation)
        │   - Agent profiles
        │   - Success history
        │   - Context store
        │
        └──→ [Metrics DB]
            - Agent performance (all repos)
            - Routing decisions
            - Success rates

Data Flow:
  1. User requests task in NuSyQ Copilot
  2. Router queries NuSyQ-Hub for agent profiles + history
  3. Router selects best agent (data-driven)
  4. MCP tool spawns agent into SimulatedVerse if needed
  5. Agent executes, returns results
  6. Results logged to all 3 repos (unified metrics)
```

---

## Part B: MCP Tool Contract Definition

### Tool 1: Query Knowledge Base (NuSyQ-Hub)

**Purpose**: Retrieve agent profiles, capabilities, and historical performance
**Endpoint**: `mcp://nusyq-hub/query`

**Request Schema** (JSON):
```json
{
  "query_type": "agent_profile | success_history | context_store",
  "agent_id": "string (optional)",
  "task_type": "string (optional, filters by CODE_GENERATION, BUG_FIX, etc.)",
  "time_range": {
    "start": "ISO 8601 timestamp (optional)",
    "end": "ISO 8601 timestamp (optional)"
  }
}
```

**Response Schema** (JSON):
```json
{
  "status": "success | error",
  "data": {
    "agent_profiles": [
      {
        "id": "agent_uuid",
        "name": "string",
        "capabilities": ["string"],
        "success_rate": 0.85,
        "avg_execution_time": 2.5,
        "last_updated": "ISO 8601"
      }
    ],
    "success_history": [
      {
        "agent_id": "string",
        "task_id": "string",
        "success": true,
        "execution_time": 2.1,
        "timestamp": "ISO 8601"
      }
    ]
  },
  "error_message": "string (if status=error)"
}
```

**Implementation Location**: [mcp_server/src/tools/nusyq_hub_client.py](mcp_server/src/tools/nusyq_hub_client.py) (to be created)

**Example Call** (from RosettaStone router):
```python
from mcp_server.src.tools.nusyq_hub_client import QueryKnowledgeBase

kb_query = QueryKnowledgeBase()
profiles = kb_query.query(
    query_type="agent_profile",
    task_type="CODE_GENERATION",
    time_range={"start": datetime.now() - timedelta(days=7)}
)
# Use profiles to weight routing decision
```

---

### Tool 2: Spawn Agent in Simulation (SimulatedVerse)

**Purpose**: Execute agent in isolated simulation environment (sandbox)
**Endpoint**: `mcp://simulatedverse/spawn`

**Request Schema** (JSON):
```json
{
  "agent_id": "string",
  "task": {
    "description": "string",
    "type": "CODE_GENERATION | BUG_FIX | REFACTOR | etc",
    "complexity": "SIMPLE | MODERATE | COMPLEX"
  },
  "environment": {
    "world_id": "string (optional, default=default_world)",
    "timeout_seconds": 300,
    "sandbox_mode": true
  }
}
```

**Response Schema** (JSON):
```json
{
  "status": "spawned | error",
  "agent_execution_id": "uuid",
  "environment_id": "string",
  "message": "Agent spawned in environment ID ...",
  "polling_url": "mcp://simulatedverse/poll/{agent_execution_id}",
  "error": "string (if status=error)"
}
```

**Polling Response** (GET `mcp://simulatedverse/poll/{agent_execution_id}`):
```json
{
  "status": "running | completed | failed | timeout",
  "output": {
    "result": "string or object",
    "success": true,
    "execution_time": 15.3,
    "artifacts": ["file1.py", "file2.md"]
  },
  "error_log": "string (if status=failed)"
}
```

**Implementation Location**: [mcp_server/src/tools/simulatedverse_client.py](mcp_server/src/tools/simulatedverse_client.py) (to be created)

**Example Call** (from orchestrator when sandboxing is needed):
```python
from mcp_server.src.tools.simulatedverse_client import SpawnAgentInSimulation

simulator = SpawnAgentInSimulation()
exec_id = simulator.spawn(
    agent_id="agent_007",
    task={"description": "...", "type": "CODE_GENERATION"},
    environment={"timeout_seconds": 300}
)
# Poll for results
result = simulator.poll(exec_id)
```

---

### Tool 3: Unified Metrics Logger

**Purpose**: Log agent execution results across all repos
**Endpoint**: `mcp://metrics/log`

**Request Schema** (JSON):
```json
{
  "agent_id": "string",
  "source_repo": "NuSyQ | NuSyQ-Hub | SimulatedVerse",
  "task": {
    "id": "string",
    "type": "CODE_GENERATION | BUG_FIX | etc",
    "complexity": "SIMPLE | MODERATE | COMPLEX"
  },
  "result": {
    "success": true,
    "execution_time": 2.5,
    "artifacts": ["file1", "file2"],
    "error_message": "string (optional)"
  },
  "context": {
    "source_ip": "string (optional)",
    "user": "string (optional)",
    "environment": "dev | staging | prod"
  }
}
```

**Response Schema** (JSON):
```json
{
  "status": "logged",
  "metric_id": "uuid",
  "timestamp": "ISO 8601",
  "message": "Metric persisted to Reports/metrics/agent_trends.json"
}
```

**Implementation Location**: [src/telemetry/unified_metrics.py](src/telemetry/unified_metrics.py) (extend omnitag.py)

**Example Call** (from any agent executor):
```python
from src.telemetry.unified_metrics import LogUnifiedMetric

logger = LogUnifiedMetric()
logger.log(
    agent_id="agent_007",
    source_repo="NuSyQ",
    task={"id": "task_123", "type": "CODE_GENERATION"},
    result={"success": True, "execution_time": 2.5}
)
```

---

## Part C: Integration Stubs (Scaffolding)

### Phase 3A: Create MCP Tool Modules (Non-Blocking)

```python
# File: mcp_server/src/tools/__init__.py
"""MCP tools for cross-repo integration."""

# File: mcp_server/src/tools/nusyq_hub_client.py
class QueryKnowledgeBase:
    """TODO: Implement in Phase 3B"""
    def __init__(self, hub_path: str = None):
        self.hub_path = hub_path or os.getenv("NUSYQ_HUB_PATH")

    def query(self, query_type: str, **filters) -> dict:
        """TODO: Load knowledge base from NuSyQ-Hub, filter results"""
        raise NotImplementedError("Phase 3B")

# File: mcp_server/src/tools/simulatedverse_client.py
class SpawnAgentInSimulation:
    """TODO: Implement in Phase 3B"""
    def __init__(self, sim_path: str = None):
        self.sim_path = sim_path or os.getenv("SIMULATEDVERSE_ROOT")

    def spawn(self, agent_id: str, task: dict, environment: dict) -> str:
        """TODO: Call SimulatedVerse HTTP API or subprocess"""
        raise NotImplementedError("Phase 3B")

    def poll(self, execution_id: str) -> dict:
        """TODO: Poll for agent execution results"""
        raise NotImplementedError("Phase 3B")

# File: src/telemetry/unified_metrics.py
class LogUnifiedMetric:
    """Extend omnitag to support cross-repo metric logging"""
    def __init__(self):
        self.logger = EventLogger()  # From omnitag

    def log(self, agent_id: str, source_repo: str, task: dict, result: dict):
        """TODO: Log to all 3 repos' metric stores"""
        raise NotImplementedError("Phase 3B")
```

---

## Part D: Integration with Existing Code

### Hook 1: Router Integration (mcp_server/main.py)

**Current**: Router selects agents randomly from agent_registry.yaml

**Enhanced**: Query NuSyQ-Hub for historical performance before routing

```python
# In handle_task():
from mcp_server.src.tools.nusyq_hub_client import QueryKnowledgeBase

kb = QueryKnowledgeBase()
profiles = kb.query(query_type="agent_profile", task_type=task.type)

# Weight routing decision by success_rate from profiles
weighted_agents = sorted(profiles, key=lambda x: x['success_rate'], reverse=True)
selected_agent = weighted_agents[0]['id']
```

### Hook 2: Orchestrator Integration (consensus_orchestrator.py)

**Current**: Runs agents locally, logs to local metrics

**Enhanced**: Optionally spawn agents into SimulatedVerse for sandboxed testing

```python
# In run_orchestration():
from mcp_server.src.tools.simulatedverse_client import SpawnAgentInSimulation

simulator = SpawnAgentInSimulation()
exec_id = simulator.spawn(
    agent_id=agent_id,
    task={"description": task_desc, "type": task.type},
    environment={"sandbox_mode": True, "timeout_seconds": 300}
)
result = simulator.poll(exec_id)
```

### Hook 3: Metrics Integration (src/telemetry/omnitag.py)

**Current**: Logs to Reports/events/nusyq_events.jsonl

**Enhanced**: Also log to unified metrics store (all 3 repos)

```python
# In log_event():
from src.telemetry.unified_metrics import LogUnifiedMetric

unified_logger = LogUnifiedMetric()
unified_logger.log(
    agent_id=outcome.get('agent'),
    source_repo="NuSyQ",
    task={"id": event_id, "type": payload.get('task_type')},
    result={"success": passed, "execution_time": duration}
)
```

---

## Part E: Risk Assessment & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| NuSyQ-Hub knowledge base corrupt or missing | Medium | Graceful fallback: use local agent_registry.yaml if KB unavailable |
| SimulatedVerse server down or unresponsive | Medium | Timeout + fallback to local execution (no simulation) |
| Network issues between repos | Low | Local cache of agent profiles + periodic sync (cron) |
| Circular dependency if repos cross-call | Low | One-way dependencies only: NuSyQ calls down to Hub/Verse, not vice versa |
| Metric logging conflicts (3 repos writing) | Low | Write to repo-specific metric files; aggregation via cron job |

---

## Part F: Success Criteria

✅ **All criteria must be met before declaring P3 complete**:

1. MCP Tool Contract documented (this file) ✅
2. Tool modules created with stubs (Phase 3A stubs)
3. Integration points identified in main.py, orchestrator, omnitag
4. Environment variables tested (NUSYQ_HUB_PATH, SIMULATEDVERSE_ROOT)
5. Documentation updated with tool usage examples
6. Risk mitigation plan approved by team

---

## Part G: Timeline (Phase 3)

| Milestone | Estimated Time | Status |
|-----------|-----------------|--------|
| Define MCP Tool Contract (this doc) | 2 hours | ✅ DONE (now) |
| Create stub modules (Phase 3A) | 1 hour | Pending (non-blocking) |
| Implement QueryKnowledgeBase | 4 hours | Pending (Phase 3B+, after Hub audited) |
| Implement SpawnAgentInSimulation | 4 hours | Pending (Phase 3B+, after Verse audited) |
| Implement LogUnifiedMetric | 2 hours | Pending (Phase 3B+) |
| Integration tests | 4 hours | Pending (Phase 3B+) |
| Documentation + rollback plan | 2 hours | Pending (Phase 3B+) |
| **Total** | **19 hours** | *Spans 2-3 weeks* |

---

## Part H: Next Steps

### Immediate (This Session)
- [x] Create this integration proposal document
- [x] Define MCP Tool Contract (3 tools)
- [x] Map integration hooks in existing code
- [x] Document risk assessment & success criteria

### Before Phase 3B (Next Sessions)
1. Audit NuSyQ-Hub repository structure
2. Audit SimulatedVerse repository structure
3. Identify actual API/file interfaces in both repos
4. Adjust MCP Tool Contract based on audit findings
5. Create Phase 3A stubs in NuSyQ

### Phase 3B (Implementation)
1. Implement QueryKnowledgeBase against actual Hub API
2. Implement SpawnAgentInSimulation against actual Verse API
3. Implement LogUnifiedMetric with unified storage
4. Add integration tests (mock external repos)
5. Create deployment guide for tripartite setup

---

## References

- [Manifest Config](nusyq.manifest.yaml#L9-L15) - Repository paths
- [Environment Config](.env#L69-L79) - Hub & Verse paths
- [Router Code](mcp_server/main.py#L200-250) - Where integration hooks go
- [Orchestrator Code](consensus_orchestrator.py#L1) - Sandbox execution target
- [Metrics Code](src/telemetry/omnitag.py#L172-210) - Event logging extension point

---

**Owner**: Architecture / Integration team
**Last Updated**: 2026-01-08
**Status**: Ready for approval (P3 - Low priority, strategic)
