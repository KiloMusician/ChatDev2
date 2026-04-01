# Consciousness Loop + Reliability Sprint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the full consciousness loop (breathing factor, Culture Ship veto, event logging) into the orchestrator runtime, and fix four reliability gaps (voter fixture, gate ordering, ruff errors, tmpclaude cleanup).

**Architecture:** A thin `ConsciousnessLoop` adapter wraps `SimulatedVerseUnifiedBridge` with lazy init, 30s factor cache, and total graceful degradation. Four orchestrator touch points are modified (init, start, execute_task, _execute_*). The `brief` output gains a Consciousness State section. Gate check ordering is rebalanced so chatdev_e2e (slow) runs last.

**Tech Stack:** Python 3.12, aiohttp, asyncio, SimulatedVerseUnifiedBridge, BackgroundTaskOrchestrator, pytest, ruff

---

## Sprint 1 — Reliability (zero-risk, no new features)

### Task 1: Fix voter fixture (3 test collection errors → 0)

**Files:**
- Modify: `tests/test_advanced_consensus_voting.py` — add `voter` fixture at top of file

**Background:** `test_majority_voting(voter)`, `test_weighted_voting(voter)`, and `test_specialization_boost(voter)` expect `voter` as a pytest fixture. The fixture doesn't exist — pytest cannot collect them. The fix is a `@pytest.fixture` that replicates the setup from `test_agent_profiling()`.

**Step 1: Write the failing collect command**

```bash
python -m pytest tests/test_advanced_consensus_voting.py --collect-only 2>&1 | grep -E "ERROR|voter"
```
Expected: 3 collection errors mentioning `voter`.

**Step 2: Add fixture to the test file**

Open `tests/test_advanced_consensus_voting.py`. After the imports (around line 18), add:

```python
import pytest

@pytest.fixture
def voter():
    """Pre-populated AdvancedConsensusVoter for dependent tests."""
    v = AdvancedConsensusVoter(learning_enabled=True)
    for _i in range(5):
        v.record_agent_result("agent-fast", True, 8.0, 200, "code_review")
        v.record_agent_result("agent-fast", True, 9.0, 210, "code_review")
    for _i in range(4):
        v.record_agent_result("agent-balanced", True, 12.0, 300, "code_review")
        v.record_agent_result("agent-balanced", False, 13.0, 310, "code_review")
    for _i in range(3):
        v.record_agent_result("agent-slow", False, 20.0, 400, "code_review")
    return v
```

**Step 3: Verify collection and pass**

```bash
python -m pytest tests/test_advanced_consensus_voting.py -v 2>&1 | tail -20
```
Expected: 6 PASSED, 0 errors.

**Step 4: Run full suite to check for regressions**

```bash
python -m pytest tests/ -q --no-header 2>&1 | tail -5
```
Expected: `1051 passed, 23 skipped, 0 errors` (was 1048 passed, 3 errors).

**Step 5: Commit**

```bash
git add tests/test_advanced_consensus_voting.py
git commit -m "fix(tests): add voter fixture to advanced_consensus_voting (3 collection errors → 0)"
```

---

### Task 2: Fix gate check ordering (chatdev_e2e budget starvation)

**Files:**
- Modify: `scripts/start_nusyq.py` — reorder `script_checks` list

**Background:** `chatdev_e2e` is currently FIRST in the gate's `script_checks` list. When the server is running, it submits a real ChatDev task that takes 5–15 minutes. With `--budget-s=60`, it consumes the entire budget in 55s, causing `openclaw_smoke`, `culture_ship_cycle`, `nogic_hotspot_ingestion`, `lint_threshold`, and `type_threshold` to all be skipped as `budget_exceeded`. Moving it LAST lets the fast checks run first.

**Step 1: Find the current order**

```bash
grep -n "chatdev_e2e\|openclaw_smoke\|culture_ship_cycle\|nogic" scripts/start_nusyq.py | head -10
```
Expected: chatdev_e2e at line ~3924 as first in the list.

