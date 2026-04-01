"""GitHub Copilot Extension for NuSyQ-Hub.

Integrated: 2025-10-13 (Task 4 completion).

This extension provides async API integration with GitHub Copilot
including proper timeout handling, error management, and metrics tracking.
"""

from .copilot_extension import CopilotExtension

__all__ = ["CopilotExtension"]
