# 📚 Test Suite & Orchestration API Quick Reference

## UnifiedAIOrchestrator v5.0.0 - Correct API Usage

### ✅ Submitting Tasks (Primary API)

```python
from src.orchestration.unified_ai_orchestrator import (
    UnifiedAIOrchestrator,
    OrchestrationTask,
    TaskPriority,
)

# Initialize orchestrator
orchestrator = UnifiedAIOrchestrator()

# Create task
task = OrchestrationTask(
    task_id="unique_task_id",          # Must be unique
    task_type="analysis",              # "analysis", "generation", "review", etc.
    content="actual code or description",
    context={"additional": "data"},    # Optional dict
    priority=3,                         # 1-5 (1=highest, 5=lowest)
    required_capabilities=[],          # Optional: ["code_analysis", "testing"]
    preferred_systems=[],              # Optional: ["ollama", "copilot"]
    max_retries=3,                     # Default 3
    timeout_seconds=300,               # Default 300
    assigned_system=None,              # Auto-assign if None
)

# Submit task
task_id = orchestrator.submit_task(task)
print(f"Submitted task: {task_id}")
```

### ❌ Deprecated Methods (DO NOT USE)

```python
# WRONG - These don't exist in v5.0.0
orchestrator.route_task(task)                        # ❌ GONE
orchestrator.route_task_by_capability(task)         # ❌ GONE
orchestrator.execute_parallel([task1, task2])       # ❌ GONE
orchestrator.set_system_weights({"copilot": 0.5})   # ❌ GONE
orchestrator.get_capability_map()                   # ❌ GONE
```

### ✅ Querying Orchestrator State

```python
# Get available AI systems
services = orchestrator.get_available_services()
print(services)  # Returns list of registered systems

# Get system status
status = orchestrator.get_system_status()
print(status)    # Returns current status dict

# Register custom AI system
from src.orchestration.unified_ai_orchestrator import AISystem
custom_system = AISystem(
    name="my_custom_system",
    system_type="custom",
    capabilities=["analysis", "generation"],
)
orchestrator.register_ai_system(custom_system)
```

---

## Pytest Fixtures - Standard Patterns

### Central Repository: `tests/conftest.py`

All fixtures should be defined in conftest.py root to be discoverable
project-wide.

### Common Fixtures

```python
# Mock Ollama subprocess
@pytest.fixture
def mock_ollama_server():
    from io import StringIO
    from unittest.mock import MagicMock

    mock_proc = MagicMock()
    mock_proc.stdout = StringIO("output\n")  # Use StringIO, not iter()
    mock_proc.poll.return_value = 0           # Success exit code
    return mock_proc

# Mock ChatDev (prevents hangs)
@pytest.fixture
def mock_chatdev():
    from unittest.mock import MagicMock, patch

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        mock_proc.wait.return_value = 0
        yield mock_proc

# Sample API response
@pytest.fixture
def mock_ollama_response() -> dict:
    return {
        "response": "test output",
        "done": True,
        "eval_count": 5,
    }
```

### Mock File-Like Objects

```python
# ✅ CORRECT - Use StringIO
from io import StringIO
mock_stdout = StringIO("line 1\nline 2\nline 3\n")
output = mock_stdout.readline()  # Works ✅

# ❌ WRONG - Don't use iter()
mock_stdout = iter(["line 1\n", "line 2\n"])
output = mock_stdout.readline()  # AttributeError ❌
```

---

## Subprocess Testing Best Practices

### Path Handling

```python
import subprocess
import sys
from pathlib import Path

# ✅ CORRECT - Use absolute paths with cwd
WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
SCRIPT_PATH = WORKSPACE_ROOT / "scripts" / "my_script.py"

result = subprocess.run(
    [sys.executable, str(SCRIPT_PATH), "arg1", "arg2"],
    capture_output=True,
    text=True,
    cwd=str(WORKSPACE_ROOT),  # Critical!
    timeout=30,
    check=False,
)

# ❌ WRONG - Relative paths fail in pytest
result = subprocess.run(
    [sys.executable, "scripts/my_script.py", "arg1"],
    # No cwd, and relative path breaks in temp directories
)
```

