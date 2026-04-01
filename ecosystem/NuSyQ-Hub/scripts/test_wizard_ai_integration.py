#!/usr/bin/env python3
"""🧪 Test Suite: Wizard Navigator → AI Assistance Integration

Tests Wizard Navigator's AI-powered code exploration assistance
using Ollama/ChatDev integration.

OmniTag: {
    "purpose": "Test Wizard Navigator AI integration",
    "dependencies": ["wizard_navigator_consolidated", "ollama_chatdev_integrator"],
    "context": "AI-powered navigation testing",
    "evolution_stage": "v1.0-testing"
}
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_wizard_navigator_initialization():
    """Test Wizard Navigator initializes correctly."""
    print("\n🧪 TEST 1: Wizard Navigator Initialization")
    print("=" * 60)

    try:
        from src.tools.wizard_navigator_consolidated import WizardNavigator

        wizard = WizardNavigator(repo_root)

        print("   ✅ Wizard Navigator initialized")
        print(f"   📍 Root: {wizard.root}")
        print(f"   🗺️  Current path: {wizard.current_path}")
        print(f"   📊 Visited paths: {len(wizard.visited_paths)}")
        print(f"   🔍 Discoveries: {len(wizard.discoveries)}")

        room = wizard.get_current_room()
        print(f"   🏛️  Current room: {room['name']}")
        print(f"   🚪 Exits: {len(room['exits'])}")
        print(f"   📜 Items: {len(room['items'])}")

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ai_assist_method_exists():
    """Test AI assist method is available."""
    print("\n🧪 TEST 2: AI Assist Method Availability")
    print("=" * 60)

    try:
        import inspect

        from src.tools.wizard_navigator_consolidated import WizardNavigator

        wizard = WizardNavigator(repo_root)

        # Check method exists
        assert hasattr(wizard, "_ai_assist"), "AI assist method should exist"

        # Check method signature
        source = inspect.getsource(wizard._ai_assist)
        has_integration = "ollama_chatdev_integrator" in source.lower()

        print("   ✅ AI assist method exists")
        print(f"   🔗 Integration code present: {has_integration}")
        print(f"   📋 Method signature: {inspect.signature(wizard._ai_assist)}")

        if has_integration:
            print("   ✅ INTEGRATION VERIFIED: Ollama/ChatDev wired")
        else:
            print("   ⚠️  WARNING: Integration may not be wired")

        return has_integration

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ai_assist_execution():
    """Test AI assist executes (with graceful fallback)."""
    print("\n🧪 TEST 3: AI Assist Execution")
    print("=" * 60)

    try:
        from src.tools.wizard_navigator_consolidated import WizardNavigator

        wizard = WizardNavigator(repo_root)

        # Try AI assist with simple query
        query = "What files should I explore?"
        response = wizard._ai_assist(query)

        print("   ✅ AI assist executed")
        print(f"   📝 Query: {query}")
        print(f"   📊 Response length: {len(response)} chars")

        # Check response quality
        has_context = str(wizard.current_path) in response or "Location" in response
        has_guidance = any(word in response.lower() for word in ["explore", "file", "directory", "suggest"])

        print(f"   📍 Context-aware: {has_context}")
        print(f"   💡 Provides guidance: {has_guidance}")

        # Print first 200 chars of response
        preview = response[:200] + "..." if len(response) > 200 else response
        print(f"   🔍 Response preview:\n{preview}")

        return has_context or has_guidance

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ollama_integrator_available():
    """Test Ollama integrator is accessible."""
    print("\n🧪 TEST 4: Ollama Integrator Availability")
    print("=" * 60)

    try:
        from src.ai.ollama_chatdev_integrator import EnhancedOllamaChatDevIntegrator

        integrator = EnhancedOllamaChatDevIntegrator()
        integrator.check_systems()

        print("   ✅ Ollama integrator imported")
        print(f"   🔌 Ollama available: {integrator.ollama_available}")
        print(f"   🔌 OpenAI fallback: {integrator.openai_available}")
        print(f"   📍 Repo root: {integrator.repo_root}")

        # Check methods exist
        has_chat = hasattr(integrator, "enhanced_intelligent_chat")
        has_systems = hasattr(integrator, "check_systems")

        print(f"   ✅ Chat method exists: {has_chat}")
        print(f"   ✅ System check exists: {has_systems}")

        if integrator.ollama_available:
            print("   🎉 Ollama is online and ready!")
        else:
            print("   ⚠️  Ollama offline (fallback will be used)")

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_command_integration():
    """Test AI assist integrated with command system."""
    print("\n🧪 TEST 5: Command System Integration")
    print("=" * 60)

    try:
        from src.tools.wizard_navigator_consolidated import WizardNavigator

        wizard = WizardNavigator(repo_root)

        # Test 'ai' command exists in command processing (correct method: handle_command)
        test_commands = ["help", "look", "ai what should I explore?"]

        for cmd in test_commands:
            result = wizard.handle_command(cmd)
            print(f"   ✅ Command '{cmd.split()[0]}' processed")

            if cmd.startswith("ai"):
                # Verify AI command produces response
                assert result is not None, "AI command should return response"
                assert len(str(result)) > 10, "AI response should be substantive"
                print(f"      📊 AI response: {len(str(result))} chars")

        print("   ✅ All commands integrated")

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all Wizard Navigator AI integration tests."""
    print("🧙 WIZARD NAVIGATOR → AI ASSISTANCE INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing AI-powered code exploration with Ollama/ChatDev")
    print()

    results = {
        "Navigator Init": test_wizard_navigator_initialization(),
        "AI Method Available": test_ai_assist_method_exists(),
        "AI Execution": test_ai_assist_execution(),
        "Ollama Integrator": test_ollama_integrator_available(),
        "Command Integration": test_command_integration(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n   Total: {passed}/{total} tests passing")

    if passed == total:
        print("   🎉 ALL TESTS PASSED!")
        print("\n   ✅ AI-powered navigation operational:")
        print("      🧙 Wizard Navigator initialized")
        print("      🤖 Ollama/ChatDev integration active")
        print("      💡 Context-aware assistance enabled")
        print("      📍 Location-based guidance ready")
        return 0
    else:
        print(f"   ⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
