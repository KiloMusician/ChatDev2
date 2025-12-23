"""
╔══════════════════════════════════════════════════════════════════════════╗
║ NuSyQ ChatDev Modular Model Adapter                                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║ PURPOSE: Patch ChatDev's ChatChain to use per-agent Ollama models       ║
║ ENABLES: Dynamic model selection based on agent role                    ║
║ TRACKS: Model performance per agent for optimization                    ║
╚══════════════════════════════════════════════════════════════════════════╝

This adapter monkey-patches ChatDev's ChatChain class to:
1. Read per-agent model assignments from RoleConfig_Modular.json
2. Dynamically select the appropriate Ollama model for each agent
3. Track model usage and performance metrics
4. Enable A/B testing and optimization experiments

Usage:
    from chatdev.modular_model_adapter import apply_modular_models
    
    # Apply the modular model system before running ChatDev
    apply_modular_models()
    
    # Now run ChatDev as normal - models will be selected per agent
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

# Import the modular manager
try:
    from chatdev.modular_agent_models import get_manager
except ImportError:
    # Add ChatDev to path if needed
    chatdev_path = Path(__file__).parent.parent
    sys.path.insert(0, str(chatdev_path))
    from chatdev.modular_agent_models import get_manager

logger = logging.getLogger(__name__)


class OllamaModelType:
    """
    Dynamic Ollama model type wrapper
    
    ChatDev expects ModelType enum values, but we need dynamic model strings.
    This class acts as a drop-in replacement that works with both systems.
    """
    
    def __init__(self, model_name: str):
        """
        Create a dynamic Ollama model type
        
        Args:
            model_name: Ollama model (e.g., "qwen2.5-coder:14b")
        """
        self.model_name = model_name
        self.value = model_name  # For compatibility with enum-like usage
        self._name_ = f"OLLAMA_{model_name.upper().replace(':', '_').replace('.', '_').replace('-', '_')}"
    
    def __str__(self):
        return self.model_name
    
    def __repr__(self):
        return f"OllamaModelType('{self.model_name}')"
    
    def __eq__(self, other):
        if isinstance(other, OllamaModelType):
            return self.model_name == other.model_name
        return str(self) == str(other)
    
    def __hash__(self):
        return hash(self.model_name)


def get_ollama_model_type(model_name: str) -> OllamaModelType:
    """
    Get an OllamaModelType instance for the given model name
    
    Args:
        model_name: Ollama model name
    
    Returns:
        OllamaModelType instance
    """
    return OllamaModelType(model_name)


def patch_chat_chain():
    """
    Monkey-patch ChatChain to use modular per-agent models
    
    This function modifies ChatDev's ChatChain class to:
    1. Load the modular model manager
    2. Assign models based on agent roles
    3. Track model usage per agent
    """
    try:
        from chatdev.chat_chain import ChatChain
    except ImportError:
        logger.error("Could not import ChatChain - modular models disabled")
        return
    
    # Store original __init__
    original_init = ChatChain.__init__
    
    def patched_init(self, *args, **kwargs):
        """Patched __init__ that sets up modular model tracking"""
        # Call original init
        original_init(self, *args, **kwargs)
        
        # Add modular model manager
        self._model_manager = get_manager()
        self._modular_models_enabled = True
        
        logger.info("✅ ChatChain initialized with modular agent models")
    
    # Store original make_recruitment method
    original_make_recruitment = ChatChain.make_recruitment
    
    def patched_make_recruitment(self, *args, **kwargs):
        """Patched make_recruitment that assigns per-agent models"""
        # Get the agent role from kwargs or args
        role = None
        if 'agent_name' in kwargs:
            role = kwargs['agent_name']
        elif len(args) > 0:
            role = args[0]
        
        # Get the appropriate model for this agent
        if role and hasattr(self, '_modular_models_enabled'):
            agent_model = self._model_manager.get_model_for_role(role)
            
            # Convert to OllamaModelType
            model_type = get_ollama_model_type(agent_model)
            
            # Override model_type in kwargs
            if 'model_type' not in kwargs:
                kwargs['model_type'] = model_type
            
            logger.info(f"🤖 Assigning {agent_model} to {role}")
        
        # Call original method
        return original_make_recruitment(self, *args, **kwargs)
    
    # Apply patches
    ChatChain.__init__ = patched_init
    ChatChain.make_recruitment = patched_make_recruitment
    
    logger.info("✅ ChatChain patched for modular agent models")


def patch_model_backend():
    """
    Patch ModelBackend to support dynamic Ollama model types
    
    This allows OllamaModelType instances to work seamlessly with
    ChatDev's existing model backend infrastructure.
    """
    try:
        from camel.model_backend import ModelBackend
    except ImportError:
        logger.error("Could not import ModelBackend - skipping patch")
        return
    
    original_init = ModelBackend.__init__
    
    def patched_backend_init(self, model_type, *args, **kwargs):
        """Patched ModelBackend.__init__ that handles OllamaModelType"""
        # If we got an OllamaModelType, extract the model name
        if isinstance(model_type, OllamaModelType):
            model_name = model_type.model_name
            logger.info(f"🔧 ModelBackend using Ollama model: {model_name}")
            
            # Set environment variable for Ollama integration
            os.environ['CHATDEV_MODEL'] = model_name
        
        # Call original init
        original_init(self, model_type, *args, **kwargs)
    
    ModelBackend.__init__ = patched_backend_init
    logger.info("✅ ModelBackend patched for Ollama model types")


def apply_modular_models():
    """
    Apply all patches to enable modular per-agent Ollama models
    
    Call this function before running ChatDev to enable the modular
    model system. It will:
    1. Patch ChatChain to use per-agent models
    2. Patch ModelBackend to support OllamaModelType
    3. Initialize the model manager
    
    Example:
        from chatdev.modular_model_adapter import apply_modular_models
        
        apply_modular_models()
        # Now run ChatDev as normal
    """
    logger.info("🚀 Applying modular agent model system...")
    
    # Initialize the manager
    manager = get_manager()
    manager.print_model_assignments()
    
    # Apply patches
    patch_model_backend()
    patch_chat_chain()
    
    logger.info("✅ Modular agent model system activated")
    return manager


def get_session_performance_report() -> dict:
    """
    Get performance report for the current session
    
    Returns:
        Dictionary with performance metrics per agent and model
    """
    manager = get_manager()
    return {
        "agent_performance": manager.get_performance_summary(),
        "model_usage": manager.get_model_usage_stats()
    }


def save_performance_report(output_path: Path):
    """
    Save performance report to file
    
    Args:
        output_path: Path to save the report
    """
    manager = get_manager()
    manager.save_session_log(output_path)


if __name__ == "__main__":
    # Demo the adapter
    print("\n" + "="*70)
    print("🧪 Testing Modular Model Adapter")
    print("="*70)
    
    # Apply patches
    manager = apply_modular_models()
    
    # Test model type creation
    print("\n🔧 Testing OllamaModelType:")
    model_type = get_ollama_model_type("qwen2.5-coder:14b")
    print(f"  Created: {model_type}")
    print(f"  Name: {model_type._name_}")
    print(f"  Value: {model_type.value}")
    
    # Test model lookup
    print("\n🔍 Testing model lookup:")
    test_roles = ["Programmer", "Code Reviewer", "Software Test Engineer"]
    for role in test_roles:
        model = manager.get_model_for_role(role)
        print(f"  {role}: {model}")
    
    print("\n✅ Adapter test complete")
    print("="*70)
