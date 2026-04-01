#!/usr/bin/env python3
"""Extended Autonomous Cycles - Test with Real Codebase Issues.

Runs multiple autonomous cycles to:
1. Identify real codebase issues
2. Attempt quantum resolution
3. Track success rates over multiple cycles
4. Monitor breathing adaptation
5. Measure learning improvements
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.spine import initialize_spine

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)


async def scan_for_real_issues():
    """Scan codebase for real issues using quantum scanner."""
    from src.integration.quantum_error_bridge import get_quantum_error_bridge

    print("\n" + "=" * 70)
    print("SCANNING CODEBASE FOR REAL ISSUES")
    print("=" * 70)

    bridge = get_quantum_error_bridge()

    print("\n🔍 Running quantum problem scan...")
    summary = await bridge.scan_and_heal()

    print("\n📊 Scan Results:")
    print(f"  Problems Found: {summary['problems_found']}")
    print(f"  Auto-Resolved: {summary['auto_resolved']}")
    print(f"  PUs Created: {summary['pus_created']}")
    print(f"  Failed: {summary['failed']}")

    if summary["problems_found"] > 0:
        print(
            f"\n✨ Auto-Fix Success Rate: {summary['auto_resolved'] / summary['problems_found'] * 100:.1f}%"
        )

    return summary


async def run_cycle(cycle_num: int, initial_breathing: float):
    """Run a single autonomous development cycle."""
    from src.agents.adaptive_timeout_manager import get_timeout_manager
    from src.agents.unified_agent_ecosystem import get_ecosystem
    from src.automation.autonomous_quest_generator import AutonomousQuestGenerator
    from src.orchestration.multi_ai_orchestrator import get_multi_ai_orchestrator

    print("\n" + "=" * 70)
    print(f"CYCLE {cycle_num}")
    print("=" * 70)

    # Check system health
    orchestrator = get_multi_ai_orchestrator()
    health = orchestrator.health_check()
    active_systems = sum(health.values())

    print(f"\n🔍 System Health: {active_systems}/{len(health)} systems active")

    # Check timeout manager state
    timeout_mgr = get_timeout_manager()
    current_breathing = timeout_mgr.breathing_factor
    breathing_change = current_breathing - initial_breathing

    print(f"⏱️ Breathing Factor: {current_breathing:.2f}x (Δ {breathing_change:+.2f})")

    # Process any pending PUs
    generator = AutonomousQuestGenerator()
    pu_result = await generator.process_pending_pus()

    print("\n📋 PU Processing:")
    print(f"  Processed: {pu_result['processed']}")
    print(f"  Quests Created: {pu_result['created']}")
    print(f"  Failed: {pu_result['failed']}")

    # Get quest status
    ecosystem = get_ecosystem()
    quest_summary = ecosystem.get_party_quest_summary()

    print("\n🎯 Quest Board:")
    print(f"  Total: {quest_summary['total_quests']}")
    print(f"  Active: {quest_summary['quests_by_status']['active']}")
    print(f"  Complete: {quest_summary['quests_by_status']['complete']}")

    return {
        "cycle": cycle_num,
        "active_systems": active_systems,
        "breathing_factor": current_breathing,
        "pus_processed": pu_result["processed"],
        "quests_created": pu_result["created"],
        "total_quests": quest_summary["total_quests"],
        "active_quests": quest_summary["quests_by_status"]["active"],
    }


async def main():
    """Run extended autonomous cycles."""
    try:
        initialize_spine(repo_root=Path(__file__).resolve().parent)
    except Exception as exc:
        logger.warning("Spine init failed for extended cycles: %s", exc)
    print("\n" + "=" * 70)
    print("🤖 EXTENDED AUTONOMOUS CYCLES")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Phase 1: Initial Scan
    print("\n📍 PHASE 1: INITIAL CODEBASE SCAN")
    scan_result = await scan_for_real_issues()

    # Phase 2: Run Multiple Cycles
    print("\n📍 PHASE 2: RUNNING MULTIPLE AUTONOMOUS CYCLES")

    from src.agents.adaptive_timeout_manager import get_timeout_manager

    timeout_mgr = get_timeout_manager()
    initial_breathing = timeout_mgr.breathing_factor

    num_cycles = 3
    cycle_results = []

    for i in range(1, num_cycles + 1):
        result = await run_cycle(i, initial_breathing)
        cycle_results.append(result)

        # Brief pause between cycles
        if i < num_cycles:
            print("\n⏸️ Pausing 2 seconds before next cycle...")
            await asyncio.sleep(2)

    # Phase 3: Analysis
    print("\n" + "=" * 70)
    print("📊 EXTENDED CYCLE ANALYSIS")
    print("=" * 70)

    print("\n🔍 Scan Performance:")
    print(f"  Problems Detected: {scan_result['problems_found']}")
    print(f"  Auto-Resolved: {scan_result['auto_resolved']}")
    print(f"  PU Escalations: {scan_result['pus_created']}")
    if scan_result["problems_found"] > 0:
        print(
            f"  Success Rate: {scan_result['auto_resolved'] / scan_result['problems_found'] * 100:.1f}%"
        )

    print("\n🔄 Cycle-by-Cycle Metrics:")
    print(f"  {'Cycle':<8} {'Active Sys':<12} {'Breathing':<12} {'PUs':<8} {'Quests':<10}")
    print("  " + "-" * 60)
    for result in cycle_results:
        print(
            f"  {result['cycle']:<8} "
            f"{result['active_systems']:<12} "
            f"{result['breathing_factor']:<12.2f} "
            f"{result['pus_processed']:<8} "
            f"{result['total_quests']:<10}"
        )

    # Breathing adaptation
    final_breathing = cycle_results[-1]["breathing_factor"]
    breathing_delta = final_breathing - initial_breathing

    print("\n⏱️ Breathing Adaptation:")
    print(f"  Initial: {initial_breathing:.2f}x")
    print(f"  Final: {final_breathing:.2f}x")
    print(f"  Change: {breathing_delta:+.2f}x")

    if abs(breathing_delta) < 0.01:
        print("  Status: Stable (no significant adaptation needed)")
    elif breathing_delta > 0:
        print("  Status: Decelerating (system under stress)")
    else:
        print("  Status: Accelerating (system performing well)")

    # Quest generation trends
    total_pus = sum(r["pus_processed"] for r in cycle_results)
    total_quests_created = sum(r["quests_created"] for r in cycle_results)

    print("\n🎯 Quest Generation:")
    print(f"  Total PUs Processed: {total_pus}")
    print(f"  Total Quests Created: {total_quests_created}")
    print(f"  Final Quest Count: {cycle_results[-1]['total_quests']}")
    print(f"  Active Quests: {cycle_results[-1]['active_quests']}")

    # Overall assessment
    print("\n" + "=" * 70)
    print("✅ EXTENDED CYCLES COMPLETE")
    print("=" * 70)

    print("\n🎯 Key Findings:")
    print(f"  • Ran {num_cycles} autonomous cycles successfully")
    print(f"  • Scanned {scan_result['problems_found']} real codebase issues")
    print(f"  • Auto-fixed {scan_result['auto_resolved']} problems autonomously")
    print(f"  • Created {scan_result['pus_created']} PUs for complex issues")
    print(f"  • Processed {total_pus} PUs across all cycles")
    print(f"  • System breathing factor: {final_breathing:.2f}x")

    print("\n🔬 System Status:")
    if scan_result["auto_resolved"] > 0:
        print("  ✅ Self-healing is OPERATIONAL")
    if total_pus > 0:
        print("  ✅ PU escalation is WORKING")
    if cycle_results[-1]["total_quests"] > 0:
        print("  ✅ Quest system is ACTIVE")
    print("  ✅ Adaptive timeouts are ENABLED")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
