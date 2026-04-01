# 🎯 NEW PROTOCOL CAPABILITIES - USER GUIDE

**Status:** ✅ READY TO USE  
**Last Tested:** 2026-02-07  

## Quick Start: What's Available Now

### 1. 🔌 **Connector System** 
```bash
nq connector list              # List all connectors
nq connector connect <id>      # Connect a specific connector
nq connector disconnect <id>   # Disconnect
nq connector health            # Check health of all connectors
```

**Use Case:** Build integrations with external APIs, webhooks, SaaS platforms.

**Example Code:**
```python
from src.connectors.registry import get_connector_registry
registry = get_connector_registry()

# List available
connectors = registry.list_connectors()

# Get one
webhook = registry.get('webhook_connector')

# Execute
result = webhook.execute('send_event', {'data': {...}})
```

---

### 2. 🧩 **Workflow Engine**
```bash
nq workflow list               # List all workflows
nq workflow create <name>      # Create new workflow
nq workflow run <id>           # Execute workflow
nq workflow history <id>       # View execution history
```

**Use Case:** Build complex automation with node-based visual design.

**Example Code:**
```python
from src.workflow.engine import get_workflow_engine
from src.workflow.nodes import TriggerNode, ActionNode, NodeType

engine = get_workflow_engine()

# Create workflow
wf = engine.create_workflow('my_workflow', 'My Workflow')

# Add nodes
trigger = TriggerNode('t1', 'Start', NodeType.TRIGGER, {})
action = ActionNode('a1', 'Action', NodeType.ACTION, {'type': 'log'})
wf.add_node(trigger)
wf.add_node(action)

# Execute
result = engine.execute_workflow(wf.id, {})
```

**Features:**
- 5 node types: TRIGGER, ACTION, CONDITION, TRANSFORM, OUTPUT
- Topological sort for proper execution order
- Persistence: save/load from JSON
- Event logging with timestamps
- Execution history tracking

---

### 3. 🧪 **TestLoop - Self-Healing Tests**
```bash
nq test-loop <target>                    # Run tests with AI fixes
nq test-loop <target> -n 5               # Max 5 iterations
nq test-loop <target> --no-ai            # Disable AI fixes
```

**Use Case:** Automatically fix failing tests with AI assistance.

**Example Code:**
```python
from src.automation.test_loop import TestLoop

loop = TestLoop(enable_ai_fixes=True)
result = loop.iterate_until_pass('tests/', max_iterations=5)

# Result contains:
# - passed_tests
# - failed_tests
# - fixes_attempted
# - final_status
```

**How It Works:**
1. Run pytest on target directory
2. Capture failed tests
3. Dispatch to AI system for fixes (if enabled)
4. Re-run tests
5. Repeat up to max_iterations
6. Event log all attempts for audit

---

### 4. 📐 **Web App Templates**
```python
from src.factories.templates import load_template

# Load Flask template
flask_app = load_template('flask_api')
print(flask_app.framework)      # 'flask'
print(flask_app.dependencies)   # ['flask', 'sqlalchemy', 'pyjwt', ...]

# Load FastAPI template
fastapi_app = load_template('fastapi_service')
print(fastapi_app.framework)    # 'fastapi'
print(fastapi_app.dependencies) # ['fastapi', 'sqlalchemy', 'pydantic', ...]

# Scaffold project
scaffold_files = flask_app.scaffold_files()
# Returns list of (path, content) tuples ready to write
```

**Available Templates:**
- **flask_api** - Flask REST API with JWT auth and SQLAlchemy
- **fastapi_service** - FastAPI service with Pydantic validation

---

### 5. 🧭 **Protocol Status Check**
```bash
nq protocol status             # Check health of all protocol facades
```

**Output:**
```
Protocol Status
=========================================

🧠 Core Facade:
   ✅ Available
   Search: ok
   Quest: ok
   Council: ok
   Background: ok

🔌 Connectors:
   ✅ Available
   Total: 0
   Enabled: 0
   Connected: 0

🧩 Workflows:
   ✅ Available
   Registered: 3

🧪 Test Loop:
   ✅ Available

=========================================
Protocol status: healthy
```