**Step 2: Reorder the script_checks list**

In `scripts/start_nusyq.py` around line 3923, find:
```python
    script_checks = [
        ("chatdev_e2e", [sys.executable, "scripts/e2e_chatdev_mcp_test.py"], 1800),
        ("openclaw_smoke", [sys.executable, "scripts/openclaw_smoke_test.py"], 180),
        (
            "culture_ship_cycle",
            ...
        ),
        (
            "nogic_hotspot_ingestion",
            ...
        ),
    ]
```

Change to:
```python
    script_checks = [
        ("openclaw_smoke", [sys.executable, "scripts/openclaw_smoke_test.py"], 180),
        (
            "culture_ship_cycle",
            [sys.executable, "scripts/test_culture_ship_cycle.py", "--dry-run"],
            300,
        ),
        (
            "nogic_hotspot_ingestion",
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "from src.integrations.nogic_quest_integration import run_architecture_analysis; "
                    "a = run_architecture_analysis(workspace_root=Path('.'), save_results=True, open_visualizer=False); "
                    "print(f'HOTSPOTS={len(a.high_complexity_functions)} ORPHANS={len(a.orphaned_symbols)}')"
                ),
            ],
            300,
        ),
        # chatdev_e2e is LAST because it can take 5-15 min when server is running.
        # Fast checks above run first; chatdev_e2e gets whatever budget remains.
        ("chatdev_e2e", [sys.executable, "scripts/e2e_chatdev_mcp_test.py"], 1800),
    ]
```

**Step 3: Verify gate runs more checks in short budget**

```bash
python scripts/start_nusyq.py system_complete --budget-s=60 2>&1 | grep -E "PASS|FAIL|SKIP|budget"
```
Expected: openclaw_smoke, culture_ship_cycle, or nogic checks now appear before chatdev_e2e.

**Step 4: Commit**

```bash
git add scripts/start_nusyq.py
git commit -m "fix(gate): move chatdev_e2e to last in system_complete — prevents budget starvation of fast checks"
```

---

### Task 3: Fix 23 ruff errors in src/

**Files:**
- Modify: Various `src/**/*.py` files

**Background:** `ruff check src/ scripts/` reports 23 errors: F541 (14 — f-strings with no placeholders), I001 (5 — import ordering), E722 (2 — bare `except:`), F841 (2 — unused variables).

**Step 1: Auto-fix what's safe**

```bash
python -m ruff check src/ --fix
python -m ruff check src/ --unsafe-fixes --fix
```

**Step 2: Check remaining**

```bash
python -m ruff check src/ 2>&1 | head -30
```

**Step 3: Manually fix any remaining**

For each remaining error, apply the minimal fix:
- F541: Remove `f` prefix from `f"plain string"` → `"plain string"`
- E722: Change `except:` to `except Exception:`
- F841: Remove the unused assignment

**Step 4: Verify clean**

```bash
python -m ruff check src/ scripts/
```
Expected: `All checks passed.`

**Step 5: Run tests to check for regressions**

```bash
python -m pytest tests/ -q --no-header 2>&1 | tail -5
```

**Step 6: Commit**

```bash
git add -A
git commit -m "fix(lint): resolve 23 ruff errors in src/ (F541 f-strings, I001 imports, E722 bare except, F841 unused)"
```

---

### Task 4: Remove orphaned tmpclaude dirs from src/

**Files:**
- Delete: `src/tmpclaude-*/` (15 directories — leftover Claude Code temp dirs)

**Background:** Claude Code creates temp directories during file operations. 15 of these ended up inside `src/`, which is on the Python import path. They add noise to module discovery and `__init__.py` scanning.

**Step 1: List them**

```bash
ls src/ | grep tmpclaude
```
Expected: 15 entries like `tmpclaude-0efb-cwd`, `tmpclaude-1db5-cwd`, etc.

**Step 2: Remove them**

```bash
rm -rf src/tmpclaude-*/
```

