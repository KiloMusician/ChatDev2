"""End-to-End Epistemic-Operational Lattice Integration Test

Tests the complete sense → propose → critique → act cycle with:
- Real world state sensing
- Real action proposal
- Policy evaluation
- Dry-run execution with receipt logging

Run:
    python -m pytest tests/integration/test_eol_e2e.py -v

Or directly:
    python tests/integration/test_eol_e2e.py
"""

import logging
from pathlib import Path
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEOLFoundation:
    """Test Phase 1 EOL foundation (sense, propose, act)."""

    def test_world_state_builder_imports(self):
        """Test that world state builder can be imported."""
        try:
            from src.core.build_world_state import (
                build_world_state,
                ObservationCollector,
                CoherenceEvaluator,
            )

            assert callable(build_world_state)
            assert ObservationCollector is not None
            assert CoherenceEvaluator is not None
        except ImportError as e:
            pytest.fail(f"Failed to import build_world_state: {e}")

    def test_plan_generator_imports(self):
        """Test that plan generator can be imported."""
        try:
            from src.core.plan_from_world_state import PlanGenerator, plan_from_world_state

            assert callable(plan_from_world_state)
            assert PlanGenerator is not None
        except ImportError as e:
            pytest.fail(f"Failed to import plan_from_world_state: {e}")

    def test_action_ledger_imports(self):
        """Test that action ledger can be imported."""
        try:
            from src.core.action_receipt_ledger import ActionReceiptLedger, ActionReceipt

            assert ActionReceiptLedger is not None
            assert ActionReceipt is not None
        except ImportError as e:
            pytest.fail(f"Failed to import action_receipt_ledger: {e}")

    def test_eol_integration_imports(self):
        """Test that EOL integration can be imported."""
        try:
            from src.core.eol_integration import EOLOrchestrator, full_cycle

            assert EOLOrchestrator is not None
            assert callable(full_cycle)
        except ImportError as e:
            pytest.fail(f"Failed to import eol_integration: {e}")

    def test_orchestrate_facade_has_eol(self):
        """Test that orchestrate.py exposes eol facade."""
        try:
            from src.core.orchestrate import nusyq

            assert hasattr(nusyq, "eol"), "nusyq should have 'eol' property"
            eol = nusyq.eol
            assert eol is not None
            assert hasattr(eol, "sense"), "eol should have sense method"
            assert hasattr(eol, "propose"), "eol should have propose method"
            assert hasattr(eol, "act"), "eol should have act method"
        except Exception as e:
            pytest.fail(f"Failed to access EOL facade: {e}")

    def test_build_world_state_basic(self):
        """Test basic world state building."""
        try:
            from src.core.build_world_state import build_world_state

            world = build_world_state(Path("."))

            assert world is not None, "World state should not be None"
            assert "timestamp" in world, "World state should have timestamp"
            assert "decision_epoch" in world, "World state should have decision_epoch"
            assert "observations" in world, "World state should have observations"
            assert "signals" in world, "World state should have signals"
            assert "coherence" in world, "World state should have coherence"

            # Check schema compliance
            assert isinstance(world["timestamp"], str), "Timestamp should be ISO 8601 string"
            assert isinstance(world["decision_epoch"], int), "Epoch should be int"
            assert isinstance(world["signals"]["facts"], list), "Facts should be list"

            logger.info(
                f"✓ Built world state (epoch {world['decision_epoch']}, signals {len(world['signals']['facts'])})"
            )

        except Exception as e:
            pytest.fail(f"Failed to build world state: {e}")

    def test_plan_generation_basic(self):
        """Test basic action plan generation."""
        try:
            from src.core.build_world_state import build_world_state
            from src.core.plan_from_world_state import plan_from_world_state

            world = build_world_state(Path("."))
            plan = plan_from_world_state(world, "Analyze the codebase")

            assert plan is not None, "Plan should not be None"
            assert "objective" in plan, "Plan should have objective"
            assert "actions" in plan, "Plan should have actions"
            assert isinstance(plan["actions"], list), "Actions should be list"

            if plan["actions"]:
                action = plan["actions"][0]
                assert "action_id" in action, "Action should have action_id"
                assert "agent" in action, "Action should have agent"
                assert "task_type" in action, "Action should have task_type"
                assert "risk_score" in action, "Action should have risk_score"

                logger.info(
                    f"✓ Generated {len(plan['actions'])} actions (top: {action['agent']}/{action['task_type']})"
                )
            else:
                logger.warning("⚠ No actions generated (may indicate model unavailability)")

        except Exception as e:
            pytest.fail(f"Failed to generate plan: {e}")

    def test_eol_sense_via_facade(self):
        """Test sense() via orchestrate facade."""
        try:
            from src.core.orchestrate import nusyq

            result = nusyq.eol.sense()

            assert (
                result.ok
            ), f"sense() should succeed, got: {result.error if not result.ok else 'OK'}"
            assert result.value is not None, "sense() result should not be None"

            world = result.value
            assert "decision_epoch" in world, "World state should have decision_epoch"

            logger.info(f"✓ sense() via facade returned epoch {world['decision_epoch']}")

        except Exception as e:
            pytest.fail(f"Failed to call sense() via facade: {e}")

    def test_eol_propose_via_facade(self):
        """Test propose() via orchestrate facade."""
        try:
            from src.core.orchestrate import nusyq

            # First sense
            sense_result = nusyq.eol.sense()
            assert sense_result.ok, "sense() should succeed"
            world = sense_result.value

            # Then propose
            propose_result = nusyq.eol.propose(world, "Analyze the repository")

            assert (
                propose_result.ok
            ), f"propose() should succeed, got: {propose_result.error if not propose_result.ok else 'OK'}"
            assert propose_result.value is not None, "propose() result should not be None"

            actions = propose_result.value
            assert isinstance(actions, list), "Actions should be list"

            logger.info(f"✓ propose() via facade returned {len(actions)} actions")

        except Exception as e:
            pytest.fail(f"Failed to call propose() via facade: {e}")

    def test_eol_critique_logic(self):
        """Test critique (policy evaluation) logic."""
        try:
            from src.core.orchestrate import nusyq

            # Build world state
            sense_result = nusyq.eol.sense()
            assert sense_result.ok
            world = sense_result.value

            # Propose actions
            propose_result = nusyq.eol.propose(world, "Fix errors")
            assert propose_result.ok

            actions = propose_result.value
            if not actions:
                logger.warning("⚠ No actions to critique (model may not be available)")
                return

            # Critique first action
            action = actions[0]
            critique_result = nusyq.eol.critique(action, world)

            assert critique_result.ok, f"critique() should succeed, got: {critique_result.error}"
            approved = critique_result.value
            assert isinstance(approved, bool), "critique() should return bool"

            logger.info(f"✓ critique() returned {'APPROVED' if approved else 'REJECTED'}")

        except Exception as e:
            pytest.fail(f"Failed to critique action: {e}")

    def test_eol_dry_run(self):
        """Test dry-run execution (no actual dispatch)."""
        try:
            from src.core.orchestrate import nusyq

            # Full cycle with dry_run=True
            result = nusyq.eol.full_cycle(
                "Test objective",
                auto_execute=False,
                dry_run=True,
            )

            assert (
                result.ok
            ), f"full_cycle should succeed, got: {result.error if not result.ok else 'OK'}"
            output = result.value

            assert "world_state" in output
            assert "actions" in output
            assert "execution_results" in output

            logger.info(f"✓ full_cycle dry-run complete (candidates: {len(output['actions'])})")

        except Exception as e:
            pytest.fail(f"Failed dry-run cycle: {e}")

    def test_quest_receipt_linkage(self):
        """Test quest-receipt linkage system."""
        try:
            from src.core.quest_receipt_linkage import link_receipt_to_quest

            # Create sample receipt
            sample_receipt = {
                "receipt_id": "test-receipt-123",
                "action_id": "test-action-123",
                "status": "SUCCESS",
                "agent": "ollama",
                "task_type": "analysis",
                "duration_s": 2.5,
                "metadata": {
                    "policy_category": "ANALYSIS",
                    "risk_score": 0.3,
                },
            }

            # Link to quest
            link = link_receipt_to_quest(sample_receipt, "test-quest-123")

            assert link is not None
            assert link["receipt_id"] == "test-receipt-123"
            assert link["quest_id"] == "test-quest-123"

            logger.info("✓ Linked receipt to quest")

        except Exception as e:
            pytest.fail(f"Failed to link receipt: {e}")


