"""CLI-level protocol tests for `nq` command surfaces."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
NQ_PATH = REPO_ROOT / "nq"
pytestmark = pytest.mark.timeout(90)


def _run_nq(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run nq as a subprocess from repo root."""
    env = os.environ.copy()
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("PYTEST_ADDOPTS", None)
    env["OTEL_SDK_DISABLED"] = "true"

    return subprocess.run(
        [sys.executable, str(NQ_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        stdin=subprocess.DEVNULL,
    )


def _combined_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout}\n{proc.stderr}"


def _load_nq_module():
    """Load the `nq` script as a module for direct CLI function tests."""
    loader = SourceFileLoader("nq_cli_module", str(NQ_PATH))
    spec = importlib.util.spec_from_loader("nq_cli_module", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nq_connector_list_cli() -> None:
    """`nq connector list` should execute successfully."""
    proc = _run_nq(["connector", "list"])
    output = _combined_output(proc)
    assert proc.returncode == 0, output
    assert "Registered Connectors" in output
    assert "Total:" in output


def test_nq_workflow_list_cli() -> None:
    """`nq workflow list` should execute successfully."""
    proc = _run_nq(["workflow", "list"])
    output = _combined_output(proc)
    assert proc.returncode == 0, output
    assert "Workflows" in output


def test_nq_test_loop_cli() -> None:
    """`nq test-loop` should support dry-run protocol validation."""
    proc = _run_nq(
        ["test-loop", "tests/test_protocol_integration.py", "-n", "1", "--no-ai", "--dry-run"],
    )
    output = _combined_output(proc)
    assert proc.returncode == 0, output
    assert "Dry run: test loop execution skipped" in output


def test_nq_protocol_status_cli() -> None:
    """`nq protocol status` should report protocol surfaces."""
    proc = _run_nq(["protocol", "status", "--quick"])
    output = _combined_output(proc)
    assert proc.returncode == 0, output
    assert "Protocol Status" in output
    assert "Quick mode enabled" in output
    assert "Protocol status: healthy" in output


def test_factory_autopilot_ci_gate_forces_strict_hooks_and_no_examples(monkeypatch) -> None:
    """`--ci-gate` must force strict hooks, disable examples, and enable workspace integrity checks."""
    nq_module = _load_nq_module()
    captured: dict[str, object] = {}

    class _FakeFactory:
        def run_autopilot(self, **kwargs):
            captured.update(kwargs)
            return {"healthy": True, "status": "healthy", "patch_plan": []}

    monkeypatch.setattr("src.factories.ProjectFactory", _FakeFactory)
    rc = nq_module.cmd_factory(["autopilot", "--ci-gate", "--json"])

    assert rc == 0
    assert captured["strict_hooks"] is True
    assert captured["include_examples"] is False
    assert captured["include_workspace"] is True


def test_factory_ci_gate_alias_maps_to_autopilot_ci_gate(monkeypatch) -> None:
    """`nq factory ci-gate` should map to strict hooks + workspace integrity semantics."""
    nq_module = _load_nq_module()
    captured: dict[str, object] = {}

    class _FakeFactory:
        def run_autopilot(self, **kwargs):
            captured.update(kwargs)
            return {"healthy": True, "status": "healthy", "patch_plan": []}

    monkeypatch.setattr("src.factories.ProjectFactory", _FakeFactory)
    rc = nq_module.cmd_factory(["ci-gate", "--json"])

    assert rc == 0
    assert captured["strict_hooks"] is True
    assert captured["include_examples"] is False
    assert captured["include_workspace"] is True


def test_bg_run_stops_when_target_completions_reached(monkeypatch) -> None:
    """`nq bg run` should honor completion targets and return success."""
    nq_module = _load_nq_module()

    class _Result:
        def __init__(
            self, success: bool, data=None, error: str | None = None, message: str | None = None
        ):
            self.success = success
            self.data = data or {}
            self.error = error
            self.message = message

    class _FakeBackground:
        def __init__(self) -> None:
            self.queued = 6
            self.completed = 10

        def status(self, task_id=None):
            return _Result(
                True,
                data={
                    "status_counts": {
                        "queued": self.queued,
                        "completed": self.completed,
                    }
                },
            )

        def process_batch(self, limit: int):
            processed = min(limit, self.queued)
            self.queued -= processed
            self.completed += processed
            return _Result(
                True,
                data={
                    "processed": processed,
                    "succeeded": processed,
                    "failed": 0,
                },
            )

    fake_bg = _FakeBackground()

    class _FakeNusyq:
        def __init__(self, background):
            self.background = background

    monkeypatch.setattr(nq_module, "nusyq", _FakeNusyq(fake_bg))

    rc = nq_module.cmd_bg(
        ["run", "--minutes", "1", "--batch", "2", "--target-completions", "4", "--json"]
    )

    assert rc == 0
    assert fake_bg.completed >= 14
    assert fake_bg.queued <= 2


def test_bg_run_returns_success_when_queue_already_empty(monkeypatch) -> None:
    """`nq bg run` should exit cleanly when there is nothing queued."""
    nq_module = _load_nq_module()

    class _Result:
        def __init__(
            self, success: bool, data=None, error: str | None = None, message: str | None = None
        ):
            self.success = success
            self.data = data or {}
            self.error = error
            self.message = message

    class _FakeBackground:
        def status(self, task_id=None):
            return _Result(True, data={"status_counts": {"queued": 0, "completed": 42}})

        def process_batch(self, limit: int):
            raise AssertionError("process_batch should not be called when queue is empty")

    class _FakeNusyq:
        def __init__(self, background):
            self.background = background

    monkeypatch.setattr(nq_module, "nusyq", _FakeNusyq(_FakeBackground()))
    rc = nq_module.cmd_bg(["run", "--minutes", "1", "--json"])
    assert rc == 0