**Step 3: Verify src/ is clean**

```bash
ls src/ | grep tmpclaude
```
Expected: no output.

**Step 4: Run tests to verify nothing depended on them**

```bash
python -m pytest tests/ -q --no-header 2>&1 | tail -5
```
Expected: same pass count as before.

**Step 5: Commit dirty tree + cleanup together**

```bash
git add -A
git commit -m "chore: remove 15 orphaned tmpclaude dirs from src/, commit debug_ollama and error_prioritization style fixes"
```

---

## Sprint 2 — Consciousness Loop

### Task 5: Create ConsciousnessLoop adapter

**Files:**
- Create: `src/orchestration/consciousness_loop.py`
- Test: `tests/test_consciousness_loop.py`

**Background:** This thin adapter wraps `SimulatedVerseUnifiedBridge`. It owns lazy initialization, a 30s breathing factor cache, and complete graceful degradation. All other tasks in this sprint depend on it.

**Step 1: Write the failing test first**

Create `tests/test_consciousness_loop.py`:

```python
"""Tests for ConsciousnessLoop adapter - graceful degradation and caching."""
import time
from unittest.mock import MagicMock, patch

import pytest

from src.orchestration.consciousness_loop import ConsciousnessLoop


def test_breathing_factor_defaults_to_one_when_bridge_unavailable():
    """When SimulatedVerse is unreachable, factor must be 1.0 (no-op)."""
    loop = ConsciousnessLoop()
    loop._bridge = None  # simulate unavailable
    assert loop.breathing_factor == 1.0


def test_breathing_factor_cached_for_30s():
    """Factor should not re-query the bridge within the cache TTL."""
    loop = ConsciousnessLoop()
    mock_bridge = MagicMock()
    mock_bridge.get_breathing_factor.return_value = 0.85
    loop._bridge = mock_bridge
    loop._factor_expires_at = time.monotonic() + 60  # cache valid
    loop._cached_factor = 0.85

    _ = loop.breathing_factor
    _ = loop.breathing_factor
    mock_bridge.get_breathing_factor.assert_not_called()  # cached


def test_approval_auto_approves_when_bridge_unavailable():
    """Culture Ship veto must auto-approve when bridge is down."""
    loop = ConsciousnessLoop()
    loop._bridge = None
    approval = loop.request_approval("execute_task", {"task_id": "t1"})
    assert approval.approved is True
    assert "unavailable" in approval.reason.lower()


def test_emit_event_does_not_raise_when_bridge_unavailable():
    """Fire-and-forget event logging must never raise."""
    loop = ConsciousnessLoop()
    loop._bridge = None
    # Must not raise
    loop.emit_event_sync("task_started", {"task_id": "t1"})


def test_consciousness_state_returns_dormant_when_unavailable():
    """Brief state must return a dormant snapshot when bridge is down."""
    loop = ConsciousnessLoop()
    loop._bridge = None
    state = loop.get_brief_state()
    assert state["available"] is False
    assert state["stage"] == "dormant"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_consciousness_loop.py -v 2>&1 | tail -15
```
Expected: `ImportError: cannot import name 'ConsciousnessLoop'`

**Step 3: Implement ConsciousnessLoop**

Create `src/orchestration/consciousness_loop.py`:

