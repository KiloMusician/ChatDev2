"""🧪 Test Repository Dictionary Systems
Simple test to verify our systems are working

OmniTag: {
    "purpose": "Test repository dictionary systems functionality",
    "dependencies": ["repository_dictionary", "system_organizer"],
    "context": "System validation and testing",
    "evolution_stage": "v1.0"
}
"""

import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))


def test_repository_systems():
    """Test our repository dictionary systems"""
    print("🧪 Testing Repository Dictionary Systems")
    print("=" * 50)

    success_count = 0
    total_tests = 0

    # Test 1: Repository Dictionary
    total_tests += 1
    try:
        from src.system.dictionary.repository_dictionary import RepositoryDictionary

        repo_dict = RepositoryDictionary(str(repo_root))

        # Quick test
        overview = repo_dict.get_system_overview()
        print("✅ Test 1: Repository Dictionary - SUCCESS")
        print(f"   Repository: {overview.get('repository', 'unknown')}")
        print(f"   Capabilities: {overview.get('total_capabilities', 0)}")
        success_count += 1

    except Exception as e:
        print(f"❌ Test 1: Repository Dictionary - FAILED: {e}")

    # Test 2: System Organizer
    total_tests += 1
    try:
        from src.system.dictionary.system_organizer import SystemOrganizer

        organizer = SystemOrganizer(str(repo_root))

        # Quick test
        systems_analysis = organizer.analyze_systems_for_organization()
        print("✅ Test 2: System Organizer - SUCCESS")
        print(f"   Total systems found: {systems_analysis.get('total_systems', 0)}")
        print(f"   Categories identified: {len(systems_analysis.get('category_breakdown', {}))}")
        success_count += 1

    except Exception as e:
        print(f"❌ Test 2: System Organizer - FAILED: {e}")

    # Test 3: Unified Mapper
    total_tests += 1
    try:
        from src.system.dictionary.unified_mapper import UnifiedMapper

        mapper = UnifiedMapper(str(repo_root))

        # Quick test - just check initialization
        print("✅ Test 3: Unified Mapper - SUCCESS")
        print(f"   Mapper initialized for: {mapper.repository_root}")
        success_count += 1

    except Exception as e:
        print(f"❌ Test 3: Unified Mapper - FAILED: {e}")

    # Test 4: Consciousness Bridge
    total_tests += 1
    try:
        from src.system.dictionary.consciousness_bridge import ConsciousnessBridge

        bridge = ConsciousnessBridge(str(repo_root))

        # Quick test - just check initialization
        print("✅ Test 4: Consciousness Bridge - SUCCESS")
        print(f"   Bridge initialized for: {bridge.repository_root}")
        success_count += 1

    except Exception as e:
        print(f"❌ Test 4: Consciousness Bridge - FAILED: {e}")

    # Summary
    print("\n📊 Test Summary:")
    print(f"   Passed: {success_count}/{total_tests}")
    print(f"   Success Rate: {(success_count / total_tests) * 100:.1f}%")

    if success_count == total_tests:
        print("🎉 All systems are working perfectly!")
        return True
    else:
        print("⚠️ Some systems need attention")
        return False


def quick_organization_demo():
    """Quick demo of organization capabilities"""
    print("\n🚀 Quick Organization Demo")
    print("=" * 50)

    try:
        from src.system.dictionary.system_organizer import SystemOrganizer

        organizer = SystemOrganizer(".")

        # Analyze systems
        analysis = organizer.analyze_systems_for_organization()

        print("📊 Organization Analysis:")
        print(f"   Total systems: {analysis.get('total_systems', 0)}")
        print(f"   Python files: {analysis.get('python_files', 0)}")
        print(f"   Config files: {analysis.get('config_files', 0)}")
        print(f"   Documentation: {analysis.get('documentation_files', 0)}")

        # Show category breakdown
        categories = analysis.get("category_breakdown", {})
        print("\n📁 Categories identified:")
        for category, count in categories.items():
            print(f"   {category}: {count} files")

        # Create plan (but don't execute)
        plan = organizer.create_organization_plan()
        print("\n📋 Organization Plan Created:")
        print(f"   Total actions: {len(plan.get('actions', []))}")
        print(f"   Categories: {len(plan.get('categories', {}))}")

        return True

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests
    systems_working = test_repository_systems()

    if systems_working:
        # Run demo
        quick_organization_demo()

    print("\n🏁 Testing complete!")
