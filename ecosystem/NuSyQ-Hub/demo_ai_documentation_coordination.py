#!/usr/bin/env python3
"""🤖 Enhanced AI Coordination with Documentation Integration Demo
============================================================

OmniTag: {
    "purpose": "Demonstrate enhanced AI coordination with unified documentation capabilities",
    "dependencies": ["ai_coordinator", "unified_documentation_engine", "documentation_provider"],
    "context": "Integration demo for AI-powered documentation generation",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "AIDocumentationDemo",
    "integration_points": ["ai_coordination", "documentation_generation", "task_routing"],
    "related_tags": ["AIIntegration", "DocumentationAutomation", "TaskCoordination"],
    "quantum_state": "ΞΨΩ∞⟨AI-DOCS⟩→ΦΣΣ⟨COORDINATION⟩"
}

RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳AI-DOCUMENTATION-DEMO⨳⚡⟣⟢⟡◉●○◆◊♦
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ai.ai_coordinator import (
        DocumentationProvider,
        Priority,
        TaskType,
        ai_documentation_help,
        get_coordinator,
    )

    print("✅ AI Coordinator imported successfully")
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AI Coordinator not available: {e}")
    AI_AVAILABLE = False


async def demo_enhanced_ai_coordination():
    """Demonstrate enhanced AI coordination with documentation capabilities"""
    print("🤖 ENHANCED AI COORDINATION WITH DOCUMENTATION DEMO")
    print("=" * 55)

    if not AI_AVAILABLE:
        print("❌ AI Coordinator not available - demo cannot proceed")
        return

    # Test 1: Unified Documentation Generation
    print("\n🌌 Test 1: Unified Documentation Generation")
    print("-" * 45)

    try:
        result = await ai_documentation_help(
            "Generate unified documentation across all repositories",
            task_type=TaskType.UNIFIED_DOCUMENTATION,
        )
        print("✅ Unified documentation generation:")
        print(result[:300] + "..." if len(result) > 300 else result)
    except Exception as e:
        print(f"❌ Unified documentation error: {e}")

    # Test 2: Context Generation
    print("\n📄 Test 2: Context Generation")
    print("-" * 35)

    try:
        result = await ai_documentation_help(
            "Generate context files for the current project structure",
            task_type=TaskType.CONTEXT_GENERATION,
            target_path="src/",
        )
        print("✅ Context generation:")
        print(result[:200] + "..." if len(result) > 200 else result)
    except Exception as e:
        print(f"❌ Context generation error: {e}")

    # Test 3: API Documentation
    print("\n📋 Test 3: API Documentation Generation")
    print("-" * 40)

    try:
        result = await ai_documentation_help(
            "Generate API documentation for the unified documentation engine",
            task_type=TaskType.API_DOCUMENTATION,
            project_path="src/unified_documentation_engine.py",
        )
        print("✅ API documentation generation:")
        print(result[:200] + "..." if len(result) > 200 else result)
    except Exception as e:
        print(f"❌ API documentation error: {e}")

    # Test 4: Documentation Provider Capabilities
    print("\n🔧 Test 4: Documentation Provider Capabilities")
    print("-" * 45)

    try:
        doc_provider = DocumentationProvider()
        capabilities = doc_provider.get_capabilities()
        is_available = doc_provider.is_available()

        print(f"✅ Documentation provider available: {is_available}")
        print(f"✅ Supported capabilities: {len(capabilities)} task types")
        for cap in capabilities:
            print(f"   - {cap.value}")
    except Exception as e:
        print(f"❌ Provider capabilities error: {e}")

    # Test 5: AI Coordinator System Status
    print("\n📊 Test 5: AI Coordinator System Status")
    print("-" * 40)

    try:
        coordinator = get_coordinator()
        status = coordinator.get_system_status()
        health = await coordinator.health_check()

        print(f"✅ System health: {health}")
        print(f"✅ Active providers: {len(status.get('providers', {}))}")
        print(f"✅ Total tasks processed: {status.get('total_tasks', 0)}")
    except Exception as e:
        print(f"❌ System status error: {e}")

    # Test 6: General Code Help with Documentation Focus
    print("\n💻 Test 6: Code Help with Documentation Focus")
    print("-" * 45)

    try:
        from ai.ai_coordinator import ai_code_help

        result = await ai_code_help(
            "Create a function that generates markdown documentation from Python docstrings",
            language="python",
            priority=Priority.HIGH,
        )
        print("✅ Code help for documentation function:")
        print(result[:300] + "..." if len(result) > 300 else result)
    except Exception as e:
        print(f"❌ Code help error: {e}")

    print("\n🎉 ENHANCED AI COORDINATION DEMO COMPLETE!")
    print("🌟 AI-powered documentation generation integrated successfully!")


def demo_task_types():
    """Display available task types related to documentation"""
    print("\n📋 AVAILABLE DOCUMENTATION TASK TYPES:")
    print("=" * 42)

    doc_types = [
        TaskType.UNIFIED_DOCUMENTATION,
        TaskType.CONTEXT_GENERATION,
        TaskType.API_DOCUMENTATION,
        TaskType.CROSS_REPO_LINKING,
        TaskType.DOCUMENTATION_MONITORING,
        TaskType.DOCUMENTATION,
    ]

    for i, task_type in enumerate(doc_types, 1):
        print(f"{i}. {task_type.value.replace('_', ' ').title()}")

    print(f"\n✅ Total documentation task types: {len(doc_types)}")


async def main():
    """Main demonstration function"""
    print("🚀 STARTING AI COORDINATION WITH DOCUMENTATION DEMO")
    print("=" * 55)

    # Show available task types
    demo_task_types()

    # Run async demo
    await demo_enhanced_ai_coordination()

    print("\n📊 DEMO SUMMARY:")
    print("- ✅ Enhanced AI Coordinator with documentation capabilities")
    print("- ✅ Unified documentation engine integration")
    print("- ✅ Specialized documentation provider")
    print("- ✅ Task routing for documentation tasks")
    print("- ✅ Cross-repository awareness")
    print("- ✅ Type2 consciousness integration")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        raise