```python
"""ConsciousnessLoop — thin adapter wiring SimulatedVerseUnifiedBridge into the orchestrator.

Responsibilities:
  - Lazy init of SimulatedVerseUnifiedBridge (never blocks startup)
  - 30s cache for breathing_factor (one filesystem read per 30s at most)
  - Graceful degradation: factor=1.0, auto-approve, empty state when unavailable
  - Fire-and-forget event logging (sync wrapper, never raises)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_TTL_S = 30.0  # seconds to cache the breathing factor


@dataclass
class ShipApproval:
    approved: bool
    reason: str


class ConsciousnessLoop:
    """Adapter between BackgroundTaskOrchestrator and SimulatedVerseUnifiedBridge."""

    def __init__(self) -> None:
        self._bridge: Any | None = None
        self._initialized = False
        self._cached_factor: float = 1.0
        self._factor_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Initialization (call once from orchestrator.start())
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Try to connect to SimulatedVerseUnifiedBridge. Returns True on success."""
        if self._initialized:
            return self._bridge is not None
        self._initialized = True
        try:
            from src.integration.simulatedverse_unified_bridge import (
                SimulatedVerseUnifiedBridge,
            )
            self._bridge = SimulatedVerseUnifiedBridge()
            logger.info("🧠 ConsciousnessLoop: SimulatedVerse bridge connected")
            return True
        except Exception as exc:
            logger.info("ConsciousnessLoop: bridge unavailable (%s) — degraded mode", exc)
            self._bridge = None
            return False

    # ------------------------------------------------------------------
    # Breathing factor (cached, never raises)
    # ------------------------------------------------------------------

    @property
    def breathing_factor(self) -> float:
        """Return the current breathing multiplier (0.60–1.50). Cached 30s."""
        if self._bridge is None:
            return 1.0
        now = time.monotonic()
        if now < self._factor_expires_at:
            return self._cached_factor
        try:
            factor = float(self._bridge.get_breathing_factor())
            self._cached_factor = max(0.5, min(2.0, factor))  # guard extremes
            self._factor_expires_at = now + _CACHE_TTL_S
            logger.debug("🫁 Breathing factor refreshed: %.2f", self._cached_factor)
        except Exception as exc:
            logger.debug("ConsciousnessLoop: breathing factor fetch failed (%s)", exc)
        return self._cached_factor

    # ------------------------------------------------------------------
    # Culture Ship approval (never raises)
    # ------------------------------------------------------------------

    def request_approval(self, action: str, context: dict[str, Any]) -> ShipApproval:
        """Ask Culture Ship to approve a sensitive action. Auto-approves when unavailable."""
        if self._bridge is None:
            return ShipApproval(approved=True, reason="unavailable — auto-approved")
        try:
            result = self._bridge.request_ship_approval(action, context)
            return ShipApproval(
                approved=bool(getattr(result, "approved", True)),
                reason=str(getattr(result, "reason", "")),
            )
        except Exception as exc:
            logger.debug("ConsciousnessLoop: approval check failed (%s) — auto-approving", exc)
            return ShipApproval(approved=True, reason=f"error — auto-approved: {exc}")

    # ------------------------------------------------------------------
    # Event logging (fire-and-forget sync wrapper, never raises)
    # ------------------------------------------------------------------

    def emit_event_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Log an event to SimulatedVerse. Never raises. Safe to call anywhere."""
        if self._bridge is None:
            return
        try:
            self._bridge.log_event(event_type, data)
        except Exception as exc:
            logger.debug("ConsciousnessLoop: event emit failed (%s)", exc)

    # ------------------------------------------------------------------
    # Brief state (for start_nusyq.py brief output)
    # ------------------------------------------------------------------

    def get_brief_state(self) -> dict[str, Any]:
        """Return consciousness state dict for brief display. Never raises."""
        if self._bridge is None:
            return {"available": False, "stage": "dormant", "level": 0.0,
                    "breathing_factor": 1.0, "directives": []}
        try:
            snapshot = self._bridge.get_consciousness_state()
            directives = self._bridge.get_ship_directives()
            return {
                "available": True,
                "level": float(getattr(snapshot, "level", 0.0)),
                "stage": str(getattr(snapshot, "stage", "unknown")),
                "active_systems": list(getattr(snapshot, "active_systems", [])),
                "breathing_factor": self.breathing_factor,
                "directives": directives,
            }
        except Exception as exc:
            logger.debug("ConsciousnessLoop: get_brief_state failed (%s)", exc)
            return {"available": False, "stage": "error", "level": 0.0,
                    "breathing_factor": 1.0, "directives": []}
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_consciousness_loop.py -v 2>&1 | tail -15
```
Expected: 5 PASSED.

