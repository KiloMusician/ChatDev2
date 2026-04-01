import logging

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""🔗 KILO-FOOLISH Copilot VS Code Integration Enhancement.

Enhances VS Code Copilot with existing KILO infrastructure context.

OmniTag: {
    "purpose": "VS Code Copilot integration leveraging existing enhanced_bridge",
    "dependencies": ["copilot.enhanced_bridge", "setup.secrets", "vscode"],
    "context": "Development workflow enhancement using existing KILO components",
    "evolution_stage": "v3.0"
}
MegaTag: {
    "type": "CopilotEnhancement",
    "integration_points": ["enhanced_bridge", "vscode", "workspace_context"],
    "related_tags": ["ExistingInfrastructure", "WorkspaceEnhancement", "ContextBridge"]
}
RSHTS: ΞΨ⟨COPILOT⟩↔⟨ENHANCED-BRIDGE⟩→ΦΩ∞
"""

import contextlib
import json
import sys
from pathlib import Path
from typing import Any

# Proper imports from existing infrastructure
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

try:
    from copilot.enhanced_bridge import EnhancedBridge
    from setup.secrets import get_config

    ENHANCED_BRIDGE_AVAILABLE = True
except ImportError:
    ENHANCED_BRIDGE_AVAILABLE = False


class CopilotKILOIntegration:
    """Integrates VS Code Copilot with existing KILO-FOOLISH enhanced bridge.

    Leverages existing OmniTag, MegaTag, and symbolic cognition systems.
    """

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize CopilotKILOIntegration with workspace_root."""
        self.workspace_root = workspace_root or Path.cwd()
        self.vscode_dir = self.workspace_root / ".vscode"
        self.copilot_context_dir = self.workspace_root / ".copilot_kilo"

        # Initialize existing infrastructure
        self.enhanced_bridge = None
        self.config = None

        if ENHANCED_BRIDGE_AVAILABLE:
            try:
                self.enhanced_bridge = EnhancedBridge(str(self.workspace_root))
                self.config = get_config()
            except (AttributeError, RuntimeError, ImportError):
                logger.debug("Suppressed AttributeError/ImportError/RuntimeError", exc_info=True)

        self.setup_directories()

    def setup_directories(self) -> None:
        """Setup required directories."""
        self.vscode_dir.mkdir(exist_ok=True)
        self.copilot_context_dir.mkdir(exist_ok=True)

    def enhance_vscode_settings_with_kilo(self) -> None:
        """Enhance VS Code settings to work with existing KILO infrastructure."""
        settings_file = self.vscode_dir / "settings.json"

        # Load existing settings
        settings: dict[str, Any] = {}
        if settings_file.exists():
            try:
                with open(settings_file) as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)

        # KILO-specific enhancements that leverage existing infrastructure
        kilo_enhancements = {
            # Enhanced Copilot with KILO context
            "github.copilot.enable": {
                "*": True,
                "python": True,
                "json": True,
                "markdown": True,
                "powershell": True,
            },
            # KILO-FOOLISH specific paths (using existing structure)
            "python.analysis.extraPaths": [
                "${workspaceFolder}/src",
                "${workspaceFolder}/KILO_Core",
                "${workspaceFolder}/LOGGING",
            ],
            # File associations for existing KILO patterns
            "files.associations": {
                "*.omnitag": "json",
                "*.megatag": "json",
                "*.rshts": "plaintext",
                "*.kilo": "python",
            },
            # Enhanced IntelliSense for better context
            "editor.inlineSuggest.enabled": True,
            "editor.quickSuggestions": {
                "other": "on",
                "comments": "on",
                "strings": "on",
            },
            # KILO workspace awareness
            "kilo.foolish.workspace": {
                "enhanced_bridge_enabled": ENHANCED_BRIDGE_AVAILABLE,
                "context_enhancement": True,
                "omnitag_processing": True,
                "megatag_processing": True,
                "symbolic_cognition": True,
            },
        }

        # Merge settings
        settings.update(kilo_enhancements)

        # Save enhanced settings
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

    def generate_copilot_context_files(self) -> None:
        """Generate context files that leverage existing KILO infrastructure."""
        # Architecture context using existing enhanced bridge
        if self.enhanced_bridge:
            arch_context = self._generate_enhanced_bridge_context()
            with open(self.copilot_context_dir / "kilo_architecture.md", "w") as f:
                f.write(arch_context)

        # Pattern reference for existing OmniTag/MegaTag systems
        patterns_ref = self._generate_existing_patterns_reference()
        with open(self.copilot_context_dir / "kilo_patterns.md", "w") as f:
            f.write(patterns_ref)

        # Integration guide for existing systems
        integration_guide = self._generate_existing_integration_guide()
        with open(self.copilot_context_dir / "integration_guide.md", "w") as f:
            f.write(integration_guide)

    def _generate_enhanced_bridge_context(self) -> str:
        """Generate context using existing enhanced bridge."""
        if not self.enhanced_bridge:
            return "# KILO Enhanced Bridge not available"

        try:
            # Get context summary from existing enhanced bridge
            context_summary = self.enhanced_bridge.summarize_context()

            return f"""# KILO-FOOLISH Enhanced Bridge Context

## Current Bridge Status
- Initialized: {context_summary.get("initialized_at", "Unknown")}
- OmniTag System: {context_summary.get("omni_tag_system_status", "Unknown")}
- MegaTag Processor: {context_summary.get("mega_tag_processor_status", "Unknown")}
- Symbolic Cognition: {context_summary.get("symbolic_cognition_status", "Unknown")}

## Contextual Memory
{json.dumps(context_summary.get("contextual_memory", {}), indent=2)}

## Integration Points
The Enhanced Bridge provides:
- OmniTag processing via `enhanced_bridge.process_omni_tag(tag_data)`
- MegaTag processing via `enhanced_bridge.process_mega_tag(tag_data)`
- Symbolic reasoning via `enhanced_bridge.perform_symbolic_reasoning(input_data)`
- Contextual memory via `enhanced_bridge.add_contextual_memory(key, value)`

## Usage Patterns
```python
# Initialize existing enhanced bridge
from src.copilot.enhanced_bridge import EnhancedBridge
bridge = EnhancedBridge()

# Process OmniTag
omni_result = bridge.process_omni_tag({{
    "purpose": "Module description",
    "dependencies": ["dep1", "dep2"],
    "context": "Usage context"
}})

# Add contextual memory
bridge.add_contextual_memory("current_task", "Developing integration")

# Perform symbolic reasoning
reasoning = bridge.perform_symbolic_reasoning("Input for analysis")
```
"""

        except Exception as e:
            return f"# Enhanced Bridge Context Error: {e}"

    def _generate_existing_patterns_reference(self) -> str:
        """Generate patterns reference for existing KILO systems."""
        return """# KILO-FOOLISH Existing Patterns Reference

## Enhanced Bridge Patterns

### OmniTag Processing (Existing System)
```python
# Use existing OmniTag system via enhanced bridge
omni_tag_data = {
    "purpose": "Clear module purpose",
    "dependencies": ["list", "of", "dependencies"],
    "context": "Usage context and environment",
    "evolution_stage": "v1.0"
}
result = enhanced_bridge.process_omni_tag(omni_tag_data)
```

### MegaTag Processing (Existing System)
```python
# Use existing MegaTag system via enhanced bridge
mega_tag_data = {
    "type": "ModuleType",
    "integration_points": ["system1", "system2"],
    "related_tags": ["Tag1", "Tag2"]
}
result = enhanced_bridge.process_mega_tag(mega_tag_data)
```

### Symbolic Cognition (Existing System)
```python
# Use existing symbolic cognition via enhanced bridge
reasoning_result = enhanced_bridge.perform_symbolic_reasoning(
    "Complex problem or data to analyze"
)
```

### Contextual Memory (Existing System)
```python
# Add context to existing enhanced bridge
enhanced_bridge.add_contextual_memory("key", "value")

# Retrieve context from existing enhanced bridge
context = enhanced_bridge.retrieve_contextual_memory("key")
```

## AI Integration Patterns (Existing)

### AI Coordinator Integration
```python
from src.ai.ai_coordinator import KILOFoolishAICoordinator, TaskType

coordinator = KILOFoolishAICoordinator()
result = await coordinator.execute_task(TaskType.CODE_GENERATION, task_data)
```

### ChatDev Adapter Integration
```python
from src.integration.chatdev_llm_adapter import ChatDevLLMAdapter

adapter = ChatDevLLMAdapter()
response = await adapter.process_chatdev_request(role, message, context)
```

## Configuration Patterns (Existing)
```python
from src.setup.secrets import get_config

config = get_config()
api_key = config.get_secret("openai", "api_key")
```
"""

    def _generate_existing_integration_guide(self) -> str:
        """Generate integration guide for existing KILO systems."""
        return """# KILO-FOOLISH Existing Integration Guide

## Working with Existing Infrastructure

### Enhanced Bridge Integration
The Enhanced Bridge is the core integration point:
- Located at `src/copilot/enhanced_bridge.py`
- Provides OmniTag, MegaTag, and symbolic cognition
- Maintains contextual memory across sessions
- Integrates with other KILO systems

### AI Coordinator Integration
- Located at `src/ai/ai_coordinator.py`
- Provides intelligent task routing
- Supports multiple AI backends (Ollama, OpenAI)
- Handles async operations

### ChatDev Adapter Integration
- Located at `src/integration/chatdev_llm_adapter.py`
- Routes ChatDev through local Ollama models
- Provides role-based model mapping
- Includes API fallback mechanisms

### Secrets Management Integration
- Located at `src/setup/secrets.py`
- Secure configuration management
- Environment-aware settings
- API key management with validation

## Development Workflow with Existing Systems

1. **Initialize Enhanced Bridge**
   ```python
   from src.copilot.enhanced_bridge import EnhancedBridge
   bridge = EnhancedBridge()
   ```

2. **Use OmniTag for Documentation**
   ```python
   tag_data = {"purpose": "...", "dependencies": [...]}
   bridge.process_omni_tag(tag_data)
   ```

3. **Leverage AI Coordinator for Tasks**
   ```python
   from src.ai.ai_coordinator import KILOFoolishAICoordinator
   coordinator = KILOFoolishAICoordinator()
   result = await coordinator.execute_task(task_type, data)
   ```

4. **Integrate with ChatDev when Needed**
   ```python
   from src.integration.chatdev_llm_adapter import ChatDevLLMAdapter
   adapter = ChatDevLLMAdapter()
   response = await adapter.process_chatdev_request(role, msg, ctx)
   ```

## Best Practices with Existing Infrastructure
- Always use existing Enhanced Bridge for context management
- Leverage AI Coordinator for intelligent task routing
- Use ChatDev Adapter for multi-agent development tasks
- Follow existing OmniTag/MegaTag patterns
- Integrate with consciousness sync when available
- Use existing secrets management for configuration
"""

    def create_workspace_integration_script(self) -> None:
        """Create script to integrate workspace with existing KILO systems."""
        script_content = '''#!/usr/bin/env python3
"""
KILO-FOOLISH Workspace Integration Script
Integrates current workspace with existing KILO infrastructure
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from copilot.enhanced_bridge import EnhancedBridge
    from ai.ai_coordinator import KILOFoolishAICoordinator
    from integration.chatdev_llm_adapter import ChatDevLLMAdapter

    class WorkspaceKILOIntegration:
        def __init__(self):
            self.bridge = EnhancedBridge()
            self.ai_coordinator = KILOFoolishAICoordinator()
            self.chatdev_adapter = ChatDevLLMAdapter()

        def enhance_current_file(self, file_path: str, content: str) -> None:
            """Enhance current file with KILO context"""
            # Add to enhanced bridge contextual memory
            self.bridge.add_contextual_memory(f"file:{file_path}", content)

            # Process with OmniTag if applicable
            if "OmniTag:" in content:
                # Extract and process OmniTag
                pass

            # Provide enhanced context for Copilot
            return self.bridge.summarize_context()

        async def get_ai_suggestion(self, prompt: str, context: str = ""):
            """Get AI suggestion using existing infrastructure"""
            from ai.ai_coordinator import TaskType

            result = await self.ai_coordinator.execute_task(
                TaskType.CODE_GENERATION,
                {"prompt": prompt, "context": context}
            )
            return result

    # Global integration instance
    workspace_integration = WorkspaceKILOIntegration()

except ImportError as e:
    print(f"KILO infrastructure not available: {e}")
    workspace_integration = None

def enhance_copilot_context(file_path: str = "", content: str = "") -> None:
    """Function to enhance Copilot context"""
    if workspace_integration:
        return workspace_integration.enhance_current_file(file_path, content)
    return {"error": "KILO infrastructure not available"}

async def get_kilo_ai_suggestion(prompt: str, context: str = ""):
    """Function to get AI suggestion via KILO infrastructure"""
    if workspace_integration:
        return await workspace_integration.get_ai_suggestion(prompt, context)
    return {"error": "KILO infrastructure not available"}
'''

        script_path = self.copilot_context_dir / "workspace_integration.py"
        with open(script_path, "w") as f:
            f.write(script_content)

    def run_full_integration(self) -> None:
        """Run full Copilot integration with existing KILO infrastructure."""
        steps = [
            ("Enhancing VS Code settings", self.enhance_vscode_settings_with_kilo),
            ("Generating context files", self.generate_copilot_context_files),
            (
                "Creating workspace integration",
                self.create_workspace_integration_script,
            ),
        ]

        for _step_name, step_func in steps:
            with contextlib.suppress(OSError, FileNotFoundError, PermissionError):
                step_func()


def main() -> None:
    """Main entry point."""
    workspace_root = Path.cwd()
    integration = CopilotKILOIntegration(workspace_root)

    if ENHANCED_BRIDGE_AVAILABLE:
        choice = (
            input("\n🚀 Run full integration with existing KILO infrastructure? (y/n): ")
            .strip()
            .lower()
        )

        if choice == "y":
            integration.run_full_integration()
        else:
            pass
    else:
        pass


if __name__ == "__main__":
    main()
