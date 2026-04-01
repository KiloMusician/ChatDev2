"""Epistemic-Operational Lattice: Observation & Coherence Planes.

Builds a unified world state by:
1. **Observation Plane:** Ingest signals from all sources (git, runtime, diagnostics, etc.)
2. **Coherence Plane:** Reconcile contradictions, establish signal precedence, detect drift

Usage:
    from src.core.build_world_state import build_world_state
    state = build_world_state()
    print(state['timestamp'], state['coherence']['contradictions'])
"""

import json
import logging
import os
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


def _extract_json_payload(raw: str) -> dict[str, Any] | None:
    """Best-effort JSON extraction from potentially mixed stdout."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        logger.debug("Suppressed JSONDecodeError", exc_info=True)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


# --- Typed Data Models ---


@dataclass
class Signal:
    """A single fact from a source with provenance and confidence."""

    id: str
    timestamp: str
    source: str  # "git_diff", "agent_probe", "quest_log", etc.
    confidence: float  # 0.0-1.0
    value: Any
    ttl_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Contradiction:
    """Two or more signals that conflict."""

    key: str  # "error_count", "agent_status", etc.
    signals: list[dict[str, Any]]  # [{"source": "...", "value": ..., "confidence": ...}, ...]
    resolved_to: Any
    reasoning: str


@dataclass
class SignalDrift:
    """A signal that changed significantly."""

    key: str
    previous_value: Any
    current_value: Any
    change_magnitude: float  # 0.0-1.0
    alert_level: str  # "info", "warning", "critical"


# --- Observation Plane: Signal Ingestion ---


class ObservationCollector:
    """Ingest signals from all sources."""

    def __init__(self, workspace_root: Path = Path(".")):
        """Initialize ObservationCollector with workspace_root."""
        self.workspace_root = workspace_root
        self.signals: list[Signal] = []
        self.epoch = 0

    @staticmethod
    def _probe_env() -> dict[str, str]:
        """Environment overrides for internal probe subprocesses.

        Keep probes lightweight and deterministic by skipping expensive startup
        hooks that are useful for humans but noisy for machine sensing cycles.
        """
        env = dict(os.environ)
        env.setdefault("NUSYQ_SPINE_STARTUP", "never")
        return env

    def observe_git_state(self) -> None:
        """Observe git repository state across all repos."""
        branch = "unknown"
        uncommitted_count: int | None = None
        probe_note: str | None = None

        try:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.workspace_root),
            )
            if branch_result.returncode == 0 and branch_result.stdout.strip():
                branch = branch_result.stdout.strip()
        except Exception as e:
            probe_note = f"branch_probe_failed: {e}"

        try:
            status_result = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                capture_output=True,
                text=True,
                timeout=8,
                cwd=str(self.workspace_root),
            )
            if status_result.returncode == 0:
                uncommitted_count = len(
                    [line for line in status_result.stdout.split("\n") if line.strip()]
                )
        except subprocess.TimeoutExpired:
            probe_note = "status_probe_timeout"
        except Exception as e:
            probe_note = f"status_probe_failed: {e}"

        try:
            self.signals.append(
                Signal(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now(UTC).isoformat(),
                    source="git_status",
                    confidence=1.0,
                    value={
                        "uncommitted_files": uncommitted_count,
                        "current_branch": branch,
                        "dirty_state": (
                            "dirty"
                            if isinstance(uncommitted_count, int) and uncommitted_count > 0
                            else "clean" if isinstance(uncommitted_count, int) else "unknown"
                        ),
                        "probe_note": probe_note,
                    },
                    ttl_seconds=60,
                )
            )
        except Exception as e:
            logger.warning(f"Failed to observe git state: {e}")

    def observe_agent_availability(self, _agent_registry_path: Path | None = None) -> None:
        """Read agent availability from the probe registry."""
        # Try to run `python scripts/start_nusyq.py dispatch status --probes --json`
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/start_nusyq.py",
                    "dispatch",
                    "status",
                    "--probes",
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.workspace_root),
                env=self._probe_env(),
            )
            if result.returncode == 0:
                data = _extract_json_payload(result.stdout) or {}
                agents = data.get("output")
                if not isinstance(agents, dict):
                    agents = data.get("agents", {})
                if not isinstance(agents, dict):
                    agents = {}
                for agent_name, agent_info in agents.items():
                    if not isinstance(agent_info, dict):
                        continue
                    status = str(agent_info.get("status", "")).strip().lower()
                    online = bool(
                        agent_info.get("online")
                        or status in {"online", "ok", "ready", "healthy", "success"}
                    )
                    self.signals.append(
                        Signal(
                            id=str(uuid.uuid4()),
                            timestamp=datetime.now(UTC).isoformat(),
                            source="agent_probe",
                            confidence=0.95,
                            value={
                                "agent": agent_name,
                                "online": online,
                                "latency_ms": agent_info.get("latency_ms"),
                            },
                            ttl_seconds=120,
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to observe agent availability: {e}")

    def observe_quest_log(
        self, quest_log_path: Path = Path("src/Rosetta_Quest_System/quest_log.jsonl")
    ) -> None:
        """Read recent events from quest log."""
        try:
            resolved_path = quest_log_path
            if not resolved_path.is_absolute():
                resolved_path = self.workspace_root / resolved_path
            if resolved_path.exists():
                # Get last 10 lines
                with open(resolved_path, encoding="utf-8") as f:
                    lines = f.readlines()[-10:]

                for line in lines:
                    try:
                        event = json.loads(line)
                        self.signals.append(
                            Signal(
                                id=str(uuid.uuid4()),
                                timestamp=datetime.now(UTC).isoformat(),
                                source="quest_log",
                                confidence=1.0,
                                value={
                                    "event_type": event.get("event"),
                                    "status": event.get("status"),
                                },
                                ttl_seconds=3600,
                            )
                        )
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to observe quest log: {e}")

    def observe_diagnostics(self) -> None:
        """Run error report and capture diagnostics."""
        try:
            result = subprocess.run(
                [sys.executable, "scripts/start_nusyq.py", "error_report", "--quick", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.workspace_root),
                env=self._probe_env(),
            )
            if result.returncode == 0:
                data = _extract_json_payload(result.stdout) or {}
                self.signals.append(
                    Signal(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(UTC).isoformat(),
                        source="diagnostic_tool",
                        confidence=0.95,
                        value={
                            "total_diagnostics": data.get("total_diagnostics", 0),
                            "errors": data.get("by_severity", {}).get("errors", 0),
                            "warnings": data.get("by_severity", {}).get("warnings", 0),
                        },
                        ttl_seconds=300,
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to observe diagnostics: {e}")

    def collect_all(self) -> list[Signal]:
        """Run all observations and return signal stream."""
        self.signals.clear()
        observations = [
            self.observe_git_state,
            self.observe_agent_availability,
            self.observe_quest_log,
            self.observe_diagnostics,
        ]
        with ThreadPoolExecutor(max_workers=len(observations)) as executor:
            futures = [executor.submit(obs) for obs in observations]
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as exc:
                    logger.warning("Observation worker failed: %s", exc)
        return self.signals


# --- Coherence Plane: Signal Reconciliation ---


class CoherenceEvaluator:
    """Detect contradictions and establish signal precedence."""

    # Precedence order: higher index = higher authority
    SOURCE_PRECEDENCE: ClassVar[dict] = {
        "user_input": 10,
        "diagnostic_tool": 9,
        "agent_probe": 8,
        "quest_log": 7,
        "git_status": 6,
        "config": 5,
    }

    def __init__(self):
        """Initialize CoherenceEvaluator."""
        self.contradictions: list[Contradiction] = []
        self.reconciled: dict[str, Any] = {}
        self.drift: list[SignalDrift] = []
        self.previous_state: dict[str, Any] | None = None

    def reconcile_signals(self, signals: list[Signal]) -> dict[str, Any]:
        """Merge conflicting signals by precedence."""
        self.contradictions.clear()
        self.reconciled.clear()

        # Group signals by key
        signal_groups: dict[str, list[Signal]] = {}
        for signal in signals:
            key = self._extract_key(signal)
            if key not in signal_groups:
                signal_groups[key] = []
            signal_groups[key].append(signal)

        # For each group, pick the highest-precedence signal
        for key, group_signals in signal_groups.items():
            if len(group_signals) == 1:
                # No conflict
                signal = group_signals[0]
                self.reconciled[key] = signal.value
            else:
                # Potential conflict; sort by precedence
                sorted_signals = sorted(
                    group_signals,
                    key=lambda s: self.SOURCE_PRECEDENCE.get(s.source, 0),
                    reverse=True,
                )

                # Check if values actually conflict
                values = set()
                for s in sorted_signals:
                    # Simplistic: convert to JSON string for comparison
                    values.add(json.dumps(s.value, default=str, sort_keys=True))

                if len(values) > 1:
                    # Real contradiction
                    winner = sorted_signals[0]
                    self.reconciled[key] = winner.value
                    self.contradictions.append(
                        Contradiction(
                            key=key,
                            signals=[
                                {
                                    "source": s.source,
                                    "value": s.value,
                                    "confidence": s.confidence,
                                }
                                for s in sorted_signals
                            ],
                            resolved_to=winner.value,
                            reasoning=(
                                f"Selected from {winner.source} "
                                f"(precedence={self.SOURCE_PRECEDENCE.get(winner.source, 0)}) "
                                f"over {len(sorted_signals) - 1} conflicting sources."
                            ),
                        )
                    )
                else:
                    # All values are equivalent
                    self.reconciled[key] = sorted_signals[0].value

        return self.reconciled

    def detect_drift(self) -> list[SignalDrift]:
        """Compare current state to previous state."""
        self.drift.clear()

        if self.previous_state is None:
            self.previous_state = self.reconciled.copy()
            return self.drift

        for key, current_value in self.reconciled.items():
            previous_value = self.previous_state.get(key)
            if previous_value is None:
                # New signal
                self.drift.append(
                    SignalDrift(
                        key=key,
                        previous_value=None,
                        current_value=current_value,
                        change_magnitude=1.0,
                        alert_level="info",
                    )
                )
            elif previous_value != current_value:
                # Changed signal
                magnitude = self._calculate_drift_magnitude(previous_value, current_value)
                alert_level = "critical" if magnitude > 0.5 else "warning"
                self.drift.append(
                    SignalDrift(
                        key=key,
                        previous_value=previous_value,
                        current_value=current_value,
                        change_magnitude=magnitude,
                        alert_level=alert_level,
                    )
                )

        # Update for next cycle
        self.previous_state = self.reconciled.copy()
        return self.drift

    def _extract_key(self, signal: Signal) -> str:
        """Extract a grouping key from a signal."""
        if isinstance(signal.value, dict):
            # Try to infer a key
            if "error_count" in signal.value or "errors" in signal.value:
                return "error_count"
            if "warnings" in signal.value:
                return "warning_count"
            if "agent" in signal.value:
                return f"agent:{signal.value['agent']}"
            if "online" in signal.value:
                return "agent_status"
        return f"{signal.source}:{id(signal)}"

    @staticmethod
    def _calculate_drift_magnitude(prev: Any, curr: Any) -> float:
        """Rough drift magnitude (0.0-1.0)."""
        if isinstance(prev, (int, float)) and isinstance(curr, (int, float)):
            # Numeric change
            if prev == 0:
                return 1.0 if curr != 0 else 0.0
            change = abs(curr - prev) / abs(prev)
            return min(change, 1.0)
        return 0.5 if prev != curr else 0.0


# --- World State Builder ---


def build_world_state(
    workspace_root: Path = Path("."), previous_state: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build a unified world state by observing + reconciling signals.

    Args:
        workspace_root: Root path for observations
        previous_state: Prior world state (for drift detection)

    Returns:
        World state object (can be persisted/validated against world_state.schema.json)
    """
    started_at = datetime.now(UTC)

    # Observation: Collect signals from all sources
    observer = ObservationCollector(workspace_root)
    signals = observer.collect_all()

    # Coherence: Reconcile contradictions
    coherence = CoherenceEvaluator()
    reconciled = coherence.reconcile_signals(signals)
    if previous_state and "coherence" in previous_state:
        prev_reconciled = previous_state["coherence"].get("reconciled_facts", {})
        if isinstance(prev_reconciled, list):
            prev_map = {}
            for entry in prev_reconciled:
                if not isinstance(entry, dict):
                    continue
                key = entry.get("key")
                if isinstance(key, str) and key:
                    prev_map[key] = entry.get("value")
            coherence.previous_state = prev_map
        elif isinstance(prev_reconciled, dict):
            coherence.previous_state = prev_reconciled
    drift = coherence.detect_drift()

    # Derive capability/runtime views from signals.
    agent_capabilities: dict[str, dict[str, Any]] = {}
    diagnostic_summary = {"linting_errors": 0, "type_checking_errors": 0, "test_failures": 0}
    recent_quest_events: list[dict[str, Any]] = []
    quest_event_count = 0
    git_branch = "unknown"
    git_uncommitted: int | None = None

    for signal in signals:
        value = signal.value if isinstance(signal.value, dict) else {}
        if signal.source == "agent_probe":
            agent_name = value.get("agent")
            if isinstance(agent_name, str) and agent_name:
                agent_capabilities[agent_name] = {
                    "online": bool(value.get("online", False)),
                    "latency_ms": value.get("latency_ms"),
                    "last_probe": signal.timestamp,
                }
        elif signal.source == "diagnostic_tool":
            diagnostic_summary = {
                "linting_errors": int(value.get("errors", 0) or 0),
                "type_checking_errors": int(value.get("warnings", 0) or 0),
                "test_failures": int(value.get("test_failures", 0) or 0),
            }
        elif signal.source == "quest_log":
            quest_event_count += 1
            if len(recent_quest_events) < 10:
                recent_quest_events.append(
                    {
                        "event_type": value.get("event_type"),
                        "status": value.get("status"),
                    }
                )
        elif signal.source == "git_status":
            if isinstance(value.get("current_branch"), str) and value.get("current_branch"):
                git_branch = value["current_branch"]
            if isinstance(value.get("uncommitted_files"), int):
                git_uncommitted = value["uncommitted_files"]

    # Build world state
    now = datetime.now(UTC).isoformat()
    world_state: dict[str, Any] = {
        "timestamp": now,
        "decision_epoch": (previous_state or {}).get("decision_epoch", 0) + 1,
        "observations": {
            "context": {
                "user_message": os.getenv("NUSYQ_USER_MESSAGE", ""),
                "request_type": os.getenv("NUSYQ_REQUEST_TYPE", "analysis"),
                "workspace_folders": [str(workspace_root)],
                "active_file": os.getenv("NUSYQ_ACTIVE_FILE"),
                "terminal_context": {
                    "cwd": str(workspace_root),
                    "terminals_active": 0,
                },
            },
            "repo_graph": {
                "repos": [
                    {
                        "name": "nusyq-hub",
                        "path": str(workspace_root),
                        "current_branch": git_branch,
                        "default_branch": "master",
                        "uncommitted_changes": (
                            git_uncommitted if git_uncommitted is not None else 0
                        ),
                    }
                ]
            },
            "runtime_state": {
                "agents": agent_capabilities,
                "services": [],
                "queued_tasks": 0,
                "resource_usage": {"memory_percent": 0.0, "cpu_percent": 0.0},
            },
            "diagnostics": diagnostic_summary,
        },
        "signals": {
            "facts": [s.to_dict() for s in signals],
        },
        "coherence": {
            "reconciled_facts": [
                {
                    "key": key,
                    "value": value,
                    "source_precedence": [],
                }
                for key, value in reconciled.items()
            ],
            "contradictions": [asdict(c) for c in coherence.contradictions],
            "signal_drift": [asdict(d) for d in drift],
        },
        "runtime_state": {
            "agent_capabilities": agent_capabilities,
            "available_memory": {
                "quest_log": {
                    "total_quests": quest_event_count,
                    "pending": 0,
                    "active": 0,
                    "completed": 0,
                    "recent_events": recent_quest_events,
                },
                "action_receipts": {
                    "total_actions": 0,
                    "successful": 0,
                    "failed": 0,
                    "recent": [],
                },
            },
        },
        "policy_state": {
            "active_policies": [],
            "resource_budgets": {
                "token_budget_remaining": int(os.getenv("NUSYQ_TOKEN_BUDGET", "5000")),
                "time_budget_remaining_s": int(os.getenv("NUSYQ_TIME_BUDGET", "300")),
                "cpu_budget_remaining": 1.0,
            },
            "safety_gates": {
                "allow_mutations": os.getenv("NUSYQ_ALLOW_MUTATIONS", "false").lower() == "true",
                "require_culture_ship_approval": True,
                "max_risk_score": 0.7,
            },
        },
        "objective": {
            "user_intent": "",
            "quest_id": None,
            "required_capabilities": [],
            "success_criteria": [],
            "time_sensitivity": "normal",
        },
        "metadata": {
            "schema_version": "0.1",
            "generated_by": "build_world_state.py",
            "build_duration_ms": int((datetime.now(UTC) - started_at).total_seconds() * 1000),
        },
    }

    try:
        from src.system.agent_awareness import emit as _emit

        _dur = world_state["metadata"]["build_duration_ms"]
        _intent = world_state.get("current_intent", {}).get("primary_intent", "unknown")
        _emit(
            "system",
            f"World state built: intent={_intent} duration={_dur}ms",
            level="INFO",
            source="build_world_state",
        )
    except Exception:
        pass

    return world_state


if __name__ == "__main__":
    # Quick test: build and display world state
    logging.basicConfig(level=logging.INFO)
    state = build_world_state()
    logger.info(json.dumps(state, indent=2, default=str))