**Step 5: Commit**

```bash
git add src/orchestration/consciousness_loop.py tests/test_consciousness_loop.py
git commit -m "feat(consciousness): add ConsciousnessLoop adapter with breathing cache, veto, event logging"
```

---

### Task 6: Wire ConsciousnessLoop into BackgroundTaskOrchestrator

**Files:**
- Modify: `src/orchestration/background_task_orchestrator.py`

**Background:** Four changes: (1) add `self._consciousness_loop` in `__init__`, (2) initialize it in `start()`, (3) add `_get_adaptive_timeout()` helper, (4) use it in the three hardcoded `total=600` executor methods.

**Step 1: Write the failing test**

Add to `tests/test_consciousness_loop.py`:

```python
def test_adaptive_timeout_scales_with_factor():
    """_get_adaptive_timeout must multiply base by breathing_factor."""
    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator
    orch = BackgroundTaskOrchestrator.__new__(BackgroundTaskOrchestrator)
    loop = ConsciousnessLoop()
    loop._bridge = None  # unavailable → factor = 1.0
    orch._consciousness_loop = loop
    assert orch._get_adaptive_timeout(600) == pytest.approx(600.0)

    # Simulate accelerating factor
    loop._cached_factor = 0.85
    loop._factor_expires_at = time.monotonic() + 60
    assert orch._get_adaptive_timeout(600) == pytest.approx(510.0)
```

