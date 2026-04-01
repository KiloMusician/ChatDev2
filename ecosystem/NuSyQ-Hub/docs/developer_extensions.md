# CopilotExtension Developer Guide

The `CopilotExtension` API lets developers add domain-specific context and commands to the NuSyQ-Hub Copilot bridge. Each extension can enrich prompts, expose commands, or link to external tools.

## CopilotExtension API

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

class CopilotExtension(ABC):
    """Base class for Copilot bridge extensions"""

    id: str
    name: str
    description: str

    @abstractmethod
    async def activate(self, context: Dict[str, Any]) -> None:
        """Set up resources when the extension is loaded."""

    @abstractmethod
    async def gather_context(self, file: Path, context: Dict[str, Any]) -> str:
        """Return extra prompt context for the given file."""

    async def deactivate(self, context: Dict[str, Any]) -> None:
        """Clean up resources when the extension is unloaded."""

    def commands(self) -> Dict[str, Any]:
        """Optional VS Code commands exposed by the extension."""
        return {}
```

### Lifecycle
1. **activate** – initialize configuration or services.
2. **gather_context** – supply text that augments Copilot prompts.
3. **commands** – (optional) expose IDE commands.
4. **deactivate** – tear down resources.

## Example Extensions

### ChatDev
```python
class ChatDevExtension(CopilotExtension):
    id = "chatdev"
    name = "ChatDev Bridge"
    description = "Expose active ChatDev thread summaries."

    async def gather_context(self, file: Path, context: Dict[str, Any]) -> str:
        summary = await chatdev.summarise_thread()
        return f"ChatDev context:\n{summary}"
```

### Jupyter
```python
class JupyterNotebookExtension(CopilotExtension):
    id = "jupyter"
    name = "Notebook Helper"
    description = "Surface relevant notebook cells."

    async def gather_context(self, file: Path, context: Dict[str, Any]) -> str:
        notebook = Notebook(file)
        return notebook.export_cells(limit=20)
```

### Godot
```python
class GodotExtension(CopilotExtension):
    id = "godot"
    name = "Godot Signals"
    description = "Provide signal and scene summaries."

    async def activate(self, context: Dict[str, Any]) -> None:
        self.project = load_godot_project(context["root"])

    async def gather_context(self, file: Path, context: Dict[str, Any]) -> str:
        return self.project.list_signals()
```

### Obsidian
```python
class ObsidianExtension(CopilotExtension):
    id = "obsidian"
    name = "Vault Reference"
    description = "Reference related notes from an Obsidian vault."

    async def gather_context(self, file: Path, context: Dict[str, Any]) -> str:
        vault = ObsidianVault(context["vault_path"])
        return vault.search_related_notes(file.name)
```

## Registering Extensions

1. Implement a subclass of `CopilotExtension`.
2. Register it with the extension registry:
   ```python
   from copilot.extension_registry import registry
   registry.register(ObsidianExtension())
   ```
3. Optionally add persistent configuration in `config/extension_registry.json`.

## Testing Extensions

Create tests under `tests/extensions/` that instantiate the extension and verify its lifecycle:

```python
def test_obsidian_extension(tmp_path):
    ext = ObsidianExtension()
    asyncio.run(ext.activate({"vault_path": tmp_path}))
    ctx = asyncio.run(ext.gather_context(tmp_path / "note.md", {}))
    assert "Related" in ctx
```

Run tests with:
```bash
pytest tests/extensions/test_obsidian_extension.py
```

A passing test confirms that the extension can be activated and that it generates context without errors.
