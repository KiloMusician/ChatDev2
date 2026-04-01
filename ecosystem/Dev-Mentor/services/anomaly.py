"""
services/anomaly.py — Anomaly Detection for Terminal Depths
===========================================================
Lightweight behavioral anomaly detection for game events and agent activity.

Uses Z-score statistical analysis + exponential smoothing to detect:
  - Unusual command frequencies
  - XP gain spikes (cheating signals)
  - CHIMERA activity bursts
  - Trust score anomalies

No ML framework needed — pure Python stats. Fast, zero-token, deterministic.

Usage:
    from services.anomaly import AnomalyDetector
    detector = AnomalyDetector()
    result = detector.observe("command_run", {"cmd": "exploit", "xp": 50})
    if result.is_anomaly:
        print(f"ANOMALY: {result.description} (z={result.z_score:.2f})")
"""
from __future__ import annotations

import json
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AnomalyResult:
    is_anomaly: bool
    event_type: str
    z_score: float
    description: str
    severity: str  # "low" | "medium" | "high" | "critical"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "is_anomaly": self.is_anomaly,
            "event_type": self.event_type,
            "z_score": round(self.z_score, 3),
            "description": self.description,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Rolling stats tracker (Welford's online algorithm)
# ---------------------------------------------------------------------------

class _RollingStats:
    """Online mean/variance using Welford's algorithm. O(1) memory."""

    def __init__(self, window: int = 100):
        self._window = window
        self._values: deque = deque(maxlen=window)
        self._n = 0
        self._mean = 0.0
        self._M2 = 0.0  # sum of squared deviations

    def update(self, x: float) -> None:
        if len(self._values) == self._window:
            # Remove oldest value (approximate — Welford doesn't support deletion natively)
            # Recompute from scratch when window full — acceptable for window=100
            self._values.append(x)
            vals = list(self._values)
            self._n = len(vals)
            self._mean = sum(vals) / self._n
            self._M2 = sum((v - self._mean) ** 2 for v in vals)
        else:
            self._values.append(x)
            self._n += 1
            delta = x - self._mean
            self._mean += delta / self._n
            delta2 = x - self._mean
            self._M2 += delta * delta2

    @property
    def mean(self) -> float:
        return self._mean

    @property
    def std(self) -> float:
        if self._n < 2:
            return 0.0
        return math.sqrt(self._M2 / (self._n - 1))

    @property
    def count(self) -> int:
        return self._n

    def z_score(self, x: float) -> float:
        s = self.std
        if s < 1e-9:
            return 0.0
        return (x - self.mean) / s


# ---------------------------------------------------------------------------
# Anomaly Detector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """
    Behavioral anomaly detector for Terminal Depths events.

    Tracks rolling statistics per event_type and flags outliers
    using configurable Z-score thresholds.
    """

    THRESHOLDS = {
        "low":      2.0,
        "medium":   2.5,
        "high":     3.0,
        "critical": 4.0,
    }

    # Event types → what numeric value to track
    EVENT_EXTRACTORS: Dict[str, Any] = {
        "command_run":   lambda d: d.get("xp", 0),
        "xp_gain":       lambda d: d.get("amount", 0),
        "trust_change":  lambda d: abs(d.get("delta", 0)),
        "faction_rep":   lambda d: abs(d.get("delta", 0)),
        "exploit_run":   lambda d: d.get("trace_level", 0),
        "agent_message": lambda d: len(d.get("text", "")),
        "timer_tick":    lambda d: d.get("remaining", 0),
    }

    def __init__(self, db_path: Optional[Path] = None, window: int = 50):
        self._stats: Dict[str, _RollingStats] = defaultdict(lambda: _RollingStats(window))
        self._history: deque = deque(maxlen=200)
        self._db_path = db_path or Path("state/anomaly_log.jsonl")
        self._recent_anomalies: deque = deque(maxlen=10)

    def observe(self, event_type: str, data: dict) -> AnomalyResult:
        """
        Observe an event. Return AnomalyResult (may or may not be anomaly).
        Thread-safe for single-process use.
        """
        extractor = self.EVENT_EXTRACTORS.get(event_type)
        if not extractor:
            return AnomalyResult(False, event_type, 0.0, "Unknown event type", "low")

        try:
            value = float(extractor(data))
        except (TypeError, ValueError):
            value = 0.0

        stats = self._stats[event_type]
        z = stats.z_score(value)

        # Determine severity
        severity = "low"
        is_anomaly = False
        for sev, threshold in [("critical", self.THRESHOLDS["critical"]),
                                ("high",     self.THRESHOLDS["high"]),
                                ("medium",   self.THRESHOLDS["medium"]),
                                ("low",      self.THRESHOLDS["low"])]:
            if abs(z) >= threshold and stats.count >= 10:
                severity = sev
                is_anomaly = True
                break

        stats.update(value)

        description = self._describe(event_type, value, z, data, is_anomaly)
        result = AnomalyResult(is_anomaly, event_type, z, description, severity)

        self._history.append(result.to_dict())
        if is_anomaly:
            self._recent_anomalies.append(result.to_dict())
            self._log(result)

        return result

    def _describe(self, event_type: str, value: float, z: float, data: dict, is_anomaly: bool) -> str:
        if not is_anomaly:
            return f"{event_type} nominal (value={value:.1f})"
        direction = "spike" if z > 0 else "dip"
        templates = {
            "command_run":   f"XP {direction} on command '{data.get('cmd','?')}': {value:.0f} XP (z={z:.2f})",
            "xp_gain":       f"XP gain {direction}: +{value:.0f} (z={z:.2f}σ) — possible exploit",
            "trust_change":  f"Trust {direction}: Δ{value:.0f} with {data.get('agent','?')} (z={z:.2f}σ)",
            "faction_rep":   f"Faction rep {direction}: Δ{value:.0f} for {data.get('faction','?')} (z={z:.2f}σ)",
            "exploit_run":   f"Trace level {direction}: {value:.0f} (z={z:.2f}σ) — CHIMERA may notice",
            "agent_message": f"Unusually {'long' if z > 0 else 'short'} agent message: {int(value)} chars",
        }
        return templates.get(event_type, f"{event_type} anomaly: value={value:.1f} z={z:.2f}")

    def _log(self, result: AnomalyResult) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._db_path, "a") as f:
                f.write(json.dumps(result.to_dict()) + "\n")
        except OSError:
            pass

    def get_recent_anomalies(self, limit: int = 10) -> List[dict]:
        return list(self._recent_anomalies)[-limit:]

    def get_stats_summary(self) -> dict:
        return {
            event_type: {
                "count": s.count,
                "mean": round(s.mean, 2),
                "std": round(s.std, 2),
            }
            for event_type, s in self._stats.items()
        }

    def health(self) -> dict:
        return {
            "status": "ok",
            "tracked_event_types": len(self._stats),
            "recent_anomalies": len(self._recent_anomalies),
            "history_size": len(self._history),
        }


# ---------------------------------------------------------------------------
# Singleton for game server use
# ---------------------------------------------------------------------------

_detector: Optional[AnomalyDetector] = None


def get_detector() -> AnomalyDetector:
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector


def observe(event_type: str, data: dict) -> AnomalyResult:
    """Module-level convenience function."""
    return get_detector().observe(event_type, data)


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    detector = AnomalyDetector()

    print("Anomaly Detector — feeding synthetic events...")
    # Warmup: 20 normal events
    for i in range(20):
        r = detector.observe("xp_gain", {"amount": 10 + (i % 5)})
    print(f"After 20 normal events: {detector.get_stats_summary()}")

    # Spike
    r = detector.observe("xp_gain", {"amount": 999})
    print(f"\nSpike: {r.to_dict()}")

    # Another normal
    r = detector.observe("xp_gain", {"amount": 12})
    print(f"Normal after spike: is_anomaly={r.is_anomaly}")

    print(f"\nHealth: {detector.health()}")
    print(f"Recent anomalies: {detector.get_recent_anomalies()}")
