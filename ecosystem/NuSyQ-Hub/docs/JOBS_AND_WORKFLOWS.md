# 🔄 Jobs, Workflows & Scheduled Tasks Documentation

**Created**: 2025-10-11  
**Purpose**: Comprehensive documentation of all jobs, workflows, task queues, and scheduled processes across the NuSyQ ecosystem  
**Scope**: NuSyQ-Hub, SimulatedVerse, NuSyQ Root

---

## 📋 Table of Contents

1. [GitHub Actions Workflows](#github-actions-workflows)
2. [Task Queue Systems](#task-queue-systems)
3. [Scheduled Jobs](#scheduled-jobs)
4. [Background Processes](#background-processes)
5. [Agent Orchestration](#agent-orchestration)
6. [Integration Points](#integration-points)

---

## 🤖 GitHub Actions Workflows

### Active Workflows (NuSyQ-Hub)

Located in `.github/workflows/`:

#### 1. **CI Pipeline** (`ci.yml`)
```yaml
Trigger: push, pull_request (main branch)
Runner: ubuntu-latest
Python: 3.11
Steps:
  - Checkout code
  - Install dependencies (requirements.txt)
  - Lint with flake8
  - Type-check with mypy
  - Run pytest
  - Compile check (compileall)
```

**Purpose**: Basic continuous integration for code quality and testing

---

#### 2. **Nightly Tech-debt Scan** (`nightly_scan.yml`)
```yaml
Trigger: schedule (cron: '0 2 * * *') + manual dispatch
Schedule: Daily at 02:00 UTC
Runner: ubuntu-latest
Python: 3.11
Steps:
  - Checkout code
  - Install dependencies
  - Run maze_solver scanner (max-depth 12)
  - Upload maze summaries as artifacts
```

**Purpose**: Automated nightly repository structure analysis  
**Output**: `logs/maze_summary_*.json` uploaded as GitHub artifacts  
**Frequency**: Daily

---

#### 3. **Security Scan** (`security-scan.yml`)
```yaml
Trigger: push (main, develop), pull_request (main)
Runner: ubuntu-latest
Steps:
  - Python syntax check (all .py files)
  - TruffleHog secret detection
  - pip-audit dependency vulnerability check
```

**Purpose**: Security vulnerability detection and secret scanning  
**Tools**: TruffleHog, pip-audit  
**Continue on Error**: Yes (security checks don't block builds)

---

#### 4. **Placeholder Workflows**
- `quality_check.yml` - Empty
- `ai_analysis.yml` - Empty
- `ai_code_review.yml` - Empty
- `manual_ai_analysis.yml` - Empty
- `quality_check_simple.yml` - Empty

**Status**: Defined but not implemented  
**Purpose**: Reserved for future AI-powered code review and quality analysis

---

### SimulatedVerse Workflows

Located in `SimulatedVerse/.github/workflows/`:

- `ci.yml` - Continuous integration
- `deploy-replit.yml` - Replit deployment automation
- `automerge.yml` - Automated PR merging
- `ai-agent-guidance.yml` - AI agent coordination
- `qquest.yml` - Quest system validation

---

## 📊 Task Queue Systems

### 1. **Unified PU Queue**

**File**: `src/automation/unified_pu_queue.py`  
**Storage**: `data/unified_pu_queue.json`  
**Purpose**: Centralized task queue for 22-agent ecosystem across 3 repositories

#### Architecture
```python
@dataclass
class PU:
    id: str
    title: str
    description: str
    priority: int  # 1-10
    status: str    # queued, voting, approved, executing, completed, failed
    repo: str      # NuSyQ-Hub, SimulatedVerse, NuSyQ
    agent_assignments: list[str]
    votes: dict[str, str]
    created_at: str
    updated_at: str
    context: dict[str, any]
```

#### Key Operations
- `submit(pu: PU)` - Add task to queue
- `vote(pu_id, agent_id, vote)` - Agent voting on tasks
- `promote(pu_id)` - Move from voting to approved
- `assign(pu_id, agent_id)` - Assign task to agent
- `complete(pu_id)` - Mark task completed
- `get_queue(filters)` - Retrieve queued tasks

#### Integration
- **NuSyQ-Hub**: Orchestration and monitoring
- **SimulatedVerse**: Culture Ship PU queue API
- **NuSyQ Root**: Multi-agent task distribution

---

### 2. **SimulatedVerse Culture Ship Queue**

**Endpoint**: `http://localhost:5002/api/culture-ship/queue`  
**Purpose**: Proof-gated unit (PU) queue for consciousness simulation tasks

#### API Methods
```python
bridge.get_pu_queue() -> list[dict]
bridge.submit_task(task_def) -> dict
bridge.check_result(task_id, timeout=30) -> dict
```

#### Features
- **Proof Requirements**: Tasks require verification before completion
- **Theater Scoring**: Tasks tracked with theater score metrics
- **Agent Integration**: Zod, Council, Redstone, Librarian, Party, Alchemist agents

---

### 3. **Colonist Scheduler**

**File**: `src/orchestration/colonist_scheduler.py`  
**Purpose**: Lightweight agent/task scheduler with skill-based assignment

#### Architecture
```python
@dataclass
class Agent:
    id: str
    skills: Dict[str, int]
    preferences: Dict[str, int]
    capabilities: List[str]
    current_task: Optional[str]
    state: str  # available, busy, resting
    metrics: Dict[str, Any]

@dataclass
class Task:
    priority: int
    id: str
    skill_req: str
    min_skill: int
    context: Dict[str, Any]
    capability: Optional[str]
    status: str  # queued, in_progress, done, failed
```

#### Scheduling Algorithm
1. Tasks queued in priority heap (min-heap with negative priority for high-first)
2. Agent scoring: `skill_weight * skill_val + pref_weight * pref_val`
3. Assignment to highest-scoring available agent
4. Capability filtering (agent must have required capability)

---

## ⏰ Scheduled Jobs

### Active Schedules

| Job | Frequency | Tool | Purpose |
|-----|-----------|------|---------|
| **Nightly Scan** | Daily 02:00 UTC | `maze_solver` | Repository structure analysis |
| **Security Scan** | On push/PR | TruffleHog + pip-audit | Vulnerability detection |
| **CI Pipeline** | On push/PR | pytest + flake8 + mypy | Code quality validation |

### Future Scheduled Jobs (Proposed)

| Job | Frequency | Tool | Purpose |
|-----|-----------|------|---------|
| **Dependency Update** | Weekly | Dependabot | Automated dependency updates |
| **ChatDev Health Check** | Daily | `chatdev_launcher.py` | Multi-agent system validation |
| **Consensus Experiment** | Weekly | `consensus_orchestrator.py` | Multi-model LLM consensus testing |
| **ZETA Progress Update** | Daily | Custom script | Progress tracker synchronization |

---

## 🔄 Background Processes

### 1. **Process Manager** (`src/system/process_manager.py`)

**Purpose**: Centralized background process management with graceful shutdown

#### Features
```python
class ProcessManager(GracefulShutdownMixin):
    def create_background_process(command, name=None)
    def _cleanup_background_processes()
    def register_cleanup_task(callback)
```

#### Managed Processes
- Long-running analysis tools
- Monitoring daemons
- File watchers
- HTTP servers

---

### 2. **Graceful Shutdown System** (`src/utils/graceful_shutdown.py`)

**Purpose**: Coordinated shutdown for monitoring loops and worker threads

#### Architecture
```python
class GracefulShutdownMixin:
    def should_stop(self) -> bool
    def stop(self) -> None

class ShutdownCoordinator:
    def register_component(name, component, priority)
    def initiate_shutdown()
    def wait_for_shutdown(timeout)
```

#### Timeout Configuration
- `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS` (default: 15.0s)
- Configurable via environment variable
- Ensures clean resource cleanup

---

### 3. **File Watchers**

**Files**:
- `src/utils/generate_structure_tree.py`
- `src/utils/generate_structure_treeBAK.py`
- `src/utils/generate_structure_tree2BAK.py`

**Purpose**: Watch repository for changes and trigger structure tree regeneration

#### Implementation
```python
observer.schedule(ChangeHandler(), str(Path.cwd()), recursive=True)
observer.start()
```

---

## 🤝 Agent Orchestration

### Multi-AI Coordination Systems

#### 1. **Multi-AI Orchestrator** (`src/orchestration/multi_ai_orchestrator.py`)
- Task queue management
- Agent coordination
- Result aggregation

#### 2. **Consensus Orchestrator** (`C:\Users\keath\NuSyQ\consensus_orchestrator.py`)
- Parallel multi-model execution
- Voting strategies (simple, weighted, ranked)
- Adaptive timeout management

#### 3. **Comprehensive Workflow Orchestrator** (`src/orchestration/comprehensive_workflow_orchestrator.py`)
- Workflow pipeline management
- Dependency-aware execution
- Multi-stage validation

---

## 🔗 Integration Points

### Cross-Repository Coordination

```
NuSyQ-Hub (Orchestration)
    ├─> SimulatedVerse (Consciousness)
    │   └─> Culture Ship Queue
    │       ├─> PU Queue API
    │       └─> Agent Results
    │
    └─> NuSyQ Root (Multi-Agent)
        ├─> ChatDev (5 agents)
        ├─> Ollama (7 agents)
        ├─> Claude Code (1 agent)
        └─> Continue.dev (1 agent)
```

### Message Flow
1. **Task Submission**: NuSyQ-Hub → Unified PU Queue
2. **Agent Voting**: Agents vote on task feasibility
3. **Task Approval**: Council promotes approved tasks
4. **Execution**: Assigned agents execute tasks
5. **Verification**: SimulatedVerse Culture Ship validates results
6. **Completion**: Results persisted to queue with status update

---

## 📝 Configuration

### Environment Variables

**Timeout Configuration** (from `.env.example`):
```bash
# Agent & Service Timeouts
SIMULATEDVERSE_RESULT_TIMEOUT_SECONDS=30
CHATDEV_STATUS_TIMEOUT_SECONDS=10
COUNCIL_VOTE_TIMEOUT_SECONDS=30
GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS=15.0

# Subprocess Management
SUBPROCESS_TIMEOUT_SECONDS=5
ANALYSIS_TOOL_TIMEOUT_SECONDS=180

# Adaptive Behavior
OLLAMA_ADAPTIVE_TIMEOUT=false
```

### Queue Persistence

**Locations**:
- Unified PU Queue: `data/unified_pu_queue.json`
- SimulatedVerse Queue: Managed by Express server (port 5002)
- Ollama Adaptive Timeouts: `.cache/ollama_timeouts.json`

---

## 🛠️ Maintenance & Monitoring

### Health Checks

**Tools**:
- `src/diagnostics/system_health_assessor.py` - Comprehensive health snapshot
- `src/diagnostics/quick_integration_check.py` - Fast integration validation
- `src/diagnostics/system_integration_checker.py` - Deep integration testing

### Logging

**Locations**:
- GitHub Actions: Artifacts uploaded per workflow
- Queue Logs: Embedded in queue JSON files
- System Logs: `logs/` directory
- Session Logs: `docs/Agent-Sessions/SESSION_*.md`

---

## 🚀 Next Steps

### Proposed Enhancements

1. **Automated Queue Monitoring**
   - Background service to monitor PU queue health
   - Alert on stale tasks (>24 hours in "queued" state)
   - Auto-reassign failed tasks

2. **Enhanced GitHub Actions**
   - Implement AI code review workflows
   - Add quality check automation
   - Create deployment pipelines for SimulatedVerse

3. **ChatDev Integration Testing**
   - Scheduled dry-runs to validate multi-agent coordination
   - Automated consensus experiments weekly
   - Performance benchmarking

4. **Cross-Repository Synchronization**
   - ZETA Progress Tracker auto-sync job
   - Knowledge base consolidation
   - Dependency graph updates

---

## 📚 References

- **Timeout Policy**: `docs/TIMEOUT_POLICY.md`
- **Workflows Context**: `.github/workflows/GITHUB_WORKFLOWS_CONTEXT.md`
- **Agent Navigation**: `AGENTS.md`
- **Copilot Instructions**: `.github/copilot-instructions.md`
- **Environment Configuration**: `.env.example`

---

*Last Updated: 2025-10-11*  
*Maintained by: NuSyQ-Hub AI Orchestration Team*
