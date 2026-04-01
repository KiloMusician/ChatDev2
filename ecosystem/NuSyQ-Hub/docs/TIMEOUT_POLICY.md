# Timeout Configuration Policy

**Status**: ✅ COMPLETED (Batch 9/9 - 100% Python coverage achieved)  
**Created**: 2025-10-11  
**Updated**: 2025-10-11

## 🎯 Objective

Eliminate hard-coded numeric timeout values throughout the NuSyQ-Hub ecosystem and replace them with environment-driven, configurable behavior. This supports:
- **Offline-first development** with local Ollama models that may take varying amounts of time
- **Adaptive timeout behavior** that learns from historical execution times
- **Flexible configuration** across different development/deployment environments
- **No forced subprocess kills** for legitimate long-running local AI inference

## 📋 Environment Variables

All timeout-related configuration is now centralized in `src/utils/timeout_config.py`.

### Global HTTP Timeouts
| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_TIMEOUT_SECONDS` | `10` | Global default for all HTTP requests |
| `OLLAMA_HTTP_TIMEOUT_SECONDS` | Uses `HTTP_TIMEOUT_SECONDS` | Ollama-specific HTTP calls |
| `SIMULATEDVERSE_HTTP_TIMEOUT_SECONDS` | Uses `HTTP_TIMEOUT_SECONDS` | SimulatedVerse HTTP calls |

### Subprocess & Process Management
| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MAX_TIMEOUT_SECONDS` | `None` | Maximum timeout for Ollama subprocess runs (None = no enforced timeout) |
| `SUBPROCESS_TIMEOUT_SECONDS` | `5` | General subprocess timeout for quick checks (git, pip, etc.) |
| `TOOL_CHECK_TIMEOUT_SECONDS` | `10` | Timeout for checking if CLI tools are installed |
| `PIP_INSTALL_TIMEOUT_SECONDS` | `300` | Timeout for pip package installation |
| `FIX_TOOL_TIMEOUT_SECONDS` | `120` | Timeout for automated fix tools (black, ruff, etc.) |
| `ANALYSIS_TOOL_TIMEOUT_SECONDS` | `180` | Timeout for analysis tools (pytest, mypy, etc.) |
| `HEAL_TIMEOUT_SECONDS` | `30` | Timeout for auto-heal subprocess attempts |
| `THREAD_JOIN_TIMEOUT_SECONDS` | `5` | Timeout when joining monitoring threads |
| `SIMULATEDVERSE_RESULT_TIMEOUT_SECONDS` | `30` | Timeout for SimulatedVerse agent result checks |
| `CHATDEV_STATUS_TIMEOUT_SECONDS` | `10` | Timeout for ChatDev status checks |
| `COUNCIL_VOTE_TIMEOUT_SECONDS` | `30` | Timeout for Council voting operations |
| `POWERSHELL_SYNTAX_TIMEOUT_SECONDS` | `30` | Timeout for PowerShell syntax validation |
| `QUEUE_GET_TIMEOUT_SECONDS` | `1.0` | Timeout for queue.get() operations in threaded components |
| `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS` | `15.0` - `20.0` | Timeout for graceful shutdown of monitoring loops and background processes |

### Adaptive Timeout Behavior
| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_ADAPTIVE_TIMEOUT` | `false` | Enable per-model adaptive timeout estimation using EMA |

When `OLLAMA_ADAPTIVE_TIMEOUT=true`, the system:
1. Records actual execution duration for each model
2. Computes an Exponential Moving Average (EMA) per model
3. Persists history to `.cache/ollama_timeouts.json`
4. Uses adaptive estimates for future runs (with optional max cap via `OLLAMA_MAX_TIMEOUT_SECONDS`)

## 🔧 Usage Examples

### Basic Configuration (Environment Variables)
```bash
# Windows PowerShell
$env:OLLAMA_HTTP_TIMEOUT_SECONDS = "10"
$env:OLLAMA_ADAPTIVE_TIMEOUT = "true"
$env:HTTP_TIMEOUT_SECONDS = "15"

# Linux/macOS
export OLLAMA_HTTP_TIMEOUT_SECONDS=10
export OLLAMA_ADAPTIVE_TIMEOUT=true
export HTTP_TIMEOUT_SECONDS=15
```

### Code Usage
```python
from src.utils.timeout_config import get_http_timeout, get_timeout, get_ollama_max_timeout

