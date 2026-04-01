"""
Breathing & Pacing Extension for Adaptive Timeout Manager
==========================================================

Integration of SimulatedVerse breathing techniques with adaptive timeout system.

Philosophy:
   "Work faster when succeeding, slower when failing - breathe with the system"

    Breathing Concept (from SimulatedVerse):
        - Tau (τ) = base work cycle time
        - Tau Prime (τ') = adjusted work cycle based on patterns
        - Breathing Factor = τ' / τ (ranges 0.6-1.5x)Integration:
    - Extends AdaptiveTimeoutManager with session-level pacing
    - Tracks success_rate, backlog_level, failure_burst, stagnation
    - Adjusts timeouts dynamically based on breathing formula

Author: Claude Code (Sonnet 4.5)
Date: 2025-10-08
Status: Production - Breathing Integration
"""

import logging
from dataclasses import dataclass
from datetime import datetime
import statistics

logger = logging.getLogger("nusyq.breathing")


@dataclass
class BreathingState:
    """Current breathing/pacing state"""
    tau_base: float              # Base cycle time (seconds)
    tau_prime: float             # Adjusted cycle time
    breathing_factor: float      # Multiplier (0.6-1.5)
    success_rate: float          # Recent success rate (0.0-1.0)
    backlog_level: float         # Queue fullness (0.0-1.0)
    failure_burst: float         # Recent failure density (0.0-1.0)
    stall_detected: bool         # Stagnation flag
    reasoning: str               # Why this breathing factor?
    timestamp: datetime


