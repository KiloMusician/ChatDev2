#!/usr/bin/env python3
"""Phase 5: Demo & Showcase Systems - CLI Gateway

Rehabilitates orphaned demo/showcase functions by providing CLI access:
- quick_demo() (examples/sns_orchestrator_demo.py)
- Various example demonstration functions

Usage:
    python scripts/run_demos.py --demo=sns_quick
    python scripts/run_demos.py --demo=all
    python scripts/run_demos.py --list
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


async def run_sns_quick_demo() -> int:
    """Run SNS orchestrator quick demo."""
    print("=" * 70)
    print("📦 SNS Orchestrator Quick Demo")
    print("=" * 70)

    try:
        from examples.sns_orchestrator_demo import quick_demo

        await quick_demo()
        print("\n✅ Demo completed successfully")
        return 0
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


async def run_sns_full_demo() -> int:
    """Run full SNS orchestrator demo suite."""
    print("=" * 70)
    print("📦 SNS Orchestrator Full Demo Suite")
    print("=" * 70)

    try:
        from examples.sns_orchestrator_demo import SNSOrchestratorDemo

        demo = SNSOrchestratorDemo()
        await demo.run_all_demos()
        print("\n✅ Full demo suite completed")
        return 0
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


async def run_all_demos() -> int:
    """Run all available demo systems sequentially."""
    print("=" * 70)
    print("🎭 Running All Demo Systems")
    print("=" * 70)

    demos = [
        ("SNS Quick Demo", run_sns_quick_demo),
        ("SNS Full Demo", run_sns_full_demo),
    ]

    results = []
    for name, demo_func in demos:
        print(f"\n▶️  {name}")
        result = await demo_func()
        results.append((name, result))
        print()

    print("=" * 70)
    print("📊 Demo Results Summary")
    print("=" * 70)
    for name, result in results:
        status = "✅ PASS" if result == 0 else "❌ FAIL"
        print(f"  {status} - {name}")

    all_passed = all(r == 0 for _, r in results)
    return 0 if all_passed else 1


def list_demos():
    """List all available demo systems."""
    print("=" * 70)
    print("📋 Available Demo Systems")
    print("=" * 70)
    print("\n🎯 SNS Orchestrator Demos:")
    print("  sns_quick     - Quick SNS orchestration demo (1 minute)")
    print("  sns_full      - Full SNS demo suite (5 minutes)")
    print("\n🎪 Meta Demos:")
    print("  all           - Run all demos sequentially")
    print("\n💡 Usage:")
    print("  python run_demos.py --demo=sns_quick")
    print("  python run_demos.py --demo=all")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Demo & showcase system gateway - rehabilitate orphaned demos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available demos
  python run_demos.py --list

  # Run quick SNS demo
  python run_demos.py --demo=sns_quick

  # Run full SNS demo suite
  python run_demos.py --demo=sns_full

  # Run all demos
  python run_demos.py --demo=all
        """,
    )

    parser.add_argument("--demo", choices=["sns_quick", "sns_full", "all"], help="Which demo to run")

    parser.add_argument("--list", action="store_true", help="List all available demos")

    args = parser.parse_args()

    if args.list:
        list_demos()
        return 0

    if not args.demo:
        parser.print_help()
        return 1

    demo_map = {
        "sns_quick": run_sns_quick_demo,
        "sns_full": run_sns_full_demo,
        "all": run_all_demos,
    }

    demo_func = demo_map[args.demo]
    return asyncio.run(demo_func())


if __name__ == "__main__":
    sys.exit(main())