# HTTP timeouts (service-specific or global fallback)
timeout = get_http_timeout("OLLAMA", default=5)  # Checks OLLAMA_HTTP_TIMEOUT_SECONDS, then HTTP_TIMEOUT_SECONDS, then default=5
response = requests.get(url, timeout=timeout)

# Subprocess timeouts (returns int or None)
timeout = get_timeout("OLLAMA_MAX_TIMEOUT_SECONDS")  # None if unset
subprocess.run(cmd, timeout=timeout)  # No timeout if None

# Ollama-specific adaptive timeout
max_timeout = get_ollama_max_timeout()  # Returns int or None
adaptive_enabled = ollama_adaptive_enabled()  # Returns bool
```

## 📊 Progress Tracking

### ✅ Batch 1 (Completed)
- **Created**: `src/utils/timeout_config.py` (central timeout helper)
- **Updated**:
  - `src/integration/simulatedverse_bridge.py` - SimulatedVerse HTTP calls
  - `scripts/start_simulatedverse_minimal.py` - Health check and agent list calls
  - `src/tools/launch-adventure.py` - Ollama probe timeouts (partial)

### ✅ Batch 2 (Completed)
- **Updated**:
  - `src/tools/launch-adventure.py` - Completed remaining Ollama HTTP calls
  - `src/setup/secrets.py` - Ollama health check timeout
  - `src/system/rpg_inventory.py` - Multiple subprocess and HTTP timeouts
  - `src/main.py` - Tool check, pip install, fix tool, and analysis tool timeouts

### ✅ Batch 3 (Completed)
- **Updated**:
  - `src/evolution/consolidated_system.py` - SimulatedVerse result timeout
  - `src/automation/auto_theater_audit.py` - SimulatedVerse result timeout
  - `src/automation/ollama_validation_pipeline.py` - 3 SimulatedVerse result timeouts (Zod, Council, Redstone)
  - `src/automation/chatdev_orchestration.py` - ChatDev status check + 4 SimulatedVerse result timeouts

### ✅ Batch 4 (Completed)
- **Updated**:
  - `src/automation/unified_pu_queue.py` - SimulatedVerse result timeout
  - `src/automation/autonomous_monitor.py` - SimulatedVerse result timeout (60s default for comprehensive audits)
  - `src/automation/autonomous_orchestrator.py` - Council vote timeout + SimulatedVerse result timeout
  - `src/diagnostics/repository_syntax_analyzer.py` - PowerShell syntax validation timeout

### ✅ Batch 5 (Completed)
- **Updated**:
  - `src/consciousness/the_oldest_house.py` - Thread join timeout + queue.get() timeout (2 replacements)
  - `src/integration/chatdev_llm_adapter.py` - ChatDevConfig response_timeout field + ollama list subprocess timeout (2 replacements)
  - `src/interface/environment_diagnostic_enhanced.py` - Git version check + git status timeouts (2 replacements)
  - `src/tools/run_and_capture.py` - Process wait timeout (1 replacement)
  - `src/tools/extract_commands.py` - LLM HTTP request timeout (1 replacement)
- **New env var**: `QUEUE_GET_TIMEOUT_SECONDS` (default 1.0s) for queue.get() operations
- **Total**: 8 timeouts replaced across 5 files

### ✅ Batch 6 (Completed)
- **Updated**:
  - `src/system/terminal_manager.py` - Cleanup timeout after main command timeout (1 replacement)
  - `src/system/process_manager.py` - Background process graceful termination + ShutdownConfig graceful_timeout (2 replacements)
  - `src/orchestration/multi_ai_orchestrator.py` - Task queue get timeout (1 replacement)
  - `src/core/performance_monitor.py` - Ollama version check + ShutdownConfig graceful_timeout (2 replacements)
- **New env var**: `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS` (default 15.0s-20.0s) for graceful shutdown operations
- **Total**: 6 timeouts replaced across 4 files

### ✅ Batch 7 (Completed)
- **Updated**:
  - `src/diagnostics/quick_integration_check.py` - Ollama API check timeout (1 replacement)
  - `src/diagnostics/system_integration_checker.py` - Ollama API connectivity check timeout (1 replacement)
  - `src/integration/ollama_integration.py` - Ollama generate API timeout (1 replacement)
  - `src/ai/ollama_chatdev_integrator.py` - Ollama system check timeout (1 replacement)
  - `src/copilot/extensions/chatdev_extension.py` - ChatDev process wait timeout (1 replacement)
- **Total**: 5 timeouts replaced across 5 files

### ✅ Batch 8 (Completed)
- **Updated**:
  - `src/scripts/empirical_llm_test.py` - 3 subprocess timeouts (Ollama version, list, ChatDev help check)
  - `src/orchestration/comprehensive_workflow_orchestrator.py` - 4 timeouts (architecture scan, Ollama service check with embedded HTTP timeout, core infrastructure tests)
  - `src/orchestration/system_testing_orchestrator.py` - 3 timeouts (Ollama service check with embedded HTTP timeout, architecture scanner test)
  - `src/diagnostics/quest_based_auditor.py` - 3 subprocess timeouts (py_compile for validation, Ollama integration, ChatDev integration)
  - `src/integration/Ollama_Integration_Hub.py` - 1 subprocess timeout (wizard navigator simulation)
- **Total**: 14 timeouts replaced across 5 files
- **Note**: Two embedded HTTP timeouts in Python command strings were converted to f-string interpolation using `get_http_timeout()`

### ✅ Batch 9 (Completed) - FINAL BATCH
- **Updated**:
  - `src/scripts/llm_validation_test.py` - 2 subprocess timeouts (Ollama version, model list checks)
  - `src/scripts/next_steps_priority_assessment.py` - 1 subprocess timeout (HTTP service check)
  - `src/diagnostics/quick_quest_audit.py` - 1 subprocess timeout (py_compile validation)
  - `src/diagnostics/systematic_src_audit.py` - 1 subprocess timeout (py_compile audit)
  - `src/diagnostics/comprehensive_test_runner.py` - 1 function signature (changed default from 30 to None)
- **Total**: 6 timeouts replaced across 5 files
- **Verification**: Final grep search confirmed 0 remaining hard-coded timeouts in Python files under src/ (excluding intentional constants in constants.py)

### 🎉 Project Complete
**Total files updated**: 38 files across 9 batches  
**Total timeouts replaced**: ~74+ hard-coded numeric timeouts  
**Coverage**: 100% of Python files in src/ directory  
**Remaining**: 1 PowerShell script (`src/setup/setup.ps1`) - outside scope of Python timeout configuration

### 🔄 Remaining Work (Out of Scope)
**PowerShell scripts** may contain hard-coded timeouts but use different configuration mechanisms (not applicable to Python timeout_config.py framework)

## 🧪 Testing Strategy

After each batch:
1. **Syntax check**: `python -c "compile(open('file.py').read(), 'file.py', 'exec')"`
2. **Import test**: `python -c "import module"`
3. **Functional smoke test**: Run a small orchestration or consensus experiment
4. **Static analysis**: Check for linter warnings (optional, not blocking)

## 🚀 Benefits

1. **Flexibility**: Developers can adjust timeouts per environment without code changes
2. **Offline-first**: Local Ollama models can run without arbitrary kills (default: no timeout)
3. **Adaptive learning**: System learns optimal timeouts per model over time
4. **Maintainability**: Centralized timeout logic in one module
5. **Debuggability**: Clear environment variable names make it easy to diagnose timeout issues

## 📝 Notes

- **Default behavior change**: Previously many subprocess calls had hard-coded 30s, 60s, 120s timeouts. Now they prefer environment configuration or sensible defaults (often higher or None for Ollama).
- **Backwards compatibility**: All new env vars are optional; system works with defaults if not set.
- **`.cache/` directory**: Adaptive timeout history stored in `.cache/ollama_timeouts.json` (git-ignored).

## 🔗 Related Files

- **Policy implementation**: `src/utils/timeout_config.py`
- **Orchestration**: `C:\Users\keath\NuSyQ\consensus_orchestrator.py` (uses adaptive timeouts)
- **ChatDev integration**: `C:\Users\keath\NuSyQ\ChatDev\run_ollama.py`, `C:\Users\keath\NuSyQ\nusyq_chatdev.py`
- **Progress tracker**: `config/ZETA_PROGRESS_TRACKER.json`
- **Todo list**: `.github/copilot-instructions.md` (session todo)

---

**Project Status**: ✅ **COMPLETED** - 100% Python timeout replacement achieved across NuSyQ-Hub src/ directory. All 38 files updated, ~74+ timeouts replaced, comprehensive environment-driven configuration in place.