---

### 6. 🏭 **Factory Orchestration Surface**
```bash
nq factory health                              # Full smoke probes
nq factory health --no-packaging              # Faster health pass
nq factory health --json                      # Machine-readable report
nq factory doctor                             # Fail-fast diagnostics
nq factory doctor --strict-hooks              # Require runtime hook execution (no skips)
nq factory doctor --fix                       # Auto-apply safe remediation actions
nq factory autopilot                          # doctor -> inspect-examples -> targeted patch plan
nq factory autopilot --fix --strict-hooks     # Execute loop + apply remediations
nq factory autopilot --ci-gate                # CI gate mode (strict hooks + no examples)
nq factory ci-gate                            # Alias for autopilot CI gate mode
nq factory inspect-examples                   # Scan Bitburner/Cogmind/etc paths
nq factory inspect-examples --json            # Machine-readable inspection report
```

**Use Case:** Agent-level factory operations beyond VS Code extension flows.

**What `factory health` verifies:**
1. Provider fallback integrity (ChatDev -> Ollama).
2. Runtime bootstrap wiring (data/event/save/mod modules active at runtime).
3. Runtime-profile packaging adapters (Steam/export hook artifacts per profile).

**What `inspect-examples` extracts:**
1. Runtime profile fingerprints (Electron/Godot/native).
2. Packaging + Steamworks signal markers.
3. Actionable platform recommendations for template/factory evolution.

**What `factory doctor` enforces:**
1. Health probes must pass (fallback/bootstrap/packaging).
2. Recent generation quality must stay below degradation thresholds (fallback churn + placeholder ratio).
3. Packaging hook contracts must validate per runtime profile; `--strict-hooks` treats skipped runtime execution as failure.

**What `factory autopilot` adds:**
1. Runs doctor + reference-game inspection in one orchestration pass.
2. Produces a prioritized patch plan based on live platform signals.
3. Optional `--fix` executes safe remediations (provider policy hardening, template/runtime corrections, packaging hook regeneration, and runtime-profile hardening for Electron/native/Godot).

---

## 🔧 Direct Python API

### Connector Registry
```python
from src.connectors.registry import get_connector_registry
from src.connectors.base import BaseConnector

registry = get_connector_registry()

# List, connect, disconnect, health check
connectors = registry.list_connectors()
status = registry.get_status()  # Overall health
registry.connect_all()
registry.disconnect_all()

# Get specific connector
connector = registry.get('webhook_connector')
if connector:
    result = connector.connect()
    result = connector.execute('send', {'data': {...}})
    result = connector.health_check()
    result = connector.disconnect()

# Custom connector
class MyConnector(BaseConnector):
    def execute(self, action, params):
        # Your implementation
        pass

registry.register(MyConnector())
```

### Workflow Engine
```python
from src.workflow.engine import get_workflow_engine
from src.workflow.nodes import (
    NodeType, WorkflowNode, 
    TriggerNode, ActionNode, ConditionNode, OutputNode
)

engine = get_workflow_engine()

# CRUD Operations
wf = engine.create_workflow('id', 'name', 'description')
workflows = engine.list_workflows()
wf = engine.load_workflow('id')
engine.save_workflow(wf)

# Execution
result = engine.execute_workflow('id', {'input': 'data'})
history = engine.get_history('id')  # Execution history

# Node operations (on workflow object)
node = TriggerNode('t1', 'Trigger', NodeType.TRIGGER, {})
wf.add_node(node)
wf.remove_node('t1')
wf.add_edge('t1', 'a1')  # Connect trigger to action
```

### TestLoop
```python
from src.automation.test_loop import TestLoop

loop = TestLoop(enable_ai_fixes=True, max_iterations=5)

# Run tests
result = loop.run_tests('tests/')
print(result.data)  # {'passed': [...], 'failed': [...]}

# Iterate with AI fixes
result = loop.iterate_until_pass('tests/', max_iterations=5)
print(result.data)  # Final status with all attempts
```