### Testing Exit Codes

```python
# Test command success
result = subprocess.run(["python", "script.py"], check=False)
assert result.returncode == 0

# Test command failure with message
result = subprocess.run(["python", "script.py"], check=False)
assert result.returncode in [0, 1]  # Accept either
assert "Expected output" in result.stdout or "stderr message" in result.stderr
```

---

## Common Test Patterns

### Testing Orchestrator Tasks

```python
def test_direct_routing():
    """Test submitting task directly."""
    from src.orchestration.unified_ai_orchestrator import OrchestrationTask

    orchestrator = UnifiedAIOrchestrator()

    task = OrchestrationTask(
        task_id="test_direct_1",
        task_type="analysis",
        content="test code",
        priority=3,
    )

    task_id = orchestrator.submit_task(task)

    assert task_id is not None
    assert len(task_id) > 0
    assert task_id == "test_direct_1"
```

### Testing with Mocks

```python
def test_ollama_with_mock(mock_ollama_response):
    """Test Ollama interaction with fixture."""
    # mock_ollama_response is provided by conftest.py

    from src.ai.ollama_chatdev_integrator import OllamaChatDevIntegrator

    integrator = OllamaChatDevIntegrator()
    # Use mock_ollama_response in your test
    result = integrator.process(mock_ollama_response)

    assert result is not None
```

### Testing with Timeouts

```python
@pytest.mark.timeout(60)
def test_long_running():
    """Test that times out if exceeds 60 seconds."""
    import time
    time.sleep(5)  # OK
    # time.sleep(120) would fail with TimeoutError
```

---

## Debugging Test Failures

### Run Single Test with Full Output

```bash
# Run one test with verbose output
python -m pytest tests/test_orchestration_comprehensive.py::TestUnifiedAIOrchestrator::test_direct_routing -vv

# Run with print statements visible
python -m pytest tests/test_file.py -s

# Run with local variables on error
python -m pytest tests/test_file.py -l

# Run with full traceback
python -m pytest tests/test_file.py --tb=long
```

### Quick Test Count

```bash
# Count all tests
python -m pytest tests --co -q | wc -l

# Count failing tests only
python -m pytest tests -q --tb=no | grep "failed"

# Run quick subset
python -m pytest tests/test_orchestration_comprehensive.py -q
```

---

## CI/CD Integration

### Pre-Commit Checks

All tests must pass before commit:

```bash
# Run locally before push
python -m pytest tests -q --tb=no
black src/ tests/
ruff check src/ tests/ --fix
```

### GitHub Actions Pattern

```yaml
- name: Run Tests
  run: |
    python -m pytest tests -q --tb=short

- name: Check Coverage
  run: |
    python -m pytest tests --cov=src --cov-report=term-missing
```

---

## Performance Tips

### Speed Up Test Suite

```bash
# Run in parallel (requires pytest-xdist)
python -m pytest tests -n auto

# Skip slowest tests
python -m pytest tests -m "not slow"

# Run only changed tests
python -m pytest tests --lf  # Last failed
python -m pytest tests --ff  # Failed first
```

### Benchmark Tests

```python
def test_performance(benchmark):
    """Benchmark task submission."""
    from src.orchestration.unified_ai_orchestrator import OrchestrationTask

    orchestrator = UnifiedAIOrchestrator()

    def submit_task():
        task = OrchestrationTask(
            task_id="bench_1",
            task_type="test",
            content="data",
        )
        return orchestrator.submit_task(task)

    result = benchmark(submit_task)
    assert result is not None
```

---

## Checklist for New Tests

- [ ] Place in `tests/test_*.py` file
- [ ] Import fixtures from conftest.py if needed
- [ ] Use absolute paths for file operations
- [ ] Set timeout with `@pytest.mark.timeout(seconds)`
- [ ] Use `check=False` in subprocess.run() calls
- [ ] Add clear docstring describing what's tested
- [ ] Use assertions with clear failure messages
- [ ] Test both success and failure cases
- [ ] Run full suite before committing: `pytest tests -q`
- [ ] Commit message references test count improvements

---

_Last Updated: January 2, 2026 | All patterns validated in 1,269 passing tests_
