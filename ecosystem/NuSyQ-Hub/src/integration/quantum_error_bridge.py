#!/usr/bin/env python3
"""Quantum Error Bridge - Connects error handling with quantum problem resolution.

Integrates:
- Autonomous Development Agent error handling
- Quantum Problem Resolver (quantum state-based healing)
- Adaptive Timeout Manager (failure tracking)
- PU Queue (error → PU conversion)

Philosophy: Errors are quantum problems - they exist in superposition until
we observe and collapse them into solutions.
"""

import logging
from pathlib import Path
from typing import Any

from src.automation.unified_pu_queue import PU, UnifiedPUQueue
from src.healing.quantum_problem_resolver import (ProblemSignature,
                                                  QuantumProblemResolver,
                                                  QuantumProblemState)

logger = logging.getLogger(__name__)


class QuantumErrorBridge:
    """Bridges error handling with quantum problem resolution.

    Workflow:
    1. Error occurs in autonomous agent
    2. Convert error → QuantumProblem (superposition state)
    3. Quantum resolver analyzes and proposes solutions
    4. If auto-fixable → Apply solution (collapse to resolved)
    5. If complex → Create PU → Quest (entangled state)
    6. Track resolution success → Update adaptive timeout
    """

    def __init__(self, root_path: Path | None = None) -> None:
        """Initialize quantum error bridge.

        Args:
            root_path: Repository root path
        """
        self.root_path = root_path or Path.cwd()
        self.quantum_resolver = QuantumProblemResolver(root_path=self.root_path)
        self.pu_queue = UnifiedPUQueue()

        logger.info("🌌 Quantum Error Bridge initialized")

    async def handle_error(
        self, error: Exception, context: dict[str, Any], auto_fix: bool = True
    ) -> dict[str, Any]:
        """Handle an error using quantum problem resolution.

        Args:
            error: Exception that occurred
            context: Error context (file, function, task, etc.)
            auto_fix: Whether to attempt automatic fixes

        Returns:
            Resolution result with status and actions taken
        """
        logger.info(f"🔮 Quantum error handling: {type(error).__name__}: {error}")

        # Convert error to quantum problem signature
        problem = self._error_to_problem(error, context)

        result: dict[str, Any] = {
            "error": str(error),
            "error_type": type(error).__name__,
            "quantum_state": problem.quantum_state.value,
            "resolution_attempted": False,
            "auto_fixed": False,
            "pu_created": False,
            "actions": [],
        }

        # Attempt quantum resolution if auto_fix enabled
        if auto_fix:
            logger.info("⚡ Attempting quantum resolution...")
            resolved = await self.quantum_resolver.resolve_quantum_problem(problem)

            result["resolution_attempted"] = True
            result["auto_fixed"] = resolved

            if resolved:
                logger.info("✅ Quantum resolution successful!")
                result["quantum_state"] = QuantumProblemState.RESOLVED.value
                result["actions"].append("quantum_auto_fix")
                return result

            logger.warning("⚠️ Quantum resolution failed, escalating...")

        # If not auto-fixed, create PU for quest system
        pu_created = self._create_error_pu(error, context, problem)
        result["pu_created"] = pu_created

        if pu_created:
            result["actions"].append("created_pu_for_manual_resolution")
            result["quantum_state"] = QuantumProblemState.ENTANGLED.value
            logger.info("📋 Created PU for manual resolution via quest system")

        return result

    def _error_to_problem(self, error: Exception, context: dict[str, Any]) -> ProblemSignature:
        """Convert an error to a quantum problem signature.

        Args:
            error: Exception
            context: Error context

        Returns:
            Quantum problem signature
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # Determine quantum state based on error type
        if "Timeout" in error_type or "timeout" in error_msg.lower():
            quantum_state = QuantumProblemState.SUPERPOSITION
            entanglement = 0.7  # Timeouts often entangled with system load
        elif "Import" in error_type or "Module" in error_type:
            quantum_state = QuantumProblemState.ENTANGLED
            entanglement = 0.9  # Import errors highly entangled
        elif "Syntax" in error_type or "Parse" in error_type:
            quantum_state = QuantumProblemState.COLLAPSED
            entanglement = 0.3  # Syntax errors usually isolated
        elif "Runtime" in error_type or "Value" in error_type:
            quantum_state = QuantumProblemState.SUPERPOSITION
            entanglement = 0.5  # Runtime errors moderately entangled
        else:
            quantum_state = QuantumProblemState.SUPERPOSITION
            entanglement = 0.5

        # Calculate resolution probability based on error type
        if error_type in ["SyntaxError", "IndentationError", "TypeError"]:
            resolution_prob = 0.8  # High probability of auto-fix
        elif error_type in ["ImportError", "ModuleNotFoundError"]:
            resolution_prob = 0.6  # Moderate probability
        elif error_type in ["TimeoutError", "ConnectionError"]:
            resolution_prob = 0.4  # Low probability (system-dependent)
        else:
            resolution_prob = 0.5

        # Narrative coherence (how well error fits expected behavior)
        narrative_coherence = 0.7  # Default moderate coherence

        problem_id = f"{error_type}_{context.get('file', 'unknown')}_{hash(error_msg) % 10000}"

        return ProblemSignature(
            problem_id=problem_id,
            quantum_state=quantum_state,
            entanglement_degree=entanglement,
            resolution_probability=resolution_prob,
            narrative_coherence=narrative_coherence,
            metadata={
                "error_type": error_type,
                "error_message": error_msg,
                "context": context,
                "file": context.get("file"),
                "function": context.get("function"),
                "task": context.get("task"),
            },
        )

    def _create_error_pu(
        self, error: Exception, context: dict[str, Any], problem: ProblemSignature
    ) -> bool:
        """Create a Processing Unit for unresolved errors.

        Args:
            error: Exception
            context: Error context
            problem: Quantum problem signature

        Returns:
            True if PU created successfully
        """
        import time

        try:
            error_type = type(error).__name__
            error_msg = str(error)

            # Determine PU type based on error
            if "Timeout" in error_type:
                pu_type = "OptimizationPU"
            elif (
                "Import" in error_type
                or "Module" in error_type
                or "Syntax" in error_type
                or "Parse" in error_type
            ):
                pu_type = "BugFixPU"
            else:
                pu_type = "BugFixPU"

            # Determine priority based on entanglement and resolution probability
            if problem.entanglement_degree > 0.7:
                priority = "high"
            elif problem.resolution_probability < 0.3:
                priority = "critical"
            else:
                priority = "medium"

            # Generate unique PU ID
            pu_id = f"PU_{error_type}_{hash(error_msg) % 10000}_{int(time.time())}"

            # Create PU (status is required parameter)
            pu = PU(
                id=pu_id,
                type=pu_type,
                title=f"Fix {error_type}: {error_msg[:50]}...",
                description=(
                    f"Error occurred in {context.get('task', 'unknown task')}\n\n"
                    f"Error: {error_type}: {error_msg}\n"
                    f"File: {context.get('file', 'unknown')}\n"
                    f"Function: {context.get('function', 'unknown')}\n\n"
                    f"Quantum Analysis:\n"
                    f"- State: {problem.quantum_state.value}\n"
                    f"- Entanglement: {problem.entanglement_degree:.0%}\n"
                    f"- Auto-fix probability: {problem.resolution_probability:.0%}"
                ),
                source_repo="NuSyQ-Hub",
                priority=priority,
                proof_criteria=[
                    f"Error no longer occurs when running {context.get('task', 'task')}",
                    "Code passes linting and type checking",
                    "Related tests pass",
                ],
                metadata={
                    "quantum_problem_id": problem.problem_id,
                    "error_context": context,
                    "auto_fix_attempted": True,
                    "auto_fix_failed": True,
                    "tags": [error_type, "auto_generated", "quantum_error"],
                },
                status="queued",
            )

            self.pu_queue.submit_pu(pu)
            logger.info(f"✅ Created {pu_type} (priority: {priority}) for {error_type}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create PU for error: {e}")
            return False

    async def scan_and_heal(self) -> dict[str, Any]:
        """Scan workspace for quantum problems and attempt healing.

        Returns:
            Healing summary with problems found and resolved
        """
        logger.info("🔍 Scanning workspace for quantum problems...")

        problems = await self.quantum_resolver.scan_quantum_problems()

        summary: dict[str, Any] = {
            "problems_found": len(problems),
            "auto_resolved": 0,
            "pus_created": 0,
            "failed": 0,
            "problems": [],
        }

        for problem in problems:
            try:
                # Attempt quantum resolution
                resolved = await self.quantum_resolver.resolve_quantum_problem(problem)

                if resolved:
                    summary["auto_resolved"] += 1
                    summary["problems"].append(
                        {
                            "id": problem.problem_id,
                            "status": "resolved",
                            "method": "quantum_auto_fix",
                        }
                    )
                else:
                    # Create PU for manual resolution
                    error_msg = problem.metadata.get("error_message", "Unknown issue")
                    context = problem.metadata.get("context", {})

                    # Simulate error for PU creation
                    simulated_error = Exception(error_msg)
                    pu_created = self._create_error_pu(simulated_error, context, problem)

                    if pu_created:
                        summary["pus_created"] += 1
                        summary["problems"].append(
                            {
                                "id": problem.problem_id,
                                "status": "escalated_to_pu",
                                "method": "manual_quest",
                            }
                        )
                    else:
                        summary["failed"] += 1
                        summary["problems"].append(
                            {
                                "id": problem.problem_id,
                                "status": "unresolved",
                                "method": "none",
                            }
                        )

            except Exception as e:
                logger.error(f"Error processing problem {problem.problem_id}: {e}")
                summary["failed"] += 1

        logger.info(
            f"🌌 Quantum healing complete: {summary['auto_resolved']} resolved, "
            f"{summary['pus_created']} PUs created, {summary['failed']} failed"
        )

        return summary


# Singleton instance
_bridge: QuantumErrorBridge | None = None


def get_quantum_error_bridge(root_path: Path | None = None) -> QuantumErrorBridge:
    """Get or create quantum error bridge singleton.

    Args:
        root_path: Repository root path

    Returns:
        Quantum error bridge instance
    """
    global _bridge
    if _bridge is None:
        _bridge = QuantumErrorBridge(root_path=root_path)
    return _bridge