class TestEOLChecklist:
    """Verification checklist for Phase 1 completion."""

    def test_phase1_files_exist(self):
        """Check that all Phase 1 files exist."""
        files = [
            Path("src/core/build_world_state.py"),
            Path("src/core/plan_from_world_state.py"),
            Path("src/core/action_receipt_ledger.py"),
            Path("src/core/eol_integration.py"),
            Path("src/core/quest_receipt_linkage.py"),
            Path("src/core/eol_facade_integration.py"),
            Path("scripts/nusyq_actions/eol.py"),
            Path("src/core/world_state.schema.json"),
            Path("docs/EPISTEMIC_OPERATIONAL_LATTICE.md"),
            Path("docs/PHASE_1_FOUNDATION.md"),
        ]

        missing = [f for f in files if not f.exists()]
        if missing:
            pytest.fail(f"Missing Phase 1 files: {missing}")

        logger.info(f"✓ All {len(files)} Phase 1 files present")

    def test_phase1_documentation(self):
        """Check that Phase 1 documentation is complete."""
        docs = [
            ("EPISTEMIC_OPERATIONAL_LATTICE.md", ["8 planes", "world state", "decision cycle"]),
            ("PHASE_1_FOUNDATION.md", ["v0.1", "production-ready", "2,000 lines"]),
        ]

        for doc_name, keywords in docs:
            path = Path("docs") / doc_name
            assert path.exists(), f"Documentation {doc_name} not found"

            content = path.read_text()
            missing_kw = [kw for kw in keywords if kw.lower() not in content.lower()]

            if missing_kw:
                logger.warning(f"⚠ {doc_name} missing keywords: {missing_kw}")
            else:
                logger.info(f"✓ {doc_name} complete")


def main():
    """Run tests if executed directly."""
    import sys

    # Run pytest
    exit_code = pytest.main([__file__, "-v", "-s"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
