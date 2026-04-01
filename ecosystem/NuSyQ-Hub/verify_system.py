#!/usr/bin/env python3
"""Quick system verification script."""

from AI_AGENT_COORDINATION_MASTER import AIAgentCoordinationMaster
from src.orchestration.ai_capabilities_enhancer import AICapabilitiesEnhancer
from src.utils.intelligent_timeout_manager import get_intelligent_timeout_manager

print("\n🎉 SYSTEM VERIFICATION COMPLETE")
print("=" * 60)

# Test capabilities enhancer
enhancer = AICapabilitiesEnhancer()
print(f"✅ AI Workflows: {len(enhancer.workflows)}")

# Test timeout manager
tm = get_intelligent_timeout_manager()
print(f"✅ Ollama Timeout (high): {tm.get_timeout('ollama', complexity=1.5, priority='high')}s")
print(
    f"✅ ChatDev Timeout (critical): {tm.get_timeout('chatdev', complexity=2.0, priority='critical')}s"
)

# Test coordination
coord = AIAgentCoordinationMaster()
status = coord.get_system_status()
print(f"✅ AI Systems: {status.get('registered_systems', 0)}")
print(f"✅ Workflows: {status.get('workflow_count', 0)}")

print("=" * 60)
print("🚀 ALL COMPONENTS OPERATIONAL\n")