### Templates
```python
from src.factories.templates import load_template, save_template

# Load by name or path
tmpl = load_template('flask_api')  # By name
tmpl = load_template('path/to/custom.yaml')  # By file

# Access properties
print(tmpl.framework)       # 'flask'
print(tmpl.dependencies)    # List of dependencies
print(tmpl.dev_dependencies)# Dev-only dependencies
print(tmpl.prompts)        # Scaffold prompts

# Generate scaffolding
files = tmpl.scaffold_files()  # [(path, content), ...]

# Save modified template
save_template(tmpl, Path('output.yaml'))
```

---

## 📊 Protocol Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    nq CLI Interface                      │
│  (connector, workflow, test-loop, protocol commands)     │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────────────────┐
       │        NEW PROTOCOL SURFACES (Phase 4-8)        │
       │                                                   │
       ├─► Web Templates                                  │
       │   ├─ Flask Service                              │
       │   └─ FastAPI Service                            │
       │                                                   │
       ├─► Connector System                              │
       │   ├─ BaseConnector                              │
       │   ├─ ConnectorRegistry                          │
       │   └─ WebhookConnector (ref impl)               │
       │                                                   │
       ├─► Workflow Engine                               │
       │   ├─ Nodes (Trigger, Action, Condition, etc.)  │
       │   └─ WorkflowEngine (execute, persist)          │
       │                                                   │
       └─► TestLoop                                      │
           └─ Iterative test runner with AI fixes        │
       │                                                   │
       └─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│        EXISTING NUSYQ INFRASTRUCTURE (Auto-Used)        │
│                                                          │
├─ Search System (SmartSearch)                            │
├─ Quest System (Background tasks, event logging)         │
├─ Council System (Multi-AI consensus)                    │
├─ Background Orchestrator (Async execution)             │
├─ SpineRegistry (Service discovery)                      │
└─ Event Logging (state/events.jsonl audit trail)        │
└─────────────────────────────────────────────────────────┘
```

---

## 🎓 Common Workflows

### Workflow 1: Create a Simple Web Service
```bash
# 1. Create project from template
tmpl=$(nq template load flask_api)

# 2. Set up connectors
nq connector list
nq connector connect webhook_connector

# 3. Create a workflow
nq workflow create "web_service_pipeline"

# 4. Run it
nq workflow run web_service_pipeline
```

### Workflow 2: Build Self-Healing Test Suite
```bash
# 1. Create test loop
nq test-loop tests/unit -n 5 --no-ai  # Dry run

# 2. Enable AI fixes
nq test-loop tests/unit -n 5          # With AI

# 3. Check results
nq test-loop tests/unit --history    # View history
```

### Workflow 3: Add External Integration
```bash
# 1. Check available connectors
nq connector list

# 2. Connect the one you need
nq connector connect stripe_connector

# 3. Create workflow to use it
nq workflow create "payment_processor"

# 4. Run workflow
nq workflow run payment_processor
```

---

## ⚡ Performance Notes

- **Lazy Loading:** Connector registry loads connectors on-demand
- **Async Support:** Background orchestration for I/O-bound operations
- **Caching:** WorkflowEngine caches execution plans
- **Event Logging:** Append-only JSONL format (efficient for large volumes)
- **Persistence:** Workflows saved as JSON (easy inspection/debugging)

---

## 🛠️ Troubleshooting

### Connector not found?
```bash
nq connector list  # Check what's available
# Register custom connectors via Python API
```

### Workflow execution failed?
```bash
nq protocol status  # Check overall health
# Review event log: state/events.jsonl
```

### Tests not auto-fixing?
```bash
nq test-loop tests/ --no-ai  # Disable AI to debug
# Check background task queue: nq bg process 5
```

---

## 📚 Next: Domain-Specific Connectors

Planned connectors (future phases):
- Stripe (payments)
- GitHub (repo operations)
- Slack (notifications)
- Email (SMTP)
- Database (multi-DB support)

---

**Documentation:** [PROTOCOL_FINAL_REPORT.md](PROTOCOL_FINAL_REPORT.md)  
**Source Code:** `src/connectors/`, `src/workflow/`, `src/automation/`  
**Tests:** `tests/test_protocol_integration.py`  
**Status:** ✅ PRODUCTION READY