Run: `python -m pytest tests/test_consciousness_loop.py::test_adaptive_timeout_scales_with_factor -v`
Expected: FAIL (method doesn't exist yet).

**Step 2: Add `_consciousness_loop` attribute to `__init__`**

In `src/orchestration/background_task_orchestrator.py`, find the `__init__` method (around line 205). After the existing culture_ship attributes, add:

```python
        # Consciousness Loop (lazy init)
        self._consciousness_loop: Optional[Any] = None
        self._consciousness_initialized: bool = False
```

Import at top of file (with other Optional imports):
```python
from src.orchestration.consciousness_loop import ConsciousnessLoop
```
(Use lazy import inside method if circular import issues arise.)

**Step 3: Add `_ensure_consciousness_loop_initialized` method**

After `_ensure_culture_ship_initialized` method (around line 1172):

```python
    async def _ensure_consciousness_loop_initialized(self) -> None:
        """Initialize ConsciousnessLoop on first use (lazy loading)."""
        if self._consciousness_initialized:
            return
        self._consciousness_initialized = True
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop
            loop = ConsciousnessLoop()
            loop.initialize()
            self._consciousness_loop = loop
        except Exception as exc:
            logger.debug("ConsciousnessLoop init skipped: %s", exc)
```

**Step 4: Call it in `start()`**

In `start()` (around line 1185), after the existing `_ensure_culture_ship_initialized` call:

```python
        await self._ensure_consciousness_loop_initialized()
```

**Step 5: Add `_get_adaptive_timeout` helper**

After `_ensure_consciousness_loop_initialized`, add:

```python
    def _get_adaptive_timeout(self, base: float) -> float:
        """Apply breathing factor to a timeout. Returns base when loop is down."""
        if self._consciousness_loop is not None:
            return base * self._consciousness_loop.breathing_factor
        return base
```

**Step 6: Replace hardcoded `total=600` in the three executor methods**

In `_execute_ollama` (line ~693):
```python
# Before:
async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=600)) as resp:
# After:
async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self._get_adaptive_timeout(600))) as resp:
```

In `_execute_lm_studio` (line ~717):
```python
# Before:
async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=600)) as resp:
# After:
async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self._get_adaptive_timeout(600))) as resp:
```

Check `_execute_chatdev` and `_execute_copilot` for any additional hardcoded timeouts and apply `_get_adaptive_timeout` similarly.

**Step 7: Verify tests pass**

```bash
python -m pytest tests/test_consciousness_loop.py tests/test_background_task_orchestrator.py -v 2>&1 | tail -20
```
Expected: all pass.

**Step 8: Commit**

```bash
git add src/orchestration/background_task_orchestrator.py tests/test_consciousness_loop.py
git commit -m "feat(consciousness): wire ConsciousnessLoop breathing factor into orchestrator timeouts"
```

---

### Task 7: Wire Culture Ship veto + event logging into execute_task()

**Files:**
- Modify: `src/orchestration/background_task_orchestrator.py` — `execute_task()` method

**Background:** Two additions to `execute_task()`: (1) a pre-execution Culture Ship veto for SECURITY tasks and `requires_approval` tasks; (2) fire-and-forget event logging at start/complete/fail.

**Step 1: Write failing tests**

Add to `tests/test_consciousness_loop.py`:

```python
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

def test_veto_blocks_security_task(tmp_path):
    """Culture Ship veto should set task to FAILED and return early."""
    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator, BackgroundTask, TaskTarget, TaskStatus, TaskPriority

    orch = BackgroundTaskOrchestrator.__new__(BackgroundTaskOrchestrator)
    orch._consciousness_loop = MagicMock()
    orch._consciousness_loop.request_approval.return_value = ShipApproval(
        approved=False, reason="test veto"
    )
    orch._save_tasks = MagicMock()
    orch._log_to_quest = MagicMock()

    task = BackgroundTask(
        task_id="t1", prompt="fix security vuln", target=TaskTarget.OLLAMA,
        metadata={"requires_approval": True}
    )

    result = asyncio.run(orch.execute_task(task))
    assert result.status == TaskStatus.FAILED
    assert "veto" in result.error.lower()
```

**Step 2: Add `_task_needs_approval` helper to the orchestrator**

```python
    def _task_needs_approval(self, task: BackgroundTask) -> bool:
        """Return True if this task requires Culture Ship approval before execution."""
        if task.metadata.get("requires_approval", False):
            return True
        # Check if task is SECURITY category via the scheduler
        try:
            if self.phase3 and hasattr(self.phase3, "scheduler"):
                from src.orchestration.enhanced_task_scheduler import TaskCategory
                cat = self.phase3.scheduler.categorize_task(task)
                return cat == TaskCategory.SECURITY
        except Exception:
            pass
        return False
```

**Step 3: Modify `execute_task()` — add veto check + event logging**

In `execute_task()` (around line 632), after `task.started_at = datetime.now(timezone.utc)` and before the target dispatch block, add:

```python
        # --- Culture Ship veto (pre-execution) ---
        if self._consciousness_loop is not None and self._task_needs_approval(task):
            approval = self._consciousness_loop.request_approval(
                action=f"execute_{task.target.value}",
                context={
                    "task_id": task.task_id,
                    "prompt_preview": task.prompt[:120],
                    "metadata": task.metadata,
                },
            )
            if not approval.approved:
                task.status = TaskStatus.FAILED
                task.error = f"Culture Ship veto: {approval.reason}"
                task.completed_at = datetime.now(timezone.utc)
                self._save_tasks()
                logger.warning("🛡️ Task %s vetoed by Culture Ship: %s", task.task_id, approval.reason)
                return task

        # --- Event: task started ---
        if self._consciousness_loop is not None:
            self._consciousness_loop.emit_event_sync("task_started", {
                "task_id": task.task_id,
                "target": task.target.value,
                "prompt_preview": task.prompt[:80],
            })
```

After `task.completed_at = datetime.now(timezone.utc)` (end of try/except block), add:

```python
        # --- Event: task completed or failed ---
        if self._consciousness_loop is not None:
            duration = (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
            event = "task_completed" if task.status == TaskStatus.COMPLETED else "task_failed"
            self._consciousness_loop.emit_event_sync(event, {
                "task_id": task.task_id,
                "status": task.status.value,
                "duration_seconds": round(duration, 2),
                "error": task.error,
            })
```

**Step 4: Run tests**

```bash
python -m pytest tests/test_consciousness_loop.py tests/test_background_task_orchestrator.py -v 2>&1 | tail -20
```

**Step 5: Commit**

```bash
git add src/orchestration/background_task_orchestrator.py tests/test_consciousness_loop.py
git commit -m "feat(consciousness): wire Culture Ship veto and event logging into execute_task()"
```

---

### Task 8: Add Consciousness State block to `brief`

**Files:**
- Modify: `scripts/start_nusyq.py` — `_handle_brief()` function (around line 3395)

**Background:** After `## Problem Signals` and before `## Available Actions`, add a `## Consciousness State` section using `ConsciousnessLoop.get_brief_state()`.

**Step 1: Add the section**

In `_handle_brief()` in `scripts/start_nusyq.py`, after the `_print_ai_section(ai_health)` block and before `print("\n## Available Actions")`, insert:

```python
    # --- Consciousness State ---
    print("\n## Consciousness State")
    try:
        from src.orchestration.consciousness_loop import ConsciousnessLoop
        cl = ConsciousnessLoop()
        cl.initialize()
        state = cl.get_brief_state()
        if state["available"]:
            factor = state["breathing_factor"]
            factor_label = (
                "accelerating" if factor < 0.95
                else "braking" if factor > 1.05
                else "steady"
            )
            print(f"  🧠 Level {state['level']:.1f} | Stage: {state['stage']}")
            print(f"  🫁 Breathing: {factor:.2f}x  ({factor_label})")
            directives = state.get("directives", [])
            if directives:
                print(f"  ⚓ Ship: {len(directives)} active directive(s)")
            else:
                print("  ⚓ Ship: no active directives")
            print("  🔗 SimulatedVerse: online")
        else:
            print("  ⚫ SimulatedVerse offline — consciousness loop inactive")
    except Exception as exc:
        print(f"  ⚠️ Consciousness state unavailable: {exc}")
```

**Step 2: Verify brief output**

```bash
python scripts/start_nusyq.py brief 2>&1 | grep -A6 "Consciousness"
```
Expected: shows `## Consciousness State` with either online data or offline message.

**Step 3: Commit**

```bash
git add scripts/start_nusyq.py
git commit -m "feat(brief): add Consciousness State section to system brief output"
```

---

## Sprint 3 — Verification

### Task 9: Full test suite + gate verification

**Step 1: Run full test suite**

```bash
python -m pytest tests/ -q --no-header 2>&1 | tail -10
```
Expected: `1051+ passed, 0 errors`.

**Step 2: Run system gate with 300s budget**

```bash
python scripts/start_nusyq.py system_complete --budget-s=300 2>&1 | grep -E "PASS|FAIL|Summary"
```
Expected: Multiple checks now pass (openclaw, culture_ship, nogic, lint — not just ai_status).

**Step 3: Run brief to see consciousness block**

```bash
python scripts/start_nusyq.py brief 2>&1
```
Expected: `## Consciousness State` section visible in output.

**Step 4: Final commit (CLAUDE.md update)**

```bash
# Update CLAUDE.md with new gotchas discovered
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with consciousness loop wiring notes and gate ordering fix"
```

---

## Summary of All Commits

| # | Commit message | Impact |
|---|---|---|
| 1 | fix(tests): add voter fixture | 3 test errors → 0 |
| 2 | fix(gate): move chatdev_e2e to last | All 6 fast checks get budget |
| 3 | fix(lint): resolve 23 ruff errors in src/ | Clean lint |
| 4 | chore: remove tmpclaude dirs, commit dirty tree | Clean src/ |
| 5 | feat(consciousness): ConsciousnessLoop adapter | Foundation for Sprint 2 |
| 6 | feat(consciousness): wire breathing factor | Adaptive timeouts live |
| 7 | feat(consciousness): veto + event logging | Culture Ship active |
| 8 | feat(brief): Consciousness State section | Visible in brief |

**Total estimated time:** 90–120 minutes
