"""EOL Facade Integration.

This file contains the EOLFacade class and integration code to add to orchestrate.py.

The EpistemicOperationalLattice is accessed via:
    nusyq.eol.sense()
    nusyq.eol.propose(world_state, objective)
    nusyq.eol.act(action, world_state, dry_run=False)
    nusyq.eol.full_cycle(objective, auto_execute=False)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.result import Fail, Ok, Result

if TYPE_CHECKING:
    from src.core.orchestrate import NuSyQOrchestrator


class EOLFacade:
    """Facade for Epistemic-Operational Lattice operations.

    Provides access to the complete sense → propose → critique → act
    decision cycle with full tracing and immutable receipts.

    Example:
        >>> from src.core.orchestrate import nusyq
        >>>
        >>> # Full cycle
        >>> result = nusyq.eol.full_cycle("Analyze errors", auto_execute=False)
        >>> if result.ok:
        ...     world_state = result.value['world_state']
        ...     actions = result.value['actions']
        >>>
        >>> # Manual phases
        >>> world = nusyq.eol.sense()
        >>> actions = nusyq.eol.propose(world, "Fix the bug")
        >>> receipt = nusyq.eol.act(actions[0], world)
    """

    def __init__(self, parent: NuSyQOrchestrator):
        """Initialize EOLFacade with parent."""
        self._parent = parent
        self._orchestrator = None

    def _get_orchestrator(self):
        """Lazily load EOL orchestrator."""
        if self._orchestrator is None:
            try:
                from src.core.eol_integration import EOLOrchestrator

                self._orchestrator = EOLOrchestrator(workspace_root=Path("."))
            except ImportError:
                return None
        return self._orchestrator

    def sense(self) -> Result[dict]:
        """Build unified world state from all signals.

        Returns:
            Result containing world state dict on success, or Fail on error.

        Example:
            >>> result = nusyq.eol.sense()
            >>> if result.ok:
            ...     print(f"Epoch: {result.value['decision_epoch']}")
            ...     print(f"Contradictions: {len(result.value['coherence']['contradictions'])}")
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            world_state = orch.sense()
            return Ok(
                world_state, message=f"World state built (epoch {world_state['decision_epoch']})"
            )

        except Exception as e:
            return Fail(str(e), code="SENSE_ERROR")

    def propose(self, world_state: dict[str, Any], objective: str = "") -> Result[list[dict]]:
        """Generate action candidates from world state + objective.

        Args:
            world_state: Output from sense()
            objective: What user wants (e.g., "Analyze errors and suggest fixes")

        Returns:
            Result containing list of Action dicts, ordered by priority.

        Example:
            >>> result = nusyq.eol.propose(world_state, "Fix failing tests")
            >>> if result.ok:
            ...     for action in result.value:
            ...         print(f"  {action['agent']}: {action['task_type']}")
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            actions = orch.propose(world_state, objective)
            return Ok(actions, message=f"Generated {len(actions)} action candidates")

        except Exception as e:
            return Fail(str(e), code="PROPOSE_ERROR")

    def critique(self, action: dict[str, Any], world_state: dict[str, Any]) -> Result[bool]:
        """Evaluate action against policy gates.

        Args:
            action: Action dict from propose()
            world_state: Current world state

        Returns:
            Result containing bool (approved=True, rejected=False).

        Example:
            >>> result = nusyq.eol.critique(actions[0], world_state)
            >>> if result.ok and result.value:
            ...     print("Action approved; ready to execute")
            ...elif result.ok:
            ...     print("Action rejected by policy")
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            approved = orch.critique(action, world_state)
            return Ok(approved, message="approved" if approved else "rejected by policy")

        except Exception as e:
            return Fail(str(e), code="CRITIQUE_ERROR")

    def act(
        self,
        action: dict[str, Any],
        world_state: dict[str, Any],
        dry_run: bool = False,
    ) -> Result[dict]:
        """Execute action with full tracing and receipt logging.

        Args:
            action: Action dict from propose()
            world_state: Current world state
            dry_run: If True, simulate without actual dispatch

        Returns:
            Result containing ActionReceipt dict.

        Example:
            >>> result = nusyq.eol.act(actions[0], world_state, dry_run=True)
            >>> if result.ok:
            ...     receipt = result.value
            ...     print(f"Status: {receipt['status']}")
            ...     print(f"Duration: {receipt['duration_s']}s")
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            receipt = orch.act(action, world_state, dry_run=dry_run)
            return Ok(receipt.to_dict(), message=f"Action executed with status {receipt.status}")

        except Exception as e:
            return Fail(str(e), code="ACT_ERROR")

    def full_cycle(
        self,
        objective: str = "",
        auto_execute: bool = False,
        dry_run: bool = False,
    ) -> Result[dict]:
        """Run complete sense → propose → critique → act cycle.

        Args:
            objective: What user wants done (e.g., "Analyze errors")
            auto_execute: If True, automatically execute top action
            dry_run: If True, simulate execution without dispatch

        Returns:
            Result containing cycle output dict with world_state, actions, results.

        Example:
            >>> result = nusyq.eol.full_cycle("Analyze errors", auto_execute=False)
            >>> if result.ok:
            ...     output = result.value
            ...     print(f"Candidates: {len(output['actions'])}")
            ...     print(f"Approved: {len(output['approved_actions'])}")
            ...     print(f"Executed: {len(output['execution_results'])}")
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            output = orch.full_cycle(objective, auto_execute=auto_execute, dry_run=dry_run)
            return Ok(output, message="Full cycle complete")

        except Exception as e:
            return Fail(str(e), code="FULL_CYCLE_ERROR")

    def stats(self) -> Result[dict]:
        """Get action execution statistics.

        Returns:
            Result containing stats dict with success rates, by_agent, etc.

        Example:
            >>> result = nusyq.eol.stats()
            >>> if result.ok:
            ...     stats = result.value
            ...     print(f"Success rate: {stats['success_rate']:.1%}")
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            stat_dict = orch.stats()
            return Ok(stat_dict)

        except Exception as e:
            return Fail(str(e), code="STATS_ERROR")

    def debug(self) -> Result[dict]:
        """Get debug information about EOL system.

        Returns:
            Result containing debug dict with paths, state, etc.
        """
        try:
            orch = self._get_orchestrator()
            if not orch:
                return Fail("EOL orchestrator not available", code="UNAVAILABLE")

            debug_dict = orch.debug_info()
            return Ok(debug_dict)

        except Exception as e:
            return Fail(str(e), code="DEBUG_ERROR")


# Code to add to NuSyQOrchestrator class
_INTEGRATION_CODE_SNIPPET = """
    def __init__(self) -> None:
        \"\"\"Initialize the NuSyQOrchestrator.

        Creates a new orchestrator instance with lazy-loaded facades
        for each subsystem. Facades are only instantiated when first accessed.
        \"\"\"
        self._search: SearchFacade | None = None
        self._quest: QuestFacade | None = None
        self._council: CouncilFacade | None = None
        self._background: BackgroundFacade | None = None
        self._factory: FactoryFacade | None = None
        self._eol: EOLFacade | None = None  # <--- ADD THIS LINE

    @property
    def eol(self) -> EOLFacade:
        \"\"\"Access the Epistemic-Operational Lattice facade.

        Returns the EOL orchestrator for sense → propose → act workflows.

        Returns:
            EOLFacade: Facade providing EOL decision cycle operations.

        Example:
            >>> result = nusyq.eol.full_cycle("Analyze errors", auto_execute=False)
            >>> if result.ok:
            ...     print(f"Actions: {len(result.value['actions'])}")
        \"\"\"
        if self._eol is None:
            self._eol = EOLFacade(self)
        return self._eol
"""

__all__ = ["EOLFacade"]
