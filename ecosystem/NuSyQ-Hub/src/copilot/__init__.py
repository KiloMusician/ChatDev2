"""Utilities for interacting with Copilot-related modules.

This file intentionally uses defensive imports so that `import src.copilot`
succeeds even if optional heavy submodules fail to import at package
initialization time (for example when sqlite or external logging hooks are
unavailable). Callers should handle None return values or ImportError from the
helper `get_enhanced_bridge()` wrapper below.
"""

# Defensive, lazy imports
import logging
from typing import TYPE_CHECKING, Any

OmniTag = {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0",
}

if TYPE_CHECKING:
    from .copilot_enhancement_bridge import (CopilotEnhancementBridge,
                                             EnhancedCopilotBridge)
else:
    CopilotEnhancementBridge = None  # type: ignore[assignment]

_logger = logging.getLogger(__name__)

workspace_enhancer: Any = None
CopilotTaskManager: Any = None
TASK_ROUTER: Any = None
_import_error_msg = None

try:
    # Try eager imports for convenience; if any fail, keep placeholders and
    # expose a helper that raises a clear ImportError when used.
    from . import workspace_enhancer
    from .copilot_enhancement_bridge import (CopilotEnhancementBridge,
                                             get_enhanced_bridge)
    from .task_manager import TASK_ROUTER, CopilotTaskManager
except ImportError as _import_error:
    _import_error_msg = str(_import_error)
    _logger.warning("Partial import of src.copilot failed: %s", _import_error)

    def get_enhanced_bridge(repository_root: str = ".") -> "EnhancedCopilotBridge":
        """Stub that explains why the real bridge isn't available."""
        msg = f"Copilot enhancement bridge unavailable for {repository_root}: {_import_error_msg}"
        raise ImportError(msg)


__all__ = [
    "TASK_ROUTER",
    "CopilotEnhancementBridge",
    "CopilotTaskManager",
    "get_enhanced_bridge",
    "workspace_enhancer",
]
