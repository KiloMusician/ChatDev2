from typing import Any

"""OmniTag: {

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Tagging"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

try:
    from src.copilot.omnitag_system import \
        OmniTagSystem as ImportedCopilotOmniTagSystem
except ImportError:  # pragma: no cover - optional dependency
    ImportedCopilotOmniTagSystem = None

CopilotOmniTagSystem: Any | None = ImportedCopilotOmniTagSystem


class OmniTagSystem:
    """Compatibility wrapper for OmniTagSystem.

    Canonical implementation lives in src/copilot/omnitag_system.py.
    This wrapper preserves legacy methods used by integration layers.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize OmniTagSystem."""
        self._copilot = CopilotOmniTagSystem(*args, **kwargs) if CopilotOmniTagSystem else None
        self.omni_tags: dict[str, str] = {}

    def initialize(self) -> None:
        """Initialize the OmniTag subsystem (legacy no-op)."""
        return None

    def create_omni_tag(self, tag_name: str | dict[str, Any], context: str | None = None) -> None:
        """Create a new OmniTag with the given name and context."""
        if isinstance(tag_name, dict):
            if self._copilot:
                self._copilot.create_omni_tag(tag_name)
                return
            return

        if tag_name in self.omni_tags:
            msg = f"OmniTag '{tag_name}' already exists."
            raise ValueError(msg)
        self.omni_tags[tag_name] = context or ""

    def retrieve_omni_tag(self, tag_name: str) -> str:
        """Retrieve the context associated with the specified OmniTag."""
        if tag_name not in self.omni_tags:
            msg = f"OmniTag '{tag_name}' not found."
            raise KeyError(msg)
        return self.omni_tags[tag_name]

    def update_omni_tag(self, tag_name: str, new_context: str) -> None:
        """Update the context of an existing OmniTag."""
        if tag_name not in self.omni_tags:
            msg = f"OmniTag '{tag_name}' not found."
            raise KeyError(msg)
        self.omni_tags[tag_name] = new_context

    def delete_omni_tag(self, tag_name: str) -> None:
        """Delete the specified OmniTag."""
        if tag_name not in self.omni_tags:
            msg = f"OmniTag '{tag_name}' not found."
            raise KeyError(msg)
        del self.omni_tags[tag_name]

    def list_omni_tags(self) -> dict[str, str]:
        """List all existing OmniTags and their contexts."""
        return self.omni_tags.copy()

    def create_tags(self, input_data: Any) -> list[dict[str, Any]]:
        """Create simple tags from input data for downstream processors."""
        text = str(input_data or "").strip()
        tags: list[dict[str, Any]] = []
        if not text:
            return tags

        tags.append({"tag": "length", "value": len(text)})
        lower_text = text.lower()
        if any(k in lower_text for k in ["bug", "fix", "error"]):
            tags.append({"tag": "category", "value": "debugging"})
        if any(k in lower_text for k in ["optimize", "improve", "refactor"]):
            tags.append({"tag": "category", "value": "optimization"})
        return tags


__all__ = ["OmniTagSystem"]
