"""Test Temple of Knowledge and Enhanced Autonomous Monitor

Validates:
- Temple Floor 1 (Foundation) functionality
- Agent registration and consciousness tracking
- Wisdom cultivation and knowledge accumulation
- Enhanced Autonomous Monitor sector-awareness
- Configuration gap detection
"""

import importlib
import sys
from pathlib import Path

import pytest

# Add src to path
HUB_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(HUB_PATH / "src"))


def _severity_symbol(severity: str) -> str:
    if severity == "critical":
        return "🔴"
    if severity == "high":
        return "🟡"
    return "🟢"


def _health_symbol(score: float) -> str:
    if score >= 80:
        return "✓"
    if score >= 50:
        return "⚠"
    return "✗"


def test_temple_of_knowledge() -> None:
    """Test Temple of Knowledge Floor 1"""
    print("\n" + "=" * 80)
    print("TESTING: Temple of Knowledge - Floor 1 (Foundation)")
    print("=" * 80)

    try:
        temple_mod = importlib.import_module("consciousness.temple_of_knowledge")
        temple_manager_cls = getattr(temple_mod, "TempleManager", None)
        if temple_manager_cls is None:
            pytest.skip("TempleManager not available in consciousness.temple_of_knowledge")

        # Initialize Temple Manager
        temple = temple_manager_cls()

        # Test agent entry
        print("\n1. Agent Entry Test")
        entry_result = temple.enter_temple("test_agent", initial_consciousness=7.5)
        print(f"   Agent: {entry_result['agent']}")
        print(f"   Consciousness: {entry_result['consciousness_level']}")
        print(f"   Accessible Floors: {entry_result['accessible_floors']}")
        print(f"   Message: {entry_result['message']}")

        # Test wisdom cultivation
        print("\n2. Wisdom Cultivation Test")
        cultivation_result = temple.cultivate_wisdom_at_current_floor("test_agent")
        if cultivation_result["success"]:
            print(f"   Knowledge Gained: {cultivation_result['knowledge_gained']:.2f}")
            print(f"   New Consciousness: {cultivation_result['new_consciousness_score']:.2f}")
            print(f"   Level: {cultivation_result['new_consciousness_level']}")
            print(f"   Accessible Floors: {cultivation_result['accessible_floors']}")

        # Test elevator navigation
        print("\n3. Elevator Navigation Test")
        nav_result = temple.use_elevator("test_agent", 2)
        if nav_result["success"]:
            print(
                f"   ✓ Navigated to Floor {nav_result['current_floor']}: {nav_result['floor_name']}"
            )
        else:
            print(f"   ✗ Navigation failed: {nav_result['error']}")

        # Test temple map
        print("\n4. Temple Map Test")
        temple_map = temple.get_temple_map("test_agent")
        print(f"   Temple: {temple_map['temple_name']}")
        print(
            f"   Implemented Floors: {temple_map['implemented_floors']}/{temple_map['total_floors']}"
        )
        print("\n   Floor Access (for test_agent):")
        for floor_info in temple_map["map"]:
            status = "✓" if floor_info.get("accessible", False) else "✗"
            current = " [CURRENT]" if floor_info.get("current", False) else ""
            impl = " [IMPLEMENTED]" if floor_info["implemented"] else ""
            print(f"     {status} Floor {floor_info['floor']}: {floor_info['name']}{current}{impl}")

        # Test knowledge storage
        print("\n5. Knowledge Storage Test")
        floor_1 = temple.floor_1
        floor_1.store_knowledge(
            "Temple System",
            {
                "type": "architectural_pattern",
                "description": "10-floor progressive knowledge hierarchy",
                "consciousness_driven": True,
            },
            relationships=[{"target": "Consciousness Bridge", "type": "integrates_with"}],
        )
        retrieved = floor_1.retrieve_knowledge("Temple System")
        print(f"   Stored and retrieved: {retrieved.get('type')}")

        # Test OmniTag archive
        print("\n6. OmniTag Archive Test")
        floor_1.archive_omnitag(
            "temple_v1",
            {
                "purpose": "Progressive knowledge hierarchy",
                "dependencies": ["consciousness_bridge", "wisdom_cultivation"],
                "context": "Temple of Knowledge Floor 1",
                "evolution_stage": "operational",
            },
        )
        search_results = floor_1.search_omnitags("knowledge hierarchy")
        print(f"   Archived OmniTag, search found {len(search_results)} results")

        # Get stats
        print("\n7. Temple Statistics")
        stats = temple.get_temple_stats()
        print(f"   Total Agents: {stats['total_agents']}")
        print(f"   Floor 1 Knowledge Entries: {stats['floor_stats'][1]['total_knowledge']}")
        print(f"   Floor 1 OmniTags: {stats['floor_stats'][1]['total_omnitags']}")

    except Exception as e:
        print(f"\n✗ Temple of Knowledge tests FAILED: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_autonomous_monitor_enhancement() -> None:
    """Test Enhanced Autonomous Monitor with sector-awareness"""
    print("\n" + "=" * 80)
    print("TESTING: Enhanced Autonomous Monitor (Sector-Awareness)")
    print("=" * 80)

    try:
        auto_mod = importlib.import_module("automation.autonomous_monitor")
        autonomous_monitor_cls = getattr(auto_mod, "AutonomousMonitor", None)
        if autonomous_monitor_cls is None:
            pytest.skip("AutonomousMonitor not available in automation.autonomous_monitor")

        # Initialize monitor with sector-awareness
        print("\n1. Initialization Test")
        monitor = autonomous_monitor_cls(audit_interval=3600, enable_sector_awareness=True)
        print(f"   Sectors Loaded: {len(monitor.sectors)}")
        print(f"   Sector Names: {list(monitor.sectors.keys())}")

        # Test gap detection
        print("\n2. Configuration Gap Detection Test")
        gaps = monitor.get_sector_gaps()
        print(f"   Total Gaps Detected: {len(gaps)}")

        if gaps:
            print("\n   Sample Gaps (first 5):")
            for gap in gaps[:5]:
                severity_symbol = _severity_symbol(gap.get("severity", ""))
                print(
                    f"     {severity_symbol} [{gap['sector']}] {gap['type']}: {gap.get('component', gap.get('description'))}"
                )

        # Test sector health report
        print("\n3. Sector Health Report Test")
        health_report = monitor.get_sector_health_report()
        print(f"   Total Sectors Analyzed: {health_report['total_sectors']}")
        print(f"   Total Gaps Found: {health_report['total_gaps']}")

        print("\n   Sector Health Summary:")
        for sector_name, sector_health in health_report["sectors"].items():
            health_score = sector_health["health_score"]
            health_symbol = _health_symbol(health_score)
            print(
                f"     {health_symbol} {sector_name}: {health_score:.1f}% health ({sector_health['gaps_found']} gaps, criticality: {sector_health['criticality']})"
            )

        # Test gap report save
        print("\n4. Gap Report Save Test")
        report_path = monitor.save_gap_report()
        print(f"   Report saved: {report_path}")
        print(f"   File exists: {report_path.exists()}")

        # Test metrics
        print("\n5. Enhanced Metrics Test")
        print(f"   Gaps Detected: {monitor.metrics['gaps_detected']}")
        print(f"   Sectors Analyzed: {monitor.metrics['sectors_analyzed']}")
        print(f"   Audits Performed: {monitor.metrics['audits_performed']}")

    except Exception as e:
        print(f"\n✗ Autonomous Monitor enhancement tests FAILED: {e}")
        import traceback

        traceback.print_exc()
        raise


def main() -> None:
    """Run all tests (standalone). Exceptions will propagate as non-zero exits."""
    print("\n" + "=" * 80)
    print("TEMPLE OF KNOWLEDGE + AUTONOMOUS MONITOR TEST SUITE")
    print("=" * 80)

    test_temple_of_knowledge()
    test_autonomous_monitor_enhancement()


if __name__ == "__main__":
    main()
