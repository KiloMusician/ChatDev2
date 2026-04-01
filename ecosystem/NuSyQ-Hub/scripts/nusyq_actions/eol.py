"""NuSyQ CLI: Epistemic-Operational Lattice (EOL) Actions

Provides CLI commands for running EOL decision cycles:
    python scripts/start_nusyq.py eol sense
    python scripts/start_nusyq.py eol propose "objective"
    python scripts/start_nusyq.py eol full-cycle "objective" --auto
    python scripts/start_nusyq.py eol full-cycle "objective" --auto-execute --live
    python scripts/start_nusyq.py eol stats
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_eol_sense(args: Any) -> int:
    """Build and display world state.

    Usage:
        python scripts/start_nusyq.py eol sense [--json]
    """
    try:
        from src.core.orchestrate import nusyq

        result = nusyq.eol.sense()

        if not result.ok:
            print(f"Error: {result.error}")
            return 1

        world_state = result.value

        if args.json:
            print(json.dumps(world_state, indent=2, default=str))
        else:
            print(f"✓ World State (Epoch {world_state['decision_epoch']})")
            print(f"  Timestamp: {world_state['timestamp']}")
            print(f"  Signals: {len(world_state['signals']['facts'])}")
            print(f"  Contradictions: {len(world_state['coherence']['contradictions'])}")
            print(f"  Signal Drift: {len(world_state['coherence']['signal_drift'])}")

            if world_state["coherence"]["contradictions"]:
                print("\n  Contradictions Detected:")
                for cnt in world_state["coherence"]["contradictions"][:3]:
                    print(f"    - {cnt['key']}: {cnt.get('reasoning', 'N/A')[:60]}...")

        return 0

    except Exception as e:
        print(f"Error running eol sense: {e}")
        logger.exception(e)
        return 1


def handle_eol_propose(args: Any) -> int:
    """Generate action candidates from world state.

    Usage:
        python scripts/start_nusyq.py eol propose "Your objective here" [--json]
    """
    try:
        from src.core.orchestrate import nusyq

        # First sense world state
        sense_result = nusyq.eol.sense()
        if not sense_result.ok:
            print(f"Error sensing world: {sense_result.error}")
            return 1

        world_state = sense_result.value
        objective = args.objective or "[No specific objective provided]"

        # Propose actions
        propose_result = nusyq.eol.propose(world_state, objective)

        if not propose_result.ok:
            print(f"Error: {propose_result.error}")
            return 1

        actions = propose_result.value

        if args.json:
            print(json.dumps({"objective": objective, "actions": actions}, indent=2, default=str))
        else:
            print(f"✓ Generated {len(actions)} Action Candidates")
            print(f"  Objective: {objective}")
            print()

            for i, action in enumerate(actions, 1):
                print(f"  {i}. {action['agent'].upper()} / {action['task_type']}")
                print(f"     Risk: {action.get('risk_score', 0.0):.2f}")
                print(
                    f"     Cost: {action['estimated_cost'].get('tokens', 0)} tokens, {action['estimated_cost'].get('time_s', 0)}s"
                )
                print(f"     ID: {action['action_id'][:8]}...")

        return 0

    except Exception as e:
        print(f"Error running eol propose: {e}")
        logger.exception(e)
        return 1


def handle_eol_full_cycle(args: Any) -> int:
    """Run complete sense → propose → critique → act cycle.

    Usage:
        python scripts/start_nusyq.py eol full-cycle "objective" [--auto|--auto-execute] [--dry-run|--live] [--json]
    """
    try:
        from src.core.orchestrate import nusyq

        objective = args.objective or "[No specific objective provided]"
        auto_execute = bool(getattr(args, "auto", False))

        # Safe default: dry-run unless explicitly switched to live mode.
        dry_run = True
        if bool(getattr(args, "dry_run", False)):
            dry_run = True
        if bool(getattr(args, "live", False)):
            dry_run = False

        result = nusyq.eol.full_cycle(objective, auto_execute=auto_execute, dry_run=dry_run)

        if not result.ok:
            print(f"Error: {result.error}")
            return 1

        output = result.value

        if args.json:
            print(json.dumps(output, indent=2, default=str))
        else:
            meta = output.get("metadata", {})
            print("✓ EOL Full Cycle Complete")
            print(f"  Epoch: {output['world_state'].get('decision_epoch', '?')}")
            print(f"  Candidates: {meta.get('total_candidates', 0)}")
            print(f"  Approved: {meta.get('approved', 0)}")
            print(f"  Executed: {meta.get('executed', 0)}")
            print(f"  Mode: {'DRY-RUN' if dry_run else 'LIVE'}")

            if auto_execute and output.get("execution_results"):
                print("\n  Execution Results:")
                for receipt in output["execution_results"]:
                    print(f"    Status: {receipt.get('status')}")
                    print(f"    Duration: {receipt.get('duration_s', 0):.2f}s")

        return 0

    except Exception as e:
        print(f"Error running eol full-cycle: {e}")
        logger.exception(e)
        return 1


def handle_eol_stats(args: Any) -> int:
    """Get EOL execution statistics.

    Usage:
        python scripts/start_nusyq.py eol stats [--json]
    """
    try:
        from src.core.orchestrate import nusyq

        result = nusyq.eol.stats()

        if not result.ok:
            print(f"Error: {result.error}")
            return 1

        stats = result.value

        if args.json:
            print(json.dumps(stats, indent=2, default=str))
        else:
            print("✓ Action Execution Stats")
            print(f"  Total: {stats.get('total_actions', 0)}")
            print(f"  Successful: {stats.get('successful', 0)}")
            print(f"  Failed: {stats.get('failed', 0)}")
            print(f"  Partial: {stats.get('partial', 0)}")
            print(f"  Success Rate: {stats.get('success_rate', 0.0):.1%}")
            print(f"  Avg Duration: {stats.get('avg_duration_s', 0.0):.1f}s")

            by_agent = stats.get("by_agent", {})
            if by_agent:
                print("\n  By Agent:")
                for agent, info in by_agent.items():
                    count = info.get("count", 0)
                    successful = info.get("successful", 0)
                    rate = successful / count if count > 0 else 0
                    print(f"    {agent}: {successful}/{count} ({rate:.0%})")

        return 0

    except Exception as e:
        print(f"Error running eol stats: {e}")
        logger.exception(e)
        return 1


def handle_eol_debug(args: Any) -> int:
    """Get debug information about EOL system.

    Usage:
        python scripts/start_nusyq.py eol debug [--json]
    """
    try:
        from src.core.orchestrate import nusyq

        result = nusyq.eol.debug()

        if not result.ok:
            print(f"Error: {result.error}")
            return 1

        debug = result.value

        if args.json:
            print(json.dumps(debug, indent=2, default=str))
        else:
            print("✓ EOL Debug Info")
            print(f"  Workspace: {debug.get('workspace_root')}")
            print(f"  Ledger: {debug.get('ledger_file')}")
            print(f"  State Snapshot: {debug.get('state_snapshot_file')}")
            print(f"  Previous Epoch: {debug.get('previous_world_state_epoch', -1)}")

            stats = debug.get("action_stats", {})
            print("\n  Stats:")
            print(f"    Total: {stats.get('total_actions', 0)}")
            print(f"    Success Rate: {stats.get('success_rate', 0.0):.1%}")

        return 0

    except Exception as e:
        print(f"Error running eol debug: {e}")
        logger.exception(e)
        return 1


def handle_eol_command(args: Any) -> int:
    """Main dispatcher for eol subcommands.

    Subcommands:
        sense           - Build world state
        propose OBJ     - Generate action candidates
        full-cycle OBJ  - Complete decision cycle
        stats           - Show execution statistics
        debug           - Show debug information
    """
    subcommand = getattr(args, "eol_subcommand", None)

    dispatch = {
        "sense": handle_eol_sense,
        "propose": handle_eol_propose,
        "full-cycle": handle_eol_full_cycle,
        "full_cycle": handle_eol_full_cycle,  # Underscore variant
        "stats": handle_eol_stats,
        "debug": handle_eol_debug,
    }

    handler = dispatch.get(subcommand)
    if not handler:
        print(f"Unknown EOL subcommand: {subcommand}")
        print("\nAvailable subcommands:")
        print("  eol sense             - Build world state")
        print("  eol propose <OBJ>     - Generate action candidates")
        print("  eol full-cycle <OBJ>  - Complete decision cycle")
        print("  eol stats             - Show execution statistics")
        print("  eol debug             - Show debug information")
        return 1

    return handler(args)


__all__ = [
    "handle_eol_command",
    "handle_eol_debug",
    "handle_eol_full_cycle",
    "handle_eol_propose",
    "handle_eol_sense",
    "handle_eol_stats",
]
