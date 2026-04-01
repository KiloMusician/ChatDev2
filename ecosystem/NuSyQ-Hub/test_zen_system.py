#!/usr/bin/env python3
"""Test script for the Zen-Engine system"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

print("🔍 Testing Zen-Engine System")
print("=" * 60)

# Test 1: Orchestrator
print("\n1️⃣ Testing ZenOrchestrator...")
try:
    from zen_engine.agents.orchestrator import ZenOrchestrator

    orch = ZenOrchestrator()
    print("   ✅ Orchestrator initialized")
    print(f"   📦 Registered agents: {list(orch.agents.keys())}")
    print(f"   📚 Codex rules loaded: {len(orch.codex.get('rules', []))}")
    print(f"   🆔 Session ID: {orch.session.session_id}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 2: Error Observer
print("\n2️⃣ Testing ErrorObserver...")
try:
    from zen_engine.agents.error_observer import ErrorObserver

    observer = ErrorObserver()
    print("   ✅ ErrorObserver initialized")
    print(f"   📋 Patterns loaded: {len(observer.patterns)}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 3: Reflex Engine
print("\n3️⃣ Testing ReflexEngine...")
try:
    from zen_engine.agents.reflex import ReflexEngine

    reflex = ReflexEngine()
    print("   ✅ ReflexEngine initialized")
    print(f"   📚 Rules loaded: {len(reflex.rules)}")

    # Test command check
    test_command = "python -m src.nonexistent_module"
    response = reflex.check_command(test_command)
    print(f"   🧪 Test command check: {response.status}")
    if response.message:
        print(f"   💬 Response: {response.message[:100]}...")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 4: Codex Loader
print("\n4️⃣ Testing CodexLoader...")
try:
    from zen_engine.agents.codex_loader import CodexLoader

    loader = CodexLoader()
    print("   ✅ CodexLoader initialized")
    print(f"   📚 Rules loaded: {len(loader.rules)}")

    # Test rule retrieval
    rule = loader.get_rule("powershell_python_misroute")
    if rule:
        print(f"   🎯 Retrieved rule: {rule.get('id')}")
        print(f"   📖 Lesson: {rule.get('lesson', {}).get('short', 'N/A')[:80]}...")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 5: Matcher
print("\n5️⃣ Testing Matcher...")
try:
    from zen_engine.agents.matcher import Matcher

    matcher = Matcher()
    print("   ✅ Matcher initialized")
    print(f"   📚 Rules indexed: {len(matcher.rules)}")

    # Test error matching
    test_error = {
        "error_lines": ["ModuleNotFoundError: No module named 'foo'"],
        "symptom": "import_error",
        "shell": "powershell",
    }
    matches = matcher.match_error_to_rules(test_error)
    print(f"   🎯 Matched {len(matches)} rules for test error")
    if matches:
        best = matches[0]
        print(f"   🏆 Best match: {best['rule']['id']} (confidence: {best['confidence']:.2f})")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 6: Orchestrator integration
print("\n6️⃣ Testing Orchestrator Integration...")
try:
    # Create a test error event
    error_event = {
        "id": "test_error_001",
        "timestamp": "2025-11-26T07:00:00",
        "shell": "powershell",
        "language_intent": "python",
        "error_lines": ["ModuleNotFoundError: No module named 'test_module'"],
        "symptom": "missing_import",
        "patterns_detected": ["missing_module_import"],
        "context": {"cwd": "/test"},
    }

    response = orch.capture_error(error_event, agent_name="copilot")
    print("   ✅ Error captured and processed")
    print(f"   📊 Matched rules: {len(response['matched_rules'])}")
    print(f"   💡 Suggestions: {len(response['suggestions'])}")

    if response["suggestions"]:
        print(f"   📝 First suggestion: {response['suggestions'][0]['strategy'][:80]}...")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 7: Session summary
print("\n7️⃣ Testing Session Management...")
try:
    summary = orch.get_session_summary()
    print("   ✅ Session summary retrieved")
    print(f"   ⏱️  Duration: {summary['duration']:.2f}s")
    print(f"   📊 Errors captured: {summary['errors_captured']}")
    print(f"   🎯 Rules triggered: {summary['rules_triggered']}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 8: Agent view
print("\n8️⃣ Testing Agent-Specific Views...")
try:
    copilot_view = orch.get_agent_view("copilot")
    print("   ✅ Copilot view generated")
    print(f"   📚 Relevant rules: {copilot_view.get('rules_count', 0)}")
    print(f"   🎯 Top rules: {copilot_view.get('top_rules', [])[:3]}")

    ollama_view = orch.get_agent_view("ollama")
    print("   ✅ Ollama view generated")
    print(f"   📚 Relevant rules: {ollama_view.get('rules_count', 0)}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n" + "=" * 60)
print("✅ Zen-Engine system test complete!")
print("=" * 60)
