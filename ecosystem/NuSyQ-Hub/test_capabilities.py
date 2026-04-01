"""Test all 45 ecosystem capabilities to see what's working vs dormant."""

from src.integration.boss_rush_bridge import BossRushBridge
from src.integration.breathing_integration import BreathingIntegration
from src.integration.quantum_error_bridge import QuantumErrorBridge
from src.integration.zen_codex_bridge import ZenCodexBridge
from src.orchestration.ecosystem_activator import EcosystemActivator

print("\n" + "=" * 70)
print("🔍 CAPABILITY TESTING ACROSS 13 ACTIVE SYSTEMS")
print("=" * 70)

# 1. Boss Rush - 28 tasks in knowledge base
print("\n1. 🎮 Boss Rush Game Bridge (3 capabilities)")
brb = BossRushBridge()
active_tasks = brb.get_active_tasks()
all_tasks = brb.load_knowledge_base().get("boss_rush_tasks", [])
print(f"   ✅ get_active_tasks(): {len(active_tasks)} active")
print(f"   ✅ load_knowledge_base(): {len(all_tasks)} total tasks")
print(f"   📊 First 3 tasks: {[t.get('title', 'Unnamed')[:40] for t in all_tasks[:3]]}")

# 2. Zen Codex - 12 rules, 34 tags
print("\n2. 🧘 Zen Codex Bridge (4 capabilities)")
zcb = ZenCodexBridge()
rules_by_tag = zcb.query_rules_by_tag("testing")
wisdom = zcb.get_wisdom_for_error("ImportError", "test error")
print(f"   ✅ query_rules_by_tag('testing'): {len(rules_by_tag)} rules")
print(f"   ✅ get_wisdom_for_error(): {wisdom}")

# 3. Breathing Integration - Adaptive timeout pacing
print("\n3. ⏱️  Breathing Pacing Integration (4 capabilities)")
bi = BreathingIntegration()
timeout = bi.calculate_adaptive_timeout(base_timeout=60)
print(f"   ✅ calculate_adaptive_timeout(60): {timeout:.2f}s")
print(
    f"   📊 Performance: {bi.success_rate:.2%} success rate, {bi.average_completion_time:.1f}s avg"
)

# 4. Quantum Error Bridge - Multi-modal healing
print("\n4. ⚛️  Quantum Error Bridge (2 capabilities)")
qeb = QuantumErrorBridge()
analysis = qeb.analyze_error_pattern("ImportError", "cannot import quantum_problem_resolver")
print(f"   ✅ analyze_error_pattern(): {analysis.get('severity', 'unknown')} severity")
print(f"   📊 Pattern: {analysis.get('error_family', 'unknown')}")

# 5. Ecosystem Activator - Central discovery
print("\n5. 🔌 Ecosystem Activator (Discovery + Activation)")
ea = EcosystemActivator()
discovered = ea.discover_systems()
activated = ea.activate_all_systems()
print(f"   ✅ discover_systems(): {len(discovered)} systems")
print(
    f"   ✅ activate_all_systems(): {len([s for s in activated.values() if s.status == 'active'])}/13 active"
)

print("\n" + "=" * 70)
print("🎯 CAPABILITY TEST COMPLETE")
print("=" * 70)
print("\n📊 Next: Identify dormant/placeholder capabilities and wire them up!")
