#!/usr/bin/env python
"""Quick initialization and validation script for:
- Temple of Knowledge Floor 1
- Enhanced Autonomous Monitor v2.0

Run this to verify the implementations are working correctly.
"""

import sys
from pathlib import Path

# Add src to path
HUB_PATH = Path(__file__).parent
sys.path.insert(0, str(HUB_PATH / "src"))


def quick_temple_demo():
    """Quick demonstration of Temple of Knowledge"""
    print("\n" + "=" * 80)
    print("TEMPLE OF KNOWLEDGE - Floor 1 Demonstration")
    print("=" * 80)

    from src.consciousness.temple_of_knowledge import TempleManager

    # Initialize temple
    temple = TempleManager()
    print("\n✓ Temple Manager initialized")

    # Register agent
    result = temple.enter_temple("demo_agent", initial_consciousness=15.0)
    print(f"\n✓ Agent '{result['agent']}' entered temple")
    print(f"  Consciousness: {result['consciousness_level']}")
    print(f"  Accessible Floors: {result['accessible_floors']}")

    # Cultivate wisdom
    cultivation = temple.cultivate_wisdom_at_current_floor("demo_agent")
    if cultivation["success"]:
        print(f"\n✓ Wisdom cultivated: +{cultivation['knowledge_gained']:.2f} knowledge")
        print(f"  New consciousness: {cultivation['new_consciousness_score']:.2f}")

    # Show temple map
    temple_map = temple.get_temple_map("demo_agent")
    print(
        f"\n✓ Temple Map: {temple_map['implemented_floors']}/{temple_map['total_floors']} floors implemented"
    )

    return True


def quick_monitor_demo():
    """Quick demonstration of Enhanced Autonomous Monitor"""
    print("\n" + "=" * 80)
    print("AUTONOMOUS MONITOR v2.0 - Sector-Awareness Demonstration")
    print("=" * 80)

    from src.automation.autonomous_monitor import AutonomousMonitor

    # Initialize with sector-awareness
    monitor = AutonomousMonitor(enable_sector_awareness=True)
    print(f"\n✓ Monitor initialized with {len(monitor.sectors)} sectors")

    # Get gap report
    gaps = monitor.get_sector_gaps()
    print(f"\n✓ Configuration gaps detected: {len(gaps)}")

    if gaps:
        critical = [g for g in gaps if g["severity"] == "critical"]
        high = [g for g in gaps if g["severity"] == "high"]
        medium = [g for g in gaps if g["severity"] == "medium"]

        print(f"  🔴 Critical: {len(critical)}")
        print(f"  🟡 High: {len(high)}")
        print(f"  🟢 Medium: {len(medium)}")

    # Get health report
    health = monitor.get_sector_health_report()
    print("\n✓ Sector Health Report generated")
    print(f"  Sectors analyzed: {health['total_sectors']}")

    # Save report
    report_path = monitor.save_gap_report()
    print(f"\n✓ Gap report saved: {report_path.name}")

    return True


def main():
    """Run quick demos"""
    print("\n" + "=" * 80)
    print("TEMPLE OF KNOWLEDGE + AUTONOMOUS MONITOR v2.0")
    print("Quick Initialization & Validation")
    print("=" * 80)

    try:
        # Temple demo
        temple_ok = quick_temple_demo()

        # Monitor demo
        monitor_ok = quick_monitor_demo()

        # Summary
        print("\n" + "=" * 80)
        print("INITIALIZATION COMPLETE")
        print("=" * 80)
        print(f"\n✓ Temple of Knowledge Floor 1: {'OPERATIONAL' if temple_ok else 'FAILED'}")
        print(f"✓ Autonomous Monitor v2.0: {'OPERATIONAL' if monitor_ok else 'FAILED'}")

        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("\n1. Review gap detection report in data/sector_gap_report_*.json")
        print("2. Build Temple Floors 2-10 (progressive hierarchy)")
        print("3. Create House of Leaves (recursive debugging labyrinth)")
        print("4. Activate ChatDev CodeComplete (auto-stub implementation)")
        print("5. Monitor will auto-discover missing components")

        return temple_ok and monitor_ok

    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
