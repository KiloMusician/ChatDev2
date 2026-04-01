# Subprocess Timeout Reference Guide

**Purpose**: Standard timeout values for subprocess operations across the NuSyQ ecosystem

## Timeout Value Guidelines

### Quick Operations (10-30 seconds)
| Operation | Timeout | Context | Rationale |
|-----------|---------|---------|-----------|
| `ollama list` | 10s | Check available models | Quick local query |
| `ruff check --statistics` | 30s | Get lint statistics | Fast static analysis |
| `git status --porcelain` | 10s | Get git status | Local git query |
| `git operations` (general) | 30s | Fetch, push, pull | Network-dependent |

### Medium Operations (120-180 seconds)
| Operation | Timeout | Context | Rationale |
|-----------|---------|---------|-----------|
| `ruff check` (full scan) | 120s | Comprehensive linting | Large codebase scan |
| System diagnostics | 180s | Health checks, awaken mode | Multiple subsystem checks |
| Grading systems | 180s | Multi-dimensional assessment | Complex metric collection |

### Long Operations (240-600 seconds)
| Operation | Timeout | Context | Rationale |
|-----------|---------|---------|-----------|
| Multi-repo error explorer | 240s | Cross-repository scanning | Multiple large repos |
| `pytest` (full suite) | 600s | Complete test execution | Includes benchmarks, slow tests |
| `sphinx-build` | 300s | Documentation generation | Many files, complex processing |
| `pip install -e .` | 300s | Package installation | Network + compilation |

### Very Long Operations (1800+ seconds)
| Operation | Timeout | Context | Rationale |
|-----------|---------|---------|-----------|
| ChatDev multi-agent workflows | 1800s | AI-driven development | Multiple agent coordination cycles |
| Complex orchestration pipelines | 300-600s | Full diagnostic + healing | Multiple subsystems in sequence |

## Usage Pattern

```python
import subprocess

# Quick operation
result = subprocess.run(
    ["ollama", "list"],
    capture_output=True,
    text=True,
    timeout=10,  # 10 seconds for quick local query
)

# Medium operation
result = subprocess.run(
    ["ruff", "check", "."],
    capture_output=True,
    text=True,
    timeout=120,  # 2 minutes for full codebase linting
)

# Long operation
result = subprocess.run(
    ["pytest", "tests/"],
    capture_output=True,
    text=True,
    timeout=600,  # 10 minutes for full test suite
)

# Very long operation (Popen with wait)
process = subprocess.Popen(cmd, ...)
exit_code = process.wait(timeout=1800)  # 30 minutes for multi-agent workflow
```

## Dynamic Timeout Configuration

For flexible timeout management, use environment variables or config:

```python
from src.utils.timeout_config import get_timeout

# Uses environment variable or default
timeout = get_timeout("SUBPROCESS_TIMEOUT_SECONDS", default=10)

result = subprocess.run(
    cmd,
    timeout=timeout,
    # ...
)
```

## Timeout Exception Handling

Always handle `subprocess.TimeoutExpired`:

```python
try:
    result = subprocess.run(
        cmd,
        timeout=timeout,
        capture_output=True,
    )
except subprocess.TimeoutExpired:
    logger.error(f"Command timed out after {timeout}s: {cmd}")
    # Handle timeout gracefully
except (subprocess.SubprocessError, OSError) as e:
    logger.error(f"Subprocess failed: {e}")
```

## Adjusting Timeouts

When to increase timeout:
- ❌ Command consistently times out in normal operation
- ❌ CI/CD environment is slower than local development
- ❌ Network latency is high (for network operations)
- ❌ Dataset/codebase size has significantly increased

When to decrease timeout:
- ✅ Command completes much faster than timeout
- ✅ Want to fail faster for better user experience
- ✅ Operation should be quick, slow means error

## Files Using Timeouts (Validated)

### ✅ Files with Proper Timeouts (as of 2025-01-18)
- `health.py` - All 7 subprocess calls have timeouts (10-300s)
- `src/copilot/task_manager.py` - 3 calls (120-600s)
- `src/utils/setup_chatdev_integration.py` - 1 call (300s)
- `src/diagnostics/comprehensive_grading_system.py` - 30s
- `src/diagnostics/actionable_intelligence_agent.py` - 10-300s
- `src/diagnostics/integrated_health_orchestrator.py` - 30-120s
- `src/diagnostics/smoke_test_runner.py` - Uses self.timeout
- `src/diagnostics/quest_based_auditor.py` - Uses get_timeout()
- `src/diagnostics/system_awakener.py` - 10s
- `src/diagnostics/multi_repo_error_explorer.py` - 60s
- `src/diagnostics/repository_syntax_analyzer.py` - Uses get_timeout()
- `src/diagnostics/quick_quest_audit.py` - Uses get_timeout()
- `src/diagnostics/comprehensive_test_runner.py` - Configurable
- `src/diagnostics/systematic_src_audit.py` - Uses get_timeout()
- `nusyq_chatdev.py` - 1800s for multi-agent workflows
- `scripts/lint_test_check.py` - 300s

### ⚠️ Known Exceptions (Intentional)
- `src/diagnostics/ecosystem_startup_sentinel.py` - Background daemon Popen (no timeout by design)

## Security Note

**Always set explicit timeouts** to prevent:
1. Indefinite hangs in automated systems
2. Resource exhaustion from stuck processes
3. Denial of service from unresponsive commands
4. CI/CD pipeline failures

**Exception**: Background daemons and monitoring processes that run indefinitely by design.

---

**Last Updated**: 2025-01-18  
**Maintained By**: NuSyQ Multi-AI Orchestration System  
**Related Documents**:
- `docs/Agent-Sessions/REMEDIATION_WAVE_20250118_SUMMARY.md`
- `src/utils/timeout_config.py` (for dynamic timeout configuration)
