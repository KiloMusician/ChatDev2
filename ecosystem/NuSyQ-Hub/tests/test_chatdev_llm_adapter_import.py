"""OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["LLM", "Python", "AI", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import importlib
import sys
from pathlib import Path

# Ensure src directory is on path for module import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_chatdev_llm_adapter_import():
    module = importlib.import_module("integration.chatdev_llm_adapter")
    adapter = module.ChatDevLLMAdapter()
    assert adapter.role_model_mapping["Chief Executive Officer"] == module.MISTRAL_7B
