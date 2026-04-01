#!/usr/bin/env python3
"""⏱️ Breathing Pacing Integration.

Integrates SimulatedVerse breathing techniques with NuSyQ-Hub timeout system.
Provides adaptive pacing based on success rates, backlog, and failure patterns.

OmniTag: {
    "purpose": "Adaptive timeout pacing with breathing formula",
    "dependencies": ["timeout_config", "breathing_pacing"],
    "context": "System pacing and performance optimization",
    "evolution_stage": "v1.0"
}
MegaTag: BREATHING⨳PACING⦾TAU_PRIME→∞
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any


def _candidate_nusyq_roots() -> list[Path]:
    """Return likely NuSyQ roots without depending on env ordering."""
    current_file = Path(__file__).resolve()
    hub_root = current_file.parents[2]
    env_root = os.environ.get("NUSYQ_ROOT_PATH")
    candidates = [
        Path(env_root).expanduser() if env_root else None,
        hub_root.parent / "NuSyQ",
        hub_root.parent.parent / "NuSyQ",
        hub_root.parent.parent.parent / "NuSyQ",
        Path("/mnt/c/Users") if Path("/mnt/c/Users").exists() else None,
    ]

    roots: list[Path] = []
    for candidate in candidates:
        if candidate is None:
            continue
        if candidate.name == "Users":
            for user_dir in candidate.iterdir():
                roots.append(user_dir / "NuSyQ")
            continue
        roots.append(candidate)
    return roots


def _is_nusyq_root(candidate: Path) -> bool:
    """Check whether a path looks like the NuSyQ repo root."""
    return candidate.exists() and (
        (candidate / "config" / "breathing_pacing.py").exists()
        or (candidate / "knowledge-base.yaml").exists()
        or (candidate / "nusyq.manifest.yaml").exists()
    )


def _resolve_nusyq_root() -> Path | None:
    """Find a usable NuSyQ root and export it for later imports."""
    for candidate in _candidate_nusyq_roots():
        if _is_nusyq_root(candidate):
            os.environ.setdefault("NUSYQ_ROOT_PATH", str(candidate))
            return candidate
    return None


def _load_breathing_pacer() -> type[Any] | None:
    """Load BreathingPacer from NuSyQ via package import or direct file import."""
    nusyq_root = _resolve_nusyq_root()
    if not nusyq_root:
        return None

    root_text = str(nusyq_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)

    try:
        from config.breathing_pacing import BreathingPacer

        return BreathingPacer
    except ImportError:
        config_path = nusyq_root / "config" / "breathing_pacing.py"
        if not config_path.exists():
            return None
        spec = importlib.util.spec_from_file_location("nusyq_breathing_pacing", config_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        breathing_pacer = getattr(module, "BreathingPacer", None)
        if isinstance(breathing_pacer, type):
            return breathing_pacer
        return None


logger = logging.getLogger(__name__)


class BreathingIntegration:
    """Integrates SimulatedVerse breathing techniques with timeout system.

    Philosophy:
        "Work faster when succeeding, slower when failing - breathe with the system"

    Breathing Formula:
        τ' = τ_base × breathing_factor

    Factor Ranges:
        - 0.60x: Emergency acceleration (high failures + heavy backlog)
        - 0.85x: Moderate acceleration (high success + moderate backlog)
        - 1.00x: Steady state (normal operation)
        - 1.20x: Moderate deceleration (failures increasing)
        - 1.50x: Emergency brake (critical failures/stall)
    """

    def __init__(self, tau_base: float = 90.0, enable_breathing: bool = True) -> None:
        """Initialize breathing integration.

        Args:
            tau_base: Base cycle time in seconds (default: 90s)
            enable_breathing: Enable breathing adjustments
        """
        self.tau_base = tau_base
        self.enable_breathing = enable_breathing
        self.current_factor = 1.0
        self.breathing_pacer = None

        # Try to load BreathingPacer from NuSyQ
        if self.enable_breathing:
            try:
                BreathingPacer = _load_breathing_pacer()
                if BreathingPacer is None:
                    raise ImportError("BreathingPacer could not be resolved")
                self.breathing_pacer = BreathingPacer(tau_base=tau_base)
                logger.info(f"⏱️  Breathing integration enabled (τ={tau_base}s)")
            except ImportError:
                logger.warning("⚠️  BreathingPacer not available, using static pacing")
                self.enable_breathing = False
        else:
            logger.info("⏱️  Breathing integration disabled")

    def calculate_breathing_factor(
        self,
        success_rate: float,
        backlog_level: float,
        failure_burst: float = 0.0,
        stall_detected: bool = False,
    ) -> float:
        """Calculate breathing factor based on system metrics.

        Args:
            success_rate: Recent success rate (0.0-1.0)
            backlog_level: Queue fullness (0.0-1.0)
            failure_burst: Recent failure density (0.0-1.0)
            stall_detected: Whether system is stalled

        Returns:
            Breathing factor multiplier (0.6-1.5)
        """
        if not self.enable_breathing or not self.breathing_pacer:
            return 1.0

        try:
            state = self.breathing_pacer.calculate_breathing(
                success_rate=success_rate,
                backlog_level=backlog_level,
                failure_burst=failure_burst,
                stall_detected=stall_detected,
            )

            self.current_factor = float(getattr(state, "breathing_factor", 1.0))
            logger.debug(
                f"⏱️  Breathing: {state.breathing_factor:.2f}x "
                f"(success={success_rate:.2%}, backlog={backlog_level:.2%}) "
                f"- {state.reasoning}"
            )

            return float(getattr(state, "breathing_factor", 1.0))

        except (AttributeError, ValueError, TypeError, RuntimeError) as e:
            logger.exception(f"❌ Breathing calculation failed: {e}")
            return 1.0

    def apply_to_timeout(self, base_timeout: float) -> float:
        """Apply breathing factor to a base timeout.

        Args:
            base_timeout: Original timeout value in seconds

        Returns:
            Adjusted timeout with breathing factor applied
        """
        if not self.enable_breathing:
            return base_timeout

        adjusted = base_timeout * self.current_factor

        # Sanity bounds
        min_timeout = base_timeout * 0.5
        max_timeout = base_timeout * 2.0
        adjusted = max(min_timeout, min(max_timeout, adjusted))

        logger.debug(
            f"⏱️  Timeout adjusted: {base_timeout}s → {adjusted:.1f}s ({self.current_factor:.2f}x)"
        )
        return adjusted

    def get_breathing_state(self) -> dict:
        """Get current breathing state.

        Returns:
            Dictionary with breathing metrics
        """
        if not self.enable_breathing or not self.breathing_pacer:
            return {
                "enabled": False,
                "tau_base": self.tau_base,
                "current_factor": 1.0,
                "message": "Breathing integration disabled",
            }

        history = self.breathing_pacer.history
        latest = history[-1] if history else None

        return {
            "enabled": True,
            "tau_base": self.tau_base,
            "current_factor": self.current_factor,
            "tau_prime": self.tau_base * self.current_factor if latest else None,
            "recent_state": (
                {
                    "breathing_factor": latest.breathing_factor if latest else 1.0,
                    "success_rate": latest.success_rate if latest else 0.0,
                    "backlog_level": latest.backlog_level if latest else 0.0,
                    "reasoning": latest.reasoning if latest else "No data",
                }
                if latest
                else None
            ),
            "history_length": len(history),
        }

    def update_metrics(
        self,
        successful_operations: int,
        failed_operations: int,
        queue_size: int,
        queue_capacity: int,
    ) -> float:
        """Update breathing metrics from system state.

        Args:
            successful_operations: Recent successful operations
            failed_operations: Recent failed operations
            queue_size: Current queue size
            queue_capacity: Maximum queue capacity

        Returns:
            Updated breathing factor
        """
        total_ops = successful_operations + failed_operations
        success_rate = successful_operations / total_ops if total_ops > 0 else 0.5
        backlog_level = queue_size / queue_capacity if queue_capacity > 0 else 0.0
        failure_burst = failed_operations / total_ops if total_ops > 0 else 0.0
        elapsed_time = 0.0  # Initialize elapsed_time (should be passed as parameter or calculated)

        # Detect stall: high backlog + low success + time elapsed
        stall_detected = backlog_level > 0.7 and success_rate < 0.3 and elapsed_time > 30.0

        return self.calculate_breathing_factor(
            success_rate=success_rate,
            backlog_level=backlog_level,
            failure_burst=failure_burst,
            stall_detected=stall_detected,
        )


# Singleton instance
breathing_integration = BreathingIntegration()


def demo_breathing() -> None:
    """Demo breathing integration with various scenarios."""
    logger.info("⏱️  Breathing Pacing Integration Demo")
    logger.info("=" * 60)

    integration = BreathingIntegration(tau_base=90.0, enable_breathing=True)
    base_timeout = 120.0

    scenarios = [
        ("High Success, Low Backlog", 0.95, 0.20, 0.05, False),
        ("Normal Operation", 0.80, 0.50, 0.10, False),
        ("High Failures", 0.40, 0.60, 0.30, False),
        ("Critical Stall", 0.20, 0.90, 0.50, True),
        ("Recovery", 0.75, 0.40, 0.15, False),
    ]

    for name, success, backlog, failure, stall in scenarios:
        factor = integration.calculate_breathing_factor(
            success_rate=success,
            backlog_level=backlog,
            failure_burst=failure,
            stall_detected=stall,
        )

        adjusted_timeout = integration.apply_to_timeout(base_timeout)

        logger.info(f"\n{name}:")
        logger.info(f"   Success Rate: {success:.0%}")
        logger.info(f"   Backlog: {backlog:.0%}")
        logger.error(f"   Failure Burst: {failure:.0%}")
        logger.info(f"   Stalled: {stall}")
        logger.info(f"   → Breathing Factor: {factor:.2f}x")
        logger.info(f"   → Timeout: {base_timeout}s → {adjusted_timeout:.1f}s")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Breathing integration demo complete")


if __name__ == "__main__":
    demo_breathing()
