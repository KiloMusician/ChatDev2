# NuSyQ Quick Reference Guide

**Version**: 2.0.0
**Last Updated**: January 7, 2026

---

## Quick Start

### Start the System

```powershell
# Complete startup (recommended)
.\NuSyQ.Orchestrator.ps1

# MCP server only
& ".\.venv\Scripts\python.exe" mcp_server/main.py
```

### Stop the System

```powershell
# Press Ctrl+C in terminal running the orchestrator
# Or kill background processes
Get-Process python | Where-Object {$_.Path -like "*NuSyQ*"} | Stop-Process
```

---

## Common Commands

### Check System Health

```powershell
# MCP server status
Invoke-RestMethod -Uri "http://localhost:3000/health" -Method GET

# Ollama models
ollama list

# Agent router
python -c "from config.agent_router import AgentRouter; r=AgentRouter(); print(f'Agents: {len(r.agents)}')"
```

### View Logs

```powershell
# Real-time MCP server logs
Get-Content -Tail 50 -Wait Logs/mcp_server.log

# Search for errors
Get-Content Logs/mcp_server.log | Select-String "ERROR|WARNING"

# Filter by topic
Get-Content Logs/mcp_server.log | Select-String "consensus|routing"
```

### Run Tests

```powershell
# All integration tests
& ".\.venv\Scripts\python.exe" tests/test_mcp_fixes.py

# Retry logic test
& ".\.venv\Scripts\python.exe" tests/test_retry_logic.py

# Check test coverage
python -c "print('5/5 tests passing = 100%')"
```

---

## MCP Tools Available

### 1. `ollama_query`
Query local Ollama models

**Parameters**:
- `model` (str): Model name (default: qwen2.5-coder:7b)
- `prompt` (str): Your prompt
- `max_tokens` (int): Max response length (default: 100)

**Example**:
```python
{
    "model": "qwen2.5-coder:14b",
    "prompt": "Explain async/await in Python",
    "max_tokens": 500
}
```

### 2. `chatdev_create`
Create software with ChatDev

**Parameters**:
- `task` (str): Development task description
- `model` (str): Ollama model (default: qwen2.5-coder:7b)
- `config` (str): ChatDev config (default: NuSyQ_Ollama)

**Example**:
```python
{
    "task": "Create a REST API with FastAPI and JWT auth",
    "model": "qwen2.5-coder:14b"
}
```

### 3. `multi_agent_orchestrate`
Multi-agent collaboration

**Parameters**:
- `task` (str): Task description
- `agents` (list, optional): Specific agents to use
- `mode` (str): PARALLEL_CONSENSUS, SEQUENTIAL, DEBATE
- `include_ai_council` (bool): Convene 11-agent council
- `implement_with_chatdev` (bool): Implement via ChatDev

**Example**:
```python
{
    "task": "Design microservices architecture for e-commerce",
    "mode": "PARALLEL_CONSENSUS",
    "include_ai_council": true,
    "implement_with_chatdev": false
}
```

### 4. `ai_council_convene`
11-agent governance discussion

**Parameters**:
- `session_type` (str): STANDUP, EMERGENCY, ADVISORY, REFLECTION
- `topic` (str): Discussion topic
- `context` (str, optional): Additional context

**Example**:
```python
{
    "session_type": "ADVISORY",
    "topic": "Should we migrate to microservices?",
    "context": "Current monolith is 50K LOC, team size 5"
}
```

### 5-9. File Operations & System Info

- `file_read` - Read files with encoding support
- `file_write` - Write files (path validation enabled)
- `jupyter_execute` - Execute Python in Jupyter kernel
- `system_info` - Get configs and model info
- `health_check` - Component health status

---

## Agent Router

### 15 Available Agents

**Ollama Models** (8):
- qwen2.5-coder:7b - Default, fast code generation
- qwen2.5-coder:14b - Advanced code, better reasoning
- qwen2.5:7b/14b - General tasks
- llama3.2:3b/1b - Lightweight, quick responses
- deepseek-r1:7b/14b - Research and analysis

**External** (2):
- claude_code - Orchestration, complex reasoning
- github_copilot - IDE integration

**ChatDev** (5):
- CEO, CTO, Programmer, Code_Reviewer, Test_Engineer

### Routing Logic

```python
from config.agent_router import AgentRouter, Task, TaskType, TaskComplexity

router = AgentRouter()

task = Task(
    description="Create JWT authentication",
    task_type=TaskType.CODE_GENERATION,
    complexity=TaskComplexity.COMPLEX,
    requires_security=True
)

decision = router.route_task(task)
print(f"Agent: {decision.agent.name}")
print(f"Rationale: {decision.rationale}")
```

### Record Completion

```python
router.record_task_completion(
    agent_name="qwen2.5-coder:14b",
    task_type="code_generation",
    success=True,
    duration=45.2,
    task_description="JWT auth implementation"
)
```

---

## Knowledge Base Learning

### Check Learnings

```powershell
# View routing learnings
Get-Content knowledge-base.yaml | Select-String "routing-learnings" -Context 10

# Count routing history
python -c "from config.agent_router import AgentRouter; r=AgentRouter(); print(f'History: {len(r.routing_history)}')"
```

### Learnings Format

```yaml
sessions:
- id: routing-learnings-20260107
  date: '2026-01-07'
  type: routing-optimization
  learnings:
    - task_type: code_generation
      recommended_agent: qwen2.5-coder:14b
      avg_duration: 52.3
      sample_size: 10
```

**Update Trigger**: Every 10 successful task completions

---

## Consensus Orchestrator

### Manual Run

