"""🗂️ Repository Dictionary System Demo
Demonstrates the unified repository organization and mapping system
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))


def demo_repository_dictionary():
    """Demonstrate Repository Dictionary functionality"""
    print("🗂️ Repository Dictionary System Demo")
    print("=" * 50)

    try:
        from src.system.dictionary.repository_dictionary import RepositoryDictionary

        repo_dict = RepositoryDictionary(str(repo_root))

        print("\n📋 System Overview:")
        overview = repo_dict.get_system_overview()
        for key, value in overview.items():
            print(f"  {key}: {value}")

        print("\n🔍 Searching capabilities for 'ai':")
        ai_capabilities = repo_dict.search_capabilities("ai")
        for i, cap in enumerate(ai_capabilities[:5]):
            print(f"  {i + 1}. {cap['name']} ({cap['type']}) - {cap['description'][:80]}...")

        print(f"\n📊 Found {len(ai_capabilities)} AI-related capabilities")

        # Test file info
        test_file = "src/ai/ai_coordinator.py"
        print(f"\n📄 File Info for {test_file}:")
        file_info = repo_dict.get_file_info(test_file)
        for key, value in file_info.items():
            if key == "capabilities" and isinstance(value, list):
                print(f"  {key}: {len(value)} capabilities")
            else:
                print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Error in Repository Dictionary demo: {e}")
        return False


def demo_system_organizer():
    """Demonstrate System Organizer functionality"""
    print("\n🗂️ System Organizer Demo")
    print("=" * 50)

    try:
        from src.system.dictionary.system_organizer import SystemOrganizer

        organizer = SystemOrganizer(str(repo_root))

        print("\n📋 Analyzing systems for organization...")
        systems_analysis = organizer.analyze_systems_for_organization()

        print("\n📊 Organization Analysis:")
        total_systems = sum(len(files) for files in systems_analysis.values())
        print(f"  Total systems to organize: {total_systems}")
        print(f"  Categories found: {len(systems_analysis)}")

        for category, files in systems_analysis.items():
            if files:
                print(f"  📁 {category}: {len(files)} files")
                for file_path in files[:3]:  # Show first 3 files
                    print(f"    - {file_path}")
                if len(files) > 3:
                    print(f"    ... and {len(files) - 3} more")

        print("\n📋 Creating organization plan...")
        plan = organizer.create_organization_plan()

        print("\n📈 Organization Plan Summary:")
        print(f"  Total actions: {len(plan['actions'])}")
        print(f"  Consciousness enhancements: {len(plan['consciousness_enhancements'])}")

        # Show some example actions
        print("\n🎯 Example organization actions:")
        for i, action in enumerate(plan["actions"][:5]):
            print(f"  {i + 1}. {action['source']} → {action['target']} ({action['category']})")

        return True

    except Exception as e:
        print(f"❌ Error in System Organizer demo: {e}")
        return False


def demo_unified_mapper():
    """Demonstrate Unified Mapper functionality"""
    print("\n🗂️ Unified Mapper Demo")
    print("=" * 50)

    try:
        from src.system.dictionary.unified_mapper import UnifiedMapper

        mapper = UnifiedMapper(str(repo_root))

        print("\n📊 Creating unified mapping...")
        mapping = mapper.create_unified_mapping()

        print("\n📈 Mapping Statistics:")
        stats = mapping["statistics"]
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n🔗 Dependency Analysis:")
        dep_analysis = mapping["dependency_analysis"]
        print(f"  Most depended upon: {len(dep_analysis['most_depended_upon'])} modules")
        print(f"  Circular dependencies: {len(dep_analysis['circular_dependencies'])} groups")
        print(f"  Orphaned modules: {len(dep_analysis['orphaned_modules'])}")

        if dep_analysis["most_depended_upon"]:
            print("\n🔝 Top Dependencies:")
            for i, (module, count) in enumerate(dep_analysis["most_depended_upon"][:5]):
                print(f"  {i + 1}. {module} ({count} dependencies)")

        print("\n🧠 Consciousness Analysis:")
        cons_analysis = mapping["consciousness_analysis"]
        print(f"  Consciousness hubs: {len(cons_analysis['consciousness_hubs'])}")
        print(f"  Awareness levels: {cons_analysis['awareness_levels']}")

        print("\n🤖 AI Coordination Analysis:")
        ai_analysis = mapping["ai_coordination_analysis"]
        print(f"  Coordination hubs: {len(ai_analysis['coordination_hubs'])}")
        print(f"  Coordination levels: {ai_analysis['coordination_levels']}")

        print(f"\n🎯 Integration Opportunities: {len(mapping['integration_opportunities'])}")
        print(f"📝 Optimization Recommendations: {len(mapping['optimization_recommendations'])}")

        return True

    except Exception as e:
        print(f"❌ Error in Unified Mapper demo: {e}")
        return False


def demo_consciousness_bridge():
    """Demonstrate Consciousness Bridge functionality"""
    print("\n🗂️ Consciousness Bridge Demo")
    print("=" * 50)

    try:
        from src.system.dictionary.consciousness_bridge import ConsciousnessBridge

        bridge = ConsciousnessBridge(str(repo_root))

        print("\n🧠 Consciousness Bridge Status:")
        print(f"  Repository: {bridge.repository_root.name}")
        print(
            f"  Consciousness Level: {bridge.repository_consciousness['repository_identity']['consciousness_level']}"
        )
        print(f"  AI Coordinators: {len(bridge.ai_coordinators)}")
        print(f"  Enhancement Bridges: {len(bridge.enhancement_bridges)}")

        # Test consciousness-enhanced categorization
        test_file = "src/ai/ai_coordinator.py"
        print(f"\n🔍 Testing enhanced categorization for {test_file}:")
        categorization = bridge.enhance_file_categorization(test_file)

        print(f"  Base Category: {categorization['base_category']}")
        print(f"  Consciousness Category: {categorization['consciousness_category']}")
        print(f"  AI Potential: {categorization['ai_coordination_potential']}")
        print(f"  Consciousness Level: {categorization['consciousness_level']}")
        print(
            f"  Enhancement Recommendations: {len(categorization['enhancement_recommendations'])}"
        )
        print(f"  Integration Opportunities: {categorization['integration_opportunities']}")

        if categorization["enhancement_recommendations"]:
            print("\n💡 Enhancement Recommendations:")
            for i, rec in enumerate(categorization["enhancement_recommendations"][:3]):
                print(
                    f"  {i + 1}. {rec['type']}: {rec['description']} (Priority: {rec['priority']})"
                )

        return True

    except Exception as e:
        print(f"❌ Error in Consciousness Bridge demo: {e}")
        return False


def main():
    """Run all demos"""
    print("🚀 Repository Dictionary System - Comprehensive Demo")
    print("=" * 60)

    results = {
        "Repository Dictionary": demo_repository_dictionary(),
        "System Organizer": demo_system_organizer(),
        "Unified Mapper": demo_unified_mapper(),
        "Consciousness Bridge": demo_consciousness_bridge(),
    }

    print("\n" + "=" * 60)
    print("📊 Demo Results Summary:")

    for component, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {component}: {status}")

    successful = sum(results.values())
    total = len(results)

    print(f"\n🎯 Overall Success: {successful}/{total} components working")

    if successful == total:
        print("\n🎉 All Repository Dictionary System components are operational!")
        print("\n📝 Next Steps:")
        print("  1. Review organization plans before execution")
        print("  2. Export unified mappings for analysis")
        print("  3. Apply consciousness enhancements")
        print("  4. Monitor system performance and optimization")
    else:
        print("\n🔧 Some components need attention - check error messages above")


if __name__ == "__main__":
    main()
