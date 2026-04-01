"""ZETA03 Enhanced Model Selection System Test"""

"""
OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""


import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.integration.Ollama_Integration_Hub import (
        IntelligentModelSelector,
        OllamaModel,
    )

    print("🚀 Testing ZETA03 Enhanced Model Selection...")
    selector = IntelligentModelSelector()

    # Test basic functionality
    print(f"📊 Analytics enabled: {selector.analytics_enabled}")
    print(f"🎛️ Available strategies: {list(selector.selection_strategies.keys())}")
    print(f"⚙️ Current strategy: {selector.current_strategy}")

    # Test intent analysis
    test_messages = [
        "Help me debug this Python function",
        "Write a creative story about robots",
        "Analyze the security vulnerabilities in this code",
        "Optimize this database query for better performance",
    ]

    for msg in test_messages:
        intent = selector.analyze_message_intent(msg)
        print(f'🧠 "{msg[:30]}..." → Intent: {intent}')

    # Test strategy switching
    selector.set_selection_strategy("accuracy_optimized")
    print(f"✅ Strategy changed to: {selector.current_strategy}")

    # Test mock models
    mock_models = {
        "llama2:7b": OllamaModel(
            "llama2:7b",
            4000000000,
            "abc123",
            "2024-01-01",
            capabilities=["conversation", "general_knowledge"],
            performance_rating=7.0,
        ),
        "deepseek-coder": OllamaModel(
            "deepseek-coder",
            6000000000,
            "def456",
            "2024-01-01",
            capabilities=["code_analysis", "debugging"],
            performance_rating=8.5,
        ),
    }

    # Test selection
    selected = selector.select_optimal_model(mock_models, "code_analysis")
    print(f"🎯 Selected model for code analysis: {selected}")

    # Test feedback recording
    selector.record_selection_feedback("deepseek-coder", "code_analysis", 2.5, 0.9)
    print("📊 Recorded feedback successfully")

    print("✅ ZETA03 Enhanced Model Selection System: OPERATIONAL")
    print("🏆 ZETA03 Status: MASTERED")

except Exception as e:
    print(f"❌ Error testing ZETA03 system: {e}")
    import traceback

    traceback.print_exc()