class BreathingPacer:
    """
    Implements SimulatedVerse breathing techniques for adaptive pacing

    Features:
    - Success-rate-based acceleration/deceleration
    - Backlog-aware pacing
    - Failure burst detection
    - Stagnation recovery
    - Statistical smoothing (prevents oscillation)

    Breathing Formula:
        τ' = τ_base × breathing_factor(metrics)

    Factor Ranges:
        - 0.60x: Emergency acceleration (high failures + heavy backlog)
        - 0.85x: Moderate acceleration (high success + moderate backlog)
        - 1.00x: Steady state (normal operation)
        - 1.20x: Moderate deceleration (failures increasing)
        - 1.50x: Emergency brake (critical failures/stall)

    Example:
        pacer = BreathingPacer(tau_base=90.0)

        # Update with session metrics
        state = pacer.calculate_breathing(
            success_rate=0.95,
            backlog_level=0.30,
            failure_burst=0.0,
            stall_detected=False
        )

        # Apply to timeout
        adjusted_timeout = base_timeout * state.breathing_factor
    """

    def __init__(
        self,
        tau_base: float = 90.0,
        bounds: tuple = (60.0, 150.0),
        smoothing_window: int = 10
    ):
        """
        Initialize breathing pacer

        Args:
            tau_base: Base cycle time in seconds (default: 90s)
            bounds: Min/max tau limits (default: 60-150s)
            smoothing_window: Number of recent states for smoothing
        """
        self.tau_base = tau_base
        self.tau_min, self.tau_max = bounds
        self.smoothing_window = smoothing_window
        self.history: list[BreathingState] = []

    def calculate_breathing(
        self,
        success_rate: float,
        backlog_level: float,
        failure_burst: float = 0.0,
        stall_detected: bool = False
    ) -> BreathingState:
        """
        Calculate breathing factor based on current session metrics

        Args:
            success_rate: Recent task success rate (0.0-1.0)
            backlog_level: Queue fullness (0.0-1.0, where 1.0 = full)
            failure_burst: Recent failure density (0.0-1.0)
            stall_detected: True if system appears stagnant

        Returns:
            BreathingState with calculated tau_prime and reasoning
        """
        # Normalize inputs
        success_rate = max(0.0, min(1.0, success_rate))
        backlog_level = max(0.0, min(1.0, backlog_level))
        failure_burst = max(0.0, min(1.0, failure_burst))

        # Calculate breathing factor using SimulatedVerse logic
        breathing_factor, reasoning = self._calculate_factor(
            success_rate,
            backlog_level,
            failure_burst,
            stall_detected
        )

        # Apply smoothing if we have history
        if len(self.history) >= 3:
            recent_factors = [
                s.breathing_factor
                for s in self.history[-self.smoothing_window:]
            ]
            recent_factors.append(breathing_factor)
            breathing_factor = statistics.median(recent_factors)
            reasoning += " (smoothed)"

        # Calculate tau_prime with bounds
        tau_prime = self.tau_base * breathing_factor
        tau_prime = max(self.tau_min, min(self.tau_max, tau_prime))

        state = BreathingState(
            tau_base=self.tau_base,
            tau_prime=tau_prime,
            breathing_factor=breathing_factor,
            success_rate=success_rate,
            backlog_level=backlog_level,
            failure_burst=failure_burst,
            stall_detected=stall_detected,
            reasoning=reasoning,
            timestamp=datetime.now()
        )

        # Store in history
        self.history.append(state)
        if len(self.history) > self.smoothing_window * 2:
            self.history = self.history[-self.smoothing_window:]

        logger.info(
            "Breathing: τ_base=%ss → τ'=%.1fs (factor=%.2fx, %s)",
            self.tau_base, tau_prime, breathing_factor, reasoning
        )

        return state

    def _calculate_factor(
        self,
        success_rate: float,
        backlog_level: float,
        failure_burst: float,
        stall_detected: bool
    ) -> tuple[float, str]:
        """
        Core breathing factor calculation (SimulatedVerse algorithm)

        Returns:
            (breathing_factor, reasoning)
        """
        # EMERGENCY BRAKE: Stalled system
        if stall_detected:
            return (1.5, "stagnation_detected")

        # EMERGENCY BRAKE: Critical failure burst
        if failure_burst > 0.7:
            return (1.5, "critical_failure_burst")

        # DECELERATE: High failures
        if success_rate < 0.5:
            if backlog_level > 0.6:
                return (1.4, "high_failures_heavy_backlog")
            else:
                return (1.2, "high_failure_rate")

        # DECELERATE: Moderate failures with heavy load
        if success_rate < 0.7 and backlog_level > 0.7:
            return (1.15, "moderate_failures_heavy_load")

        # ACCELERATE: High success, light/moderate backlog
        if success_rate > 0.9:
            if backlog_level < 0.3:
                return (0.85, "high_success_light_backlog")
            elif backlog_level < 0.5:
                return (0.9, "high_success_moderate_backlog")

        # ACCELERATE: High success, manageable load
        if success_rate > 0.8 and backlog_level < 0.6:
            return (0.95, "good_success_manageable_load")

        # STEADY STATE: Normal operation
        return (1.0, "steady_state")

    def get_recent_trend(self, lookback: int = 5) -> str:
        """
        Analyze recent breathing trend

        Returns:
            "accelerating", "decelerating", "stable", or "insufficient_data"
        """
        if len(self.history) < lookback:
            return "insufficient_data"

        recent = self.history[-lookback:]
        factors = [s.breathing_factor for s in recent]

        if len(set(factors)) == 1:
            return "stable"

        # Check trend
        first_half = statistics.mean(factors[:len(factors)//2])
        second_half = statistics.mean(factors[len(factors)//2:])

        if second_half < first_half * 0.95:
            return "accelerating"
        elif second_half > first_half * 1.05:
            return "decelerating"
        else:
            return "stable"


def integrate_breathing_with_timeout(
    base_timeout: float,
    pacer: BreathingPacer,
    success_rate: float,
    backlog_level: float = 0.0,
    failure_burst: float = 0.0,
    stall_detected: bool = False
) -> tuple[float, BreathingState]:
    """
    Helper function to integrate breathing with adaptive timeout

    Args:
        base_timeout: Timeout from AdaptiveTimeoutManager
        pacer: BreathingPacer instance
        success_rate: Recent success rate
        backlog_level: Queue fullness
        failure_burst: Recent failure density
        stall_detected: Stagnation flag

    Returns:
        (adjusted_timeout, breathing_state)

    Example:
        from config.adaptive_timeout_manager import (
            get_timeout_manager, AgentType, TaskComplexity
        )
        from config.breathing_pacing import (
            BreathingPacer, integrate_breathing_with_timeout
        )

        # Get base timeout
        timeout_mgr = get_timeout_manager()
        rec = timeout_mgr.get_timeout(
            AgentType.LOCAL_QUALITY, TaskComplexity.MODERATE
        )

        # Apply breathing
        bp = BreathingPacer(tau_base=rec.timeout_seconds)
        adjusted, breath = integrate_breathing_with_timeout(
            base_timeout=rec.timeout_seconds,
            pacer=bp,
            success_rate=0.95,
            backlog_level=0.30
        )

        print(f"Base: {rec.timeout_seconds}s → "
              f"Adjusted: {adjusted:.1f}s")
        print(f"Breathing: {breath.reasoning}")
    """
    state = pacer.calculate_breathing(
        success_rate=success_rate,
        backlog_level=backlog_level,
        failure_burst=failure_burst,
        stall_detected=stall_detected
    )

    adjusted_timeout = base_timeout * state.breathing_factor

    logger.info(
        "Breathing integration: %.1fs × %.2f = %.1fs (%s)",
        base_timeout, state.breathing_factor, adjusted_timeout,
        state.reasoning
    )

    return adjusted_timeout, state


# Example/Test code
if __name__ == "__main__":
    import sys
    import io

    # Fix Windows UTF-8
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    logging.basicConfig(level=logging.INFO)

    print("=== Breathing & Pacing Demo ===\n")

    pacer = BreathingPacer(tau_base=90.0)

    # Scenario 1: High success, light backlog → Accelerate
    print("Scenario 1: High success (95%), light backlog (30%)")
    state = pacer.calculate_breathing(success_rate=0.95, backlog_level=0.30)
    print(f"  τ_base={state.tau_base}s → τ'={state.tau_prime:.1f}s (×{state.breathing_factor:.2f})")
    print(f"  Reasoning: {state.reasoning}\n")

    # Scenario 2: Low success → Decelerate
    print("Scenario 2: Low success (40%), heavy backlog (70%)")
    state = pacer.calculate_breathing(success_rate=0.40, backlog_level=0.70)
    print(f"  τ_base={state.tau_base}s → τ'={state.tau_prime:.1f}s (×{state.breathing_factor:.2f})")
    print(f"  Reasoning: {state.reasoning}\n")

    # Scenario 3: Stagnation → Emergency brake
    print("Scenario 3: Stagnation detected")
    state = pacer.calculate_breathing(success_rate=0.0, backlog_level=0.95, stall_detected=True)
    print(f"  τ_base={state.tau_base}s → τ'={state.tau_prime:.1f}s (×{state.breathing_factor:.2f})")
    print(f"  Reasoning: {state.reasoning}\n")

    print(f"Trend analysis: {pacer.get_recent_trend()}")