```powershell
python
>>> from consensus_orchestrator import ConsensusOrchestrator
>>> orchestrator = ConsensusOrchestrator(["qwen2.5-coder:7b", "qwen2.5-coder:14b"])
>>> result = orchestrator.run_consensus("Explain dependency injection", voting="weighted")
>>> print(result.consensus_response)
>>> print(f"Agreement: {result.agreement_rate * 100}%")
```

### Voting Methods

- **weighted** - Weight by model size/reliability
- **simple** - Each model gets 1 vote
- **ranked** - Rank by response quality

### View Results

```powershell
# Latest consensus result
$latest = Get-ChildItem Reports/consensus/ -Filter "*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Get-Content $latest.FullName | ConvertFrom-Json | Format-List
```

---

## Monitoring & Debugging

### Real-Time Monitoring

```powershell
# MCP server logs
Get-Content -Tail 50 -Wait Logs/mcp_server.log

# Ollama logs (if enabled)
Get-Content -Tail 50 -Wait C:\Users\keath\.ollama\logs\server.log

# Windows Task Manager
# Check python.exe CPU/Memory usage
```

### Common Issues

**Issue**: MCP server won't start
**Fix**: Check port 3000 not in use
```powershell
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
# If found, kill process or use different port
```

**Issue**: Ollama timeout
**Fix**: Increase timeout in ai-ecosystem.yaml
```yaml
local_models:
  ollama:
    timeout: 120  # Increase from 60
```

**Issue**: Agent router not loading
**Fix**: Check registry file exists
```powershell
Test-Path config/agent_registry.yaml
# Should return True
```

---

## Performance Tips

### Optimize Model Selection

**Fast tasks**: Use llama3.2:3b or qwen2.5-coder:7b
**Complex tasks**: Use qwen2.5-coder:14b or deepseek-r1:14b
**Security**: Use deepseek-r1:14b (research-focused)

### Reduce Latency

1. **Preload models**: Keep frequently-used models loaded
   ```powershell
   ollama run qwen2.5-coder:14b  # Preload
   # Ctrl+D to exit, but model stays in memory
   ```

2. **Adjust consensus agents**: Use 2-3 agents max for speed
   ```python
   agents = ["qwen2.5-coder:7b", "qwen2.5-coder:14b"]  # Fast
   # vs
   agents = [all 8 ollama models]  # Slow but thorough
   ```

3. **Disable optional phases**:
   ```python
   result = await multi_agent_orchestrate({
       "task": task,
       "include_ai_council": False,  # Skip council
       "implement_with_chatdev": False  # Skip ChatDev
   })
   ```

---

## Configuration Files

### Quick Edit

```powershell
# MCP server config
code config/config_manager.py

# Agent registry
code config/agent_registry.yaml

# Ollama settings
code ai-ecosystem.yaml

# Knowledge base
code knowledge-base.yaml
```

### Backup

```powershell
# Backup all configs
$date = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path config/*.yaml -DestinationPath "State/config_backup_$date.zip"
```

---

## Useful Scripts

### Check System Status

```powershell
# Create: scripts/check_status.ps1
$status = @{
    "Python" = (python --version 2>&1)
    "Ollama" = (ollama list | Measure-Object).Count
    "Agents" = (python -c "from config.agent_router import AgentRouter; r=AgentRouter(); print(len(r.agents))")
    "MCP_Health" = try { (Invoke-RestMethod -Uri "http://localhost:3000/health").status } catch { "Offline" }
}
$status | Format-Table -AutoSize
```

### Daily Cleanup

```powershell
# Create: scripts/daily_cleanup.ps1
# Remove old consensus reports (keep last 100)
Get-ChildItem Reports/consensus/ -Filter "*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 100 |
    Remove-Item

# Compress old logs (older than 7 days)
Get-ChildItem Logs/ -Filter "*.log.*" |
    Where-Object LastWriteTime -lt (Get-Date).AddDays(-7) |
    ForEach-Object { Compress-Archive -Path $_.FullName -DestinationPath "Logs/archive_$(Get-Date -Format 'yyyyMMdd').zip" -Update }
```

---

## Keyboard Shortcuts (VS Code)

- **Ctrl+Shift+P** → "Tasks: Run Task" → Quick task launcher
- **Ctrl+`** → Open integrated terminal
- **Ctrl+Shift+L** → Select all occurrences (useful for refactoring)
- **F5** → Start debugging (if configured)

---

## Emergency Procedures

### System Unresponsive

```powershell
# Kill all Python processes (nuclear option)
Get-Process python | Where-Object {$_.Path -like "*NuSyQ*"} | Stop-Process -Force

# Clear temporary files
Remove-Item State/*.tmp -Force

# Restart Ollama
ollama serve
```

### Corrupted Knowledge Base

```powershell
# Restore from backup
Copy-Item "State/config_backup_YYYYMMDD_HHMMSS.zip" -Destination "knowledge-base.yaml"

# Or reset to default
git checkout knowledge-base.yaml
```

---

## Contact & Support

**Documentation**:
- [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Full system guide
- [KNOWLEDGE_BASE_INTEGRATION.md](KNOWLEDGE_BASE_INTEGRATION.md) - Learning system
- [NUSYQ_IMPROVEMENTS_COMPLETE.md](NUSYQ_IMPROVEMENTS_COMPLETE.md) - Technical details

**Logs**:
- MCP Server: `Logs/mcp_server.log`
- Consensus: `Reports/consensus/*.json`
- Ship Memory: `State/ship_memory.json`

**Community**:
- GitHub Issues: (if public repo)
- Discord: (if applicable)
- Email: (if applicable)

---

*Quick Reference v2.0.0*
*For detailed documentation, see IMPLEMENTATION_COMPLETE.md*
